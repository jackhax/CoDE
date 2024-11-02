import os
import sys

def generate_blob(byte_count, output_file):
    """Generate a blob of random bytes of specified size and write to output file."""
    try:
        # Generate random bytes
        blob_data = os.urandom(byte_count)
        
        # Write to the specified file
        with open(output_file, 'wb') as f:
            f.write(blob_data)
        
        print(f"Blob of {byte_count} bytes written to '{output_file}'")
    
    except Exception as e:
        print(f"Error generating blob: {e}")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python generate_blob.py <byte_count> <output_file>")
        sys.exit(1)

    try:
        byte_count = int(sys.argv[1])
        output_file = sys.argv[2]
        generate_blob(byte_count, output_file)
    except ValueError:
        print("Error: byte_count must be an integer")
        sys.exit(1)
