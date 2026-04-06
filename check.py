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


def dump_text_flags(page, title: str) -> None:
    text = page.locator("body").inner_text(timeout=15000)
    print(f"\n=== {title} ===")
    print("現在URL:", page.url)
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

        reqs = []
        ress = []
        console_logs = []

        def on_request(req):
            if "jal.co.jp" in req.url:
                reqs.append((req.method, req.url))
                print(f"[request] {req.method} {req.url}")

        def on_response(res):
            if "jal.co.jp" in res.url:
                body_preview = None
                try:
                    if any(x in res.url for x in ["fltInfoWeb", "detail", "seat", "map", "aircraft", "flight-status"]):
                        body_preview = res.text()[:1500]
                except Exception:
                    body_preview = None
                ress.append((res.status, res.url, body_preview))
                print(f"[response] {res.status} {res.url}")

        def on_console(msg):
            console_logs.append(f"{msg.type}: {msg.text}")
            print(f"[console] {msg.type}: {msg.text}")

        page.on("request", on_request)
        page.on("response", on_response)
        page.on("console", on_console)

        try:
            print("=== テスト開始 ===")
            print("URL =", URL)

            goto_with_retry(page, URL)
            dump_text_flags(page, "初期表示")

            buttons = page.locator("button.js-toggle-show_btn")
            count = buttons.count()
            print("\n=== 詳細ボタン一覧 ===")
            print("js-toggle-show_btn count =", count)
            if count == 0:
                raise RuntimeError("js-toggle-show_btn が見つかりません")

            target = None
            for i in range(count):
                btn = buttons.nth(i)
                text = (btn.inner_text() or "").strip()
                print(f"[{i}] text='{text}'")
                if "3082" in text:
                    target = btn
                    print(f"JAL3082候補ボタン発見: index={i}")
                    break

            if target is None:
                target = buttons.first
                print("3082を含むボタンが見つからないので先頭を使用")

            print("\n=== ボタン周辺HTML(クリック前) ===")
            try:
                print(target.evaluate("(el) => el.outerHTML"))
            except Exception as e:
                print("button outerHTML取得失敗:", e)

            try:
                print("\n--- 親要素 outerHTML ---")
                print(target.evaluate("(el) => el.parentElement ? el.parentElement.outerHTML : ''"))
            except Exception as e:
                print("parent outerHTML取得失敗:", e)

            try:
                print("\n--- 祖父要素 outerHTML ---")
                print(target.evaluate("""
                (el) => {
                    const p = el.parentElement;
                    const gp = p ? p.parentElement : null;
                    return gp ? gp.outerHTML : '';
                }
                """))
            except Exception as e:
                print("grandparent outerHTML取得失敗:", e)

            try:
                target.scroll_into_view_if_needed(timeout=5000)
            except Exception:
                pass

            target.click(force=True, timeout=5000)
            print("\n詳細ボタンクリック成功")
            page.wait_for_timeout(6000)

            dump_text_flags(page, "クリック後")

            print("\n=== request log tail ===")
            for method, url in reqs[-20:]:
                print(method, url)

            print("\n=== response log tail ===")
            for status, url, preview in ress[-20:]:
                print(status, url)
                if preview:
                    print("--- preview ---")
                    print(preview)
                    print("--- end preview ---")

            print("\n=== console log tail ===")
            for msg in console_logs[-20:]:
                print(msg)

            print("\n=== クリック後のbutton周辺HTML ===")
            try:
                print(target.evaluate("(el) => el.outerHTML"))
            except Exception as e:
                print("button outerHTML取得失敗:", e)

            try:
                print("\n--- 親要素 outerHTML ---")
                print(target.evaluate("(el) => el.parentElement ? el.parentElement.outerHTML : ''"))
            except Exception as e:
                print("parent outerHTML取得失敗:", e)

            try:
                print("\n--- 祖父要素 outerHTML ---")
                print(target.evaluate("""
                (el) => {
                    const p = el.parentElement;
                    const gp = p ? p.parentElement : null;
                    return gp ? gp.outerHTML : '';
                }
                """))
            except Exception as e:
                print("grandparent outerHTML取得失敗:", e)

        except Exception as e:
            print("=== 例外 ===")
            print(e)
            traceback.print_exc()
            raise
        finally:
            browser.close()


if __name__ == "__main__":
    main()
