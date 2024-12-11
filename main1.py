import re
import time
import asyncio
import logging
from telethon import TelegramClient, events
from playwright.async_api import async_playwright
from playwright.async_api._generated import Page

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

API_ID = 21968589
API_HASH = 'b7270cc2655ab46c60fca0abc005cd96'
BOT_TOKEN = '7679124575:AAEwLlbVV03iAH5i_wCzyOwE4ec_r01Pmmc'
CHANNEL_USERNAME = '@nhan_otp_vinaphone_d3_bot' 
VIEWPORT_SIZE = {"width": 420, "height": 800}
TIMEOUT = 10000  

pending_orders = {}
all_urls = {}

def extract_order_data(message_text: str) -> dict:
    order_data = {}
    order_data['OrderID'] = re.search(r'OrderID:\s*(\S+)', message_text).group(1) if re.search(r'OrderID:\s*(\S+)', message_text) else None
    order_data['Phone'] = re.search(r'Phone:\s*(\S+)', message_text).group(1) if re.search(r'Phone:\s*(\S+)', message_text) else None
    order_data['Description'] = re.search(r'Description:\s*([\w\d-]+)', message_text).group(1) if re.search(r'Description:\s*([\w\d-]+)', message_text) else None
    order_data['OTP'] = re.search(r'OTP Code:\s*(\S+)', message_text).group(1) if re.search(r'OTP Code:\s*(\S+)', message_text) else None
    return order_data

# async def handle_browser_automation(order_data: dict) -> None:
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        await page.goto(order_data['link'])
        await page.click('button[data-text="Đăng ký ngay"]')

        await page.wait_for_selector('div.ant-modal.form-modal', state='visible')
        await page.fill('input#phone', order_data['Phone'])
        await page.click('button[data-text="Đăng ký ngay"]')
        
        await page.wait_for_selector('div.ant-modal.otp-modal', state='visible')
        await page.wait_for_selector('input#otp', state='visible')

        if order_data.get('OTP'):  
            await page.fill('input#otp', order_data['OTP'])
        else:
            print("OTP not provided.")

        await page.click('button[data-text="Tiếp tục"]')

        error_selector = 'div.ant-form-item-explain-error'
        try:
            await page.wait_for_selector(error_selector, state='visible', timeout=10000)  # Timeout after 10 seconds
            error_text = await page.text_content(error_selector)
            print(f"Error message: {error_text}")

            if "Mã OTP không chính xác hoặc hết hiệu lực" in error_text:
                wrong_otp = 'button.Button tiny primary has-ripple'
                await page.click(wrong_otp)
                print("Clicked the wrong OTP button.")
        except Exception:
            print("No Error message.")
            is_success_visible = await page.is_visible('div.order-success.pt-5.text-center')
            is_failed_visible = await page.is_visible('div.order-failure.pt-5.text-center')
            if is_failed_visible:
                print("Error message indicates failure.")
            elif is_success_visible:
                print("Order processed successfully.")
            else:
                print("Error message not visible.")

        await browser.close()

async def handle_browser_automation(order_data):
    """
    Automates the process of interacting with a web page using Playwright.
    """
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False, args=["--window-size=420,800"])
            context = await browser.new_context(viewport=VIEWPORT_SIZE)
            page = await context.new_page()
            
            await navigate_to_page(page, order_data["link"])
            await fill_form(page, order_data)
            time.sleep(5)
            await handle_result(page, order_data)
            time.sleep(30)
            await browser.close()
    except Exception as e:
        logging.error(f"Automation failed: {e}")


async def navigate_to_page(page: Page, link: str):
    """
    Navigate to the provided link and wait for the page to load.
    """
    logging.info(f"Navigating to {link}")
    await page.goto(link, timeout=1000000)
    await page.wait_for_selector(".body-content", timeout=TIMEOUT)
    logging.info("Page loaded and dynamic content detected.")


async def fill_form(page: Page, order_data: dict):
    """
    Fill out the form on the page using the provided order data.
    """
    logging.info("Filling out the form...")
    await page.click('button[data-text="Đăng ký ngay"]')
    await page.wait_for_selector('div.ant-modal.form-modal', state="visible", timeout=TIMEOUT)
    await page.fill('input#phone', order_data["Phone"])
    time.sleep(2)
    await page.click('button#submit_btn')
    await page.wait_for_selector('div.ant-modal.otp-modal', state="visible", timeout=TIMEOUT)
    if order_data.get("OTP"):
        await page.fill('input#otp', order_data["OTP"])
        logging.info("OTP provided and filled.")
    else:
        logging.warning("No OTP provided. Skipping OTP step.")
    time.sleep(2)
    modal_selector = ".ant-modal.otp-modal"
    modal = page.locator(modal_selector)
    await modal.locator('button.btn-custom.btn-hover2').click()

async def handle_result(page: Page, order_data: dict):
    """
    Handle the result of the form submission and log appropriate messages.
    """
    error_selector = 'div.ant-form-item-explain-error'
    try:
        # Check for errors
        await page.wait_for_selector(error_selector, state="visible", timeout=TIMEOUT)
        error_text = await page.text_content(error_selector)
        logging.error(f"Error message detected: {error_text}")

        if "Mã OTP không chính xác hoặc hết hiệu lực" in error_text:
            await page.click('button.Button.tiny.primary.has-ripple')
            logging.info("Clicked the wrong OTP button.")
    except Exception:
        # Check for success or failure
        is_success_visible = await page.is_visible('div.order-success.pt-5.text-center')
        is_failed_visible = await page.is_visible('div.order-failure.pt-5.text-center')

        if is_success_visible:
            logging.info("Order submitted successfully.")
        elif is_failed_visible:
            logging.error("Order submission failed.")
        else:
            logging.warning("No visible success or failure state detected.")

async def main():
    """Main function to run the bot."""
    client = TelegramClient('session_name', API_ID, API_HASH).start(bot_token=BOT_TOKEN)

    @client.on(events.NewMessage)
    async def handler(event):
        message_text = event.message.message

        link_match = re.search(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\$\$,]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', message_text)

        if link_match:
            url = link_match.group(0)
            order_data = extract_order_data(message_text)
            order_data['link'] = url  

            pending_orders[order_data['OrderID']] = order_data
            # await event.reply(f"Received Order with link: {url}")
            await handle_browser_automation(order_data)

        else:
            order_data = extract_order_data(message_text)

            if order_data.get('OrderID') in pending_orders:
                previous_data = pending_orders[order_data['OrderID']]
                previous_data.update(order_data)
                await event.reply(f"Complete order data received for OrderID {order_data['OrderID']}: {previous_data}")
                # await process_complete_order(previous_data)
            else:
                await event.reply("Could not find matching OrderID for the data in your message.")

    # Run the bot
    await client.start()
    await client.run_until_disconnected()

if __name__ == '__main__':
    asyncio.run(main())
