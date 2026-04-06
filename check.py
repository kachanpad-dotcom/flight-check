from datetime import datetime, timedelta, timezone
import traceback

from playwright.sync_api import sync_playwright


FLIGHT_NO = "3082"


def tomorrow_jst_parts() -> tuple[str, str, str]:
    jst = timezone(timedelta(hours=9))
    d = datetime.now(jst).date() + timedelta(days=1)
    return str(d.year), str(d.month), str(d.day)


def print_select_info(page, selector: str, label: str) -> None:
    locator = page.locator(selector)
    count = locator.count()
    print(f"{label} count={count}")
    if count == 0:
        return

    try:
        sel = locator.first
        current_value = sel.input_value()
        print(f"{label} current_value={current_value}")

        options = sel.locator("option")
        option_count = options.count()
        print(f"{label} option_count={option_count}")

        max_show = min(option_count, 20)
        for i in range(max_show):
            opt = options.nth(i)
            text = (opt.inner_text() or "").strip()
            value = opt.get_attribute("value") or ""
            print(f"{label} option[{i}] text='{text}' value='{value}'")
    except Exception as e:
        print(f"{label} 読み取り失敗: {e}")


def main() -> None:
    year, month, day = tomorrow_jst_parts()

    print("=== テスト開始 ===")
    print(f"便名: JAL{FLIGHT_NO}")
    print(f"日付: {year}-{month.zfill(2)}-{day.zfill(2)}")

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
            page.goto(
                "https://www.jal.co.jp/jp/ja/dom/flight-status/",
                wait_until="commit",
                timeout=60000,
            )
            page.wait_for_timeout(5000)

            print("=== フォーム部品確認 ===")

            radio = page.locator('input[name="status-dom-select-radio"]')
            print(f"status-dom-select-radio count={radio.count()}")
            for i in range(radio.count()):
                try:
                    r = radio.nth(i)
                    print(
                        f"radio[{i}] "
                        f"value='{r.get_attribute('value')}' "
                        f"checked={r.is_checked()}"
                    )
                except Exception as e:
                    print(f"radio[{i}] 読み取り失敗: {e}")

            flight_input = page.get_by_placeholder("例：101")
            print(f"placeholder 例：101 count={flight_input.count()}")

            print_select_info(
                page,
                'select[name="JS_domIntlStatus_selectFlightDate"]',
                "年select",
            )
            print_select_info(
                page,
                'select[name="JS_domIntlStatus_selectFlightDate1"]',
                "月select",
            )
            print_select_info(
                page,
                'select[name="JS_domIntlStatus_selectFlightDate2"]',
                "日select",
            )

            print("=== ボタン候補 ===")
            buttons = page.locator("button, input[type='submit']")
            button_count = buttons.count()
            print(f"button count={button_count}")
            for i in range(min(button_count, 20)):
                try:
                    b = buttons.nth(i)
                    text = (b.inner_text() or "").strip()
                    value = b.get_attribute("value") or ""
                    print(f"button[{i}] text='{text}' value='{value}'")
                except Exception as e:
                    print(f"button[{i}] 読み取り失敗: {e}")

            print("=== 実入力開始 ===")

            # 便名検索に切り替え
            if radio.count() >= 2:
                radio.nth(1).check()
                page.wait_for_timeout(1000)
                print("radio[1] を選択")
            elif radio.count() == 1:
                radio.first.check()
                page.wait_for_timeout(1000)
                print("radio[0] を選択")
            else:
                print("radioが見つからない")

            if flight_input.count() > 0:
                flight_input.first.fill(FLIGHT_NO)
                print("便名入力完了")
            else:
                raise RuntimeError("便名入力欄が見つかりません")

            # 日付選択
            try:
                y = page.locator('select[name="JS_domIntlStatus_selectFlightDate"]')
                if y.count() > 0:
                    try:
                        y.first.select_option(value=year)
                    except Exception:
                        y.first.select_option(label=year)
                    print(f"年選択: {year}")
            except Exception as e:
                print(f"年選択失敗: {e}")

            try:
                m = page.locator('select[name="JS_domIntlStatus_selectFlightDate1"]')
                if m.count() > 0:
                    candidates = [month, month.zfill(2)]
                    done = False
                    for c in candidates:
                        try:
                            m.first.select_option(value=c)
                            done = True
                            break
                        except Exception:
                            pass
                    if not done:
                        for c in candidates:
                            try:
                                m.first.select_option(label=c)
                                done = True
                                break
                            except Exception:
                                pass
                    print(f"月選択: {month}")
            except Exception as e:
                print(f"月選択失敗: {e}")

            try:
                d = page.locator('select[name="JS_domIntlStatus_selectFlightDate2"]')
                if d.count() > 0:
                    candidates = [day, day.zfill(2)]
                    done = False
                    for c in candidates:
                        try:
                            d.first.select_option(value=c)
                            done = True
                            break
                        except Exception:
                            pass
                    if not done:
                        for c in candidates:
                            try:
                                d.first.select_option(label=c)
                                done = True
                                break
                            except Exception:
                                pass
                    print(f"日選択: {day}")
            except Exception as e:
                print(f"日選択失敗: {e}")

            # 検索ボタンは role/button を優先
            clicked = False
            for name in ["検索する", "検索", "運航状況を検索"]:
                try:
                    locator = page.get_by_role("button", name=name)
                    if locator.count() > 0:
                        locator.first.click()
                        page.wait_for_timeout(5000)
                        print(f"ボタンクリック: {name}")
                        clicked = True
                        break
                except Exception:
                    pass

            if not clicked:
                for i in range(min(button_count, 20)):
                    try:
                        b = buttons.nth(i)
                        text = (b.inner_text() or "").strip()
                        value = b.get_attribute("value") or ""
                        if "検索" in text or "検索" in value:
                            b.click()
                            page.wait_for_timeout(5000)
                            print(f"button[{i}] をクリック")
                            clicked = True
                            break
                    except Exception:
                        pass

            print("=== 検索後チェック ===")
            text = page.locator("body").inner_text(timeout=15000)

            print(f"現在URL: {page.url}")
            print(f"3082を含む: {'3082' in text}")
            print(f"JAL3082を含む: {'JAL3082' in text}")
            print(f"73Hを含む: {'73H' in text}")
            print(f"737-800を含む: {'737-800' in text}")
            print(f"国際線機材を含む: {'国際線機材' in text}")
            print(f"国際線仕様を含む: {'国際線仕様' in text}")

            print("=== 検索後冒頭 ===")
            print(text[:4000])
            print("=== end ===")

        except Exception as e:
            print("=== 例外 ===")
            print(str(e))
            traceback.print_exc()
            raise
        finally:
            browser.close()


if __name__ == "__main__":
    main()
