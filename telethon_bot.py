from telethon import TelegramClient, events
import asyncio
import time

api_id = 21968589
api_hash = 'b7270cc2655ab46c60fca0abc005cd96'

bot_token = '7679124575:AAEwLlbVV03iAH5i_wCzyOwE4ec_r01Pmmc'

client = TelegramClient('shine', api_id, api_hash)

async def main():
    await client.start(bot_token = bot_token)

    @client.on(events.NewMessage(chats='nhan_otp_vinaphone_d3_bot'))
    async def handler(event):
        message = event.message.text
        print("New message:", message)
        await perform_operations_based_on_data(message)

    await client.run_until_disconnected()

async def perform_operations_based_on_data(message):
    from playwright.async_api import async_playwright

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()

        await page.goto('https://yourwebsite.com')

        if 'specific keyword' in message:
            # For example, if the message contains a keyword, click a button
            await page.click('button[data-action="specific_action"]')

        # You can perform further actions like filling out a form, submitting, etc.
        await page.fill('input#data_field', message)  # Example of filling a form field
        await page.click('button#submit_button')

        # Wait for the result
        await page.wait_for_selector('.result')  # Replace with a real result selector

        await browser.close()

loop = asyncio.get_event_loop()
loop.run_until_complete(main())
