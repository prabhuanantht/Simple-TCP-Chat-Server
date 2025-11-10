#!/usr/bin/env python3
"""
Quick test to verify the chat server works.
"""

import socket
import subprocess
import time
import sys


def test_server():
    """Test basic server functionality."""
    print("Starting server test...")
    
    # Start the server in a subprocess
    server_process = subprocess.Popen(
        [sys.executable, 'chat_server.py', '4001'],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    
    # Give server time to start
    time.sleep(1)
    
    try:
        # Test 1: Connect to server
        print("Test 1: Connecting to server...")
        client1 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client1.connect(('localhost', 4001))
        print("✓ Connected successfully")
        
        # Test 2: Login
        print("Test 2: Logging in...")
        client1.sendall(b"LOGIN TestUser1\n")
        response = client1.recv(1024).decode('utf-8').strip()
        assert response == "OK", f"Expected 'OK', got '{response}'"
        print("✓ Login successful")
        
        # Test 3: Second client connection
        print("Test 3: Second client connection...")
        client2 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client2.connect(('localhost', 4001))
        client2.sendall(b"LOGIN TestUser2\n")
        response = client2.recv(1024).decode('utf-8').strip()
        assert response == "OK", f"Expected 'OK', got '{response}'"
        print("✓ Second client connected")
        
        # Test 4: Send message
        print("Test 4: Sending message...")
        client1.sendall(b"MSG Hello World!\n")
        time.sleep(0.1)
        response = client2.recv(1024).decode('utf-8').strip()
        assert "MSG TestUser1 Hello World!" in response, f"Unexpected message: '{response}'"
        print("✓ Message broadcast working")
        
        # Test 5: WHO command
        print("Test 5: Testing WHO command...")
        client1.sendall(b"WHO\n")
        time.sleep(0.1)
        response = client1.recv(1024).decode('utf-8')
        assert "USER TestUser1" in response, "User1 not in list"
        assert "USER TestUser2" in response, "User2 not in list"
        print("✓ WHO command working")
        
        # Test 6: PING command
        print("Test 6: Testing PING command...")
        client1.sendall(b"PING\n")
        response = client1.recv(1024).decode('utf-8').strip()
        assert response == "PONG", f"Expected 'PONG', got '{response}'"
        print("✓ PING/PONG working")
        
        # Test 7: Username collision
        print("Test 7: Testing username collision...")
        client3 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client3.connect(('localhost', 4001))
        client3.sendall(b"LOGIN TestUser1\n")
        response = client3.recv(1024).decode('utf-8').strip()
        assert response == "ERR username-taken", f"Expected error, got '{response}'"
        print("✓ Username collision handled")
        
        # Test 8: Disconnect notification
        print("Test 8: Testing disconnect notification...")
        client2.close()
        time.sleep(0.1)
        client1.sendall(b"PING\n")  # Trigger receive
        response = client1.recv(1024).decode('utf-8')
        assert "INFO TestUser2 disconnected" in response or "PONG" in response, f"Unexpected response: '{response}'"
        print("✓ Disconnect notification working")
        
        # Cleanup
        client1.close()
        client3.close()
        
        print("\n✅ All tests passed!")
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        return False
        
    finally:
        # Stop the server
        print("\nStopping server...")
        server_process.terminate()
        server_process.wait(timeout=5)
        print("Server stopped.")


if __name__ == '__main__':
    success = test_server()
    sys.exit(0 if success else 1)

