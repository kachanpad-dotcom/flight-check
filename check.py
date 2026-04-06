from playwright.sync_api import sync_playwright
import traceback


URL = "https://www.jal.co.jp/flight-status/dom/"


def force_activate_flightnum_tab(page) -> None:
    radio = page.locator('input[name="form-radio-item"][value="flightNum"]').first
    label = page.locator('label[for="form-radio-item-02"]').first

    print(f"flightNum radio count={page.locator('input[name=\"form-radio-item\"][value=\"flightNum\"]').count()}")
    print(f"flightNum label count={page.locator('label[for=\"form-radio-item-02\"]').count()}")

    # 1) labelクリック
    try:
        if label.count() > 0:
            label.click(force=True, timeout=5000)
            page.wait_for_timeout(1500)
            print("label click(force=True) 成功")
            return
    except Exception as e:
        print(f"label click失敗: {e}")

    # 2) radioをforce click
    try:
        radio.click(force=True, timeout=5000)
        page.wait_for_timeout(1500)
        print("radio click(force=True) 成功")
        return
    except Exception as e:
        print(f"radio force click失敗: {e}")

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
        print(f"radio JS切替失敗: {e}")
        raise RuntimeError("便名検索タブ切替に失敗しました")


def run_one(page, flight_no: str) -> None:
    print("\n==============================")
    print(f"テスト便名入力: {flight_no}")
    print("==============================")

    page.goto(URL, wait_until="commit", timeout=60000)
    page.wait_for_timeout(5000)

    force_activate_flightnum_tab(page)

    forms = page.locator("form")
    print(f"form count={forms.count()}")
    target_form = forms.nth(1)

    # 翌日指定
    radios = target_form.locator('input[name="dateAttribute"]')
    print(f"dateAttribute count={radios.count()}")
    for i in range(radios.count()):
        r = radios.nth(i)
        try:
            print(
                f"dateAttribute[{i}] value='{r.get_attribute('value')}' checked={r.is_checked()}"
            )
        except Exception as e:
            print(f"dateAttribute[{i}] 読み取り失敗: {e}")

    tomorrow_radio = target_form.locator('input[name="dateAttribute"][value="2"]').first
    if tomorrow_radio.count() > 0:
        try:
            tomorrow_radio.click(force=True, timeout=5000)
            page.wait_for_timeout(1000)
            print("dateAttribute=2 click(force=True) 成功")
        except Exception as e:
            print(f"dateAttribute force click失敗: {e}")
            try:
                page.evaluate("""
                () => {
                    const el = document.querySelector('input[name="dateAttribute"][value="2"]');
                    if (!el) throw new Error("dateAttribute=2 not found");
                    el.checked = true;
                    el.dispatchEvent(new Event('input', { bubbles: true }));
                    el.dispatchEvent(new Event('change', { bubbles: true }));
                    el.dispatchEvent(new MouseEvent('click', { bubbles: true }));
                }
                """)
                page.wait_for_timeout(1000)
                print("dateAttribute=2 JS切替 成功")
            except Exception as e2:
                print(f"dateAttribute JS切替失敗: {e2}")

    airline = target_form.locator('select[name="airlineCode"]').first
    print(f"airlineCode count={target_form.locator('select[name=\"airlineCode\"]').count()}")
    if airline.count() > 0:
        try:
            airline.select_option(value="JAL")
            print("airlineCode=JAL を選択")
        except Exception as e:
            print(f"airlineCode選択失敗: {e}")

    flight_input = target_form.locator('input[name="flightSerNo"]').first
    print(f"flightSerNo count={target_form.locator('input[name=\"flightSerNo\"]').count()}")
    if flight_input.count() == 0:
        raise RuntimeError("flightSerNo が見つかりません")

    flight_input.fill("")
    flight_input.fill(flight_no)
    page.wait_for_timeout(500)
    print(f"flightSerNo={flight_no} 入力完了")

    search_button = target_form.get_by_text("検索する", exact=False).first
    print(f"検索するボタン count={target_form.get_by_text('検索する', exact=False).count()}")
    if search_button.count() == 0:
        raise RuntimeError("検索するボタンが見つかりません")

    try:
        search_button.click(force=True, timeout=5000)
        page.wait_for_timeout(6000)
        print("検索ボタンクリック成功")
    except Exception as e:
        print(f"検索ボタンクリック失敗: {e}")
        try:
            page.evaluate("""
            () => {
                const forms = document.querySelectorAll('form');
                const form = forms[1];
                if (!form) throw new Error("target form not found");
                const btn = Array.from(form.querySelectorAll('button')).find(b => (b.innerText || '').includes('検索する'));
                if (!btn) throw new Error("search button not found");
                btn.click();
            }
            """)
            page.wait_for_timeout(6000)
            print("検索ボタン JSクリック成功")
        except Exception as e2:
            print(f"検索ボタン JSクリック失敗: {e2}")
            raise

    text = page.locator("body").inner_text(timeout=15000)

    print("=== 検索後チェック ===")
    print(f"現在URL: {page.url}")
    print(f"3082を含む: {'3082' in text}")
    print(f"JAL3082を含む: {'JAL3082' in text}")
    print(f"082を含む: {'082' in text}")
    print(f"73Hを含む: {'73H' in text}")
    print(f"737-800を含む: {'737-800' in text}")
    print(f"国際線機材を含む: {'国際線機材' in text}")
    print(f"国際線仕様を含む: {'国際線仕様' in text}")

    print("=== 検索後冒頭 ===")
    print(text[:5000])
    print("=== end ===")


def main() -> None:
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
            print(f"URL: {URL}")

            run_one(page, "3082")
            run_one(page, "082")

        except Exception as e:
            print("=== 例外 ===")
            print(str(e))
            traceback.print_exc()
            raise
        finally:
            browser.close()


if __name__ == "__main__":
    main()
