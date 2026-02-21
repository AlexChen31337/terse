import json
import os
import requests

# Define the Telegram API token
telegram_token = 'YOUR_TELEGRAM_TOKEN'

# Define the Telegram chat ID
telegram_chat_id = 'YOUR_TELEGRAM_CHAT_ID'

# Function to send a message to Telegram
def send_message(message):
    url = f'https://api.telegram.org/bot{telegram_token}/sendMessage'
    params = {'chat_id': telegram_chat_id, 'text': message}
    requests.post(url, params=params)

# Function to format a review message
def format_review_message(asset_id, review):
    message = f'Review for {asset_id}:
{review}'
    return message

# Function to send a review message to Telegram
def send_review_message(asset_id, review):
    message = format_review_message(asset_id, review)
    send_message(message)
