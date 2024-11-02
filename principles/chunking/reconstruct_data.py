import os

chunks_dir = 'chunks'

chunk_names = os.listdir(chunks_dir)

# Filter out only files (exclude directories)
chunk_names = [f for f in chunk_names if os.path.isfile(os.path.join(chunks_dir, f))]

# Sort the list of file names
chunk_names.sort()

print(chunk_names)

file_name = chunk_names[0].split('_')[0]

with open(file_name,'wb') as file:
	for chunk_file in chunk_names:
		with open(os.path.join(chunks_dir,chunk_file),'rb') as chunk:
			chunk_size = int.from_bytes(chunk.read(4))
			file.write(chunk.read())