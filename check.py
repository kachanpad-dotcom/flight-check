from datetime import datetime, timedelta, timezone
from playwright.sync_api import sync_playwright
import traceback


FLIGHT_NO = "3082"


def tomorrow_jst() -> str:
    jst = timezone(timedelta(hours=9))
    return (datetime.now(jst) + timedelta(days=1)).strftime("%Y%m%d")


def main() -> None:
    flight_date = tomorrow_jst()

    urls = [
        f"https://www.jal.co.jp/jp/ja/dom/flight-status/?flightNumber={FLIGHT_NO}&flightDate={flight_date}",
        f"https://www.jal.co.jp/dom/flight-status/?flightNumber={FLIGHT_NO}&flightDate={flight_date}",
        "https://www.jal.co.jp/jp/ja/dom/flight-status/",
        "https://www.jal.co.jp/dom/flight-status/",
    ]

    print("=== テスト開始 ===")
    print(f"便名: JAL{FLIGHT_NO}")
    print(f"日付: {flight_date}")

    with sync_playwright() as p:
        browser = p.firefox.launch(headless=True)

        context = browser.new_context(
            locale="ja-JP",
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:137.0) "
                "Gecko/20100101 Firefox/137.0"
            ),
            ignore_https_errors=True,
        )

        page = context.new_page()
        page.set_default_timeout(30000)

        loaded = False
        last_error = None

        try:
            for url in urls:
                print(f"\n--- アクセス試行: {url}")
                try:
                    page.goto(url, wait_until="commit", timeout=60000)
                    page.wait_for_timeout(5000)

                    current_url = page.url
                    text = page.locator("body").inner_text(timeout=15000)

                    print(f"現在URL: {current_url}")
                    print("=== ページ冒頭 ===")
                    print(text[:2500])
                    print("=== end ===")

                    print("=== 判定用チェック ===")
                    print(f"3082を含む: {'3082' in text}")
                    print(f"JAL3082を含む: {'JAL3082' in text}")
                    print(f"73Hを含む: {'73H' in text}")
                    print(f"737-800を含む: {'737-800' in text}")
                    print(f"国際線機材を含む: {'国際線機材' in text}")
                    print(f"国際線仕様を含む: {'国際線仕様' in text}")

                    loaded = True
                    break

                except Exception as e:
                    last_error = e
                    print(f"アクセス失敗: {e}")

            if not loaded:
                print("\n=== 最終エラー ===")
                print(last_error)
                if last_error:
                    traceback.print_exception(type(last_error), last_error, last_error.__traceback__)

        finally:
            browser.close()


if __name__ == "__main__":
    main()
