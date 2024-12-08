from playwright.async_api import async_playwright
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext
import re

pending_orders = {}

# Function to extract order data from a message
def extract_order_data(message_text: str):
    order_data = {}
    order_data['OrderID'] = re.search(r'OrderID:\s*(\S+)', message_text).group(1) if re.search(r'OrderID:\s*(\S+)', message_text) else None
    order_data['Phone'] = re.search(r'Phone:\s*(\S+)', message_text).group(1) if re.search(r'Phone:\s*(\S+)', message_text) else None
    order_data['Description'] = re.search(r'Description:\s*([\w\d-]+)', message_text).group(1) if re.search(r'Description:\s*([\w\d-]+)', message_text) else None
    order_data['OTP'] = re.search(r'OTP Code:\s*(\S+)', message_text).group(1) if re.search(r'OTP Code:\s*(\S+)', message_text) else None
    
    return order_data

# Start command handler 
async def start(update: Update, context: CallbackContext):
    await update.message.reply_text('Bot is running!')

# Handle incoming messages
async def handle_message(update: Update, context: CallbackContext):
    message_text = update.message.text
    
    link_match = re.search(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', message_text)
    
    if link_match:
        url = link_match.group(0)
        order_data = extract_order_data(message_text)
        order_data['link'] = url  
        
        pending_orders[order_data['OrderID']] = order_data
        await update.message.reply_text(f"Received Order with link: {url}")
        await handle_browser_automation(order_data)  # Proceed to browser automation
        
    else:
        order_data = extract_order_data(message_text)
        
        if order_data['OrderID'] in pending_orders:
            previous_data = pending_orders[order_data['OrderID']]
            previous_data.update(order_data)  # Combine order data with the previous one
            
            await update.message.reply_text(f"Complete order data received for OrderID {order_data['OrderID']}: {previous_data}")
            await process_complete_order(previous_data)  # You can now process the complete order
        else:
            await update.message.reply_text(f"Could not find matching OrderID for the data in your message.")

async def handle_browser_automation(order_data):
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
            await page.fill('input#otp',  order_data['OTP'])
        else:
            print("OTP not provided.")

        await page.click('button[data-text="Tiếp tục"]') 

        error_selector = 'div.ant-form-item-explain-error'
        try:
            await page.wait_for_selector(error_selector, state='visible', timeout=10000)  # 10 seconds timeout
            error_text = await page.text_content(error_selector)
            print(f"Error message: {error_text}")

            if "Mã OTP không chính xác hoặc hết hiệu lực" in error_text:
                wrong_otp = 'button.Button tiny primary has-ripple'  
                await page.click(wrong_otp)
                print("Clicked the wrong_otp button.")

        except Exception as e:
            print(f"No Error message ")
            is_success_visible = await page.is_visible('div.order-success.pt-5.text-center')
            is_failed_visible = await page.is_visible('div.order-failure.pt-5.text-center')
            if is_failed_visible:
                print("Error message is failed.")
            else:
                if is_success_visible:
                    print("Error message is success.")

                print("Error message is not visible.") 
            
        await browser.close()

async def process_complete_order(order_data):
    print(f"Processing order: {order_data}")

async def main():
    application = Application.builder().token("7679124575:AAEwLlbVV03iAH5i_wCzyOwE4ec_r01Pmmc").build()

    # Add handlers
    # application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # # Run the bot with polling (this internally handles the event loop)
    # await application.run_polling()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
