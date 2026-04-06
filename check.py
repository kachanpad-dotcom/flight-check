import re
import traceback
from datetime import date, timedelta

from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError


FLIGHT_NO = "JAL3082"


def tomorrow_jst_str() -> str:
    return (date.today() + timedelta(days=1)).isoformat()


def extract_numeric_flight_no(flight_no: str) -> str:
    m = re.search(r"(\d+)$", flight_no.upper().replace(" ", ""))
    if not m:
        raise ValueError(f"便名の数値部分を取得できません: {flight_no}")
    return m.group(1)


def is_international_spec(text: str) -> bool:
    return ("国際線機材" in text) or ("国際線仕様" in text)


def dump_page(page, title: str, limit: int = 5000) -> None:
    try:
        text = page.locator("body").inner_text(timeout=10000)
        print(f"\n=== {title} ===")
        print(text[:limit])
        print("=== end ===\n")
    except Exception as e:
        print(f"{title} の取得失敗: {e}")


def safe_click_by_text(page, candidates, label):
    for text in candidates:
        try:
            locator = page.get_by_text(text, exact=False)
            count = locator.count()
            print(f"[{label}] 候補 '{text}' count={count}")
            if count > 0:
                locator.first.click(timeout=5000)
                page.wait_for_timeout(3000)
                print(f"[{label}] クリック成功: {text}")
                return True
        except Exception as e:
            print(f"[{label}] クリック失敗: {text} / {e}")
    return False


def main() -> None:
    flight_number = extract_numeric_flight_no(FLIGHT_NO)
    target_date = tomorrow_jst_str()

    print("=== テスト開始 ===")
    print(f"便名: {FLIGHT_NO}")
    print(f"数値便名: {flight_number}")
    print(f"搭乗日: {target_date}")
    print("想定区間: 名古屋(中部) → 成田")

    with sync_playwright() as p:
        browser = p.firefox.launch(
            headless=True
        )
        page = browser.new_page(locale="ja-JP")
        page.set_default_timeout(20000)

        try:
            page.goto(
                "https://www.jal.co.jp/jp/ja/dom/",
                wait_until="commit",
                timeout=90000
            )
            page.wait_for_timeout(5000)
            dump_page(page, "トップページ")

            safe_click_by_text(page, ["閉じる", "OK", "同意する"], "ポップアップ閉じる")

            safe_click_by_text(
                page,
                ["空席照会", "予約", "航空券予約", "国内線予約", "今すぐ検索"],
                "予約導線"
            )
            dump_page(page, "予約導線後")

            inputs = page.locator("input").all()
            print(f"input数: {len(inputs)}")

            for i, inp in enumerate(inputs):
                try:
                    placeholder = inp.get_attribute("placeholder") or ""
                    aria = inp.get_attribute("aria-label") or ""
                    name = inp.get_attribute("name") or ""
                    label = f"{placeholder} {aria} {name}".strip()
                    print(f"input[{i}] label='{label}'")

                    if "便" in label:
                        inp.fill(flight_number, timeout=2000)
                        print(f"input[{i}] 便名入力成功")

                    if "日付" in label or "搭乗日" in label:
                        inp.fill(target_date, timeout=2000)
                        print(f"input[{i}] 日付入力成功")
                except Exception as e:
                    print(f"input[{i}] 入力失敗: {e}")

            dump_page(page, "入力後")

            safe_click_by_text(
                page,
                ["検索", "空席照会", "次へ", "この条件で検索", "便を検索"],
                "検索実行"
            )
            page.wait_for_timeout(5000)
            dump_page(page, "検索後")

            safe_click_by_text(
                page,
                ["シートマップを表示", "シートマップ", "座席表", "座席を確認する"],
                "シートマップ"
            )
            page.wait_for_timeout(5000)
            dump_page(page, "最終画面", 7000)

            final_text = page.locator("body").inner_text(timeout=10000)

            patterns = [
                r"\b73H\b",
                r"\b738\b",
                r"\b737-800\b",
            ]
            found = []
            for pat in patterns:
                found.extend(re.findall(pat, final_text, flags=re.IGNORECASE))
            found = sorted(set(found))

            print("=== 判定結果 ===")
            print(f"検出機材表記: {found if found else 'なし'}")
            print(f"国際線仕様キーワード有無: {is_international_spec(final_text)}")

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
