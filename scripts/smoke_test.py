"""Verifies Playwright + Chromium can launch and load a page.

Runs on every push via .github/workflows/test.yml so a broken Playwright
setup is caught independently of eCARI itself being reachable.
"""

from playwright.sync_api import sync_playwright


def main() -> None:
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto("https://example.com")

        assert page.title() == "Example Domain"

        browser.close()

    print("Playwright-Smoke-Test erfolgreich.")


if __name__ == "__main__":
    main()
