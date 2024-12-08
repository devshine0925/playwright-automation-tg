import requests
import re
import time

# Replace with your bot's API token
BOT_TOKEN = "7679124575:AAEwLlbVV03iAH5i_wCzyOwE4ec_r01Pmmc"

# Telegram Bot API Base URL
BASE_URL = f"https://api.telegram.org/bot{BOT_TOKEN}/"

# Function to get updates
def get_updates(offset=None):
    url = f"{BASE_URL}getUpdates"
    params = {"offset": offset, "timeout": 30}  # Long polling timeout
    response = requests.get(url, params=params)

    if response.status_code == 200:
        return response.json()
    else:
        print(f"Failed to fetch updates: {response.text}")
        return None
def extract_order_data(message_text: str):
    order_data = {}
    order_data['OrderID'] = re.search(r'OrderID:\s*(\S+)', message_text).group(1) if re.search(r'OrderID:\s*(\S+)', message_text) else None
    order_data['Phone'] = re.search(r'Phone:\s*(\S+)', message_text).group(1) if re.search(r'Phone:\s*(\S+)', message_text) else None
    order_data['Description'] = re.search(r'Description:\s*([\w\d-]+)', message_text).group(1) if re.search(r'Description:\s*([\w\d-]+)', message_text) else None
    order_data['OTP'] = re.search(r'OTP Code:\s*(\S+)', message_text).group(1) if re.search(r'OTP Code:\s*(\S+)', message_text) else None
    
    return order_data
# Process updates
def process_updates(updates):
    for update in updates["result"]:
        message = update.get("message", {})
        chat_id = message.get("chat", {}).get("id")
        text = message.get("text", "")
        # data  = extract_order_data(text)
        print(f"New message in chat {text}")
       
# Send a message to a chat
def send_message(chat_id, text):
    url = f"{BASE_URL}sendMessage"
    payload = {"chat_id": chat_id, "text": text}
    response = requests.post(url, json=payload)

    if response.status_code == 200:
        print(f"Message sent: {text}")
    else:
        print(f"Failed to send message: {response.text}")

# Main function
def main():
    offset = None
    while True:
        updates = get_updates(offset)
        if updates and "result" in updates and len(updates["result"]) > 0:
            process_updates(updates)
            offset = updates["result"][-1]["update_id"] + 1  # Update the offset
            time.sleep(10)
if __name__ == "__main__":
    main()
#