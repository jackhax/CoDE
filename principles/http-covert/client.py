from random import randint
from tqdm import tqdm  # Import tqdm for progress bars
from utils import send_file

# Configuration Constants
URL = 'http://127.0.0.1:5000/CoDE/http'


# send_file('blob_10mb')

import threading

# Define the configuration constants and send_file function here
# (Ensure this section has the previous code provided with send_file function)

def send_file_in_thread(file_path, url):
    """Wrapper function to run send_file in a separate thread."""
    send_file(file_path, url)

# List of files to send
files_to_send = ['blob']  # Add your file paths here

# Create and start a thread for each file
threads = []
for file in files_to_send:
    thread = threading.Thread(target=send_file_in_thread, args=(file,URL))
    threads.append(thread)
    thread.start()

# Wait for all threads to complete
for thread in threads:
    thread.join()

# print("All files have been sent.")