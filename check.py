from playwright.sync_api import sync_playwright
import traceback
import time


URL = "https://www.jal.co.jp/flight-status/dom/"
FLIGHT_NO = "082"


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


def fill_flight_form(page) -> None:
    forms = page.locator("form")
    if forms.count() < 2:
        raise RuntimeError("form[1] が見つかりません")

    target_form = forms.nth(1)

    # hidden FsBtn
    fsbtn = target_form.locator('input[name="FsBtn"]')
    print("FsBtn count =", fsbtn.count())
    if fsbtn.count() > 0:
        print("FsBtn value =", fsbtn.first.get_attribute("value"))

    # dateAttribute=2
    tomorrow_radio = target_form.locator('input[name="dateAttribute"][value="2"]')
    print("dateAttribute=2 count =", tomorrow_radio.count())
    if tomorrow_radio.count() > 0:
        try:
            tomorrow_radio.first.click(force=True, timeout=5000)
            page.wait_for_timeout(500)
            print("dateAttribute=2 click成功")
        except Exception as e:
            print("dateAttribute click失敗:", e)
            target_form.evaluate("""
            (form) => {
                const el = form.querySelector('input[name="dateAttribute"][value="2"]');
                if (!el) throw new Error("dateAttribute=2 not found");
                el.checked = true;
                el.dispatchEvent(new Event('input', { bubbles: true }));
                el.dispatchEvent(new Event('change', { bubbles: true }));
                el.dispatchEvent(new MouseEvent('click', { bubbles: true }));
            }
            """)
            page.wait_for_timeout(500)
            print("dateAttribute=2 JS切替成功")

    # airlineCode = JAL
    airline = target_form.locator('select[name="airlineCode"]')
    print("airlineCode count =", airline.count())
    if airline.count() > 0:
        try:
            airline.first.select_option(value="JAL")
            print("airlineCode=JAL 選択成功")
        except Exception as e:
            print("airlineCode選択失敗:", e)
            target_form.evaluate("""
            (form) => {
                const el = form.querySelector('select[name="airlineCode"]');
                if (!el) throw new Error("airlineCode not found");
                el.value = "JAL";
                el.dispatchEvent(new Event('input', { bubbles: true }));
                el.dispatchEvent(new Event('change', { bubbles: true }));
            }
            """)
            print("airlineCode=JAL JS設定成功")

    # flightSerNo
    flight_input = target_form.locator('input[name="flightSerNo"]')
    print("flightSerNo count =", flight_input.count())
    if flight_input.count() == 0:
        raise RuntimeError("flightSerNo が見つかりません")

    try:
        flight_input.first.fill("")
        flight_input.first.fill(FLIGHT_NO)
        flight_input.first.dispatch_event("input")
        flight_input.first.dispatch_event("change")
        print(f"flightSerNo={FLIGHT_NO} 入力成功")
    except Exception as e:
        print("flightSerNo fill失敗:", e)
        target_form.evaluate(f"""
        (form) => {{
            const el = form.querySelector('input[name="flightSerNo"]');
            if (!el) throw new Error("flightSerNo not found");
            el.value = "{FLIGHT_NO}";
            el.dispatchEvent(new Event('input', {{ bubbles: true }}));
            el.dispatchEvent(new Event('change', {{ bubbles: true }}));
            el.dispatchEvent(new KeyboardEvent('keyup', {{ bubbles: true }}));
        }}
        """)
        print(f"flightSerNo={FLIGHT_NO} JS入力成功")


def click_search(page) -> None:
    btn = page.locator("button.JS_FSFlightNumSearchBtn")
    print("JS_FSFlightNumSearchBtn count =", btn.count())
    if btn.count() == 0:
        raise RuntimeError("JS_FSFlightNumSearchBtn が見つかりません")

    # まず通常クリック
    try:
        btn.first.click(force=True, timeout=5000)
        print("検索ボタン click(force=True) 成功")
        page.wait_for_timeout(5000)
        return
    except Exception as e:
        print("検索ボタン click失敗:", e)

    # 次にJS click
    try:
        page.evaluate("""
        () => {
            const btn = document.querySelector('button.JS_FSFlightNumSearchBtn');
            if (!btn) throw new Error("search button not found");
            btn.click();
        }
        """)
        print("検索ボタン JS click成功")
        page.wait_for_timeout(5000)
        return
    except Exception as e:
        print("検索ボタン JS click失敗:", e)

    # フォーム submit の保険
    try:
        page.evaluate("""
        () => {
            const forms = document.querySelectorAll('form');
            const form = forms[1];
            if (!form) throw new Error("form[1] not found");
            if (typeof form.requestSubmit === "function") {
                form.requestSubmit();
            } else {
                form.submit();
            }
        }
        """)
        print("form submit成功")
        page.wait_for_timeout(5000)
    except Exception as e:
        print("form submit失敗:", e)
        raise


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
            print("URL =", URL)
            print("FLIGHT_NO =", FLIGHT_NO)

            goto_with_retry(page, URL)
            fill_flight_form(page)
            click_search(page)

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
            print(text[:4000])
            print("=== end ===")

        except Exception as e:
            print("=== 例外 ===")
            print(e)
            traceback.print_exc()
            raise
        finally:
            browser.close()


if __name__ == "__main__":
    main()
