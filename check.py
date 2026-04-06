from playwright.sync_api import sync_playwright
import traceback
import time


URL = "https://www.jal.co.jp/jp/ja/flight-status/dom/?FsBtn=flightNum&airlineCode=JAL&dateAttribute=2&flightSerNo=3082"


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


def print_flags(text: str, title: str) -> None:
    print(f"\n=== {title} ===")
    print("3082を含む:", "3082" in text)
    print("082を含む:", "082" in text)
    print("73Hを含む:", "73H" in text)
    print("737-800を含む:", "737-800" in text)
    print("国際線機材を含む:", "国際線機材" in text)
    print("国際線仕様を含む:", "国際線仕様" in text)
    print("シートマップを含む:", "シートマップ" in text)
    print("座席を含む:", "座席" in text)
    print("機材を含む:", "機材" in text)


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
            print("URL =", URL)

            goto_with_retry(page, URL)

            btn = page.locator('button.js-toggle-show_btn[aria-controls="toggle-0"]').first
            target = page.locator("#toggle-0").first

            print("button count =", page.locator('button.js-toggle-show_btn[aria-controls="toggle-0"]').count())
            print("toggle-0 count =", page.locator("#toggle-0").count())

            if btn.count() == 0 or target.count() == 0:
                raise RuntimeError("必要要素が見つかりません")

            print("aria-expanded(before) =", btn.get_attribute("aria-expanded"))

            # 一応クリック
            try:
                btn.click(force=True, timeout=5000)
                page.wait_for_timeout(2000)
                print("button click成功")
            except Exception as e:
                print("button click失敗:", e)

            print("aria-expanded(after) =", btn.get_attribute("aria-expanded"))

            # 1) hiddenのまま textContent を読む
            text_content = target.evaluate("(el) => el.textContent || ''")
            print_flags(text_content, "toggle-0 textContent")

            print("\n=== toggle-0 textContent 冒頭 ===")
            print(text_content[:5000])
            print("=== end ===")

            # 2) innerHTML を読む
            inner_html = target.evaluate("(el) => el.innerHTML || ''")
            print("\n=== toggle-0 innerHTML 冒頭 ===")
            print(inner_html[:8000])
            print("=== end ===")

            # 3) 強制表示して inner_text を読む
            page.evaluate("""
            () => {
                const el = document.querySelector('#toggle-0');
                if (!el) throw new Error('toggle-0 not found');
                el.style.display = 'block';
                el.hidden = false;
                el.setAttribute('style', 'display: block;');
            }
            """)
            page.wait_for_timeout(1000)

            forced_text = target.inner_text(timeout=5000)
            print_flags(forced_text, "toggle-0 強制表示後 inner_text")

            print("\n=== toggle-0 強制表示後 inner_text 冒頭 ===")
            print(forced_text[:5000])
            print("=== end ===")

        except Exception as e:
            print("=== 例外 ===")
            print(e)
            traceback.print_exc()
            raise
        finally:
            browser.close()


if __name__ == "__main__":
    main()
