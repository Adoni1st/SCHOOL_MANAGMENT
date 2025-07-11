import json
import struct

def create_header(data):
    """Create a header for the data"""
    header = struct.pack('!I', len(data))
    return header

def send_data(socket, data):
    """Send data through the socket"""
    try:
        # Convert data to JSON string
        json_data = json.dumps(data)
        # Encode to bytes
        data_bytes = json_data.encode('utf-8')
        # Create header
        header = create_header(data_bytes)
        # Send header and data
        socket.sendall(header + data_bytes)
        return True
    except:
        return False

def receive_data(socket):
    """Receive data from the socket"""
    try:
        # Receive header (4 bytes)
        header = socket.recv(4)
        if not header:
            return None
        
        # Unpack header to get data length
        data_length = struct.unpack('!I', header)[0]
        
        # Receive data
        data = b''
        while len(data) < data_length:
            chunk = socket.recv(min(data_length - len(data), 4096))
            if not chunk:
                return None
            data += chunk
        
        # Decode and parse JSON
        json_data = data.decode('utf-8')
        return json.loads(json_data)
    except:
        return None
