from playwright.sync_api import sync_playwright

def save_telegram_session():
    """
    Launch Telegram Web, log in manually, and save the session for future use.
    """
    with sync_playwright() as p:
        # Launch the browser
        browser = p.chromium.launch(headless=False)  # Use headless=True for background mode
        context = browser.new_context()

        # Open Telegram Web
        page = context.new_page()
        page.goto("https://web.telegram.org")

        # Prompt the user to log in manually
        print("Please log in to Telegram Web.")
        input("After logging in, press Enter to save the session...")

        # Save the session data to a file
        context.storage_state(path="telegram_session.json")
        print("Session saved successfully as 'telegram_session.json'.")

        browser.close()

if __name__ == "__main__":
    save_telegram_session()
