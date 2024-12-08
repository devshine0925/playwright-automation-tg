import requests
import time

# Replace with your bot's API token
BOT_TOKEN = "7679124575:AAEwLlbVV03iAH5i_wCzyOwE4ec_r01Pmmc"

# Telegram Bot API Base URL
BASE_URL = f"https://api.telegram.org/bot{BOT_TOKEN}/"

# Add the specific chat IDs you want to process
ALLOWED_CHAT_IDS = ["7192802252"]  # Replace with your chat IDs

# Function to get updates
def get_updates(offset=None):
    try:
        url = f"{BASE_URL}getUpdates"
        params = {"offset": offset, "timeout": 30}  # Long polling timeout
        response = requests.get(url, params=params)
        response.raise_for_status()  # Raise an exception for HTTP errors

        data = response.json()
        if not data.get("ok"):
            print(f"Error from Telegram API: {data}")
            return None
        return data
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
        return None

# Process updates
def process_updates(updates):
    for update in updates.get("result", []):
        message = update.get("message", {})
        chat_id = message.get("chat", {}).get("id")
        text = message.get("text", "")

        if chat_id not in ALLOWED_CHAT_IDS:
            print(f"Ignoring message from chat {chat_id}")
            continue

        print(f"New message in chat {chat_id}: {text}")

        # Respond to the message (optional)
        if text.lower() == "hello":
            send_message(chat_id, "Hi there! How can I help you?")
        elif text.lower() == "bye":
            send_message(chat_id, "Goodbye! Have a great day!")

# Send a message to a chat
def send_message(chat_id, text):
    try:
        url = f"{BASE_URL}sendMessage"
        payload = {"chat_id": chat_id, "text": text}
        response = requests.post(url, json=payload)
        response.raise_for_status()

        if response.status_code == 200:
            print(f"Message sent to {chat_id}: {text}")
        else:
            print(f"Failed to send message to {chat_id}: {response.text}")
    except requests.exceptions.RequestException as e:
        print(f"Failed to send message: {e}")

# Main function
def main():
    offset = None
    print("Bot is running... Press Ctrl+C to stop.")
    try:
        while True:
            updates = get_updates(offset)
            if updates and "result" in updates and len(updates["result"]) > 0:
                process_updates(updates)
                offset = updates["result"][-1]["update_id"] + 1  # Update the offset
            time.sleep(1000)  # Respect rate limits
    except KeyboardInterrupt:
        print("\nBot stopped gracefully.")

if __name__ == "__main__":
    main()
