import re
import time
import asyncio
import logging
import os
from dotenv import load_dotenv
from telethon import TelegramClient, events
from telethon.errors import FloodWaitError
from playwright.async_api import async_playwright
from playwright.async_api._generated import Page

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
load_dotenv()

API_ID = os.getenv('API_ID') 
API_HASH = os.getenv('API_HASH') 
BOT_TOKEN = os.getenv('BOT_TOKEN') 
CHAT_ID = os.getenv('CHAT_ID') 

CHANNEL_USERNAME = '@kinhdoanhviettel_bot'
VIEWPORT_SIZE = {"width": 420, "height": 720}
TIMEOUT = 100000  

pending_orders = {}
all_urls = {}
ORDERS = []
msg = {}
browswer = None
async def close_broswer(br):
    await br.close()
    global browser
    browser = None
    
def extract_number(pattern, message_text: str) -> str:
    match = re.search(pattern, message_text)
    if match:
        _number = match.group(1)  # Extract the phone number
        if len(_number) > 2:
            return _number[1:-1] 
        else:
            return None  
    return None 

def extract_order_data(message_text: str) -> dict:
    order_data = {}
    order_data['OrderID'] = re.search(r'OrderID:\s*(\S+)', message_text).group(1) if re.search(r'OrderID:\s*(\S+)', message_text) else None
    order_data['Phone'] = extract_number(r'Phone:\s*(\S+)',message_text)
    order_data['Description'] = re.search(r'Description:\s*([\w\d-]+)', message_text).group(1) if re.search(r'Description:\s*([\w\d-]+)', message_text) else None
    order_data['OTP'] = extract_number(r'OTP Code:\s*(\S+)', message_text)
    return order_data

async def handle_browser_automation(order_data):
    try:
        global browser
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False, args=["--window-size=420,720"])
            context = await browser.new_context(viewport=VIEWPORT_SIZE)
            page = await context.new_page()

            await navigate_to_page(page, order_data["link"], browser)
            await fill_form(page, order_data)
            await asyncio.sleep(10)
            await handle_result(page, order_data)
            await asyncio.sleep(10)
            await browser.close()
            browser =  None
    except Exception as e:
        logging.error(f"Automation failed for OrderID {order_data['OrderID']}: {e}")
        await send_telegram_message("automation faild")

async def navigate_to_page(page: Page, link: str, browser):
    max_retries = 5
    attempt = 0

    while attempt < max_retries:
        try:
            logging.info(f"Navigating to {link} (Attempt {attempt + 1})")
            await page.goto(link, timeout=TIMEOUT) 
            await page.wait_for_selector(".body-content", timeout=TIMEOUT)
            await page.wait_for_selector('button[data-text="Đăng ký ngay"]', timeout=10000)
            logging.info("Page loaded and dynamic content detected.")
            break 
        except TimeoutError as e:
            logging.error(f"Loading page failed: {e}. Retrying...")
            await page.reload(timeout=TIMEOUT)
            attempt += 1
            if attempt == max_retries:
                logging.error(f"Failed to load {link} after {max_retries} attempts.")
                if browser:
                    await close_broswer(browser)
            else:
                time.sleep(30)

async def fill_otp(page, order_data):
    max_retries = 300
    attempt = 0
    while attempt < max_retries:
        otp_data =  get_otp_from_pending_orders(order_data['OrderID'])
        if otp_data:
            await page.fill('input#otp', order_data["OTP"])
            logging.info("OTP provided and filled.")
            return  
        else:
            logging.warning(f"Attempt {attempt + 1}: No OTP found. Retrying...")
            attempt += 1
            await asyncio.sleep(1)
             

    logging.info("Failed to find OTP after 100 attempts.")
    await send_telegram_message("otp failed.")
    if browser:
        await close_broswer(browser) 

def get_otp_from_pending_orders(order_id):
    order_data = pending_orders.get(order_id)
    if order_data and 'OTP' in order_data:
        return order_data['OTP']
    else:
        return None

