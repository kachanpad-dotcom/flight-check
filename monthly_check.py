import json
import os
import re
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List

import requests
from playwright.sync_api import sync_playwright


DATA_FILE = Path("data.json")

LINE_CHANNEL_TOKEN = os.getenv("LINE_CHANNEL_TOKEN")
LINE_USER_ID = os.getenv("LINE_USER_ID")

TARGET_KEYWORD = "国際線仕様機材"

# 月次: JAL予約画面用
# url は「翌月分の予約結果ページURL」を入れる
# 便名ごとに表示されたカードから判定する
MONTHLY_TARGETS = [
    {
        "flight_no": "JAL3082",
        "url": "https://booking.jal.co.jp/jl/dom-bkg/upsell/outbound",
        "flight_label_pattern": r"JAL\s*3082",
    },
    # 追加例
    # {
    #     "flight_no": "JAL3084",
    #     "url": "https://booking.jal.co.jp/jl/dom-bkg/upsell/outbound",
    #     "flight_label_pattern": r"JAL\s*3084",
    # },
]


def load_data() -> Dict[str, Any]:
    if not DATA_FILE.exists():
        return {
            "monthly": {},
            "daily": {},
            "errors": {
                "monthly": {},
                "daily": {},
            },
        }

    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {
            "monthly": {},
            "daily": {},
            "errors": {
                "monthly": {},
                "daily": {},
            },
        }


def save_data(data: Dict[str, Any]) -> None:
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def send_line_message(message: str) -> None:
    if not LINE_CHANNEL_TOKEN or not LINE_USER_ID:
        print("LINE secrets are not set.")
        print(message)
        return

    url = "https://api.line.me/v2/bot/message/push"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {LINE_CHANNEL_TOKEN}",
    }
    payload = {
        "to": LINE_USER_ID,
        "messages": [{"type": "text", "text": message[:5000]}],
    }

    response = requests.post(url, headers=headers, json=payload, timeout=30)
    print("LINE status:", response.status_code)
    print(response.text)
    response.raise_for_status()


def normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def next_month_key_jst() -> str:
    jst = timezone(timedelta(hours=9))
    now = datetime.now(jst)
    year = now.year
    month = now.month + 1
    if month == 13:
        year += 1
        month = 1
    return f"{year:04d}-{month:02d}"


def goto_with_retry(page, url: str, retries: int = 3) -> None:
    last_error = None
    for attempt in range(1, retries + 1):
        try:
            print(f"Access attempt {attempt}/{retries}: {url}")
            page.goto(url, wait_until="commit", timeout=60000)
            page.wait_for_timeout(5000)
            return
        except Exception as e:
            last_error = e
            print(f"Access failed {attempt}/{retries}: {e}")
            if attempt < retries:
                time.sleep(3)

    if last_error:
        raise last_error
    raise RuntimeError("Unknown access error")


def find_flight_card_text(page, flight_label_pattern: str) -> str:
    candidates = page.locator("section, article, li, div")
    count = candidates.count()

    for i in range(min(count, 700)):
        try:
            el = candidates.nth(i)
            text = el.inner_text(timeout=500)
            if not text:
                continue

            normalized = normalize_text(text)
            if re.search(flight_label_pattern, normalized, flags=re.IGNORECASE):
                if len(normalized) >= 30:
                    return normalized
        except Exception:
            continue

    body_text = normalize_text(page.locator("body").inner_text(timeout=15000))
    if re.search(flight_label_pattern, body_text, flags=re.IGNORECASE):
        return body_text

    raise RuntimeError("便カードを見つけられませんでした")


def extract_equipment(card_text: str) -> str:
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
        r"\b359\b",
        r"\bA350-900\b",
    ]

    hits: List[str] = []
    for pat in patterns:
        hits.extend(re.findall(pat, card_text, flags=re.IGNORECASE))

    uniq = sorted(set(hits))
    return ", ".join(uniq) if uniq else "不明"


def check_monthly_target(target: Dict[str, str]) -> Dict[str, Any]:
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
            goto_with_retry(page, target["url"])
            card_text = find_flight_card_text(page, target["flight_label_pattern"])
            return {
                "flight_no": target["flight_no"],
                "equipment": extract_equipment(card_text),
                "is_target": TARGET_KEYWORD in card_text,
                "matched_text": card_text[:3000],
                "url": page.url,
            }
        finally:
            browser.close()


def main() -> None:
    data = load_data()
    monthly_state = data.get("monthly", {})
    errors = data.get("errors", {})
    monthly_errors = errors.get("monthly", {})

    next_month = next_month_key_jst()
    notify_messages: List[str] = []
    error_messages: List[str] = []

    if next_month not in monthly_state:
        monthly_state[next_month] = {}

    for target in MONTHLY_TARGETS:
        flight_no = target["flight_no"]

        try:
            current = check_monthly_target(target)
            monthly_errors[flight_no] = False

            previous = monthly_state[next_month].get(flight_no)
            monthly_state[next_month][flight_no] = current

            if current["is_target"]:
                if previous is None:
                    notify_messages.append(
                        "\n".join(
                            [
                                "📅 月次チェック",
                                f"対象月: {next_month}",
                                f"便名: {flight_no}",
                                f"機材: {current['equipment']}",
                                "判定: 国際線仕様機材",
                            ]
                        )
                    )
                else:
                    changed = (
                        previous.get("equipment") != current.get("equipment")
                        or previous.get("is_target") != current.get("is_target")
                    )
                    if changed:
                        notify_messages.append(
                            "\n".join(
                                [
                                    "📅 月次チェック更新",
                                    f"対象月: {next_month}",
                                    f"便名: {flight_no}",
                                    f"前回機材: {previous.get('equipment', '不明')}",
                                    f"今回機材: {current['equipment']}",
                                    "判定: 国際線仕様機材",
                                ]
                            )
                        )

        except Exception as e:
            prev_error = monthly_errors.get(flight_no, False)
            if not prev_error:
                error_messages.append(
                    "\n".join(
                        [
                            "⚠️ 月次取得失敗",
                            f"便名: {flight_no}",
                            f"エラー: {str(e)}",
                        ]
                    )
                )
            monthly_errors[flight_no] = True

    data["monthly"] = monthly_state
    errors["monthly"] = monthly_errors
    data["errors"] = errors
    save_data(data)

    all_messages = notify_messages + error_messages
    if all_messages:
        send_line_message("\n\n".join(all_messages))
    else:
        print("No monthly changes.")


if __name__ == "__main__":
    main()
