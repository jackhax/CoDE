import threading
import argparse
from utils import send_file

# Configuration Constants
DEFAULT_URL = 'http://127.0.0.1:5000/CoDE/http'

def send_file_in_thread(file_path, url):
    """Wrapper function to run send_file in a separate thread."""
    send_file(file_path, url)

if __name__ == "__main__":
    # Argument parser for URL
    parser = argparse.ArgumentParser(description="Send files to HTTP CoDE server.")
    parser.add_argument("url", nargs="?", default=DEFAULT_URL, help="URL of the server (default: http://127.0.0.1:5000/CoDE/http)")
    parser.add_argument("files", nargs="+", help="List of file paths to send")
    args = parser.parse_args()

    # List of files to send
    files_to_send = args.files

    # Create and start a thread for each file
    threads = []
    for file in files_to_send:
        thread = threading.Thread(target=send_file_in_thread, args=(file, args.url))
        threads.append(thread)
        thread.start()

    # Wait for all threads to complete
    for thread in threads:
        thread.join()

    print("All files have been sent.")
