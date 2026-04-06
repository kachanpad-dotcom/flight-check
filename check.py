from playwright.sync_api import sync_playwright
import traceback
import time


TOP_URL = "https://www.jal.co.jp/jp/ja/dom/"


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


def dump_basic(page, title: str) -> None:
    text = page.locator("body").inner_text(timeout=15000)
    print(f"\n=== {title} ===")
    print("現在URL:", page.url)
    print("今すぐ検索するを含む:", "今すぐ検索する" in text)
    print("シートマップを含む:", "シートマップ" in text)
    print("座席を含む:", "座席" in text)
    print("機材を含む:", "機材" in text)
    print("予約を含む:", "予約" in text)
    print("航空券を含む:", "航空券" in text)
    print("=== 冒頭 ===")
    print(text[:4000])
    print("=== end ===")


def close_popups(page) -> None:
    for label in ["閉じる", "OK", "同意する", "確認"]:
        try:
            locator = page.get_by_text(label, exact=False)
            if locator.count() > 0:
                locator.first.click(force=True, timeout=1500)
                page.wait_for_timeout(500)
                print(f"ポップアップ処理: {label}")
        except Exception:
            pass


def list_candidate_buttons(page) -> None:
    print("\n=== ボタン候補一覧 ===")
    loc = page.locator("a, button")
    count = loc.count()
    print("a/button count =", count)

    keywords = [
        "今すぐ検索",
        "検索",
        "予約",
        "航空券",
        "シート",
        "座席",
        "機材",
        "詳細",
    ]

    hit = 0
    for i in range(count):
        try:
            el = loc.nth(i)
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
        print("候補なし")


def click_search_now(page) -> None:
    print("\n=== 今すぐ検索するクリック試行 ===")

    # まずテキストで探す
    candidates = [
        "今すぐ検索する",
        "今すぐ検索",
        "検索する",
    ]

    for label in candidates:
        try:
            locator = page.get_by_text(label, exact=False)
            count = locator.count()
            print(f"候補 '{label}' count={count}")
            if count == 0:
                continue

            locator.first.click(force=True, timeout=5000)
            page.wait_for_timeout(5000)
            print(f"クリック成功: {label}")
            return
        except Exception as e:
            print(f"クリック失敗 {label}: {e}")

    # 次に role=button / link
    for label in candidates:
        try:
            locator = page.get_by_role("button", name=label)
            if locator.count() > 0:
                locator.first.click(force=True, timeout=5000)
                page.wait_for_timeout(5000)
                print(f"button roleクリック成功: {label}")
                return
        except Exception:
            pass

        try:
            locator = page.get_by_role("link", name=label)
            if locator.count() > 0:
                locator.first.click(force=True, timeout=5000)
                page.wait_for_timeout(5000)
                print(f"link roleクリック成功: {label}")
                return
        except Exception:
            pass

    raise RuntimeError("今すぐ検索する導線をクリックできませんでした")


def list_forms(page) -> None:
    print("\n=== form一覧 ===")
    forms = page.locator("form")
    form_count = forms.count()
    print("form count =", form_count)

    for i in range(form_count):
        form = forms.nth(i)
        try:
            action = form.get_attribute("action") or ""
            method = form.get_attribute("method") or ""
            print(f"\n--- form[{i}] action='{action}' method='{method}' ---")

            items = form.locator("input, select, textarea, button")
            item_count = items.count()
            print("item count =", item_count)

            for j in range(min(item_count, 40)):
                item = items.nth(j)
                tag = item.evaluate("el => el.tagName")
                item_type = item.get_attribute("type") or ""
                name = item.get_attribute("name") or ""
                value = item.get_attribute("value") or ""
                placeholder = item.get_attribute("placeholder") or ""
                cls = item.get_attribute("class") or ""
                try:
                    text = (item.inner_text() or "").strip()
                except Exception:
                    text = ""

                print(
                    f"item[{j}] "
                    f"tag='{tag}' type='{item_type}' "
                    f"name='{name}' value='{value}' "
                    f"placeholder='{placeholder}' class='{cls}' text='{text}'"
                )
        except Exception as e:
            print(f"form[{i}] 読み取り失敗: {e}")


def list_iframes(page) -> None:
    print("\n=== iframe一覧 ===")
    frames = page.frames
    print("frame count =", len(frames))
    for i, frame in enumerate(frames):
        try:
            print(f"[{i}] name='{frame.name}' url='{frame.url}'")
        except Exception as e:
            print(f"[{i}] 読み取り失敗: {e}")


def list_detail_candidates(page) -> None:
    print("\n=== 詳細候補リンク一覧 ===")
    loc = page.locator("a, button")
    count = loc.count()
    print("a/button count =", count)

    keywords = [
        "シートマップ",
        "座席",
        "機材",
        "詳細",
        "便",
        "空席",
        "予約",
    ]

    hit = 0
    for i in range(count):
        try:
            el = loc.nth(i)
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
        print("候補なし")


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
            print("TOP_URL =", TOP_URL)

            goto_with_retry(page, TOP_URL)
            close_popups(page)
            dump_basic(page, "トップページ")
            list_candidate_buttons(page)

            click_search_now(page)

            dump_basic(page, "今すぐ検索するクリック後")
            list_iframes(page)
            list_forms(page)
            list_detail_candidates(page)

        except Exception as e:
            print("=== 例外 ===")
            print(e)
            traceback.print_exc()
            raise
        finally:
            browser.close()


if __name__ == "__main__":
    main()
