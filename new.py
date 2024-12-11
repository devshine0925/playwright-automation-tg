import logging
from telethon import TelegramClient, events

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def perform_operations_based_on_data(message):
    # Implement your data handling logic here
    # Add debug logs if necessary
    logger.debug(f"Processing message: {message}")

async def main(bot_token):
    # Create a new instance of the Telegram client
    async with TelegramClient('session_name', api_id, api_hash) as client:
        await client.start(bot_token=bot_token)

        @client.on(events.NewMessage(chats='@nhan_otp_vinaphone_d3_bot'))
        async def handler(event):
            message = event.message.text
            logger.info("New message received: %s", message)

            try:
                await perform_operations_based_on_data(message)
            except Exception as e:
                logger.error("Error occurred while processing message: %s", e)

        logger.info("Client started, waiting for messages...")
        await client.run_until_disconnected()

if __name__ == "__main__":
    api_id = 21968589
    api_hash = 'b7270cc2655ab46c60fca0abc005cd96'
    bot_token = '7679124575:AAEwLlbVV03iAH5i_wCzyOwE4ec_r01Pmmc'
    
    try:
        import asyncio
        asyncio.run(main(bot_token))
    except Exception as e:
        logger.error("An error occurred in the main event loop: %s", e)
