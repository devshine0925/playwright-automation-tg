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

# Set up logging  
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")  
load_dotenv()  

# Configuration class for environment variables  
class Config:  
    API_ID = os.getenv('API_ID')   
    API_HASH = os.getenv('API_HASH')   
    BOT_TOKEN = os.getenv('BOT_TOKEN')   
    CHAT_ID = os.getenv('CHAT_ID')   
    CHANNEL_USERNAME = os.getenv('CHANNEL_USERNAME')  
    VIEWPORT_SIZE = {"width": 430, "height": 720}  
    TIMEOUT = 100000  

class OrderProcessor:  
    def __init__(self):  
        self.pending_orders = {}  
        self.todos = []  
        self.browser = None  

    async def close_browser(self):  
        if self.browser:  
            await self.browser.close()  
            self.browser = None  

    def find_item(self, orderID):
        matching_messages = [msg for msg in self.todos if self.extract_order_id(msg) == orderID]
        if len(matching_messages)>0:
            return matching_messages[0]    
        else:
            return {}
    
    def extract_order_id(self, message):  
        match = re.search(r'OrderID:\s*(\d+)', message.text)  
        return match.group(1) if match else None   
    
    def extract_number(self, pattern, message_text):
        match = re.search(pattern, message_text)
        if match:
            _number = match.group(1)  # Extract the phone number
            if len(_number) > 2:
                return _number[1:-1] 
            else:
                return None  
        return None 

    def extract_order_data(self, message) :
        order_data = {}
        order_data['OrderID'] = re.search(r'OrderID:\s*(\S+)', message).group(1) if re.search(r'OrderID:\s*(\S+)', message) else None
        order_data['Phone'] = self.extract_number(r'Phone:\s*(\S+)',message)
        order_data['Description'] = re.search(r'Description:\s*([\w\d-]+)', message).group(1) if re.search(r'Description:\s*([\w\d-]+)', message) else None
        order_data['OTP'] = self.extract_number(r'OTP Code:\s*(\S+)', message)
        return order_data
     
    async def handle_browser_automation(self, order_data):  
        try:  
            async with async_playwright() as p:  
                self.browser = await p.chromium.launch(headless=False, args=["--window-size=430,720"])  
                context = await self.browser.new_context(viewport=Config.VIEWPORT_SIZE)  
                page = await context.new_page()  

                await self.navigate_to_page(page, order_data["link"])  
                await self.fill_form(page, order_data)  
                await asyncio.sleep(3)  
                await self.handle_result(page, order_data['OrderID'])  
        except Exception as e:  
            logging.error(f"Automation failed for OrderID {order_data['OrderID']}: {e}")  
            await self.send_telegram_message("Automation failed", order_data['OrderID'])  
        finally:  
            await self.close_browser()  

    async def navigate_to_page(self, page: Page, link: str):  
        max_retries = 5  
        for attempt in range(max_retries):  
            try:  
                logging.info(f"Navigating to {link} (Attempt {attempt + 1})")  
                await page.goto(link, timeout=Config.TIMEOUT)   
                await page.wait_for_selector(".body-content", timeout=Config.TIMEOUT)  
                await page.wait_for_selector('button[data-text="Đăng ký ngay"]', timeout=10000)  
                logging.info("Page loaded successfully.")  
                break   
            except Exception as e:  
                logging.error(f"Error loading page: {e}. Retrying...")  
                if attempt == max_retries - 1:  
                    await self.close_browser()  
                    break  
                await asyncio.sleep(30)  

    async def fill_otp(self, page, order_data):  
        max_retries = 300  
        for attempt in range(max_retries):  
            otp_data = self.get_otp_from_pending_orders(order_data['OrderID'])  
            if otp_data:  
                await page.fill('input#otp', order_data["OTP"])  
                logging.info("OTP provided and filled.")  
                return  
            else:  
                logging.warning(f"Attempt {attempt + 1}: No OTP found. Retrying...")  
                await asyncio.sleep(1)  

        logging.info("Failed to find OTP after retries.")  
        await self.send_telegram_message("OTP failed", order_data['OrderID'])  
        await self.close_browser()  

    def get_otp_from_pending_orders(self, order_id):  
        order_data = self.pending_orders.get(order_id)  
        return order_data.get('OTP') if order_data else None  

    async def fill_form(self, page: Page, order_data: dict):  
        logging.info("Filling out the form...")  
        await page.click('button[data-text="Đăng ký ngay"]')  
        await page.wait_for_selector('div.ant-modal.form-modal', state="visible", timeout=Config.TIMEOUT)  
        await page.fill('input#phone', order_data["Phone"])  
        await asyncio.sleep(2)  
        await page.click('button#submit_btn')  
        await asyncio.sleep(5)  

        try:  
            await page.wait_for_selector('div.ant-modal.otp-modal', state="visible", timeout=Config.TIMEOUT)  
            await self.fill_otp(page, order_data)  
            await asyncio.sleep(3)  
            await page.locator(".ant-modal.otp-modal").locator('button.btn-custom.btn-hover2').click()  
        except Exception as e:  
            logging.error("Error occurred while filling form: %s", e)  
            await self.close_browser()  

    async def send_telegram_message(self, message, order_id):  
        msg = self.find_item(order_id)  
        if message == "Success":  
            await self.find_and_click_button(msg, "Success")  
        elif message == "Wrong OTP":  
            await self.find_and_click_button(msg, "Wrong OTP")  
        else:    
            await self.find_and_click_button(msg, "Failure")  

    async def handle_result(self, page: Page, order_id):  
        error_selector = 'div.ant-form-item-explain-error'  
        try:  
            await page.wait_for_selector(error_selector, state="visible", timeout=Config.TIMEOUT)  
            error_text = await page.text_content(error_selector)  
            logging.error(f"Error message detected: {error_text}")  
            if "Mã OTP không chính xác hoặc hết hiệu lực" in error_text:  
                await self.send_telegram_message("Wrong OTP", order_id)  
            else:  
                await self.send_telegram_message("Failure", order_id)  
        except Exception:  
            if await page.is_visible('div.order-success.pt-5.text-center'):  
                await self.send_telegram_message("Success", order_id)  
            elif await page.is_visible('div.order-failure.pt-5.text-center'):  
                await self.send_telegram_message("Failure", order_id)  
            else:  
                await self.send_telegram_message("Unknown failure", order_id)  

    async def find_and_click_button(self, message, button_text):  
        if message and message.reply_markup:  
            logging.info(f"Looking for button with text: '{button_text}'")  
            button_map = {  
                "Success": b'success',  
                "Wrong OTP": b'error_otp',  
                "Failure": b'failure'  
            }  
            await message.click(data=button_map.get(button_text, b''))  
            logging.info(f"Clicked button for '{button_text}'")  
        else:  
            logging.info("Message data doesn't exist!")  

async def main():  
    async with TelegramClient('session_name', Config.API_ID, Config.API_HASH) as client:  
        await client.start(bot_token=Config.BOT_TOKEN)  
        order_processor = OrderProcessor()  

        @client.on(events.NewMessage(chats=Config.CHANNEL_USERNAME))  
        async def handler(event):  
            message_text = event.message.text  
            link_match = re.search(r'http[s]?://\S+', message_text)  

            if link_match:  
                url = link_match.group(0)  
                order_data = order_processor.extract_order_data(message_text)  
                order_data['link'] = url  
                order_processor.pending_orders[order_data['OrderID']] = order_data  
                await order_processor.handle_browser_automation(order_data)  
            else:  
                # Handle messages without links  
                order_data = order_processor.extract_order_data(message_text)  
                if order_data.get('OrderID'):  
                    order_processor.todos.append(event.message)  
                    if order_data['OrderID'] in order_processor.pending_orders:  
                        previous_data = order_processor.pending_orders[order_data['OrderID']]  
                        previous_data.update(order_data)  
                    else:  
                        logging.warning('Non-matched message with OrderID')  

        await client.run_until_disconnected()  

if __name__ == '__main__':  
    asyncio.run(main())