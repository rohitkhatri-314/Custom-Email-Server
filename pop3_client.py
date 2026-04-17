import socket
import time

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect(("localhost", 1110))
print(s.recv(1024).decode())

s.sendall(b"USER khatri@example.com\r\n")
print(s.recv(1024).decode())

s.sendall(b"PASS secret\r\n")
print(s.recv(1024).decode())

s.sendall(b"LIST\r\n")
print(s.recv(4096).decode())

s.sendall(b"RETR 2\r\n")

# IMPORTANT: Wait longer and receive more data
time.sleep(1)  # Give server time to send
response = s.recv(8192).decode()  # Bigger buffer
print("=== EMAIL ===")
print(response)

s.sendall(b"QUIT\r\n")
s.close()