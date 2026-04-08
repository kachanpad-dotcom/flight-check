import requests

# 試す機体（まず1機）
TARGET_REG = "JA601J"

url = "https://opensky-network.org/api/states/all"

params = {
    "extended": 1
}

res = requests.get(url, params=params, timeout=20)

print("status:", res.status_code)

data = res.json()

states = data.get("states", [])

found = []

for s in states:
    callsign = (s[1] or "").strip()
    icao24 = s[0]

    # callsignにJALが含まれる機体探す
    if "JAL" in callsign:
        found.append({
            "icao24": icao24,
            "callsign": callsign
        })

# 結果表示
print("JAL機体数:", len(found))

for f in found[:10]:
    print(f)
