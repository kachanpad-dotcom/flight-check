from playwright.sync_api import sync_playwright
import traceback


URL = "https://www.jal.co.jp/flight-status/dom/"


def main() -> None:
    print("=== テスト開始 ===")
    print(f"URL: {URL}")

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

        try:
            page.goto(URL, wait_until="commit", timeout=60000)
            page.wait_for_timeout(5000)

            text = page.locator("body").inner_text(timeout=15000)
            print("=== ページ冒頭 ===")
            print(text[:3000])
            print("=== end ===")

            print("\n=== form一覧 ===")
            forms = page.locator("form")
            form_count = forms.count()
            print(f"form count={form_count}")

            for i in range(form_count):
                form = forms.nth(i)
                try:
                    action = form.get_attribute("action") or ""
                    method = form.get_attribute("method") or ""
                    print(f"\n--- form[{i}] action='{action}' method='{method}' ---")

                    inputs = form.locator("input, select, textarea, button")
                    item_count = inputs.count()
                    print(f"item count={item_count}")

                    for j in range(min(item_count, 80)):
                        item = inputs.nth(j)
                        tag = item.evaluate("el => el.tagName")
                        item_type = item.get_attribute("type") or ""
                        name = item.get_attribute("name") or ""
                        value = item.get_attribute("value") or ""
                        placeholder = item.get_attribute("placeholder") or ""
                        aria = item.get_attribute("aria-label") or ""
                        try:
                            visible_text = (item.inner_text() or "").strip()
                        except Exception:
                            visible_text = ""

                        print(
                            f"item[{j}] "
                            f"tag='{tag}' type='{item_type}' "
                            f"name='{name}' value='{value}' "
                            f"placeholder='{placeholder}' aria='{aria}' "
                            f"text='{visible_text}'"
                        )
                except Exception as e:
                    print(f"form[{i}] 読み取り失敗: {e}")

            print("\n=== input全体から候補だけ抽出 ===")
            all_items = page.locator("input, select, button")
            all_count = all_items.count()
            print(f"all item count={all_count}")

            keywords = [
                "flight", "便", "date", "日付", "status", "search",
                "FLT", "DATE", "CARR", "APORT", "DPORT", "FsBtn"
            ]

            for i in range(all_count):
                try:
                    item = all_items.nth(i)
                    tag = item.evaluate("el => el.tagName")
                    item_type = item.get_attribute("type") or ""
                    name = item.get_attribute("name") or ""
                    value = item.get_attribute("value") or ""
                    placeholder = item.get_attribute("placeholder") or ""
                    aria = item.get_attribute("aria-label") or ""
                    text2 = f"{tag} {item_type} {name} {value} {placeholder} {aria}".lower()

                    if any(k.lower() in text2 for k in keywords):
                        print(
                            f"candidate[{i}] "
                            f"tag='{tag}' type='{item_type}' "
                            f"name='{name}' value='{value}' "
                            f"placeholder='{placeholder}' aria='{aria}'"
                        )
                except Exception:
                    pass

        except Exception as e:
            print("=== 例外 ===")
            print(str(e))
            traceback.print_exc()
            raise
        finally:
            browser.close()


if __name__ == "__main__":
    main()
