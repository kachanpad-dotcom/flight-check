import os
import requests

# 環境変数から取得
LINE_CHANNEL_TOKEN = os.environ["LINE_CHANNEL_TOKEN"]
LINE_USER_ID = os.environ["LINE_USER_ID"]

# LINE APIエンドポイント
url = "https://api.line.me/v2/bot/message/push"

# ヘッダー
headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {LINE_CHANNEL_TOKEN}"
}

# 送信データ
data = {
    "to": LINE_USER_ID,
    "messages": [
        {
            "type": "text",
            "text": "テスト送信成功！"
        }
    ]
}

# リクエスト送信
response = requests.post(url, headers=headers, json=data)

# 結果表示（超重要）
print(response.status_code)
print(response.text)
