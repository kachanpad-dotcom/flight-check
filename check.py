from playwright.sync_api import sync_playwright
import traceback
import time


URL = "https://www.jal.co.jp/flight-status/dom/"
FLIGHT_NO = "082"  # 今回はこれだけ試す


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


def force_activate_flightnum_tab(page) -> None:
    selector = 'input[name="form-radio-item"][value="flightNum"]'
    label_selector = 'label[for="form-radio-item-02"]'

    radio_count = page.locator(selector).count()
    label_count = page.locator(label_selector).count()

    print("flightNum radio count=", radio_count)
    print("flightNum label count=", label_count)

    if label_count > 0:
        try:
            page.locator(label_selector).first.click(force=True, timeout=5000)
            page.wait_for_timeout(1500)
            print("label click(force=True) 成功")
            return
        except Exception as e:
            print("label click失敗:", e)

    if radio_count > 0:
        try:
            page.locator(selector).first.click(force=True, timeout=5000)
            page.wait_for_timeout(1500)
            print("radio click(force=True) 成功")
            return
        except Exception as e:
            print("radio force click失敗:", e)

    try:
        page.evaluate("""
        () => {
            const radio = document.querySelector('input[name="form-radio-item"][value="flightNum"]');
            if (!radio) throw new Error("flightNum radio not found");
            radio.checked = true;
            radio.dispatchEvent(new Event('input', { bubbles: true }));
            radio.dispatchEvent(new Event('change', { bubbles: true }));
            radio.dispatchEvent(new MouseEvent('click', { bubbles: true }));
        }
        """)
        page.wait_for_timeout(1500)
        print("radio JS切替 成功")
    except Exception as e:
        print("radio JS切替失敗:", e)
        raise RuntimeError("便名検索タブ切替に失敗しました")


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
            print("便名:", FLIGHT_NO)

            goto_with_retry(page, URL)

            force_activate_flightnum_tab(page)

            forms = page.locator("form")
            form_count = forms.count()
            print("form count=", form_count)
            if form_count < 2:
                raise RuntimeError("便名検索フォームが見つかりません")

            target_form = forms.nth(1)

            tomorrow_radio = target_form.locator('input[name="dateAttribute"][value="2"]')
            print("dateAttribute=2 count=", tomorrow_radio.count())
            if tomorrow_radio.count() > 0:
                try:
                    tomorrow_radio.first.click(force=True, timeout=5000)
                    page.wait_for_timeout(1000)
                    print("dateAttribute=2 click成功")
                except Exception as e:
                    print("dateAttribute click失敗:", e)
                    page.evaluate("""
                    () => {
                        const el = document.querySelector('input[name="dateAttribute"][value="2"]');
                        if (!el) throw new Error("dateAttribute=2 not found");
                        el.checked = true;
                        el.dispatchEvent(new Event('change', { bubbles: true }));
                    }
                    """)
                    page.wait_for_timeout(1000)
                    print("dateAttribute JS切替成功")

            airline = target_form.locator('select[name="airlineCode"]')
            print("airlineCode count=", airline.count())
            if airline.count() > 0:
                airline.first.select_option(value="JAL")
                print("airlineCode=JAL")

            flight_input = target_form.locator('input[name="flightSerNo"]')
            print("flightSerNo count=", flight_input.count())
            if flight_input.count() == 0:
                raise RuntimeError("flightSerNoなし")

            flight_input.first.fill("")
            flight_input.first.fill(FLIGHT_NO)
            print("便名入力完了")

            search_button = target_form.get_by_text("検索する", exact=False)
            print("検索するボタン count=", search_button.count())
            if search_button.count() == 0:
                raise RuntimeError("検索するボタンが見つかりません")

            search_button.first.click(force=True, timeout=5000)
            page.wait_for_timeout(6000)

            text = page.locator("body").inner_text(timeout=15000)

            print("=== 検索後チェック ===")
            print("URL:", page.url)
            print("3082:", "3082" in text)
            print("082:", "082" in text)
            print("73H:", "73H" in text)
            print("737-800:", "737-800" in text)
            print("国際線機材:", "国際線機材" in text)
            print("国際線仕様:", "国際線仕様" in text)

            print("=== 冒頭 ===")
            print(text[:3000])

        except Exception as e:
            print("=== 例外 ===")
            print(e)
            traceback.print_exc()
            raise
        finally:
            browser.close()


if __name__ == "__main__":
    main()
