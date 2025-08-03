# Import required modules
import time
from datetime import datetime, timedelta, date
from playwright.sync_api import sync_playwright

# The specific time slot we want to book
TARGET_SLOT = "16:00 - 17:00"

# Number of retry attempts (with a 3-second delay between each),
# approximately 2 minutes of retrying total
RETRIES = 40

def get_tomorrows_date_str():
    """
    Returns tomorrow's date in 'YYYY-MM-DD' string format,
    which is the format required by the booking site.
    """
    return (datetime.today() + timedelta(days=1)).strftime("%Y-%m-%d")

def wait_until_5pm():
    """
    Waits until a specific time of day (here set to 1:59 PM — seems meant to be 5 PM but uses 13:59).
    Sleeps until that time is reached. Used to ensure booking starts at the right time.
    """
    now = datetime.now()
    target = now.replace(hour=14, minute=27, second=0, microsecond=0)  # Change this if you meant 17:00 instead of 13:59
    if now >= target:
        return  # Already past the target time
    delta = (target - now).total_seconds()
    print(f"[WAIT] Sleeping {int(delta)} seconds until 5PM...")
    time.sleep(delta)

def run_search(page, date_str):
    """
    Opens the reservation page and performs a search for Pickleball sessions in Saint-Léonard
    for the given date.
    """
    # Navigate to the search page
    page.goto("https://loisirs.montreal.ca/IC3/#/U6510/search")
    page.wait_for_timeout(1000)  # Wait 1 second for the page to load

    print("[UI] Setting filters...")

    # Enter 'pickleball' into the search field
    page.locator("input#u6510_edSearch").fill("pickleball")

    # Open borough selector tree (MUST open first)
    page.locator("button#u6510_btnTreeBorough").click()
    page.wait_for_timeout(500)

    # Click the Saint-Léonard checkbox
    saint_leonard_checkbox = page.locator("input#u2000_chkValue11")
    saint_leonard_checkbox.wait_for(state="visible")
    saint_leonard_checkbox.click()

    # Click the "Confirm" button to apply the borough filter
    page.locator("button#u2000_btnTreeSelectConfirm").click()

    # Fill in the date input with the desired reservation date
    date_input = page.locator("input[name='reserveDate']")
    date_input.fill(date_str)

    # Wait 2 seconds for search results to load
    page.wait_for_timeout(2000)

def try_find_slot(page):
    """
    Scans the search results in #searchResult for a row in the 'Quand' column that matches TARGET_SLOT.
    If found, clicks the '+' reserve button and returns True.
    """
    print("[SCAN] Scanning for 7PM slot...")

    # 1. Wait until #searchResult appears
    page.wait_for_selector("div#searchResult")

    # 2. Locate all column headers in the <thead> to determine 'Quand' column index
    headers = page.locator("div#searchResult thead tr th")
    quand_index = None

    for i in range(headers.count()):
        header_text = headers.nth(i).inner_text().strip().lower()
        if "quand" in header_text:
            quand_index = i + 1  # nth-child is 1-based
            break

    if quand_index is None:
        print("❌ 'Quand' column not found.")
        return False

    # 3. Iterate over each row in the table body
    rows = page.locator("div#searchResult tbody tr")

    for i in range(rows.count()):
        # Locate the 'Quand' cell using the index we found
        cell = rows.nth(i).locator(f"td:nth-child({quand_index})")
        cell_text = cell.inner_text().strip()

        if TARGET_SLOT in cell_text:
            print(f"✅ Found target slot at row {i+1}: {cell_text}")

            # Click the '+' button in the row
            plus_button = rows.nth(i).locator("button:has(i.fa-plus)")
            plus_button.click()
            return True

    print("⛔ Target slot not found.")
    return False

def main():
    """
    Main script flow:
    - Waits until reservation time (1:59PM).
    - Launches browser with saved session (so user stays logged in).
    - Repeats the search up to RETRIES times.
    - If the slot is found, stops and selects it.
    """
    # Get tomorrow's date in the required string format
    date_str = get_tomorrows_date_str()

    # Wait until 1:59PM before starting the booking attempts
    wait_until_5pm()

    # Start a synchronous Playwright session
    with sync_playwright() as p:
        # Launch a visible (non-headless) Chromium browser
        browser = p.chromium.launch(headless=False)

        # Load session state from "session.json" (must contain login state)
        context = browser.new_context(storage_state="session.json")

        # Create a new browser page
        page = context.new_page()

        # Try up to RETRIES times to find and reserve the desired slot
        for attempt in range(RETRIES):
            print(f"[{attempt+1}/{RETRIES}] Checking for {TARGET_SLOT}...")

            # Perform the filtered search
            run_search(page, date_str)

            # Try to find and reserve the slot
            if try_find_slot(page):
                print("🟢 Slot selected. (Paused before booking.)")
                page.wait_for_timeout(8000)  # Wait 8 seconds for you to manually confirm booking
                break
            else:
                print("🔄 Slot not found. Retrying...")
                time.sleep(3)  # Wait 3 seconds before retrying

        else:
            # If loop ends without break (i.e., no slot found in RETRIES)
            print("❌ No 7PM slot found after retry window.")
        
        # Wait 5 seconds before closing browser (for visibility/debug)
        page.wait_for_timeout(5000)
        browser.close()

# Entry point: only runs if script is executed directly
if __name__ == "__main__":
    main()
