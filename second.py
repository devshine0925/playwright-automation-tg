import asyncio
from playwright.async_api import async_playwright

async def control_telegram():
    async with async_playwright() as p:
        # Launch browser (headless=False to see the browser)
        browser = await p.chromium.launch(headless=False)

        # Open a new browser page
        page = await browser.new_page()

        # Go to Telegram Web login page
        await page.goto("https://web.telegram.org/")

        # Wait for the QR code to load and scan it
        print("Scan the QR code with your mobile device")

        # Optionally, wait for some element that indicates the user is logged in
        await page.wait_for_selector("div[aria-label='Chat list']")  # This selector may change

        print("Logged in successfully!")

        # Send a message to a specific chat/channel (for example, you can send to the bot channel)
        channel_name = "Your Channel Name"  # Replace with your channel name
        message = "Hello from Playwright!"

        # Find the chat by channel name and open it
        await page.click(f"text={channel_name}")

        # Wait for the chat to open and input the message
        await page.fill("textarea[placeholder='Message']", message)
        await page.press("textarea[placeholder='Message']", "Enter")

        print("Message sent!")

        # Close the browser
        await browser.close()

# Run the function
asyncio.run(control_telegram())
