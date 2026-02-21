import argparse
import os
import sys

# Define the quarantine directory
quarantine_dir = os.path.expanduser('~/.evoclaw/quarantine/')

# Define the approved directory
approved_dir = os.path.expanduser('~/.evoclaw/approved/')

# Function to install a file from quarantine to approved
def install_file(file_path):
    file_hash = os.path.basename(file_path)
    approved_path = os.path.join(approved_dir, file_hash)
    os.makedirs(approved_path, exist_ok=True)
    shutil.copytree(os.path.join(quarantine_dir, file_hash), approved_path)
    return approved_path

# Function to list the files in quarantine
def list_files():
    files = os.listdir(quarantine_dir)
    return files

# Function to approve a file in quarantine
def approve_file(file_path):
    file_hash = os.path.basename(file_path)
    approved_path = os.path.join(approved_dir, file_hash)
    os.makedirs(approved_path, exist_ok=True)
    shutil.copytree(os.path.join(quarantine_dir, file_hash), approved_path)
    return approved_path

# Function to reject a file in quarantine
def reject_file(file_path):
    file_hash = os.path.basename(file_path)
    os.remove(os.path.join(quarantine_dir, file_hash))
