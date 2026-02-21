import json
import os
import re

# Define the quarantine directory
quarantine_dir = os.path.expanduser('~/.evoclaw/quarantine/')

# Define the scan rules file
scan_rules_file = os.path.join(os.path.dirname(__file__), 'config/scan_rules.json')

# Load the scan rules
with open(scan_rules_file, 'r') as f:
    scan_rules = json.load(f)

# Function to scan a file for vulnerabilities
def scan_file(file_path):
    vulnerabilities = []
    with open(file_path, 'r') as f:
        content = f.read()
        for rule in scan_rules:
            if re.search(rule['pattern'], content):
                vulnerabilities.append(rule['description'])
    return vulnerabilities

# Function to scan a directory for vulnerabilities
def scan_directory(directory):
    vulnerabilities = []
    for root, dirs, files in os.walk(directory):
        for file in files:
            file_path = os.path.join(root, file)
            vulnerabilities.extend(scan_file(file_path))
    return vulnerabilities
