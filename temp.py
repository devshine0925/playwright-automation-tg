import requests
import time

# Replace with your bot's API token
BOT_TOKEN = "7679124575:AAEwLlbVV03iAH5i_wCzyOwE4ec_r01Pmmc"

# Base URL for Telegram API
BASE_URL = f"https://api.telegram.org/bot{BOT_TOKEN}/"

# List of chat IDs (replace with valid IDs)
chat_ids = ["7192802252"]

# Function to send a message
def send_message(text, chat_id):
    url = f"{BASE_URL}sendMessage"
    payload = {"chat_id": chat_id, "text": text}

    response = requests.post(url, json=payload)

    if response.status_code == 200:
        print("--------------------------------")
        print(f"{text}")
    else:
        print(f"Failed to send message to {chat_id}: {response.text}")

# Message content
message_text = """OrderID: 202412042118370888888888
Phone: 0888888888
Description: blockbig90
Link: https://digishop.vnpt.vn/di-dong/blockbig90/3661?aff=VNP018670"""

# Send messages every 20 seconds to each chat ID
try:
    while True:  # Infinite loop for continuous sending
        for chat_id in chat_ids:
            send_message(message_text, chat_id)
        time.sleep(50)  # Wait 20 seconds before the next iteration
except KeyboardInterrupt:
    print("Stopped sending messages.")
