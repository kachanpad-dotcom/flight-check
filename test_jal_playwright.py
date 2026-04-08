from playwright.sync_api import sync_playwright
import random
import time

URL = "https://booking.jal.co.jp/jl/dom-bkg/upsell/outbound"

def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-blink-features=AutomationControlled"
            ]
        )

        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36",
            locale="ja-JP",
            viewport={"width": 1280, "height": 800}
        )

        page = context.new_page()

        # ちょっと待つ（人間っぽく）
        time.sleep(random.uniform(1, 3))

        print("OPEN:", URL)

        page.goto(URL, timeout=120000)

        # 追加で待つ
        time.sleep(random.uniform(3, 6))

        text = page.locator("body").inner_text()

        print("===== RESULT =====")

        if "国際線仕様機材" in text:
            print("FOUND: 国際線仕様機材")
        else:
            print("NOT FOUND")

        print(text[:1000])

        browser.close()

if __name__ == "__main__":
    main()
