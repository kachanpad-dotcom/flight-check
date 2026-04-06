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

            body_text = page.locator("body").inner_text(timeout=15000)
            print_flags(body_text, "初期本文")

            btn = page.locator('button.js-toggle-show_btn[aria-controls="toggle-0"]').first
            print("\n=== 詳細ボタン情報 ===")
            print("count =", page.locator('button.js-toggle-show_btn[aria-controls="toggle-0"]').count())

            if btn.count() == 0:
                raise RuntimeError('aria-controls="toggle-0" の詳細ボタンが見つかりません')

            print("button outerHTML =")
            print(btn.evaluate("(el) => el.outerHTML"))
            print("aria-expanded(before) =", btn.get_attribute("aria-expanded"))

            # まずクリック
            try:
                btn.scroll_into_view_if_needed(timeout=5000)
            except Exception:
                pass

            clicked = False

            try:
                btn.click(force=True, timeout=5000)
                page.wait_for_timeout(3000)
                print("button click(force=True) 成功")
                clicked = True
            except Exception as e:
                print("button click失敗:", e)

            if not clicked:
                try:
                    btn.evaluate("(el) => el.click()")
                    page.wait_for_timeout(3000)
                    print("button JS click成功")
                    clicked = True
                except Exception as e:
                    print("button JS click失敗:", e)

            print("aria-expanded(after) =", btn.get_attribute("aria-expanded"))

            # 展開先そのものを直接読む
            target = page.locator("#toggle-0")
            print("\n=== toggle-0 情報 ===")
            print("count =", target.count())

            if target.count() > 0:
                try:
                    outer_html = target.first.evaluate("(el) => el.outerHTML")
                    print("--- toggle-0 outerHTML 冒頭 ---")
                    print(outer_html[:8000])
                    print("--- end ---")
                except Exception as e:
                    print("toggle-0 outerHTML取得失敗:", e)

                try:
                    inner_text = target.first.inner_text(timeout=5000)
                except Exception:
                    inner_text = ""

                print_flags(inner_text, "toggle-0 inner_text")

                if inner_text.strip():
                    print("\n=== toggle-0 text 冒頭 ===")
                    print(inner_text[:4000])
                    print("=== end ===")
            else:
                print("toggle-0 が存在しません")

            # 保険でHTML全体から toggle-0 周辺を抜く
            html = page.content()
            idx = html.find('id="toggle-0"')
            print("\n=== page.content() から toggle-0 周辺 ===")
            if idx >= 0:
                start = max(0, idx - 500)
                end = min(len(html), idx + 8000)
                snippet = html[start:end]
                print(snippet)
            else:
                print('id="toggle-0" が HTML 内に見つかりません')

        except Exception as e:
            print("=== 例外 ===")
            print(e)
            traceback.print_exc()
            raise
        finally:
            browser.close()


if __name__ == "__main__":
    main()
