from pathlib import Path
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
import time
import random

URL = "https://www.jal.co.jp/jp/ja/"
OUT_DIR = Path("artifacts")
OUT_DIR.mkdir(exist_ok=True)


def safe_text(page):
    try:
        return page.locator("body").inner_text(timeout=5000)
    except Exception:
        return ""


def search_flight(page):
    print("OPEN:", URL)

    try:
        response = page.goto(URL, wait_until="domcontentloaded", timeout=90000)
        print("goto response:", response.status if response else "no response")
    except Exception as e:
        print("goto failed:", repr(e))
        page.screenshot(path=str(OUT_DIR / "goto_failed.png"), full_page=True)
        text = safe_text(page)
        (OUT_DIR / "goto_failed.txt").write_text(text, encoding="utf-8")
        raise

    time.sleep(random.uniform(3, 5))
    page.screenshot(path=str(OUT_DIR / "top.png"), full_page=True)

    text = safe_text(page)
    (OUT_DIR / "top.txt").write_text(text, encoding="utf-8")
    print("PAGE HEAD:")
    print(text[:1000])

    if "システムエラー" in text or "やり直してください" in text:
        print("JAL returned error page")
        return False

    # ここではまだ遷移確認だけ
    return True


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-blink-features=AutomationControlled",
            ],
        )

        context = browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/122.0.0.0 Safari/537.36"
            ),
            locale="ja-JP",
            viewport={"width": 1365, "height": 900},
        )

        page = context.new_page()
        result = search_flight(page)
        print("RESULT:", result)
        browser.close()


if __name__ == "__main__":
    main()
