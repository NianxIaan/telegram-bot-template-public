from flask import Flask, request
import requests
import os
import threading
import time

app = Flask(__name__)

BOT_TOKEN = '7921739120:AAFD5LF8WunXJM96TuBETt6QDuF3bZ0_eWw'
TELEGRAM_API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"
WATCHED_WALLETS = {WATCHED_WALLETS = {
    "0x34780c209d5c575cc1c1ceb57af95d4d2a69ddcf": "Whale #01",
    "0x6decd32f5a2ab9b43bc6ad8923eb6d2395de145b": "Whale #02",
    "0xc6661aaba803f542841335d9585c164d81995b6f": "Whale #03",
    "0xf4241da70734375dff580bfeebf4e5b748424575": "Whale #04",
    "0x940bc3c2022d17d10a6227a0a4e640ec35a05c5c": "Whale #05",
    "0xa29e963992597b21bcdcaa969d571984869c4ff5": "Whale #06",
    "0x34ee844d4e6f3cb19d029e2028e52983dc445f14": "Whale #07",
    "0x89552309d7140e5343821559ef19c0998720292f": "Whale #08",
    "0xed9b8f05224b881a222ece2e20bd2f4bdb71d0f8": "Whale #09",
    "0x5ee84d30c7ee57f63f71c92247ff31f95e26916b": "Whale #10",
    "0x0dd9336991d8642d5e15695eadcfec42d15694cd": "Whale #11",
    "0x585e77dd1334e8b59f5af46841862f65520403af": "Whale #12",
    "0xd32fa356b235430df8fa53c851388d2c30b6119a": "Whale #13",
    "0x61fbf5140a5bf3770d0305fce2c6f84f7c218bd4": "Whale #14",
    "0xd2e281bdf6a2a89b8004a10de76f32803f667238": "Whale #15",
    "0xc9f9f694ae147b1333c4f53266c5ccd5c6e4c04f": "Whale #16",
    "0xa9f5248d100c6217f7811bd13209e3046451a2b1": "Whale #17",
    "0x26ca0fea5c32ef8297c0c98d12fd3b41bbf51b03": "Whale #18",
    "0xc333e80ef2dec2805f239e3f1e810612d294f771": "Whale #19",
    "0x85cedfd30f75a57a59294c9632f2d308c67758d0": "Whale #20",
    "0x74aa5387681505c806ff1e972b12cdfd01406828": "Whale #21",
    "0x1ca3675407963eafb03701a33825b36cd58cea10": "Whale #22",
    "0xbec12bf8e94a6e6a37342a56301d9eb21ee10ee1": "Whale #23",
    "0x8e407b22de830e67ac853ce56e131cab039733a7": "Whale #24"
}

}
LAST_BALANCES = {}

# 가격 조회
def get_price(symbol="bitcoin"):
    url = f"https://api.coingecko.com/api/v3/simple/price?ids={symbol}&vs_currencies=usd&include_24hr_change=true"
    try:
        response = requests.get(url)
        data = response.json()
        price = data[symbol]["usd"]
        change = data[symbol]["usd_24h_change"]
        return f"{symbol.upper()} 현재가: ${price:,.2f} (24h: {change:+.2f}%)"
    except Exception as e:
        return f"{symbol.upper()} 가격 조회 실패: {e}"

# 텔레그램 메세지 전송
def send_telegram_message(chat_id, text):
    requests.post(
        f"{TELEGRAM_API_URL}/sendMessage",
        json={"chat_id": chat_id, "text": text}
    )

# 지갑잔고 조회 함수 (etherscan 사용 예시)
def get_wallet_usdc_balance(address):
    url = f"https://api.ethplorer.io/getAddressInfo/{address}?apiKey=freekey"
    try:
        res = requests.get(url)
        data = res.json()
        tokens = data.get("tokens", [])
        for token in tokens:
            if token["tokenInfo"]["symbol"].lower() == "usdc":
                raw = float(token["rawBalance"]) / 10 ** 6
                return raw
    except:
        return None
    return None

# 🐋 고래 지갑 감시 루프 (백그라운드)
def whale_watch_loop():
    while True:
        for addr, label in WATCHED_WALLETS.items():
            balance = get_wallet_usdc_balance(addr)
            if balance is None:
                continue
            prev = LAST_BALANCES.get(addr, balance)
            if abs(balance - prev) >= 100000:  # 10만 USDC 이상 변화
                text = f"📡 {label} 감지됨\n잔고 변화: {prev:,.0f} → {balance:,.0f} USDC"
                send_telegram_message(YOUR_CHAT_ID, text)
            LAST_BALANCES[addr] = balance
        time.sleep(600)  # 10분마다 반복

# 웹훅 수신
@app.route('/', methods=['POST'])
def webhook():
    data = request.get_json()
    if "message" in data and "text" in data["message"]:
        chat_id = data["message"]["chat"]["id"]
        text = data["message"]["text"].strip()

        if text == "/price":
            btc = get_price("bitcoin")
            eth = get_price("ethereum")
            reply = f"{btc}\n{eth}"
        elif text == "/whales":
            lines = []
            for addr, label in WATCHED_WALLETS.items():
                bal = LAST_BALANCES.get(addr, "조회중")
                lines.append(f"{label}: {bal} USDC")
            reply = "\n".join(lines)
        else:
            reply = f"니안 봇이 받았어! 네가 보낸 메시지: {text}"

        send_telegram_message(chat_id, reply)
    return "ok", 200

@app.route('/', methods=['GET'])
def index():
    return 'Bot is running!', 200

if __name__ == '__main__':
    # YOUR_CHAT_ID를 본인의 텔레그램 사용자 ID로 대체
    global YOUR_CHAT_ID
    YOUR_CHAT_ID = os.environ.get("ADMIN_CHAT_ID", "jackpotxdjenny")  # 배포 시 ENV로 설정 추천

    # 🛰️ 백그라운드 스레드 실행
    threading.Thread(target=whale_watch_loop, daemon=True).start()

    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
