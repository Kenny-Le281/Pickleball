import time
from datetime import datetime, timedelta
from playwright.sync_api import sync_playwright

# Priority-ordered list of desired time slots
PRIORITY_SLOTS = [
    "21:00 - 22:00",  # Priority 3 (9 PM)
    # "22:00 - 23:00",  # Priority 4 (10 PM)
]

RETRIES = 40

def get_tomorrows_date_str():
    return (datetime.today() + timedelta(days=1)).strftime("%Y-%m-%d")

def wait_until_5pm():
    now = datetime.now()
    target = now.replace(hour=14, minute=27, second=0, microsecond=0)  # Adjust if needed
    if now >= target:
        return
    delta = (target - now).total_seconds()
    time.sleep(delta)

def run_search(page, date_str):
    page.goto("https://loisirs.montreal.ca/IC3/#/U6510/search")
    page.wait_for_timeout(1000)

    print("[UI] Setting filters...")
    page.locator("input#u6510_edSearch").fill("pickleball")
    page.locator("button#u6510_btnTreeBorough").click()
    page.wait_for_timeout(500)

    saint_leonard_checkbox = page.locator("input#u2000_chkValue11")
    saint_leonard_checkbox.wait_for(state="visible")
    saint_leonard_checkbox.click()
    page.locator("button#u2000_btnTreeSelectConfirm").click()

    date_input = page.locator("input[name='reserveDate']")
    date_input.fill("")
    date_input.fill(date_str)
    page.wait_for_timeout(2000)

def try_find_slot(page, priority_slots):
    print("[SCAN] Scanning for priority slots...")
    page.wait_for_selector("div#searchResult")

    headers = page.locator("div#searchResult thead tr th")
    quand_index = None
    for i in range(headers.count()):
        header_text = headers.nth(i).inner_text().strip().lower()
        if "quand" in header_text:
            quand_index = i + 1
            break

    if quand_index is None:
        print("❌ 'Quand' column not found.")
        return None  # No column to check

    rows = page.locator("div#searchResult tbody tr")
    for priority, slot in enumerate(priority_slots, 1):
        for i in range(rows.count()):
            cell = rows.nth(i).locator(f"td:nth-child({quand_index})")
            cell_text = cell.inner_text().strip()
            if slot in cell_text:
                print(f"✅ [P{priority}] Found target slot '{slot}' at row {i+1}")
                plus_button = rows.nth(i).locator("button:has(i.fa-plus)")
                plus_button.click()
                return slot  # Return the slot that was successfully selected
    print("⛔ No priority slots found.")
    return None

def select_user_and_confirm(page):
    print("[STEP] Selecting user...")
    select_button = page.locator("button#u3600_btnSelect0")
    select_button.wait_for(state="visible", timeout=5000)
    select_button.click()

    print("[STEP] Confirming cart...")
    confirm_button = page.locator("button#u3600_btnCheckout0")
    confirm_button.wait_for(state="visible", timeout=5000)
    confirm_button.click()

def finalize_checkout(page):
    print("[STEP] Finalizing checkout...")
    complete_button = page.locator("button#u3600_btnCartShoppingCompleteStep")
    complete_button.wait_for(state="visible", timeout=5000)
    complete_button.click()
    print("✅ Cart section confirmed.")

def confirm_terms_and_submit(page):
    print("[STEP] Accepting conditions...")

    checkbox1 = page.locator("#u3600_chkElectronicPaymentCondition")
    checkbox1.wait_for(state="visible", timeout=5000)
    checkbox1.check()

    checkbox2 = page.locator("#u3600_chkLocationCondition")
    checkbox2.wait_for(state="visible", timeout=5000)
    checkbox2.check()

    print("[STEP] Submitting final confirmation...")

    confirm_button = page.locator("button#u3600_btnCartPaymentCompleteStep")
    confirm_button.wait_for(state="visible", timeout=5000)
    confirm_button.click()

    print("🎉 Reservation fully confirmed!")

def main():
    date_str = get_tomorrows_date_str()
    assert date_str != datetime.today().strftime("%Y-%m-%d"), "❌ ERROR: Today's date is selected. Only tomorrow is allowed."

    wait_until_5pm()

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(storage_state="ricky.json")
        page = context.new_page()

        for attempt in range(RETRIES):
            print(f"[{attempt+1}/{RETRIES}] Checking for time slots on {date_str}...")
            run_search(page, date_str)

            found_slot = try_find_slot(page, PRIORITY_SLOTS)
            if found_slot:
                print(f"🟢 Slot '{found_slot}' selected.")
                page.wait_for_timeout(2000)
                select_user_and_confirm(page)
                page.wait_for_timeout(2000)
                finalize_checkout(page)
                page.wait_for_timeout(2000)
                confirm_terms_and_submit(page)
                break
            else:
                print("🔄 No available slot found. Retrying...")
                time.sleep(3)

        else:
            print("❌ No priority slots found after retry window.")

        page.wait_for_timeout(5000)
        browser.close()

if __name__ == "__main__":
    main()
