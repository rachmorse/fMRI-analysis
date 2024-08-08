    
import tarfile
import os

# Define paths
tarball_path = '/home/rachel/Downloads/freesurfer-Linux-centos6_x86_64-stable-pub-v6.0.0.tar.gz'
extract_path = os.path.expanduser('~/freesurfer')

# create the target directory if it doesn't exist
os.makedirs(extract_path, exist_ok=True)

# Extract
with tarfile.open(tarball_path, 'r:gz') as tar:
    tar.extractall(path=extract_path)

print("Extraction completed!")