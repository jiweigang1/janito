from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    page = browser.new_page()
    page.goto("https://example.com")
    # Grab an ARIA-style accessibility tree for the whole page
    ax_tree = page.accessibility.snapshot()
    print(ax_tree)
    browser.close()
