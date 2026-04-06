import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests


DATA_FILE = Path("data.json")

LINE_CHANNEL_TOKEN = os.getenv("LINE_CHANNEL_TOKEN")
LINE_USER_ID = os.getenv("LINE_USER_ID")

# 日次: 航空情報サイト用
# ここはあとで使うサイトに合わせて get_daily_equipment() を差し替える
DAILY_TARGETS = [
    "JAL3082",
    # "JAL3084",
]

# 変更後がこれらなら通知対象
TARGET_EQUIPMENT_KEYWORDS = [
    "73H",
    "737-800",
    "788",
    "787-8",
    "789",
    "787-9",
    "763",
    "767-300ER",
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


def is_target_equipment(equipment: str) -> bool:
    normalized = equipment.upper()
    return any(keyword.upper() in normalized for keyword in TARGET_EQUIPMENT_KEYWORDS)


def get_daily_equipment(flight_no: str) -> Optional[str]:
    """
    ここを航空情報サイト用に差し替える。
    戻り値:
      - 例: "73H"
      - 例: "B737-800"
      - 取れなければ None
    """

    # 仮実装
    sample_map = {
        "JAL3082": "73H",
    }
    return sample_map.get(flight_no)


def main() -> None:
    data = load_data()
    daily_state = data.get("daily", {})
    errors = data.get("errors", {})
    daily_errors = errors.get("daily", {})

    notify_messages: List[str] = []
    error_messages: List[str] = []

    for flight_no in DAILY_TARGETS:
        try:
            current_equipment = get_daily_equipment(flight_no)

            if not current_equipment:
                prev_error = daily_errors.get(flight_no, False)
                if not prev_error:
                    error_messages.append(
                        "\n".join(
                            [
                                "⚠️ 日次取得失敗",
                                f"便名: {flight_no}",
                                "機材情報を取得できませんでした。",
                            ]
                        )
                    )
                daily_errors[flight_no] = True
                continue

            daily_errors[flight_no] = False

            prev = daily_state.get(flight_no)

            if prev is None:
                daily_state[flight_no] = {
                    "equipment": current_equipment,
                    "is_target": is_target_equipment(current_equipment),
                }

                notify_messages.append(
                    "\n".join(
                        [
                            "🆕 日次初回取得",
                            f"便名: {flight_no}",
                            f"機材: {current_equipment}",
                            f"判定: {'対象' if is_target_equipment(current_equipment) else '対象外'}",
                        ]
                    )
                )
                continue

            prev_equipment = prev.get("equipment", "")
            current_is_target = is_target_equipment(current_equipment)

            if prev_equipment != current_equipment and current_is_target:
                notify_messages.append(
                    "\n".join(
                        [
                            "✈️ 日次変更検知",
                            f"便名: {flight_no}",
                            f"前回機材: {prev_equipment}",
                            f"今回機材: {current_equipment}",
                            "判定: 対象機材",
                        ]
                    )
                )

            daily_state[flight_no] = {
                "equipment": current_equipment,
                "is_target": current_is_target,
            }

        except Exception as e:
            prev_error = daily_errors.get(flight_no, False)
            if not prev_error:
                error_messages.append(
                    "\n".join(
                        [
                            "⚠️ 日次取得失敗",
                            f"便名: {flight_no}",
                            f"エラー: {str(e)}",
                        ]
                    )
                )
            daily_errors[flight_no] = True

    data["daily"] = daily_state
    errors["daily"] = daily_errors
    data["errors"] = errors
    save_data(data)

    all_messages = notify_messages + error_messages
    if all_messages:
        send_line_message("\n\n".join(all_messages))
    else:
        print("No daily changes.")


if __name__ == "__main__":
    main()
