from playwright.sync_api import sync_playwright
import time

def extract_message_data(message_element):
    """
    Extracts relevant data (like text content, URLs, or codes) from a message element.
    """
    message_text = message_element.query_selector(".text-content").inner_text()
    if not message_text:
        return None

    # Example of extracting specific information
    order_id = None
    phone = None
    url = None
    otp_code = None

    # Extract OrderID
    if "OrderID:" in message_text:
        order_id = message_text.split("OrderID:")[1].split()[0]

    # Extract Phone
    if "Phone:" in message_text:
        phone = message_text.split("Phone:")[1].split()[0]

    # Extract URL
    if "http" in message_text:
        url = message_text.split("http")[1].split()[0]
        url = "http" + url  # Add 'http' prefix back

    # Extract OTP Code
    if "OTP Code:" in message_text:
        otp_code = message_text.split("OTP Code:")[1].split()[0]

    return {
        "text": message_text,
        "order_id": order_id,
        "phone": phone,
        "url": url,
        "otp_code": otp_code,
    }


def monitor_telegram_channel(page):
    """
    Monitors Telegram Web for new messages and processes them in real-time.
    """
    print("Monitoring Telegram Web for messages...")
    processed_message_ids = set()

    while True:
        # Locate the messages container
        messages = page.query_selector_all(".message-list-item")

        for message in messages:
            message_id = message.get_attribute("data-message-id")

            # Skip already processed messages
            if message_id in processed_message_ids:
                continue

            # Extract and process the message content
            data = extract_message_data(message)
            if data:
                print("New Message Data:", data)

                # Perform additional actions based on the message data
                if data["url"]:
                    print(f"URL detected: {data['url']}")

            # Mark the message as processed
            processed_message_ids.add(message_id)

        # Wait before checking again
        time.sleep(1)


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)  # Set headless=True for production
        context = browser.new_context()

        # Load a saved session or ask the user to log in
        try:
            context.storage_state(path="telegram_session.json")
        except Exception:
            print("No session found. Logging in manually.")
            page = context.new_page()
            page.goto("https://web.telegram.org")
            input("Log in to Telegram Web and press Enter...")

            # Save session state for reuse
            context.storage_state(path="telegram_session.json")

        # Open Telegram Web
        page = context.new_page()
        page.goto("https://web.telegram.org")

        # Monitor the Telegram channel for messages
        monitor_telegram_channel(page)


if __name__ == "__main__":
    main()
