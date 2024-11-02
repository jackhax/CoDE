from flask import Flask, jsonify, request
import utils
import struct
import os
import logging

app = Flask(__name__)
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

# Constants for flag types and buffer size
INIT_FLAG = 0                # Flag for init packet
PAYLOAD_FLAG = 1             # Flag for payload packet
FIN_FLAG = 2                 # Flag for fin packet
WINDOW_SIZE = 2048           # Buffer size in bytes (2KB)
CTYPE_STDOUT = 0             # Type for stdout (not used here but defined for completeness)
CTYPE_BLOB = 1               # Type for blob data

# Dictionary to hold pending files and buffers
pending_files = {}
buffers = {}

def generate_unique_filename(filename):
    """Generates a unique filename by appending _1, _2, etc., if the file already exists."""
    base, ext = os.path.splitext(filename)
    counter = 1
    unique_filename = filename
    
    while os.path.exists(unique_filename):
        unique_filename = f"{base}_{counter}{ext}"
        counter += 1
    
    return unique_filename

@app.route('/CoDE/http', methods=['GET'])
def get_data():
    try:
        # Retrieve and decode the CSRF token (payload)
        token = request.headers.get('X-Csrf-Token')
        if not token:
            return jsonify({"error": "Missing X-Csrf-Token"}), 400
        payload = bytes.fromhex(token)

        # Unpack header (first 12 bytes)
        if len(payload) < 12:
            return jsonify({"error": "Invalid CSRF"}), 400
        chunk_size, seq, crc32_id, flag, data_type = struct.unpack('!H I I B B', payload[:12])

        # Handle based on the flag
        if flag == INIT_FLAG:  # Init packet
            original_filename = payload[12:].decode('utf-8').strip('\x00')
            unique_filename = generate_unique_filename(original_filename)
            
            # Open file with a unique name and store the file handler in pending_files
            pending_files[crc32_id] = open(unique_filename, 'ab')
            buffers[crc32_id] = b""
            
            print(f"New file initialized: {unique_filename} (ID: {crc32_id})")
            return jsonify({"message": "File opened for writing", "ID": crc32_id, "filename": unique_filename}), 200

        elif flag == PAYLOAD_FLAG:  # Payload packet
            if crc32_id not in pending_files:
                return jsonify({"error": "File not open or ID not found"}), 400
            
            # Store payload in buffer
            buffers[crc32_id] += payload[12:]
            if len(buffers[crc32_id]) >= WINDOW_SIZE:
                pending_files[crc32_id].write(buffers[crc32_id])
                buffers[crc32_id] = b""
            
            # print(f"Received PAYLOAD packet, seq: {seq}, ID: {crc32_id}")
            return jsonify({"message": "Data chunk received", "seq": seq}), 200

        elif flag == FIN_FLAG:  # Fin packet
            file = pending_files.pop(crc32_id, None)
            if file:
                file.write(buffers.pop(crc32_id, b""))  # Write remaining buffer
                file.close()
                
                print(f"File transfer complete: {file.name} (ID: {crc32_id})")
                return jsonify({"message": "File closed"}), 200
            else:
                return jsonify({"error": "File not open or ID not found"}), 400

        else:
            return jsonify({"error": "Invalid flag"}), 400

    except Exception as e:
        print(f"Server error: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host='127.0.0.1', port=5000)
