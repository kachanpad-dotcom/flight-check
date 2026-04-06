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


def dump_state(page, title: str) -> str:
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
    print("=== 冒頭 ===")
    print(text[:5000])
    print("=== end ===")
    return text


def list_toggle_buttons(page) -> None:
    print("\n=== 詳細ボタン一覧 ===")
    buttons = page.locator("button.js-toggle-show_btn")
    count = buttons.count()
    print("js-toggle-show_btn count =", count)

    for i in range(count):
        try:
            btn = buttons.nth(i)
            text = (btn.inner_text() or "").strip()
            cls = btn.get_attribute("class") or ""
            print(f"[{i}] text='{text}' class='{cls}'")
        except Exception as e:
            print(f"[{i}] 読み取り失敗: {e}")


def click_target_toggle(page) -> None:
    buttons = page.locator("button.js-toggle-show_btn")
    count = buttons.count()
    print("クリック対象ボタン数 =", count)

    if count == 0:
        raise RuntimeError("js-toggle-show_btn が見つかりません")

    target_index = None

    for i in range(count):
        try:
            btn = buttons.nth(i)
            text = (btn.inner_text() or "").strip()
            if "JAL3082" in text or "3082" in text:
                target_index = i
                print(f"JAL3082候補ボタン発見: index={i}")
                break
        except Exception:
            pass

    if target_index is None:
        target_index = 0
        print("3082を含むボタンが見つからないので index=0 を使用")

    btn = buttons.nth(target_index)

    try:
        btn.scroll_into_view_if_needed(timeout=5000)
    except Exception:
        pass

    try:
        btn.click(force=True, timeout=5000)
        page.wait_for_timeout(5000)
        print("詳細ボタンクリック成功")
        return
    except Exception as e:
        print("詳細ボタンクリック失敗:", e)

    try:
        btn.evaluate("(el) => el.click()")
        page.wait_for_timeout(5000)
        print("詳細ボタン JS click成功")
        return
    except Exception as e:
        print("詳細ボタン JS click失敗:", e)

    raise RuntimeError("詳細ボタンを開けませんでした")


def inspect_expanded_area(page) -> None:
    print("\n=== 展開後の候補要素 ===")

    selectors = [
        ".js-toggle-show_target",
        ".toggle_target",
        ".toggle_contents",
        ".toggleBox",
        ".accordion_body",
        ".detail",
        ".flight-detail",
        ".flightDetail",
    ]

    for selector in selectors:
        try:
            loc = page.locator(selector)
            count = loc.count()
            print(f"{selector} count = {count}")
            for i in range(min(count, 3)):
                text = (loc.nth(i).inner_text(timeout=3000) or "").strip()
                if text:
                    print(f"[{selector}][{i}]")
                    print(text[:3000])
        except Exception as e:
            print(f"{selector} 読み取り失敗: {e}")


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
            dump_state(page, "検索結果ページ")
            list_toggle_buttons(page)
            click_target_toggle(page)
            dump_state(page, "詳細展開後")
            inspect_expanded_area(page)

        except Exception as e:
            print("=== 例外 ===")
            print(e)
            traceback.print_exc()
            raise
        finally:
            browser.close()


if __name__ == "__main__":
    main()
