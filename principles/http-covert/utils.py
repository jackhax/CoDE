import binascii
import struct
import requests

def crc32(file_path):
    """Calculate the CRC32 checksum of a file and return it as bytes."""
    checksum = 0
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b""):
            checksum = binascii.crc32(chunk, checksum)
    checksum &= 0xffffffff  # Ensures a 32-bit unsigned integer result
    return struct.pack('>I', checksum)

def set_header(chunk_size: int, SEQ: int, ID: bytes, flag: int, ctype: int, file_name: str = None):
	#fail fast
	assert chunk_size >= 0 and chunk_size <= 500, "Invalid chunk_size"
	assert SEQ >= 0 and SEQ < 2**32, "Invalid seq size"
	assert ctype  in [0,1], "Invalid Type"

	assert flag in [0,1,2], "Invalid flag"

	assert type(ID) is bytes and len(ID) == 4, "Invalid ID"

	if flag == 0:
		assert file_name != None, "file name required for flag = 0"
		file_name = file_name.encode('utf-8')
		# file_name += b'\x00'*(256-len(file_name))
	else:
		file_name = b''
	

	chunk_size = int.to_bytes(chunk_size, length=2, byteorder='big')
	SEQ = int.to_bytes(SEQ, length=4, byteorder='big')
	flag = int.to_bytes(flag, length=1, byteorder='big')
	ctype = int.to_bytes(ctype, length=1, byteorder='big')
	

	return chunk_size + SEQ + ID + flag + ctype + file_name

def get_header(byte_data):
	print(len(byte_data))
	chunk_size = int.from_bytes(byte_data[:2])
	SEQ = int.from_bytes(byte_data[2:6])
	ID = int.from_bytes(byte_data[6:10])
	flag = int.from_bytes(byte_data[10:11])
	ctype = int.from_bytes(byte_data[11:12])
	
	if flag == 0:
		file_name = byte_data[12:].decode('utf-8')
	else:
		file_name = None

	return {
		'chunk_size': chunk_size,
		'SEQ': SEQ,
		'ID': ID,
		'flag': flag,
		'type': ctype,
		'file_name': file_name
	}

def send_request_with_csrf(url: str, payload: bytes):
    # Fail-fast validations
    assert isinstance(url, str) and url.startswith("http"), "Invalid URL: URL must be a valid HTTP/HTTPS URL."
    assert isinstance(payload, bytes) and payload, "Invalid CSRF token: Payload must be a non-empty."

    payload = payload.hex()
    
    # Define headers to mimic a browser request, including X-Csrf-Token
    headers = {
        "X-Csrf-Token": payload,
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1"
    }
    
    # Send a GET request with the custom headers
    response = requests.get(url, headers=headers)
    return response