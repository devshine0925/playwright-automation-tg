import os
import logging
import asyncio
from telethon import TelegramClient, events
from dotenv import load_dotenv  # Requires python-dotenv package to load env variables

# Load environment variables from a .env file
load_dotenv()

# Logging configuration
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Fetch sensitive info from environment variables
API_ID = os.getenv("API_ID")
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_USERNAME = "@nhan_otp_vinaphone_d3_bot"

async def fetch_messages(client: TelegramClient) -> None:
    """Function to fetch messages from the specified channel."""
    try:
        logger.info("Fetching messages...")
        async for message in client.iter_messages(CHANNEL_USERNAME, limit=100):
            logger.info(f"Message ID: {message.id}, Sender: {message.sender_id}, Message: {message.text}")
            await asyncio.sleep(0.1)  # To avoid hitting rate limits
        logger.info("Finished fetching messages.")
    except Exception as e:
        logger.error(f"An error occurred while fetching messages: {e}")

async def new_message_handler(event) -> None:
    """Handler for new messages in the specified channel."""
    message = event.message
    logger.info(f"New message from {message.sender_id}: {message.text}")

async def main() -> None:
    """Main function to create the Telegram client and start listening for new messages."""
    try:
        async with TelegramClient('bot_session', API_ID, API_HASH) as client:
            await client.start(bot_token=BOT_TOKEN)
            logger.info("Bot started...")
            
            # Event handler for new messages
            client.on(events.NewMessage(chats=CHANNEL_USERNAME))(new_message_handler)

            # Fetch initial messages (if needed)
            await fetch_messages(client)

            # Run the client until disconnected
            await client.run_until_disconnected()
    except Exception as e:
        logger.error(f"An error occurred in the main function: {e}")

if __name__ == "__main__":
    try:
        # Execute the main asyncio program
        asyncio.run(main())
    except Exception as e:
        logger.error(f"An error occurred while running the bot: {e}")
