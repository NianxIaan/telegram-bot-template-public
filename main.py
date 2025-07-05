from flask import Flask, request
import requests
import os
import threading
import time

app = Flask(__name__)

# --- 설정 ---
BOT_TOKEN = '7921739120:AAFD5LF8WunXJM96TuBETt6QDuF3bZ0_eWw'
TELEGRAM_API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"
TELEGRAM_USER_ID = '792173912'  # 니안의 user_id (정수)

# --- 고래 추적 대상 지갑 ---
WATCHED_WALLETS = {
    "0x89552309d7140e5343821559ef19c0998720292f": "USDT 117K Whale",
    "0xed9b8f05224b881a222ece2e20bd2f4bdb71d0f8": "ERC20 Active Whale",
    "0x5ee84d30c7ee57f63f71c92247ff31f95e26916b": "Frequent Transfer Whale",
    "0x0dd9336991d8642d5e15695eadcfec42d15694cd": "Newly Active Whale",
    "0x585e77dd1334e8b59f5af46841862f65520403af": "Diversified Wallet",
    "0x26ca0fea5c32ef8297c0c98d12fd3b41bbf51b03": "500K USDC Whale",
    "0xc333e80ef2dec2805f239e3f1e810612d294f771": "Suspicious Inflow",
    "0x85cedfd30f75a57a59294c9632f2d308c67758d0": "Unknown Source",
    "0xd2e281bdf6a2a89b8004a10de76f32803f667238": "USDC Movement",
    "0xc9f9f694ae147b1333c4f53266c5ccd5c6e4c04f": "High Inflow Wallet",
    "0x74aa5387681505c806ff1e972b12cdfd01406828": "Consistent Activity",
    "0x1ca3675407963eafb03701a33825b36cd58cea10": "New Add Whale",
    "0xbec12bf8e94a6e6a37342a56301d9eb21ee10ee1": "New Whale 2",
    "0x8e407b22de830e67ac853ce56e131cab039733a7": "New Whale 3"
}

# --- 가격 조회 함수 ---
def get_price(symbol="bitcoin"):
    url = f"https://api.coingecko.com/api/v3/simple/price?ids={symbol}&vs_currencies=usd&include_24hr_change=true"
    try:
        response = requests.get(url, timeout=10)
        data = response.json()
        price = data[symbol]["usd"]
        change = data[symbol]["usd_24h_change"]
        return f"{symbol.upper()} 현재가: ${price:,.2f} (24h: {change:+.2f}%)"
    except Exception as e:
        return f"{symbol.upper()} 가격 조회 실패: {e}"

# --- 텔레그램 메시지 전송 함수 ---
def send_message(text):
    requests.post(
        f"{TELEGRAM_API_URL}/sendMessage",
        json={"chat_id": TELEGRAM_USER_ID, "text": text}
    )

# --- 고래 감시 백그라운드 스레드 ---
def monitor_whales():
    last_balances = {}
    while True:
        try:
            for wallet, label in WATCHED_WALLETS.items():
                url = f"https://api.etherscan.io/api?module=account&action=balance&address={wallet}&tag=latest&apikey=YourApiKeyToken"
                res = requests.get(url)
                data = res.json()
                balance = int(data["result"]) if data["status"] == "1" else None
                if balance is not None:
                    prev = last_balances.get(wallet)
                    if prev and balance != prev:
                        change = balance - prev
                        change_eth = change / 1e18
                        send_message(f"📡 [{label}] 지갑 활동 감지됨\n변화량: {change_eth:.4f} ETH")
                    last_balances[wallet] = balance
        except Exception as e:
            send_message(f"⚠️ 고래 감시 오류 발생: {e}")
        time.sleep(60 * 10)  # 10분 간격

# --- 웹훅 처리 ---
@app.route('/', methods=['POST'])
def webhook():
    data = request.get_json()
    if "message" in data and "text" in data["message"]:
        chat_id = data["message"]["chat"]["id"]
        text = data["message"]["text"].strip().lower()

        if text == "/price":
            btc = get_price("bitcoin")
            eth = get_price("ethereum")
            reply = f"{btc}\n{eth}"
        elif text == "/check":
            reply = "📊 시스템 정상 작동 중입니다.\n고래 모니터링 백그라운드 가동 중입니다."
        else:
            reply = f"니안 봇이 받았어! 네가 보낸 메시지: {text}"

        requests.post(
            f"{TELEGRAM_API_URL}/sendMessage",
            json={"chat_id": chat_id, "text": reply}
        )
    return "ok", 200

# --- 헬스체크 ---
@app.route('/', methods=['GET'])
def index():
    return 'Bot is running!', 200

# --- 서버 실행 ---
if __name__ == '__main__':
    # 고래 감시 스레드 실행
    threading.Thread(target=monitor_whales, daemon=True).start()
    
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
