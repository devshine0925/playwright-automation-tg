import re
import time
import asyncio
import logging
import uuid
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

CHANNEL_USERNAME =os.getenv('CHANNEL_USERNAME')
VIEWPORT_SIZE = {"width": 420, "height": 720}
TIMEOUT = 100000  

pending_orders = {}
all_urls = {}
ORDERS = []
MSG = []
browser_variables = []

async def close_broswer(br):
    await br.close()
    global browser
    browser = None

def remove_item(order_id):
    global MSG
    if len(MSG)>0:
        MSG = [msg for msg in MSG if extract_order_id(msg) != order_id]

def extract_order_id(message):
    match = re.search(r'OrderID:\s*(\d+)', message.text)
    return match.group(1) if match else None 

def find_item(orderID):
   matching_messages = [msg for msg in MSG if extract_order_id(msg) == orderID]
   if len(matching_messages)>0:
       return matching_messages[0]    
   else:
       return {}
   
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
        global browser_variables
        async with async_playwright() as p:
            
            browser = await p.chromium.launch(headless=False, args=["--window-size=430,720"])
            context = await browser.new_context(viewport=VIEWPORT_SIZE)
            page = await context.new_page()
            variable_id = str(uuid.uuid4())
            browser_variables.append({
                "id": variable_id,
                "variable": browser
            })
            await navigate_to_page(page, order_data["link"], browser)
            await fill_form(page, order_data)
            await asyncio.sleep(3)
            await handle_result(page, order_data['OrderID'])
            await asyncio.sleep(3)
            await browser.close()
    except Exception as e:
        logging.error(f"Automation failed for OrderID {order_data['OrderID']}: {e}")
        await send_telegram_message("automation faild", order_data['OrderID'])

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
            attempt += 1
            logging.error(f"Loading page failed: {e}. Retrying...")
            try:
                await page.reload(timeout=TIMEOUT)
                if attempt == max_retries:
                    logging.error(f"Failed to load {link} after {max_retries} attempts.")
                    if browser:
                        await close_broswer(browser)
                else:
                    time.sleep(30)
            except:
                logging.error('returning logic error')
                pass
        except Exception as e:
            logging.error(f"Unexpected error: {str(e)}. Attempt {attempt + 1} failed.")
            attempt += 1
            
            if attempt < max_retries:
                await page.reload(timeout=TIMEOUT)
                await asyncio.sleep(5)  # Pause before retrying for a short duration
            else:
                logging.error(f"Failed to load {link} after {max_retries} attempts due to: {str(e)}.")
                await close_broswer(browser)
                return

        finally:
            logging.error('returning logic end')
            pass

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
        # if browswer:
        #     await browswer.close()   

async def send_telegram_message(message, order_id):
    msg = find_item(order_id)

    print(order_id)
    if message == "Success":
        await find_and_click_button(msg,"Success")
    elif message == "Wrong OTP":
        await find_and_click_button(msg,"Wrong OTP")
    else:    
        await find_and_click_button(msg, "Failure")

    remove_item(order_id)

async def extract_order_info( page: Page):
        """Extract status text and image source from the order result."""
        try:
            # Extract the text "ĐĂNG KÝ THÀNH CÔNG"
            status_text = await page.inner_text('.order-result-info__title-status span')
            # Extract the src attribute of the img element
            img_src = await page.get_attribute('.order-result-info__ic-status img', 'src')
            if status_text == "ĐĂNG KÝ THÀNH CÔNG" or img_src == "/static/imgs/ic_order_success.svg":
                return True
            else:
                return False         
        except Exception as e:
            print(f"An error occurred during extraction: {e}")
            return False
     

async def handle_result(page: Page, order_id):
    error_selector = 'div.ant-form-item-explain-error'
    try:
        await page.wait_for_selector(error_selector, state="visible", timeout=TIMEOUT)
        error_text = await page.text_content(error_selector)
        logging.error(f"Error message detected: {error_text}")
        if "Mã OTP không chính xác hoặc hết hiệu lực" in error_text:
            logging.info("Clicked the wrong OTP button.")
            await send_telegram_message("Wrong OTP", order_id)
            return  
        else:
            await send_telegram_message("Failure", order_id)

    except Exception:
        is_success_visible = await page.is_visible('div.order-success.pt-5.text-center')

        if is_success_visible:
            logging.info("Order submitted successfully.")
            await send_telegram_message("Success", order_id)
            return
        
        if await extract_order_info(page):
            logging.info("Success message is visible.")
            await send_telegram_message("Success", order_id)
            return
        is_failed_visible = await page.is_visible('div.order-failure.pt-5.text-center')
        if is_failed_visible:
            logging.error("Order submission failed.")
            await send_telegram_message("Failure", order_id)
            return
        else:
            logging.warning("No visible success or failure state detected.")
            await send_telegram_message("Failure", order_id)
            return
        # if browswer:
        #     await browswer.close()

async def find_and_click_button(message, button_text):
    if message:
        logging.info(f"Looking for button with text: '{button_text}'")
        
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
            global MSG
            order_data = extract_order_data(message_text)
            if order_data.get('OrderID'):
                MSG.append(event.message)
            if order_data.get('OrderID') in pending_orders:
                previous_data = pending_orders[order_data['OrderID']]
                previous_data.update(order_data)
                pending_orders[order_data['OrderID']] = previous_data
            else:
                print('non-matched message with OrderId')

    await client.run_until_disconnected()

if __name__ == '__main__':
    asyncio.run(main())
