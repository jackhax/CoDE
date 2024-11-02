import binascii
import struct

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
	assert chunk_size >=52 and chunk_size <= 500, "Invalid chunk_size"
	assert SEQ > 0 and SEQ < 2**32, "Invalid seq size"
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
	ID = byte_data[6:10]
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

ID = crc32('secret.txt')
header = set_header(56,1,ID,0,1,'secret.txt')
print(get_header(header))