from playwright.sync_api import sync_playwright
from datetime import datetime, timedelta, timezone


FLIGHT_NO = "3082"


def tomorrow_jst():
    jst = timezone(timedelta(hours=9))
    return (datetime.now(jst) + timedelta(days=1)).strftime("%Y%m%d")


def main():
    date = tomorrow_jst()

    url = f"https://www.jal.co.jp/dom/flight-status/?flightNumber={FLIGHT_NO}&flightDate={date}"

    print("=== テスト開始 ===")
    print(f"URL: {url}")

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-dev-shm-usage"
            ]
        )

        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120 Safari/537.36"
        )

        page = context.new_page()

        try:
            page.goto(url, timeout=60000)
            page.wait_for_timeout(5000)

            text = page.locator("body").inner_text()

            print("=== 判定用チェック ===")
            print(f"3082を含む: {'3082' in text}")
            print(f"73Hを含む: {'73H' in text}")
            print(f"737-800を含む: {'737-800' in text}")
            print(f"国際線機材を含む: {'国際線機材' in text}")
            print(f"国際線仕様を含む: {'国際線仕様' in text}")

        except Exception as e:
            print("エラー:", e)

        finally:
            browser.close()


if __name__ == "__main__":
    main()
