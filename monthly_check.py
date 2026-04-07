import json
import os
import time
import random
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

import requests

DATA_FILE = Path("data.json")

LINE_CHANNEL_TOKEN = os.getenv("LINE_CHANNEL_TOKEN")
LINE_USER_ID = os.getenv("LINE_USER_ID")

ALL_FLIGHTS = [
    "JAL101", "JAL103", "JAL111", "JAL113", "JAL115", "JAL117", "JAL119", "JAL121",
    "JAL125", "JAL127", "JAL131", "JAL133", "JAL135", "JAL137", "JAL139", "JAL141",
    "JAL143", "JAL145", "JAL147", "JAL149", "JAL151", "JAL153", "JAL158", "JAL185",
    "JAL187", "JAL189", "JAL193", "JAL201", "JAL209", "JAL213", "JAL215", "JAL217",
    "JAL220", "JAL221", "JAL225", "JAL231", "JAL233", "JAL237", "JAL239", "JAL241",
    "JAL253", "JAL255", "JAL257", "JAL259", "JAL263", "JAL265", "JAL267", "JAL277",
    "JAL279", "JAL283", "JAL285", "JAL303", "JAL305", "JAL307", "JAL309", "JAL311",
    "JAL313", "JAL315", "JAL317", "JAL319", "JAL321", "JAL323", "JAL325", "JAL327",
    "JAL329", "JAL331", "JAL333", "JAL335", "JAL373", "JAL375", "JAL377", "JAL431",
    "JAL433", "JAL435", "JAL437", "JAL439", "JAL441", "JAL443", "JAL453", "JAL455",
    "JAL459", "JAL461", "JAL463", "JAL465", "JAL475", "JAL477", "JAL479", "JAL481",
    "JAL483", "JAL485", "JAL487", "JAL491", "JAL493", "JAL495", "JAL497", "JAL499",
    "JAL501", "JAL503", "JAL505", "JAL507", "JAL509", "JAL511", "JAL513", "JAL515",
    "JAL517", "JAL519", "JAL521", "JAL523", "JAL525", "JAL527", "JAL529", "JAL531",
    "JAL541", "JAL543", "JAL545", "JAL551", "JAL553", "JAL555", "JAL557", "JAL565",
    "JAL567", "JAL569", "JAL573", "JAL575", "JAL577", "JAL579", "JAL585", "JAL587",
    "JAL589", "JAL599", "JAL605", "JAL607", "JAL609", "JAL611", "JAL613", "JAL615",
    "JAL623", "JAL625", "JAL627", "JAL629", "JAL631", "JAL633", "JAL635", "JAL637",
    "JAL639", "JAL641", "JAL643", "JAL645", "JAL647", "JAL649", "JAL651", "JAL653",
    "JAL655", "JAL659", "JAL661", "JAL663", "JAL665", "JAL667", "JAL669", "JAL671",
    "JAL687", "JAL695", "JAL901", "JAL903", "JAL905", "JAL907", "JAL909", "JAL913",
    "JAL915", "JAL917", "JAL919", "JAL921", "JAL923", "JAL925", "JAL987", "JAL3009",
    "JAL3083", "JAL3087",
]

ALL_FLIGHTS = list(dict.fromkeys(ALL_FLIGHTS))

INTERNATIONAL_REGS = {
    "JA304J", "JA305J", "JA312J", "JA315J", "JA317J", "JA321J",
    "JA601J", "JA602J", "JA603J", "JA606J", "JA607J", "JA608J",
    "JA610J", "JA611J", "JA612J", "JA613J", "JA614J", "JA615J",
    "JA616J", "JA617J", "JA618J", "JA619J", "JA620J", "JA621J",
    "JA622J", "JA623J", "JA733J", "JA735J", "JA736J", "JA737J",
    "JA738J", "JA739J", "JA740J", "JA741J", "JA823J", "JA826J",
    "JA829J", "JA830J", "JA831J", "JA832J", "JA833J", "JA834J",
    "JA835J", "JA837J", "JA838J", "JA839J", "JA840J", "JA841J",
    "JA842J", "JA843J", "JA844J", "JA845J", "JA846J", "JA847J",
    "JA848J", "JA849J", "JA861J", "JA862J", "JA863J", "JA864J",
    "JA865J", "JA866J", "JA867J", "JA868J", "JA869J", "JA870J",
    "JA871J", "JA872J", "JA873J", "JA874J", "JA875J", "JA876J",
    "JA877J", "JA878J", "JA879J", "JA880J", "JA881J", "JA882J",
}

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/135.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "ja,en-US;q=0.9,en;q=0.8",
    "Referer": "https://www.flightradar24.com/",
    "Origin": "https://www.flightradar24.com",
    "Connection": "keep-alive",
}


def safe_get(d: dict, *keys, default=None):
    cur = d
    for k in keys:
        if not isinstance(cur, dict):
            return default
        cur = cur.get(k)
        if cur is None:
            return default
    return cur


def parse_flight_dict(data: dict) -> Optional[dict]:
    return {
        "reg": data.get("registration"),
        "dep": safe_get(data, "airport", "origin", "code", "iata"),
        "arr": safe_get(data, "airport", "destination", "code", "iata"),
        "model": safe_get(data, "aircraft", "model", "text", default="") or "",
    }


