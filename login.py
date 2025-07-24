from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    context = browser.new_context()
    page = context.new_page()
    page.goto("https://loisirs.montreal.ca/IC3/")
    input("🔑 Log in manually, then press Enter to save session...")
    context.storage_state(path="session.json")
    browser.close()
