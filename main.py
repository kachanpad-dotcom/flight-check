import requests
import os

def send_line(msg):
    url = "https://api.line.me/v2/bot/message/push"

    headers = {
        "Authorization": f"Bearer {os.getenv('LINE_CHANNEL_TOKEN')}",
        "Content-Type": "application/json"
    }

    data = {
        "to": os.getenv("LINE_USER_ID"),
        "messages": [
            {
                "type": "text",
                "text": msg
            }
        ]
    }

    response = requests.post(url, headers=headers, json=data)
    print(response.text)


# テスト送信
send_line("🎉 GitHubからLINE通知成功！")
