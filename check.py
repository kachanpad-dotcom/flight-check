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


def print_basic_check(page, title: str) -> str:
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
    print(text[:4000])
    print("=== end ===")
    return text


def list_candidate_links(page) -> None:
    print("\n=== 候補リンク一覧 ===")
    links = page.locator("a, button")
    count = links.count()
    print("link/button count =", count)

    keywords = [
        "シート",
        "マップ",
        "座席",
        "機材",
        "詳細",
        "便情報",
        "運航",
    ]

    hit = 0
    for i in range(count):
        try:
            el = links.nth(i)
            tag = el.evaluate("e => e.tagName")
            text = (el.inner_text() or "").strip()
            href = el.get_attribute("href") or ""
            cls = el.get_attribute("class") or ""
            joined = f"{text} {href} {cls}"

            if any(k in joined for k in keywords):
                print(f"[{i}] tag={tag} text='{text}' href='{href}' class='{cls}'")
                hit += 1
        except Exception:
            pass

    if hit == 0:
        print("候補リンクなし")


def try_click_candidates(page) -> None:
    candidates = [
        "シートマップを表示",
        "シートマップ",
        "座席表",
        "座席",
        "機材",
        "詳細",
        "便情報",
    ]

    for label in candidates:
        try:
            locator = page.get_by_text(label, exact=False)
            count = locator.count()
            print(f"\n候補 '{label}' count={count}")
            if count == 0:
                continue

            locator.first.click(force=True, timeout=5000)
            page.wait_for_timeout(5000)

            text = print_basic_check(page, f"クリック後: {label}")

            if (
                "73H" in text
                or "737-800" in text
                or "国際線機材" in text
                or "国際線仕様" in text
            ):
                print(f"→ '{label}' クリックで欲しい情報に到達した可能性あり")
                return

            # 元ページに戻る
            page.go_back(timeout=30000)
            page.wait_for_timeout(5000)

        except Exception as e:
            print(f"'{label}' クリック失敗: {e}")


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
            print_basic_check(page, "検索結果ページ")
            list_candidate_links(page)
            try_click_candidates(page)

        except Exception as e:
            print("=== 例外 ===")
            print(e)
            traceback.print_exc()
            raise
        finally:
            browser.close()


if __name__ == "__main__":
    main()
