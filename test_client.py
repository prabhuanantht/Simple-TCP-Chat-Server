#!/usr/bin/env python3
"""
Simple test client for the chat server.
Usage: python3 test_client.py <username> [port]
"""

import socket
import sys
import threading


class ChatClient:
    def __init__(self, username, host='localhost', port=4000):
        self.username = username
        self.host = host
        self.port = port
        self.socket = None
        self.running = False
        
    def connect(self):
        """Connect to the chat server."""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((self.host, self.port))
            print(f"Connected to {self.host}:{self.port}")
            
            # Send login
            self.send(f"LOGIN {self.username}")
            response = self.receive()
            
            if response == "OK":
                print(f"Logged in as {self.username}")
                self.running = True
                return True
            else:
                print(f"Login failed: {response}")
                self.socket.close()
                return False
                
        except Exception as e:
            print(f"Connection failed: {e}")
            return False
            
    def send(self, message):
        """Send a message to the server."""
        try:
            self.socket.sendall(f"{message}\n".encode('utf-8'))
        except Exception as e:
            print(f"Send failed: {e}")
            self.running = False
            
    def receive(self):
        """Receive a message from the server."""
        try:
            data = b''
            while b'\n' not in data:
                chunk = self.socket.recv(1024)
                if not chunk:
                    return None
                data += chunk
            return data.split(b'\n', 1)[0].decode('utf-8')
        except Exception as e:
            return None
            
    def receive_loop(self):
        """Continuously receive messages from the server."""
        while self.running:
            message = self.receive()
            if message:
                print(f"< {message}")
            else:
                print("Disconnected from server")
                self.running = False
                break
                
    def run(self):
        """Run the chat client."""
        if not self.connect():
            return
            
        # Start receive thread
        receive_thread = threading.Thread(target=self.receive_loop, daemon=True)
        receive_thread.start()
        
        # Main input loop
        print("\nCommands:")
        print("  MSG <text>           - Send a message")
        print("  WHO                  - List users")
        print("  DM <user> <text>     - Direct message")
        print("  PING                 - Ping server")
        print("  quit                 - Exit")
        print()
        
        try:
            while self.running:
                try:
                    user_input = input("> ")
                    
                    if user_input.lower() == 'quit':
                        break
                        
                    if user_input.strip():
                        self.send(user_input)
                        
                except EOFError:
                    break
                    
        except KeyboardInterrupt:
            print("\nExiting...")
            
        finally:
            self.running = False
            if self.socket:
                self.socket.close()


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 test_client.py <username> [port]")
        sys.exit(1)
        
    username = sys.argv[1]
    port = int(sys.argv[2]) if len(sys.argv) > 2 else 4000
    
    client = ChatClient(username, port=port)
    client.run()


if __name__ == '__main__':
    main()