def fetch_once(session: requests.Session, flight_no: str) -> Optional[dict]:
    url = f"https://data-live.flightradar24.com/clickhandler/?flight={flight_no}"
    res = session.get(url, headers=HEADERS, timeout=20)

    print(f"{flight_no} status={res.status_code}")
    print(f"{flight_no} content-type={res.headers.get('content-type')}")

    if res.status_code != 200:
        return None

    text = res.text.strip()

    if not text:
        print(f"{flight_no} empty response")
        return None

    print(f"{flight_no} response head: {text[:200]!r}")

    if text.startswith("Array"):
        print(f"{flight_no} invalid JSON (Array)")
        return None

    if not (text.startswith("{") or text.startswith("[")):
        print(f"{flight_no} non-json response")
        return None

    try:
        data = json.loads(text)
    except Exception as e:
        print(f"{flight_no} json parse failed: {e}")
        return None

    if isinstance(data, dict):
        return parse_flight_dict(data)

    if isinstance(data, list):
        print(f"{flight_no} returned list length={len(data)}")
        if not data:
            return None
        first = data[0]
        if isinstance(first, dict):
            return parse_flight_dict(first)
        return None

    return None


def get_flight_info(session: requests.Session, flight_no: str) -> Optional[dict]:
    try:
        info = fetch_once(session, flight_no)
        if info and info.get("reg"):
            return info

        retry_wait = random.uniform(8, 15)
        print(f"{flight_no} retry after {retry_wait:.1f}s")
        time.sleep(retry_wait)

        info = fetch_once(session, flight_no)
        return info
    except Exception as e:
        print(f"{flight_no} FR24 error: {e}")
        return None


def is_big(model: str) -> bool:
    return any(x in (model or "") for x in ["787", "777"])


def split_into_n_groups(items, n):
    return [items[i::n] for i in range(n)]


def get_current_group():
    now = datetime.utcnow() + timedelta(hours=9)
    hour = now.hour

    run_hours = [6, 9, 12, 15, 18, 21]
    groups = split_into_n_groups(ALL_FLIGHTS, 6)

    if hour in run_hours:
        idx = run_hours.index(hour)
        print(f"▶ グループ{idx + 1}/6 実行")
        return groups[idx]

    print("▶ 実行時刻外なので後半グループ扱い")
    return groups[-1]


def load_data():
    if not DATA_FILE.exists():
        return {"daily": {}, "errors": {"daily": {}}}
    return json.loads(DATA_FILE.read_text(encoding="utf-8"))


def save_data(data):
    DATA_FILE.write_text(
        json.dumps(data, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def send_line(msg):
    if not LINE_CHANNEL_TOKEN or not LINE_USER_ID:
        print(msg)
        return

    requests.post(
        "https://api.line.me/v2/bot/message/push",
        headers={
            "Authorization": f"Bearer {LINE_CHANNEL_TOKEN}",
            "Content-Type": "application/json",
        },
        json={
            "to": LINE_USER_ID,
            "messages": [{"type": "text", "text": msg[:5000]}],
        },
        timeout=20,
    )


def main():
    data = load_data()
    state = data.get("daily", {})
    errors = data.get("errors", {}).get("daily", {})
    messages = []

    target_flights = get_current_group()

    with requests.Session() as session:
        for flight in target_flights:
            info = get_flight_info(session, flight)

            if not info or not info["reg"]:
                if not errors.get(flight):
                    messages.append(f"⚠️取得失敗\n{flight}")
                errors[flight] = True
                time.sleep(random.uniform(7, 11))
                continue

            errors[flight] = False

            reg = info["reg"]
            dep = info["dep"] or "???"
            arr = info["arr"] or "???"
            model = info["model"] or ""

            is_target = reg in INTERNATIONAL_REGS
            big = is_big(model)

            prev = state.get(flight)

            if not prev:
                if big:
                    messages.append(
                        f"🔥大当たり\n"
                        f"{flight}\n"
                        f"{dep} → {arr}\n"
                        f"{model}\n"
                        f"{reg}"
                    )
                elif is_target:
                    messages.append(
                        f"{flight}\n"
                        f"{dep} → {arr}\n"
                        f"{reg}"
                    )

                state[flight] = {"reg": reg}
                time.sleep(random.uniform(7, 11))
                continue

            if prev["reg"] != reg:
                if big:
                    messages.append(
                        f"🔥大当たり\n"
                        f"{flight}\n"
                        f"{dep} → {arr}\n"
                        f"{model}\n"
                        f"{prev['reg']} → {reg}"
                    )
                elif is_target:
                    messages.append(
                        f"{flight}\n"
                        f"{dep} → {arr}\n"
                        f"{prev['reg']} → {reg}"
                    )

            state[flight] = {"reg": reg}
            time.sleep(random.uniform(7, 11))

    data["daily"] = state
    data["errors"] = {"daily": errors}
    save_data(data)

    if messages:
        send_line("\n\n".join(messages))
    else:
        print("no change")


if __name__ == "__main__":
    main()
