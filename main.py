import requests
from bs4 import BeautifulSoup

ACCESS_TOKEN = "ここにトークン"
USER_ID = "ここにユーザーID"

FLIGHT_NUMBER = "JAL123"
TARGET_AIRCRAFT = ["B787-9", "B777-300ER"]

URL = f"https://www.flightradar24.com/data/flights/{FLIGHT_NUMBER.lower()}"

headers = {"User-Agent": "Mozilla/5.0"}
res = requests.get(URL, headers=headers)
soup = BeautifulSoup(res.text, "html.parser")

text = soup.get_text()

found = None
for aircraft in TARGET_AIRCRAFT:
    if aircraft in text:
        found = aircraft
        break

if found:
    message = f"当たり！\n{FLIGHT_NUMBER}\n機材:{found}"

    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }

    data = {
        "to": USER_ID,
        "messages": [{"type": "text", "text": message}]
    }

    requests.post(
        "https://api.line.me/v2/bot/message/push",
        headers=headers,
        json=data
    )
