import json
import os
import shutil

# Define the quarantine directory
quarantine_dir = os.path.expanduser('~/.evoclaw/quarantine/')

# Define the approved directory
approved_dir = os.path.expanduser('~/.evoclaw/approved/')

# Function to merge a file from quarantine to approved
def merge_file(file_path):
    file_hash = os.path.basename(file_path)
    approved_path = os.path.join(approved_dir, file_hash)
    os.makedirs(approved_path, exist_ok=True)
    shutil.copytree(os.path.join(quarantine_dir, file_hash), approved_path)
    return approved_path
