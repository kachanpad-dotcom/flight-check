import os
from pathlib import Path
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

URL = os.getenv("JAL_TEST_URL", "https://booking.jal.co.jp/jl/dom-bkg/upsell/outbound")
OUT_DIR = Path("artifacts")
OUT_DIR.mkdir(exist_ok=True)

KEYWORDS = [
    "国際線仕様機材",
    "787",
    "777",
    "座席モニター",
    "USB",
    "AC電源",
]

def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(locale="ja-JP")
        page = context.new_page()

        print(f"OPEN: {URL}")
        page.goto(URL, wait_until="domcontentloaded", timeout=120000)

        # 画面が落ち着くまで少し待つ
        try:
            page.wait_for_load_state("networkidle", timeout=15000)
        except PlaywrightTimeoutError:
            print("networkidle timeout -> continue")

        page.screenshot(path=str(OUT_DIR / "jal_page.png"), full_page=True)
        html = page.content()
        (OUT_DIR / "jal_page.html").write_text(html, encoding="utf-8")

        text = page.locator("body").inner_text(timeout=10000)
        (OUT_DIR / "jal_page.txt").write_text(text, encoding="utf-8")

        found = []
        for kw in KEYWORDS:
            if kw in text:
                found.append(kw)

        print("===== KEYWORD CHECK =====")
        if found:
            print("FOUND:", ", ".join(found))
        else:
            print("FOUND: none")

        print("===== PAGE TEXT HEAD =====")
        print(text[:3000])

        browser.close()

if __name__ == "__main__":
    main()
