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


def print_airline_options(target_form) -> None:
    airline = target_form.locator('select[name="airlineCode"]')
    print("airlineCode count =", airline.count())
    if airline.count() == 0:
        return

    options = airline.first.locator("option")
    print("airline option count =", options.count())
    for i in range(options.count()):
        opt = options.nth(i)
        try:
            text = (opt.inner_text() or "").strip()
            value = opt.get_attribute("value")
            selected = opt.evaluate("el => el.selected")
            print(f"airline option[{i}] text='{text}' value='{value}' selected={selected}")
        except Exception as e:
            print(f"airline option[{i}] 読み取り失敗: {e}")


def print_form_state(target_form, label: str) -> None:
    print(f"\n=== {label} ===")

    try:
        fsbtn = target_form.locator('input[name="FsBtn"]')
        if fsbtn.count() > 0:
            print("FsBtn =", fsbtn.first.get_attribute("value"))
    except Exception as e:
        print("FsBtn 読み取り失敗:", e)

    try:
        radios = target_form.locator('input[name="dateAttribute"]')
        print("dateAttribute count =", radios.count())
        for i in range(radios.count()):
            r = radios.nth(i)
            print(
                f"dateAttribute[{i}] value='{r.get_attribute('value')}' "
                f"checked={r.is_checked()}"
            )
    except Exception as e:
        print("dateAttribute 読み取り失敗:", e)

    try:
        airline = target_form.locator('select[name="airlineCode"]')
        if airline.count() > 0:
            print("airline current value =", airline.first.input_value())
    except Exception as e:
        print("airline current value 読み取り失敗:", e)

    try:
        flight_input = target_form.locator('input[name="flightSerNo"]')
        if flight_input.count() > 0:
            cls = flight_input.first.get_attribute("class")
            value = flight_input.first.input_value()
            print("flightSerNo value =", value)
            print("flightSerNo class =", cls)
    except Exception as e:
        print("flightSerNo 読み取り失敗:", e)

    try:
        btn = target_form.locator("button.JS_FSFlightNumSearchBtn")
        if btn.count() > 0:
            print("button outerHTML =", btn.first.evaluate("el => el.outerHTML"))
    except Exception as e:
        print("button 読み取り失敗:", e)


def activate_tab(page) -> None:
    selector = 'input[name="form-radio-item"][value="flightNum"]'
    label_selector = 'label[for="form-radio-item-02"]'

    print("flightNum radio count =", page.locator(selector).count())
    print("flightNum label count =", page.locator(label_selector).count())

    try:
        if page.locator(label_selector).count() > 0:
            page.locator(label_selector).first.click(force=True, timeout=5000)
            page.wait_for_timeout(1500)
            print("label click成功")
            return
    except Exception as e:
        print("label click失敗:", e)

    try:
        if page.locator(selector).count() > 0:
            page.locator(selector).first.click(force=True, timeout=5000)
            page.wait_for_timeout(1500)
            print("radio click成功")
            return
    except Exception as e:
        print("radio click失敗:", e)

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
    print("radio JS切替成功")


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

        requests_log = []
        responses_log = []
        console_log = []

        def on_request(req):
            if "jal.co.jp" in req.url:
                requests_log.append((req.method, req.url))
                print(f"[request] {req.method} {req.url}")

        def on_response(res):
            if "jal.co.jp" in res.url:
                responses_log.append((res.status, res.url))
                print(f"[response] {res.status} {res.url}")

        def on_console(msg):
            console_log.append(msg.text)
            print(f"[console] {msg.type}: {msg.text}")

        page.on("request", on_request)
        page.on("response", on_response)
        page.on("console", on_console)

        try:
            print("=== テスト開始 ===")
            print("URL =", URL)
            print("FLIGHT_NO =", FLIGHT_NO)

            goto_with_retry(page, URL)
            activate_tab(page)

            forms = page.locator("form")
            print("form count =", forms.count())
            if forms.count() < 2:
                raise RuntimeError("form[1] が見つかりません")

            target_form = forms.nth(1)

            print_airline_options(target_form)
            print_form_state(target_form, "入力前")

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

            # airlineCode は value を見て JAL を選ぶ
            airline = target_form.locator('select[name="airlineCode"]')
            if airline.count() > 0:
                selected = False
                for candidate in ["JAL", "JL", "0"]:
                    try:
                        airline.first.select_option(value=candidate)
                        page.wait_for_timeout(300)
                        print(f"airlineCode value={candidate} 選択成功")
                        selected = True
                        break
                    except Exception:
                        pass

                if not selected:
                    try:
                        airline.first.select_option(label="JAL")
                        page.wait_for_timeout(300)
                        print("airlineCode label=JAL 選択成功")
                        selected = True
                    except Exception as e:
                        print("airlineCode 選択失敗:", e)

            # 便名入力
            flight_input = target_form.locator('input[name="flightSerNo"]')
            if flight_input.count() == 0:
                raise RuntimeError("flightSerNo が見つかりません")

            inp = flight_input.first
            inp.click()
            inp.fill("")
            page.wait_for_timeout(200)
            inp.type(FLIGHT_NO, delay=100)
            page.wait_for_timeout(200)
            inp.dispatch_event("input")
            inp.dispatch_event("change")
            inp.dispatch_event("blur")
            page.wait_for_timeout(500)
            print("flightSerNo 入力完了")

            print_form_state(target_form, "入力後")

            # 検索ボタン
            btn = target_form.locator("button.JS_FSFlightNumSearchBtn")
            if btn.count() == 0:
                raise RuntimeError("JS_FSFlightNumSearchBtn が見つかりません")

            try:
                btn.first.click(force=True, timeout=5000)
                print("検索ボタン click成功")
            except Exception as e:
                print("検索ボタン click失敗:", e)
                page.evaluate("""
                () => {
                    const btn = document.querySelector('button.JS_FSFlightNumSearchBtn');
                    if (!btn) throw new Error("search button not found");
                    btn.click();
                }
                """)
                print("検索ボタン JS click成功")

            page.wait_for_timeout(6000)

            text = page.locator("body").inner_text(timeout=15000)

            print("\n=== 検索後チェック ===")
            print("URL:", page.url)
            print("3082:", "3082" in text)
            print("082:", "082" in text)
            print("73H:", "73H" in text)
            print("737-800:", "737-800" in text)
            print("国際線機材:", "国際線機材" in text)
            print("国際線仕様:", "国際線仕様" in text)

            print("\n=== 検索後冒頭 ===")
            print(text[:3000])

            print("\n=== request log tail ===")
            for method, url in requests_log[-15:]:
                print(method, url)

            print("\n=== response log tail ===")
            for status, url in responses_log[-15:]:
                print(status, url)

            print("\n=== console log tail ===")
            for msg in console_log[-20:]:
                print(msg)

        except Exception as e:
            print("=== 例外 ===")
            print(e)
            traceback.print_exc()
            raise
        finally:
            browser.close()


if __name__ == "__main__":
    main()
