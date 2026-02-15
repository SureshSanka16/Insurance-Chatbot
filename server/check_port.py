import socket

# Test if port 8000 is listening
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.settimeout(2)
result = sock.connect_ex(('localhost', 8000))
sock.close()

if result == 0:
    print("✅ Port 8000 is OPEN and listening")
else:
    print(f"❌ Port 8000 is CLOSED (error code: {result})")
