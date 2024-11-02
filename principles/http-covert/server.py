from flask import Flask, jsonify, request
import utils
import struct

app = Flask(__name__)

# Dictionary to hold pending files with their associated IDs
pending = {}

# Basic route for testing
@app.route('/', methods=['GET'])
def home():
    return "Welcome to the CoDE HTTP Server!", 200

# Route to handle CoDE HTTP data with custom header parsing
@app.route('/CoDE/http', methods=['GET'])
def get_data():
    try:
        # Extract and decode the payload from headers
        token = request.headers.get('X-Csrf-Token')
        if not token:
            return jsonify({"error": "Missing X-Csrf-Token"}), 400
        payload = bytes.fromhex(token)

        # Unpack the header (first 12 or 268 bytes depending on flag)
        if len(payload) < 12:
            return jsonify({"error": "Invalid CSRF"}), 400

        # Parse header fields
        chunk_size, seq, crc32_id, flag, data_type = struct.unpack('!H I I B B', payload[:12])

        # Initialize file name only if flag is `0` (init) and header is 268 bytes
        file_name = None
        if flag == 0:
            file_name = payload[12:].decode('utf-8').strip('\x00')

        # Print header info for debugging
        print(f"Header Info: Chunk Size: {chunk_size}, SEQ: {seq}, CRC32 ID: {crc32_id}, Flag: {flag}, Type: {data_type}, File Name: {file_name}")

        # Handle based on the flag
        if flag == 0:  # Init: Start a new file
            if file_name is None:
                return jsonify({"error": "File name missing in init packet"}), 400
            file = open(file_name, 'ab')
            pending[crc32_id] = file
            data = {"message": "File opened for writing", "ID": crc32_id}
            return jsonify(data), 200

        elif flag == 1:  # Payload: Write data to the existing file
            file = pending.get(crc32_id)
            if not file:
                return jsonify({"error": "File not open or ID not found"}), 400

            # Write the remaining data after the header to the file
            file.write(payload[12:])
            data = {"message": "Data chunk appended"}
            return jsonify(data), 200

        elif flag == 2:  # Fin: Close the file
            file = pending.pop(crc32_id, None)
            if file:
                file.close()
                data = {"message": "File closed"}
                return jsonify(data), 200
            else:
                return jsonify({"error": "File not open or ID not found"}), 400

        else:
            return jsonify({"error": "Invalid flag"}), 400

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Run the app
if __name__ == "__main__":
    app.run(host='127.0.0.1', port=5000)
