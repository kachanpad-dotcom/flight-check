from playwright.sync_api import sync_playwright
import traceback
import time


URLS = [
    "https://www.jal.co.jp/flight-status/dom/sp/?FsBtn=flightNum&airlineCode=JAL&dateAttribute=2&flightSerNo=3082",
    "https://www.jal.co.jp/flight-status/dom/sp/?FsBtn=flightNum&airlineCode=JAL&dateAttribute=2&flightSerNo=082",
    "https://www.jal.co.jp/jp/ja/flight-status/dom/sp/?FsBtn=flightNum&airlineCode=JAL&dateAttribute=2&flightSerNo=3082",
    "https://www.jal.co.jp/jp/ja/flight-status/dom/sp/?FsBtn=flightNum&airlineCode=JAL&dateAttribute=2&flightSerNo=082",
]


def goto_with_retry(page, url: str, retries: int = 3) -> None:
    last_error = None
    for attempt in range(1, retries + 1):
        try:
            print(f"アクセス試行 {attempt}/{retries}: {url}")
            page.goto(url, wait_until="commit", timeout=60000)
            page.wait_for_timeout(5000)
            print("アクセス成功")
            return
        except Exception as e:
            last_error = e
            print(f"アクセス失敗 {attempt}/{retries}: {e}")
            if attempt < retries:
                time.sleep(3)
    raise last_error


def run_one(page, url: str) -> None:
    print("\n==============================")
    print("URL:", url)
    print("==============================")

    goto_with_retry(page, url)

    text = page.locator("body").inner_text(timeout=15000)

    print("=== 判定用チェック ===")
    print("現在URL:", page.url)
    print("3082を含む:", "3082" in text)
    print("082を含む:", "082" in text)
    print("73Hを含む:", "73H" in text)
    print("737-800を含む:", "737-800" in text)
    print("国際線機材を含む:", "国際線機材" in text)
    print("国際線仕様を含む:", "国際線仕様" in text)

    print("=== ページ冒頭 ===")
    print(text[:5000])
    print("=== end ===")


def main():
    with sync_playwright() as p:
        browser = p.firefox.launch(headless=True)

        context = browser.new_context(
            locale="ja-JP",
            user_agent=(
                "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) "
                "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 "
                "Mobile/15E148 Safari/604.1"
            ),
            viewport={"width": 390, "height": 844},
            ignore_https_errors=True,
        )

        page = context.new_page()
        page.set_default_timeout(30000)

        try:
            print("=== テスト開始 ===")
            for url in URLS:
                try:
                    run_one(page, url)
                except Exception as e:
                    print("このURLは失敗:", e)

        except Exception as e:
            print("=== 例外 ===")
            print(e)
            traceback.print_exc()
            raise
        finally:
            browser.close()


if __name__ == "__main__":
    main()
