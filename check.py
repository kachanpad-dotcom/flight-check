from playwright.sync_api import sync_playwright
import traceback


URL = "https://www.jal.co.jp/flight-status/dom/"


def force_activate_flightnum_tab(page) -> None:
    selector = 'input[name="form-radio-item"][value="flightNum"]'
    label_selector = 'label[for="form-radio-item-02"]'

    radio = page.locator(selector).first
    label = page.locator(label_selector).first

    print("flightNum radio count=", page.locator(selector).count())
    print("flightNum label count=", page.locator(label_selector).count())

    # 1) labelクリック
    try:
        if label.count() > 0:
            label.click(force=True, timeout=5000)
            page.wait_for_timeout(1500)
            print("label click(force=True) 成功")
            return
    except Exception as e:
        print("label click失敗:", e)

    # 2) radioをforce click
    try:
        radio.click(force=True, timeout=5000)
        page.wait_for_timeout(1500)
        print("radio click(force=True) 成功")
        return
    except Exception as e:
        print("radio force click失敗:", e)

    # 3) JSで直接切替
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
        return
    except Exception as e:
        print("radio JS切替失敗:", e)
        raise RuntimeError("便名検索タブ切替に失敗しました")


def run_one(page, flight_no: str) -> None:
    print("\n==============================")
    print("テスト便名入力:", flight_no)
    print("==============================")

    page.goto(URL, wait_until="commit", timeout=60000)
    page.wait_for_timeout(5000)

    force_activate_flightnum_tab(page)

    forms = page.locator("form")
    print("form count=", forms.count())
    target_form = forms.nth(1)

    # 翌日
    tomorrow_radio = target_form.locator('input[name="dateAttribute"][value="2"]').first
    if tomorrow_radio.count() > 0:
        try:
            tomorrow_radio.click(force=True, timeout=5000)
            page.wait_for_timeout(1000)
            print("dateAttribute=2 click成功")
        except Exception:
            page.evaluate("""
            () => {
                const el = document.querySelector('input[name="dateAttribute"][value="2"]');
                el.checked = true;
                el.dispatchEvent(new Event('change', { bubbles: true }));
            }
            """)
            print("dateAttribute JS切替")

    # airline
    airline = target_form.locator('select[name="airlineCode"]').first
    if airline.count() > 0:
        airline.select_option(value="JAL")
        print("airlineCode=JAL")

    # 便名
    flight_input = target_form.locator('input[name="flightSerNo"]').first
    if flight_input.count() == 0:
        raise RuntimeError("flightSerNoなし")

    flight_input.fill(flight_no)
    print("便名入力完了")

    # 検索
    search_button = target_form.get_by_text("検索する", exact=False).first
    search_button.click(force=True)
    page.wait_for_timeout(6000)

    text = page.locator("body").inner_text()

    print("=== 検索後チェック ===")
    print("URL:", page.url)
    print("3082:", "3082" in text)
    print("082:", "082" in text)
    print("73H:", "73H" in text)
    print("国際線仕様:", "国際線仕様" in text)

    print("=== 冒頭 ===")
    print(text[:2000])


def main():
    with sync_playwright() as p:
        browser = p.firefox.launch(headless=True)
        context = browser.new_context(locale="ja-JP")
        page = context.new_page()

        try:
            print("=== テスト開始 ===")
            run_one(page, "3082")
            run_one(page, "082")

        except Exception as e:
            print("=== 例外 ===")
            print(e)
            traceback.print_exc()
            raise
        finally:
            browser.close()


if __name__ == "__main__":
    main()
