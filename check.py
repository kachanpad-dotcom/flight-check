from playwright.sync_api import sync_playwright
import traceback


URL = "https://www.jal.co.jp/flight-status/dom/"


def run_one(page, flight_no: str) -> None:
    print("\n==============================")
    print(f"テスト便名入力: {flight_no}")
    print("==============================")

    page.goto(URL, wait_until="commit", timeout=60000)
    page.wait_for_timeout(5000)

    # 便名検索タブへ切替
    tab_radio = page.locator('input[name="form-radio-item"][value="flightNum"]')
    print(f"form-radio-item flightNum count={tab_radio.count()}")
    if tab_radio.count() > 0:
        tab_radio.first.check()
        page.wait_for_timeout(1500)
        print("便名検索タブに切替完了")
    else:
        print("便名検索タブのradioが見つかりません")

    # form[1] を対象
    forms = page.locator("form")
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
        except Exception:
            pass

    # 明日 = value=2 を選ぶ
    tomorrow_radio = target_form.locator('input[name="dateAttribute"][value="2"]')
    if tomorrow_radio.count() > 0:
        tomorrow_radio.first.check()
        page.wait_for_timeout(1000)
        print("dateAttribute=2 を選択")
    else:
        print("dateAttribute=2 が見つかりません")

    # airlineCode = JAL
    airline = target_form.locator('select[name="airlineCode"]')
    print(f"airlineCode count={airline.count()}")
    if airline.count() > 0:
        try:
            airline.first.select_option(value="JAL")
            print("airlineCode=JAL を選択")
        except Exception as e:
            print(f"airlineCode選択失敗: {e}")

    # 便名入力
    flight_input = target_form.locator('input[name="flightSerNo"]')
    print(f"flightSerNo count={flight_input.count()}")
    if flight_input.count() == 0:
        raise RuntimeError("flightSerNo が見つかりません")

    flight_input.first.fill("")
    flight_input.first.fill(flight_no)
    page.wait_for_timeout(500)
    print(f"flightSerNo={flight_no} 入力完了")

    # ボタン押下
    search_button = target_form.get_by_text("検索する", exact=False)
    print(f"検索するボタン count={search_button.count()}")
    if search_button.count() == 0:
        raise RuntimeError("検索するボタンが見つかりません")

    search_button.first.click()
    page.wait_for_timeout(6000)

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

            # まず 3082 で試す
            run_one(page, "3082")

            # ダメなら 082 でも試す
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
