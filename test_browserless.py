from playwright.sync_api import sync_playwright
import os
import time

# ★ここに自分のトークン入れる
BROWSERLESS_WS = "wss://chrome.browserless.io?token=ここに貼る"

def main():
    with sync_playwright() as p:
        browser = p.chromium.connect_over_cdp(BROWSERLESS_WS)

        context = browser.new_context(locale="ja-JP")
        page = context.new_page()

        print("JAL開く")

        page.goto("https://www.jal.co.jp/jp/ja/", timeout=60000)

        time.sleep(5)

        text = page.locator("body").inner_text()

        if "航空券" in text:
            print("成功：JAL開けた")
        else:
            print("失敗")

        browser.close()

if __name__ == "__main__":
    main()
