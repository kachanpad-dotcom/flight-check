import re
from datetime import date, timedelta

from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError


FLIGHT_NO = "JAL3082"
DEP_AIRPORT = "福岡"
ARR_AIRPORT = "成田"


def tomorrow_jst_str() -> str:
    return (date.today() + timedelta(days=1)).isoformat()


def extract_numeric_flight_no(flight_no: str) -> str:
    m = re.search(r"(\d+)$", flight_no.upper().replace(" ", ""))
    if not m:
        raise ValueError(f"便名の数値部分を取得できません: {flight_no}")
    return m.group(1)


def is_international_spec(text: str) -> bool:
    keywords = [
        "国際線機材",
        "国際線仕様",
    ]
    return any(k in text for k in keywords)


def main() -> None:
    flight_number = extract_numeric_flight_no(FLIGHT_NO)
    target_date = tomorrow_jst_str()

    print("=== テスト開始 ===")
    print(f"便名: {FLIGHT_NO}")
    print(f"搭乗日: {target_date}")
    print(f"区間: {DEP_AIRPORT} → {ARR_AIRPORT}")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(locale="ja-JP")

        try:
            # JAL国内線トップ
            page.goto("https://www.jal.co.jp/jp/ja/dom/", wait_until="domcontentloaded", timeout=60000)
            page.wait_for_timeout(3000)

            # ポップアップっぽいものを閉じる
            for text in ["閉じる", "OK", "同意する"]:
                locator = page.get_by_text(text, exact=False)
                if locator.count() > 0:
                    try:
                        locator.first.click(timeout=1000)
                        page.wait_for_timeout(500)
                    except Exception:
                        pass

            # 予約・空席照会っぽい導線を押す
            clicked = False
            for text in ["空席照会", "予約", "航空券予約", "国内線予約", "今すぐ検索"]:
                locator = page.get_by_text(text, exact=False)
                if locator.count() > 0:
                    try:
                        locator.first.click(timeout=3000)
                        page.wait_for_timeout(3000)
                        clicked = True
                        print(f"クリック成功: {text}")
                        break
                    except Exception:
                        pass

            if not clicked:
                print("予約/空席照会導線のクリックは未確定。ページ上で続行を試みます。")

            # 入力欄に総当たりで入力
            inputs = page.locator("input").all()

            for inp in inputs:
                try:
                    placeholder = inp.get_attribute("placeholder") or ""
                    aria = inp.get_attribute("aria-label") or ""
                    name = inp.get_attribute("name") or ""
                    label = f"{placeholder} {aria} {name}"

                    if "便" in label:
                        inp.fill(flight_number, timeout=1500)
                        print("便名入力")
                    elif "出発" in label:
                        inp.fill(DEP_AIRPORT, timeout=1500)
                        print("出発空港入力")
                    elif "到着" in label:
                        inp.fill(ARR_AIRPORT, timeout=1500)
                        print("到着空港入力")
                    elif "日付" in label or "搭乗日" in label:
                        inp.fill(target_date, timeout=1500)
                        print("日付入力")
                except Exception:
                    pass

            # 検索ボタン候補
            for text in ["検索", "空席照会", "次へ", "この条件で検索", "便を検索"]:
                locator = page.get_by_text(text, exact=False)
                if locator.count() > 0:
                    try:
                        locator.first.click(timeout=3000)
                        page.wait_for_load_state("domcontentloaded", timeout=30000)
                        page.wait_for_timeout(4000)
                        print(f"検索クリック成功: {text}")
                        break
                    except Exception:
                        pass

            body_text = page.locator("body").inner_text(timeout=10000)

            print("=== 検索後テキスト冒頭 ===")
            print(body_text[:3000])
            print("=== ここまで ===")

            # 便名が見えるか確認
            if flight_number not in body_text:
                print(f"警告: 画面上で便名 {flight_number} を見つけられていません。")

            # シートマップ導線を押す
            seatmap_clicked = False
            for text in ["シートマップを表示", "シートマップ", "座席表", "座席を確認する"]:
                locator = page.get_by_text(text, exact=False)
                if locator.count() > 0:
                    try:
                        locator.first.click(timeout=5000)
                        page.wait_for_load_state("domcontentloaded", timeout=30000)
                        page.wait_for_timeout(4000)
                        seatmap_clicked = True
                        print(f"シートマップクリック成功: {text}")
                        break
                    except Exception:
                        pass

            if not seatmap_clicked:
                print("シートマップ導線は見つからず。現在画面の内容で判定します。")

            final_text = page.locator("body").inner_text(timeout=10000)

            print("=== 最終テキスト冒頭 ===")
            print(final_text[:5000])
            print("=== ここまで ===")

            # 機材っぽい表記を拾う
            patterns = [
                r"\b73H\b",
                r"\b738\b",
                r"\b737-800\b",
                r"\b787-8\b",
                r"\b787-9\b",
                r"\b767-300ER\b",
                r"\b763\b",
                r"\b788\b",
                r"\b789\b",
            ]
            found = []
            for pat in patterns:
                found.extend(re.findall(pat, final_text, flags=re.IGNORECASE))

            found = sorted(set(found))

            print("=== 判定結果 ===")
            print(f"検出機材表記: {found if found else 'なし'}")

            if is_international_spec(final_text):
                print("判定: 国際線仕様機材")
            else:
                print("判定: 国際線仕様機材ではない、または判定不能")

        except PlaywrightTimeoutError as e:
            print(f"タイムアウト: {e}")
            raise
        finally:
            browser.close()


if __name__ == "__main__":
    main()
