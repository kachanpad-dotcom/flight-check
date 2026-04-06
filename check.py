import requests
from datetime import datetime, timedelta, timezone


FLIGHT_NO = "3082"


def tomorrow_jst():
    jst = timezone(timedelta(hours=9))
    return (datetime.now(jst) + timedelta(days=1)).strftime("%Y%m%d")


def main():
    date = tomorrow_jst()

    print("=== テスト開始 ===")
    print(f"便名: JAL{FLIGHT_NO}")
    print(f"日付: {date}")

    # 仮URL（まずは取得できるか確認）
    url = f"https://www.jal.co.jp/dom/flight-status/?flightNumber={FLIGHT_NO}&flightDate={date}"

    print(f"URL: {url}")

    try:
        res = requests.get(url, timeout=20)
        text = res.text

        print("=== 判定用チェック ===")
        print(f"3082を含む: {'3082' in text}")
        print(f"73Hを含む: {'73H' in text}")
        print(f"737-800を含む: {'737-800' in text}")
        print(f"国際線機材を含む: {'国際線機材' in text}")
        print(f"国際線仕様を含む: {'国際線仕様' in text}")

        print("\n=== 先頭2000文字 ===")
        print(text[:2000])

    except Exception as e:
        print("エラー:", e)


if __name__ == "__main__":
    main()
