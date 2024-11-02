from random import randint
file_path = 'secret.txt'

min_chunk_size = 64
max_chunk_size = 512

id = 0

with open(file_path, 'rb') as file:
    while True:
        chunk_size = randint(min_chunk_size, max_chunk_size + 1)
        chunk = file.read(chunk_size)
        
        if not chunk:
            break
        
        id += 1
        with open(f'chunks/{file_path}_{id}', 'wb') as chunk_bin:
            print(chunk_size)
            chunk_bin.write(int.to_bytes(chunk_size, length=4, byteorder='big') + chunk)

