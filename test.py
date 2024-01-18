import os

# Example file path
file_path = '/path/to/your/file.txt'

# Extracting the file name
file_name = os.path.basename(file_path)

print("File Name:", file_name)