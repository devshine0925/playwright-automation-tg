import logging
from playwright.async_api import async_playwright
from playwright.async_api._generated import Page
import time

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Constants
VIEWPORT_SIZE = {"width": 420, "height": 800}
TIMEOUT = 10000  # Timeout in milliseconds


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
    # await page.click('button.btn-custom.btn-hover2')


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
    """
    Entry point of the script.
    """
    order_data = {
        "link": "https://digishop.vnpt.vn/di-dong/blockbig90/3661?aff=VNP018670",
        "Phone": "0888888888",
        "OTP": "888888"
    }
    await handle_browser_automation(order_data)


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
