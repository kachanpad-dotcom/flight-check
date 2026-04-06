import re
import traceback
from datetime import datetime, timedelta, timezone

from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError


FLIGHT_NO = "3082"


def tomorrow_jst_parts() -> tuple[str, str, str]:
    jst = timezone(timedelta(hours=9))
    d = datetime.now(jst).date() + timedelta(days=1)
    return str(d.year), str(d.month), str(d.day)


def dump_page(page, title: str, limit: int = 5000) -> None:
    try:
        text = page.locator("body").inner_text(timeout=10000)
        print(f"\n=== {title} ===")
        print(text[:limit])
        print("=== end ===\n")
    except Exception as e:
        print(f"{title} の取得失敗: {e}")


def main() -> None:
    year, month, day = tomorrow_jst_parts()

    print("=== テスト開始 ===")
    print(f"便名: JAL{FLIGHT_NO}")
    print(f"日付: {year}-{month.zfill(2)}-{day.zfill(2)}")

    with sync_playwright() as p:
        browser = p.firefox.launch(headless=True)
        page = browser.new_page(locale="ja-JP")
        page.set_default_timeout(20000)

        try:
            # トップではなく運航状況ページを直接開く
            page.goto(
                "https://www.jal.co.jp/jp/ja/dom/flight-status/",
                wait_until="commit",
                timeout=90000
            )
            page.wait_for_timeout(5000)
            dump_page(page, "運航状況ページ")

            # よくあるポップアップ閉じ
            for text in ["閉じる", "OK", "同意する", "確認"]:
                try:
                    locator = page.get_by_text(text, exact=False)
                    if locator.count() > 0:
                        locator.first.click(timeout=1000)
                        page.wait_for_timeout(500)
                        print(f"ポップアップ処理: {text}")
                except Exception:
                    pass

            # 便名入力欄を狙い撃ち
            flight_input = None

            # placeholder「例：101」を優先
            try:
                locator = page.get_by_placeholder("例：101")
                if locator.count() > 0:
                    flight_input = locator.first
                    print("便名入力欄: placeholder 例：101 を使用")
            except Exception:
                pass

            # name属性でも保険
            if flight_input is None:
                for name in [
                    "status-dom-flight-number",
                    "flightNumber",
                    "flight_number",
                ]:
                    try:
                        locator = page.locator(f'input[name="{name}"]')
                        if locator.count() > 0:
                            flight_input = locator.first
                            print(f"便名入力欄: name={name} を使用")
                            break
                    except Exception:
                        pass

            if flight_input is None:
                # 最後の保険: input群から placeholder/label を見て選ぶ
                inputs = page.locator("input").all()
                for i, inp in enumerate(inputs):
                    try:
                        placeholder = inp.get_attribute("placeholder") or ""
                        aria = inp.get_attribute("aria-label") or ""
                        name = inp.get_attribute("name") or ""
                        label = f"{placeholder} {aria} {name}"
                        if "101" in label or "flight" in label.lower():
                            flight_input = inp
                            print(f"便名入力欄: input[{i}] を使用 / {label}")
                            break
                    except Exception:
                        pass

            if flight_input is None:
                raise RuntimeError("便名入力欄を見つけられませんでした")

            flight_input.fill(FLIGHT_NO)
            print("便名入力完了")

            # 日付の select/input を狙う
            # ログに出ていた name を優先的に使う
            date_filled = False

            date_select_candidates = [
                ('select[name="JS_domIntlStatus_selectFlightDate"]', year),
                ('select[name="JS_domIntlStatus_selectFlightDate1"]', month),
                ('select[name="JS_domIntlStatus_selectFlightDate2"]', day),
            ]

            try:
                ok = 0
                for selector, value in date_select_candidates:
                    locator = page.locator(selector)
                    if locator.count() > 0:
                        locator.first.select_option(value=value)
                        print(f"日付選択: {selector} = {value}")
                        ok += 1
                if ok >= 2:
                    date_filled = True
            except Exception as e:
                print(f"selectでの日付入力失敗: {e}")

            # selectで無理なら input に直接
            if not date_filled:
                for selector, value in [
                    ('input[name="JS_domIntlStatus_selectFlightDate"]', year),
                    ('input[name="JS_domIntlStatus_selectFlightDate1"]', month),
                    ('input[name="JS_domIntlStatus_selectFlightDate2"]', day),
                ]:
                    try:
                        locator = page.locator(selector)
                        if locator.count() > 0:
                            locator.first.fill(value)
                            print(f"日付入力: {selector} = {value}")
                    except Exception as e:
                        print(f"日付入力失敗 {selector}: {e}")

            dump_page(page, "入力後")

            # 検索ボタンをかなり限定して押す
            clicked = False
            for text in ["検索する", "運航状況を検索", "検索"]:
                try:
                    locator = page.get_by_role("button", name=re.compile(text))
                    if locator.count() > 0:
                        locator.first.click(timeout=5000)
                        page.wait_for_timeout(5000)
                        print(f"検索ボタン押下: {text}")
                        clicked = True
                        break
                except Exception:
                    pass

            if not clicked:
                # ボタンroleで無理ならテキスト
                for text in ["検索する", "運航状況を検索"]:
                    try:
                        locator = page.get_by_text(text, exact=False)
                        if locator.count() > 0:
                            locator.first.click(timeout=5000)
                            page.wait_for_timeout(5000)
                            print(f"検索テキスト押下: {text}")
                            clicked = True
                            break
                    except Exception:
                        pass

            dump_page(page, "検索後", 7000)

            final_text = page.locator("body").inner_text(timeout=10000)

            print("=== 判定用チェック ===")
            print(f"3082を含む: {'3082' in final_text}")
            print(f'JAL3082を含む: {"JAL3082" in final_text}')
            print(f'73Hを含む: {"73H" in final_text}')
            print(f'737-800を含む: {"737-800" in final_text}')
            print(f'国際線機材を含む: {"国際線機材" in final_text}')
            print(f'国際線仕様を含む: {"国際線仕様" in final_text}')

        except PlaywrightTimeoutError as e:
            print("=== タイムアウト例外 ===")
            print(str(e))
            traceback.print_exc()
            raise
        except Exception as e:
            print("=== 一般例外 ===")
            print(str(e))
            traceback.print_exc()
            raise
        finally:
            browser.close()


if __name__ == "__main__":
    main()
