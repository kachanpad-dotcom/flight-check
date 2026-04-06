from playwright.sync_api import sync_playwright
import traceback
import time


URL = "https://www.jal.co.jp/flight-status/dom/"


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


def main():
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
            print("=== テスト開始 ===")
            goto_with_retry(page, URL)

            forms = page.locator("form")
            print("form count =", forms.count())
            if forms.count() < 2:
                raise RuntimeError("form[1] が見つかりません")

            target_form = forms.nth(1)

            print("\n=== form[1] outerHTML ===")
            print(target_form.evaluate("el => el.outerHTML"))

            print("\n=== form[1] 内の button 情報 ===")
            buttons = target_form.locator("button")
            print("button count =", buttons.count())
            for i in range(buttons.count()):
                btn = buttons.nth(i)
                try:
                    print(f"\n--- button[{i}] ---")
                    print("text =", btn.inner_text())
                    print("type =", btn.get_attribute("type"))
                    print("name =", btn.get_attribute("name"))
                    print("value =", btn.get_attribute("value"))
                    print("id =", btn.get_attribute("id"))
                    print("class =", btn.get_attribute("class"))
                    print("onclick =", btn.get_attribute("onclick"))
                    print("outerHTML =", btn.evaluate("el => el.outerHTML"))
                except Exception as e:
                    print(f"button[{i}] 読み取り失敗:", e)

            print("\n=== form[1] の input/select 情報 ===")
            items = target_form.locator("input, select")
            print("item count =", items.count())
            for i in range(items.count()):
                item = items.nth(i)
                try:
                    tag = item.evaluate("el => el.tagName")
                    print(
                        f"item[{i}] "
                        f"tag={tag} "
                        f"type={item.get_attribute('type')} "
                        f"name={item.get_attribute('name')} "
                        f"value={item.get_attribute('value')} "
                        f"placeholder={item.get_attribute('placeholder')} "
                        f"class={item.get_attribute('class')}"
                    )
                except Exception as e:
                    print(f"item[{i}] 読み取り失敗:", e)

            print("\n=== form[1] に紐づく script / on* 属性候補 ===")
            scripts = page.locator("script")
            print("script count =", scripts.count())
            for i in range(min(scripts.count(), 30)):
                try:
                    txt = scripts.nth(i).inner_text()
                    if any(k in txt for k in ["flightSerNo", "dateAttribute", "airlineCode", "FsBtn", "検索", "flightNum"]):
                        print(f"\n--- script[{i}] ---")
                        print(txt[:3000])
                except Exception:
                    pass

        except Exception as e:
            print("=== 例外 ===")
            print(e)
            traceback.print_exc()
            raise
        finally:
            browser.close()


if __name__ == "__main__":
    main()
