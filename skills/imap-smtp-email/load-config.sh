#!/bin/bash
# Decrypt and load email config into environment
# Usage: source <(./load-config.sh)
KEY_FILE="/home/bowen/clawd/memory/encrypted/.key"
ENC_FILE="/home/bowen/clawd/memory/encrypted/imap-smtp-env.enc"
openssl enc -aes-256-cbc -d -salt -pbkdf2 -in "$ENC_FILE" -pass "pass:$(cat $KEY_FILE)"
