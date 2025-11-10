#!/usr/bin/env python3
"""
Simple TCP Chat Server
Handles multiple clients, login, messaging, and disconnects.
"""

import socket
import threading
import time
import os
import sys
from datetime import datetime


class ChatServer:
    def __init__(self, host='0.0.0.0', port=4000):
        self.host = host
        self.port = port
        self.server_socket = None
        self.clients = {}  # {socket: {'username': str, 'last_activity': timestamp}}
        self.clients_lock = threading.Lock()
        self.running = False
        self.idle_timeout = 60  # seconds
        
    def start(self):
        """Start the chat server."""
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        try:
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(10)  # Support up to 10 queued connections
            self.running = True
            
            print(f"[SERVER] Chat server started on {self.host}:{self.port}")
            print(f"[SERVER] Waiting for connections...")
            
            # Start idle timeout checker thread
            timeout_thread = threading.Thread(target=self._check_idle_timeouts, daemon=True)
            timeout_thread.start()
            
            # Accept client connections
            while self.running:
                try:
                    client_socket, client_address = self.server_socket.accept()
                    print(f"[SERVER] New connection from {client_address}")
                    
                    # Handle client in a new thread
                    client_thread = threading.Thread(
                        target=self._handle_client,
                        args=(client_socket, client_address),
                        daemon=True
                    )
                    client_thread.start()
                    
                except Exception as e:
                    if self.running:
                        print(f"[ERROR] Error accepting connection: {e}")
                        
        except Exception as e:
            print(f"[ERROR] Failed to start server: {e}")
            sys.exit(1)
            
    def stop(self):
        """Stop the chat server."""
        print("\n[SERVER] Shutting down...")
        self.running = False
        
        # Close all client connections
        with self.clients_lock:
            for client_socket in list(self.clients.keys()):
                try:
                    client_socket.close()
                except:
                    pass
                    
        # Close server socket
        if self.server_socket:
            self.server_socket.close()
            
        print("[SERVER] Server stopped.")
        
    def _handle_client(self, client_socket, client_address):
        """Handle a single client connection."""
        username = None
        
        try:
            # Wait for LOGIN command
            while True:
                data = self._receive_message(client_socket)
                if not data:
                    print(f"[SERVER] Client {client_address} disconnected before login")
                    client_socket.close()
                    return
                    
                command = data.strip()
                
                if command.startswith('LOGIN '):
                    username = command[6:].strip()
                    
                    if not username:
                        self._send_message(client_socket, "ERR invalid-username\n")
                        continue
                        
                    # Check if username is already taken
                    with self.clients_lock:
                        if any(c['username'] == username for c in self.clients.values()):
                            self._send_message(client_socket, "ERR username-taken\n")
                            continue
                            
                        # Register the client
                        self.clients[client_socket] = {
                            'username': username,
                            'last_activity': time.time()
                        }
                        
                    self._send_message(client_socket, "OK\n")
                    print(f"[SERVER] User '{username}' logged in from {client_address}")
                    break
                else:
                    self._send_message(client_socket, "ERR must-login-first\n")
                    
            # Handle messages after login
            while self.running:
                data = self._receive_message(client_socket)
                if not data:
                    break
                    
                # Update last activity
                with self.clients_lock:
                    if client_socket in self.clients:
                        self.clients[client_socket]['last_activity'] = time.time()
                        
                command = data.strip()
                
                if command.startswith('MSG '):
                    message_text = command[4:].strip()
                    if message_text:
                        self._broadcast_message(username, message_text)
                        print(f"[MSG] {username}: {message_text}")
                        
                elif command == 'WHO':
                    self._send_user_list(client_socket)
                    
                elif command.startswith('DM '):
                    # Parse DM command: DM <username> <text>
                    parts = command[3:].strip().split(' ', 1)
                    if len(parts) == 2:
                        target_username, dm_text = parts
                        self._send_direct_message(username, target_username, dm_text)
                    else:
                        self._send_message(client_socket, "ERR invalid-dm-format\n")
                        
                elif command == 'PING':
                    self._send_message(client_socket, "PONG\n")
                    
                else:
                    self._send_message(client_socket, "ERR unknown-command\n")
                    
        except Exception as e:
            print(f"[ERROR] Error handling client {username or client_address}: {e}")
            
        finally:
            # Clean up on disconnect
            self._handle_disconnect(client_socket, username)
            
    def _handle_disconnect(self, client_socket, username):
        """Handle client disconnect."""
        with self.clients_lock:
            if client_socket in self.clients:
                username = self.clients[client_socket]['username']
                del self.clients[client_socket]
                
        try:
            client_socket.close()
        except:
            pass
            
        if username:
            print(f"[SERVER] User '{username}' disconnected")
            self._broadcast_info(f"{username} disconnected")
            
    def _broadcast_message(self, sender_username, message_text):
        """Broadcast a message to all connected clients."""
        message = f"MSG {sender_username} {message_text}\n"
        
        with self.clients_lock:
            for client_socket in list(self.clients.keys()):
                try:
                    self._send_message(client_socket, message)
                except Exception as e:
                    print(f"[ERROR] Failed to send to {self.clients[client_socket]['username']}: {e}")
                    
    def _broadcast_info(self, info_text):
        """Broadcast an info message to all connected clients."""
        message = f"INFO {info_text}\n"
        
        with self.clients_lock:
            for client_socket in list(self.clients.keys()):
                try:
                    self._send_message(client_socket, message)
                except:
                    pass
                    
    def _send_direct_message(self, sender_username, target_username, message_text):
        """Send a direct message to a specific user."""
        with self.clients_lock:
            # Find target user's socket
            target_socket = None
            for client_socket, info in self.clients.items():
                if info['username'] == target_username:
                    target_socket = client_socket
                    break
                    
            if target_socket:
                message = f"DM {sender_username} {message_text}\n"
                try:
                    self._send_message(target_socket, message)
                    print(f"[DM] {sender_username} -> {target_username}: {message_text}")
                except Exception as e:
                    print(f"[ERROR] Failed to send DM: {e}")
            else:
                # Send error to sender
                sender_socket = None
                for client_socket, info in self.clients.items():
                    if info['username'] == sender_username:
                        sender_socket = client_socket
                        break
                if sender_socket:
                    self._send_message(sender_socket, f"ERR user-not-found\n")
                    
    def _send_user_list(self, client_socket):
        """Send list of active users to a client."""
        with self.clients_lock:
            for info in self.clients.values():
                message = f"USER {info['username']}\n"
                try:
                    self._send_message(client_socket, message)
                except:
                    pass
                    
    def _check_idle_timeouts(self):
        """Check for idle clients and disconnect them."""
        while self.running:
            time.sleep(10)  # Check every 10 seconds
            
            current_time = time.time()
            with self.clients_lock:
                for client_socket, info in list(self.clients.items()):
                    if current_time - info['last_activity'] > self.idle_timeout:
                        print(f"[SERVER] User '{info['username']}' timed out due to inactivity")
                        try:
                            self._send_message(client_socket, "INFO idle-timeout\n")
                            threading.Thread(
                                target=self._handle_disconnect,
                                args=(client_socket, info['username']),
                                daemon=True
                            ).start()
                        except:
                            pass
                            
    def _send_message(self, client_socket, message):
        """Send a message to a client socket."""
        try:
            client_socket.sendall(message.encode('utf-8'))
        except Exception as e:
            raise e
            
    def _receive_message(self, client_socket):
        """Receive a message from a client socket."""
        try:
            # Receive data in chunks until we get a newline
            data = b''
            while b'\n' not in data:
                chunk = client_socket.recv(1024)
                if not chunk:
                    return None
                data += chunk
                
            # Return the first line (up to newline)
            line = data.split(b'\n', 1)[0]
            return line.decode('utf-8')
        except Exception as e:
            return None


def main():
    """Main entry point."""
    # Get port from environment variable or command-line argument
    port = 4000
    
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
        except ValueError:
            print(f"Error: Invalid port number '{sys.argv[1]}'")
            sys.exit(1)
    elif 'CHAT_PORT' in os.environ:
        try:
            port = int(os.environ['CHAT_PORT'])
        except ValueError:
            print(f"Error: Invalid CHAT_PORT value '{os.environ['CHAT_PORT']}'")
            sys.exit(1)
            
    # Create and start server
    server = ChatServer(port=port)
    
    try:
        server.start()
    except KeyboardInterrupt:
        server.stop()


if __name__ == '__main__':
    main()

