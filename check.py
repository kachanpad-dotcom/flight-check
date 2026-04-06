from playwright.sync_api import sync_playwright
from datetime import datetime, timedelta, timezone
import traceback
import time


URL = "https://www.jal.co.jp/flight-status/dom/"
FLIGHT_NO = "082"


def tomorrow_jst_yyyymmdd() -> str:
    jst = timezone(timedelta(hours=9))
    d = datetime.now(jst).date() + timedelta(days=1)
    return d.strftime("%Y%m%d")


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


def activate_flightnum_tab(page) -> None:
    selector = 'input[name="form-radio-item"][value="flightNum"]'
    label_selector = 'label[for="form-radio-item-02"]'

    print("flightNum radio count =", page.locator(selector).count())
    print("flightNum label count =", page.locator(label_selector).count())

    try:
        if page.locator(label_selector).count() > 0:
            page.locator(label_selector).first.click(force=True, timeout=5000)
            page.wait_for_timeout(1000)
            print("label click成功")
            return
    except Exception as e:
        print("label click失敗:", e)

    try:
        if page.locator(selector).count() > 0:
            page.locator(selector).first.click(force=True, timeout=5000)
            page.wait_for_timeout(1000)
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
    page.wait_for_timeout(1000)
    print("radio JS切替成功")


def fill_form_and_click(page, flight_no: str) -> None:
    forms = page.locator("form")
    if forms.count() < 2:
        raise RuntimeError("form[1] が見つかりません")

    target_form = forms.nth(1)

    # 明日
    tomorrow_radio = target_form.locator('input[name="dateAttribute"][value="2"]')
    print("dateAttribute=2 count =", tomorrow_radio.count())
    if tomorrow_radio.count() > 0:
        try:
            tomorrow_radio.first.click(force=True, timeout=5000)
            page.wait_for_timeout(300)
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
            page.wait_for_timeout(300)
            print("dateAttribute=2 JS切替成功")

    # JAL
    airline = target_form.locator('select[name="airlineCode"]')
    print("airlineCode count =", airline.count())
    if airline.count() > 0:
        try:
            airline.first.select_option(value="JAL")
            page.wait_for_timeout(300)
            print("airlineCode=JAL 選択成功")
        except Exception as e:
            print("airlineCode 選択失敗:", e)

    # 便名
    flight_input = target_form.locator('input[name="flightSerNo"]')
    print("flightSerNo count =", flight_input.count())
    if flight_input.count() == 0:
        raise RuntimeError("flightSerNo が見つかりません")

    inp = flight_input.first
    inp.click()
    inp.fill("")
    page.wait_for_timeout(100)
    inp.type(flight_no, delay=80)
    inp.dispatch_event("input")
    inp.dispatch_event("change")
    inp.dispatch_event("blur")
    page.wait_for_timeout(300)
    print(f"flightSerNo={flight_no} 入力成功")

    # 検索クリック
    btn = target_form.locator("button.JS_FSFlightNumSearchBtn")
    print("JS_FSFlightNumSearchBtn count =", btn.count())
    if btn.count() == 0:
        raise RuntimeError("検索ボタンが見つかりません")

    btn.first.click(force=True, timeout=5000)
    print("検索ボタン click成功")


def main():
    search_date = tomorrow_jst_yyyymmdd()
    api_url = f"https://www.jal.co.jp/fltInfoWeb/flt/get?indSearch=F&carrierCode=JL&flightNo={FLIGHT_NO}&indDate=D&searchDate={search_date}"

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

        captured_response = {"url": None, "status": None, "text": None}

        def on_response(res):
            try:
                url = res.url
                if "/fltInfoWeb/flt/get" in url:
                    captured_response["url"] = url
                    captured_response["status"] = res.status
                    try:
                        captured_response["text"] = res.text()
                    except Exception as e:
                        captured_response["text"] = f"[response text read error] {e}"
                    print(f"[capture] status={res.status} url={url}")
            except Exception as e:
                print("[capture error]", e)

        page.on("response", on_response)

        try:
            print("=== テスト開始 ===")
            print("画面URL =", URL)
            print("想定API =", api_url)
            print("flightNo =", FLIGHT_NO)
            print("searchDate =", search_date)

            goto_with_retry(page, URL)
            activate_flightnum_tab(page)
            fill_form_and_click(page, FLIGHT_NO)

            page.wait_for_timeout(6000)

            print("\n=== APIキャプチャ結果 ===")
            print("captured url =", captured_response["url"])
            print("captured status =", captured_response["status"])

            if captured_response["text"] is not None:
                text = captured_response["text"]
                print("3082:", "3082" in text)
                print("082:", "082" in text)
                print("73H:", "73H" in text)
                print("737-800:", "737-800" in text)
                print("国際線機材:", "国際線機材" in text)
                print("国際線仕様:", "国際線仕様" in text)

                print("\n=== APIレスポンス冒頭 ===")
                print(text[:5000])
                print("=== end ===")
            else:
                print("APIレスポンス本文を取得できませんでした")

            # 保険: 直接APIを叩いてみる
            print("\n=== 直接API取得テスト ===")
            api_res = context.request.get(
                api_url,
                headers={
                    "Referer": "https://www.jal.co.jp/jp/ja/flight-status/dom/",
                    "X-Requested-With": "XMLHttpRequest",
                },
                timeout=60000,
            )
            api_text = api_res.text()
            print("direct status =", api_res.status)
            print("3082:", "3082" in api_text)
            print("082:", "082" in api_text)
            print("73H:", "73H" in api_text)
            print("737-800:", "737-800" in api_text)
            print("国際線機材:", "国際線機材" in api_text)
            print("国際線仕様:", "国際線仕様" in api_text)

            print("\n=== 直接APIレスポンス冒頭 ===")
            print(api_text[:5000])
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
