import socket

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.settimeout(1)
result = sock.connect_ex(('127.0.0.1', 8189))
sock.close()
if result == 0:
    print("Port 8189 is open")
else:
    print("Port 8189 is closed")