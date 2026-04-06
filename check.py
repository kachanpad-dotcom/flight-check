import json
import os
from pathlib import Path
from typing import Dict, Any, List, Optional

import requests

DATA_FILE = Path("data.json")

# ここに監視したい便名を入れる
FLIGHTS_TO_CHECK = [
    "JAL208",
    "JAL123",
]

LINE_CHANNEL_TOKEN = os.getenv("LINE_CHANNEL_TOKEN")
LINE_USER_ID = os.getenv("LINE_USER_ID")


def load_data() -> Dict[str, Any]:
    if not DATA_FILE.exists():
        return {"flights": {}, "errors": {}}

    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"flights": {}, "errors": {}}


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
        "messages": [
            {
                "type": "text",
                "text": message[:5000]
            }
        ]
    }

    response = requests.post(url, headers=headers, json=payload, timeout=30)
    print("LINE status:", response.status_code)
    print(response.text)
    response.raise_for_status()


def get_flight_equipment(flight_no: str) -> Optional[str]:
    """
    ここを実際の取得処理に差し替える。
    取れたら機材名の文字列、取れなければ None を返す。
    """

    # 仮実装
    sample_map = {
        "JAL208": "B737-800",
        "JAL123": "A350-900",
    }
    return sample_map.get(flight_no)


def main() -> None:
    data = load_data()
    flights_state = data.get("flights", {})
    errors_state = data.get("errors", {})

    changed_messages: List[str] = []
    error_messages: List[str] = []

    for flight_no in FLIGHTS_TO_CHECK:
        try:
            current_equipment = get_flight_equipment(flight_no)

            if not current_equipment:
                prev_error = errors_state.get(flight_no, False)

                # 取得失敗時は最初の1回だけ通知
                if not prev_error:
                    error_messages.append(
                        f"⚠️ 情報取得失敗\n便名: {flight_no}\n機材情報を取得できませんでした。"
                    )

                errors_state[flight_no] = True
                continue

            # 取得成功したらエラー状態解除
            errors_state[flight_no] = False

            prev_equipment = flights_state.get(flight_no)

            if prev_equipment is None:
                # 初回は通知して保存
                changed_messages.append(
                    f"🆕 初回取得\n便名: {flight_no}\n機材: {current_equipment}"
                )
                flights_state[flight_no] = current_equipment
                continue

            if prev_equipment != current_equipment:
                changed_messages.append(
                    f"✈️ 機材変更を検知\n便名: {flight_no}\n前回: {prev_equipment}\n今回: {current_equipment}"
                )
                flights_state[flight_no] = current_equipment

        except Exception as e:
            prev_error = errors_state.get(flight_no, False)

            if not prev_error:
                error_messages.append(
                    f"⚠️ 情報取得失敗\n便名: {flight_no}\nエラー: {str(e)}"
                )

            errors_state[flight_no] = True

    data["flights"] = flights_state
    data["errors"] = errors_state
    save_data(data)

    all_messages = changed_messages + error_messages

    if all_messages:
        send_line_message("\n\n".join(all_messages))
    else:
        print("No changes.")


if __name__ == "__main__":
    main()
