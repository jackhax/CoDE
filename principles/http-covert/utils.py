import binascii
import struct
import requests
import utils
import os
import sys
import time
from random import randint
from tqdm import tqdm

# Constants
MIN_CHUNK_SIZE_1 = 0        # Minimum chunk size for payloads
MIN_CHUNK_SIZE_2 = 64
MAX_CHUNK_SIZE = 500       # Maximum chunk size for payloads
WINDOW_SIZE = 2048         # Sliding window size in bytes (2KB)
TIMEOUT = 5                # Retransmission timeout in seconds
FIN_RETRY_ATTEMPTS = 3     # Number of retry attempts for the FIN packet

# Packet Flags
INIT_FLAG = 0              # Initialization flag for the first packet
PAYLOAD_FLAG = 1           # Payload flag for regular data packets
FIN_FLAG = 2               # Finalization flag to close file transfer

# Data Types
CTYPE_STDOUT = 0           # Type for stdout
CTYPE_BLOB = 1             # Type for binary data transfer


def crc32(file_path):
    """Calculate the CRC32 checksum of a file and return it as a 4-byte packed integer."""
    checksum = 0
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b""):
            checksum = binascii.crc32(chunk, checksum)
    return struct.pack('>I', checksum & 0xffffffff)  # Ensure 32-bit unsigned integer

def set_header(chunk_size, seq, crc_id, flag, ctype, file_name=None):
    """Constructs a packet header with optional file name for init (flag=0) packets."""
    assert MIN_CHUNK_SIZE_1 <= chunk_size <= MAX_CHUNK_SIZE, "Invalid chunk_size"
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


def send_file(file_path, url, min_chunk_size=MIN_CHUNK_SIZE_2, max_chunk_size=MAX_CHUNK_SIZE, window_size=WINDOW_SIZE, timeout=TIMEOUT, fin_retry_attempts=FIN_RETRY_ATTEMPTS):
    """Sends a file in chunks over HTTP with retransmission and windowing."""

    # Generate CRC32 ID and file name
    crc = utils.crc32(file_path)
    file_name = os.path.basename(file_path)
    
    try:
        # Initialize sequence number, buffer, and acknowledgment tracking
        seq = 0
        buffer = []
        acked_chunks = set()  # Track acknowledged sequence numbers
        sent_chunks = {}      # Dictionary to track sent packets and timestamps

        # Open the file and get the total file size for progress tracking
        total_size = os.path.getsize(file_path)
        with open(file_path, 'rb') as file:
            
            # Send the init packet with flag=INIT_FLAG
            init_header = utils.set_header(0, seq, crc, INIT_FLAG, CTYPE_BLOB, file_name)
            response = utils.send_request_with_csrf(url, init_header)
            
            if response.status_code != 200:
                print(f"Init packet failed with status code: {response.status_code}")
                return
            print(f"Init packet sent successfully for file '{file_name}' with CRC32 ID {crc}")
            
            seq += 1

            # Initialize progress bar for packet sending
            with tqdm(total=total_size, unit="B", unit_scale=True, desc=f"Sending {file_name}") as pbar:
                
                # Fill the initial buffer with up to WINDOW_SIZE of chunks
                while True:
                    # Check if buffer size is full (2KB) or end of file
                    while sum(len(chunk) for _, chunk in buffer) < window_size:
                        chunk_size = randint(min_chunk_size, max_chunk_size)
                        chunk = file.read(chunk_size)
                        if not chunk:  # End of file
                            print("End of file reached.")
                            break
                        payload_header = utils.set_header(len(chunk), seq, crc, PAYLOAD_FLAG, CTYPE_BLOB)
                        buffer.append((seq, payload_header + chunk))
                        sent_chunks[seq] = {'data': payload_header + chunk, 'timestamp': time.time()}
                        seq += 1

                    # Send each chunk in the buffer
                    for seq_num, payload in list(sent_chunks.items()):
                        if seq_num not in acked_chunks:
                            response = utils.send_request_with_csrf(url, payload['data'])
                            acked_seq = utils.receive_acknowledgment(response)
                            if acked_seq is not None:
                                acked_chunks.add(acked_seq)
                                sent_chunks.pop(acked_seq, None)
                                # Update progress bar with acknowledged data size
                                pbar.update(len(payload['data']))
                            elif time.time() - payload['timestamp'] > timeout:
                                # Retransmit chunk if timeout exceeded
                                response = utils.send_request_with_csrf(url, payload['data'])
                                sent_chunks[seq_num]['timestamp'] = time.time()

                    # Remove acknowledged chunks from buffer
                    buffer = [chunk for chunk in buffer if chunk[0] not in acked_chunks]

                    # If buffer and file are exhausted, proceed to send FIN
                    if not buffer and not chunk:
                        print("All chunks acknowledged, preparing to send FIN packet.")
                        break

                # Send the fin packet with flag=FIN_FLAG after all chunks are acknowledged
                fin_header = utils.set_header(0, seq, crc, FIN_FLAG, CTYPE_BLOB)
                fin_sent = False
                attempts = 0

                while not fin_sent and attempts < fin_retry_attempts:
                    response = utils.send_request_with_csrf(url, fin_header)
                    if response.status_code == 200:
                        print("Fin packet sent successfully, file transmission completed.")
                        fin_sent = True
                    else:
                        print(f"Fin packet failed with status code: {response.status_code}, retrying...")
                        attempts += 1
                        time.sleep(timeout)

                if not fin_sent:
                    print("Failed to send Fin packet after multiple attempts.")
                    sys.exit(1)

    except Exception as e:
        print(f"An error occurred: {e}")
        sys.exit(1)