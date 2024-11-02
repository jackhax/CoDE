from random import randint
import utils
import os
import sys

# Configuration
file_path = '../chunking/secret.txt'
url = 'http://127.0.0.1:5000/CoDE/http'
min_chunk_size = 64
max_chunk_size = 500

# Generate CRC32 ID and file name
crc = utils.crc32(file_path)
file_name = os.path.basename(file_path)

try:
    # Initialize the sequence number
    seq = 0

    # Open the file and send the init packet
    with open(file_path, 'rb') as file:
        
        # Send the init packet with flag=0 (init)
        init_header = utils.set_header(0, seq, crc, 0, 1, file_name)
        response = utils.send_request_with_csrf(url, init_header)
        
        # Check if init packet was successful
        if response.status_code != 200:
            print(f"Init packet failed with status code: {response.status_code}")
            sys.exit(1)
        print(f"Init packet sent successfully for file '{file_name}' with CRC32 ID {crc}")

        # Increment sequence number
        seq += 1

        # Read and send file chunks
        while True:
            # Generate a random chunk size
            chunk_size = randint(min_chunk_size, max_chunk_size)
            print(chunk_size)
            # Read a chunk from the file
            chunk = file.read(chunk_size)
            
            # If no more data, break the loop
            if not chunk:
                break
            
            # Set header with flag=1 (payload)
            payload_header = utils.set_header(len(chunk), seq, crc, 1, 1)
            payload = payload_header + chunk
            
            # Send the payload packet
            response = utils.send_request_with_csrf(url, payload)
            
            # Check if payload packet was successful
            if response.status_code != 200:
                print(f"Payload packet failed at sequence {seq} with status code: {response.status_code}")
                sys.exit(1)
            print(f"Payload packet {seq} sent with chunk size {len(chunk)}")

            # Increment sequence number for the next chunk
            seq += 1

        # Send the fin packet with flag=2 (fin)
        fin_header = utils.set_header(0, seq, crc, 2, 1)
        response = utils.send_request_with_csrf(url, fin_header)

        # Check if fin packet was successful
        if response.status_code != 200:
            print(f"Fin packet failed with status code: {response.status_code}")
            sys.exit(1)
        print("Fin packet sent successfully, file transmission completed.")

except Exception as e:
    print(f"An error occurred: {e}")
    sys.exit(1)
