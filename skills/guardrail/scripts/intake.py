import hashlib
import json
import os

# Define the quarantine directory
quarantine_dir = os.path.expanduser('~/.evoclaw/quarantine/')

# Define the blacklist and approved files
blacklist_file = os.path.join(quarantine_dir, 'blacklist.json')
approved_file = os.path.join(quarantine_dir, 'approved.json')

# Load the blacklist and approved lists
try:
    with open(blacklist_file, 'r') as f:
        blacklist = json.load(f)
except FileNotFoundError:
    blacklist = []

try:
    with open(approved_file, 'r') as f:
        approved = json.load(f)
except FileNotFoundError:
    approved = []

# Function to compute the SHA256 of a file
def compute_sha256(file_path):
    with open(file_path, 'rb') as f:
        return hashlib.sha256(f.read()).hexdigest()

# Function to check if a file is blacklisted
def is_blacklisted(file_path):
    file_hash = compute_sha256(file_path)
    return file_hash in blacklist

# Function to check if a file is approved
def is_approved(file_path):
    file_hash = compute_sha256(file_path)
    return file_hash in approved

# Function to add a file to the quarantine directory
def add_to_quarantine(file_path):
    file_hash = compute_sha256(file_path)
    quarantine_path = os.path.join(quarantine_dir, file_hash)
    os.makedirs(quarantine_path, exist_ok=True)
    with open(os.path.join(quarantine_path, 'metadata.json'), 'w') as f:
        json.dump({'file_path': file_path, 'file_hash': file_hash}, f)
    return file_hash
