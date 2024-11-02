from random import randint
import utils
import os
import sys

# Configuration Constants
FILE_PATH = '../chunking/secret.txt'
URL = 'http://127.0.0.1:5000/CoDE/http'
MIN_CHUNK_SIZE = 64           # Minimum chunk size in bytes
MAX_CHUNK_SIZE = 500          # Maximum chunk size in bytes
WINDOW_SIZE = 2048            # Sliding window size in bytes (2KB)
INIT_FLAG = 0                 # Flag for init packet
PAYLOAD_FLAG = 1              # Flag for payload packet
FIN_FLAG = 2                  # Flag for fin packet
CTYPE_STDOUT = 0              # Type for stdout (not used here but defined for completeness)
CTYPE_BLOB = 1                # Type for blob data

# Generate CRC32 ID and file name
crc = utils.crc32(FILE_PATH)
file_name = os.path.basename(FILE_PATH)

try:
    # Initialize sequence number and buffer
    seq = 0
    buffer = []
    acked_chunks = set()  # Track acknowledged sequence numbers

    # Open the file and send the init packet
    with open(FILE_PATH, 'rb') as file:
        
        # Send the init packet with INIT_FLAG
        init_header = utils.set_header(0, seq, crc, INIT_FLAG, CTYPE_BLOB, file_name)
        response = utils.send_request_with_csrf(URL, init_header)
        
        if response.status_code != 200:
            print(f"Init packet failed with status code: {response.status_code}")
            sys.exit(1)
        print(f"Init packet sent successfully for file '{file_name}' with CRC32 ID {crc}")
        
        seq += 1

        # Fill the initial buffer with up to WINDOW_SIZE of chunks
        while sum(len(chunk) for _, chunk in buffer) < WINDOW_SIZE:
            chunk_size = randint(MIN_CHUNK_SIZE, MAX_CHUNK_SIZE)
            chunk = file.read(chunk_size)
            if not chunk:
                break
            payload_header = utils.set_header(len(chunk), seq, crc, PAYLOAD_FLAG, CTYPE_BLOB)
            buffer.append((seq, payload_header + chunk))
            seq += 1

        # Send the initial window of chunks and handle acknowledgments
        while buffer:
            for seq_num, payload in buffer:
                if seq_num not in acked_chunks:
                    response = utils.send_request_with_csrf(URL, payload)
                    acked_seq = utils.receive_acknowledgment(response)
                    if acked_seq is not None:
                        print(f"Acknowledged packet with seq {acked_seq}")
                        acked_chunks.add(acked_seq)

            # Remove acknowledged chunks from the buffer
            buffer = [chunk for chunk in buffer if chunk[0] not in acked_chunks]

            # Refill buffer up to WINDOW_SIZE with new chunks
            while sum(len(chunk) for _, chunk in buffer) < WINDOW_SIZE:
                chunk_size = randint(MIN_CHUNK_SIZE, MAX_CHUNK_SIZE)
                chunk = file.read(chunk_size)
                if not chunk:
                    break
                payload_header = utils.set_header(len(chunk), seq, crc, PAYLOAD_FLAG, CTYPE_BLOB)
                buffer.append((seq, payload_header + chunk))
                response = utils.send_request_with_csrf(URL, payload_header + chunk)
                acked_seq = utils.receive_acknowledgment(response)
                if acked_seq is not None:
                    print(f"Acknowledged packet with seq {acked_seq}")
                    acked_chunks.add(acked_seq)
                seq += 1

        # Send the fin packet with FIN_FLAG after all chunks are acknowledged
        fin_header = utils.set_header(0, seq, crc, FIN_FLAG, CTYPE_BLOB)
        response = utils.send_request_with_csrf(URL, fin_header)
        if response.status_code != 200:
            print(f"Fin packet failed with status code: {response.status_code}")
            sys.exit(1)
        print("Fin packet sent successfully, file transmission completed.")

except Exception as e:
    print(f"An error occurred: {e}")
    sys.exit(1)
