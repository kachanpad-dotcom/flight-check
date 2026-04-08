from playwright.sync_api import sync_playwright
import time
import random

URL = "https://www.jal.co.jp/jp/ja/"

def search_flight(page, dep, arr):
    page.goto(URL, timeout=60000)
    time.sleep(random.uniform(2, 4))

    # 出発地クリック
    page.click("text=名古屋（中部）", timeout=10000)
    time.sleep(1)

    page.click("text=東海・北陸")
    time.sleep(1)

    page.click("text=名古屋（中部）")
    time.sleep(1)

    # 到着地クリック
    page.click("text=東京（成田）")
    time.sleep(1)

    page.click("text=東京（成田）")
    time.sleep(1)

    # 検索ボタン
    page.keyboard.press("Enter")
    time.sleep(random.uniform(5, 8))

    text = page.locator("body").inner_text()

    if "国際線仕様機材" in text:
        return True
    return False


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-blink-features=AutomationControlled"]
        )

        context = browser.new_context(
            user_agent="Mozilla/5.0",
            locale="ja-JP"
        )

        page = context.new_page()

        result = search_flight(page, "NGO", "NRT")

        print("RESULT:", result)

        browser.close()


if __name__ == "__main__":
    main()