async def fill_form(page: Page, order_data: dict):
    logging.info("Filling out the form...")
    await page.click('button[data-text="Đăng ký ngay"]')
    await page.wait_for_selector('div.ant-modal.form-modal', state="visible", timeout=TIMEOUT)
    # print("Order_data",order_data )
    await page.fill('input#phone', order_data["Phone"])
    time.sleep(2)
    await page.click('button#submit_btn')
    time.sleep(5)
    try: 
        await page.wait_for_selector('div.ant-modal.otp-modal', state="visible", timeout=TIMEOUT)
        await fill_otp(page, order_data)
        time.sleep(3)
        modal_selector = ".ant-modal.otp-modal"
        modal = page.locator(modal_selector)
        await modal.locator('button.btn-custom.btn-hover2').click()
    except Exception:
        logging.info("error is occured.")
        if browswer:
            await browswer.close()   
async def send_telegram_message(message):
    if message == "Success":
        print(message)
        await find_and_click_button(msg,"Success")
    elif message == "Wrong OTP":
        await find_and_click_button(msg,"Wrong OTP")
    else:    
        print("send message here.", message)
        await find_and_click_button(msg, "Failure")
    
async def handle_result(page: Page, order_data: dict):
    error_selector = 'div.ant-form-item-explain-error'
    try:
        await page.wait_for_selector(error_selector, state="visible", timeout=TIMEOUT)
        error_text = await page.text_content(error_selector)
        logging.error(f"Error message detected: {error_text}")
        if "Mã OTP không chính xác hoặc hết hiệu lực" in error_text:
            logging.info("Clicked the wrong OTP button.")
            await send_telegram_message("Wrong OTP")
        await send_telegram_message("Failure")

    except Exception:
        is_success_visible = await page.is_visible('div.order-success.pt-5.text-center')
        is_failed_visible = await page.is_visible('div.order-failure.pt-5.text-center')

        if is_success_visible:
            logging.info("Order submitted successfully.")
            await send_telegram_message("Success")
        elif is_failed_visible:
            logging.error("Order submission failed.")
            await send_telegram_message("Failure")
        else:
            logging.warning("No visible success or failure state detected.")
            await send_telegram_message("Failure")
        if browswer:
            await browswer.close()

async def find_and_click_button(message, button_text):
    if message:
        logging.info(f"Looking for button with text: '{button_text}'")
        logging.info(f"MESSAGES: '{message}'")
        
        if message.reply_markup:
            if button_text ==  "Success":
                await message.click(data=b'success')
                logging.info("click success button")
                
            elif button_text == "Wrong OTP":
                await message.click(data=b'error_otp')
                logging.info("click wrong otp button")
               
            else:
                await message.click(data=b'failure')
                logging.info("click failure button")
            
            return
    else:
        logging.info("message data doesn't exsist!")
    # if browser:
    #     await close_broswer(browser)                
async def main():
  async with TelegramClient('session_name', API_ID, API_HASH) as client:
    await client.start(bot_token=BOT_TOKEN)
    @client.on(events.NewMessage(chats=CHANNEL_USERNAME))
    async def handler(event):
        message_text = event.message.text

        link_match = re.search(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\$\$,]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', message_text)

        if link_match:
            url = link_match.group(0)
            order_data = extract_order_data(message_text)
            order_data['link'] = url  
            pending_orders[order_data['OrderID']] = order_data
            ORDERS.append(order_data['OrderID']) 
            await handle_browser_automation(order_data)
            
        else:
            global msg
            msg = event.message
            print("message info===>",msg)
            order_data = extract_order_data(message_text)

            if order_data.get('OrderID') in pending_orders:
                previous_data = pending_orders[order_data['OrderID']]
                previous_data.update(order_data)
                pending_orders[order_data['OrderID']] = previous_data
            else:
                print('non-matched message with OrderId')

    await client.run_until_disconnected()

if __name__ == '__main__':
    asyncio.run(main())
