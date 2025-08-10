import time
import json
from datetime import datetime, timedelta
from playwright.sync_api import sync_playwright
from zoneinfo import ZoneInfo


RETRIES = 40

def load_priority_slots():
    """
    Load priority slots from a JSON file created from form responses.
    Example slots.json:
    {
      "slots": ["19:00 - 20:00", "20:00 - 21:00"]
    }
    """
    try:
        with open("slots.json", "r") as f:
            data = json.load(f)
            return data.get("slots", [])
    except Exception as e:
        print(f"❌ Could not load slots.json: {e}")
        return []
    
def now_montreal():
    return datetime.now(ZoneInfo("America/Toronto"))

def get_target_slot(all_slots):
    """
    Decide which single slot to search for based on current hour.
    If run just before the release (e.g., 17:59), bump to next hour.
    """
    now = now_montreal()
    hour = now.hour

    # Grace period: if between :00 and :02, use the previous hour
    if 0 <= now.minute <= 2:
        hour -= 1

    mapping = {
        9: "12:00 - 13:00",
        #16: "19:00 - 20:00",  # run at 5pm → book 7–8pm slot
        18: "21:00 - 22:00",  # run at 7pm → book 9–10pm slot
    }

    target = mapping.get(hour)
    if target and target in all_slots:
        print(f"🎯 Target slot for this run: {target}")
        return [target]  # return as list so try_find_slot works
    else:
        print("❌ No valid target slot at this time.")
        return []


def get_tomorrows_date_str():
    return (datetime.today() + timedelta(days=1)).strftime("%Y-%m-%d")

def run_search(page, date_str):
    page.goto("https://loisirs.montreal.ca/IC3/#/U6510/search")
    page.wait_for_timeout(1000)

    print("[UI] Setting filters...")
    page.locator("input#u6510_edSearch").fill("pickleball")
    page.locator("button#u6510_btnTreeBorough").click()
    page.wait_for_timeout(500)

    # ✅ Only select Saint-Leonard if not already checked
    saint_leonard_checkbox = page.locator("input#u2000_chkValue11")
    saint_leonard_checkbox.wait_for(state="visible")
    if not saint_leonard_checkbox.is_checked():
        saint_leonard_checkbox.click()

    page.locator("button#u2000_btnTreeSelectConfirm").click()

    date_input = page.locator("input[name='reserveDate']")
    date_input.fill("")
    date_input.fill(date_str)
    page.wait_for_timeout(2000)

def try_find_slot(page, priority_slots, prefer_second=False):
    """
    prefer_second = False → Script A: select the FIRST occurrence immediately
    prefer_second = True  → Script B: select the SECOND occurrence immediately
    """
    print("[SCAN] Scanning for priority slots (with pagination)...")
    matched = 0  # number of matches found so far

    while True:  # loop through result pages
        page.wait_for_selector("div#searchResult")

        # find the 'Quand' column index
        headers = page.locator("div#searchResult thead tr th")
        quand_index = None
        for i in range(headers.count()):
            header_text = headers.nth(i).inner_text().strip().lower()
            if "quand" in header_text:
                quand_index = i + 1
                break

        if quand_index is None:
            print("❌ 'Quand' column not found.")
            return None

        rows = page.locator("div#searchResult tbody tr")

        # Loop through rows and slots
        for priority, slot in enumerate(priority_slots, 1):
            for i in range(rows.count()):
                cell = rows.nth(i).locator(f"td:nth-child({quand_index})")
                cell_text = cell.inner_text().strip()
                if slot in cell_text:
                    matched += 1
                    print(f"🔍 Found match #{matched}: '{slot}' at row {i+1}")

                    # Decide based on counter
                    if not prefer_second and matched == 1:
                        print(f"✅ [P{priority}] Script A booking FIRST occurrence '{slot}'")
                        rows.nth(i).locator("button:has(i.fa-plus)").click()
                        return slot

                    if prefer_second and matched == 2:
                        print(f"✅ [P{priority}] Script B booking SECOND occurrence '{slot}'")
                        rows.nth(i).locator("button:has(i.fa-plus)").click()
                        return slot

        # --- pagination handling ---
        next_li = page.locator("li.pagination-next")
        if next_li.count() > 0:
            li_class = next_li.first.get_attribute("class") or ""
            if "disabled" in li_class:
                print("⛔ Last page reached.")
                break
            else:
                print("➡️ Moving to next page...")
                next_li.locator("a.ng-binding", has_text=">").click()
                page.wait_for_timeout(1500)
                continue
        else:
            break

    # --- nothing booked ---
    if prefer_second:
        print("⛔ Fewer than 2 total matches found — Script B will skip.")
    else:
        print("⛔ No matches found — Script A will skip.")
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
    # 🔑 Load slots from JSON, but filter to just the one relevant for this hour
    all_slots = load_priority_slots()
    priority_slots = get_target_slot(all_slots)
    if not priority_slots:
        print("❌ No target slot for this run, exiting.")
        return


    date_str = get_tomorrows_date_str()
    assert date_str != datetime.today().strftime("%Y-%m-%d"), "❌ ERROR: Today's date is selected. Only tomorrow is allowed."

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(storage_state="calvin.json")
        page = context.new_page()

        for attempt in range(RETRIES):
            print(f"[{attempt+1}/{RETRIES}] Checking for time slots on {date_str}...")
            run_search(page, date_str)

            found_slot = try_find_slot(page, priority_slots, prefer_second=False)  # Script A → first match
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
