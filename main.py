from flask import Flask, request
import requests
import os
import threading
import time

app = Flask(__name__)

# 텔레그램 봇 설정
BOT_TOKEN = '7921739120:AAFD5LF8WunXJM96TuBETt6QDuF3bZ0_eWw'
TELEGRAM_API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"
ADMIN_CHAT_ID = "6202991499"  # 니안의 텔레그램 chat_id

# 추적 중인 고래 지갑 목록
WATCHED_WALLETS = [
    "0x89552309d7140e5343821559ef19c0998720292f",
    "0xed9b8f05224b881a222ece2e20bd2f4bdb71d0f8",
    "0x5ee84d30c7ee57f63f71c92247ff31f95e26916b",
    "0x0dd9336991d8642d5e15695eadcfec42d15694cd",
    "0x585e77dd1334e8b59f5af46841862f65520403af",
    "0xd32fa356b235430df8fa53c851388d2c30b6119a",
    "0x61fbf5140a5bf3770d0305fce2c6f84f7c218bd4",
    "0xd2e281bdf6a2a89b8004a10de76f32803f667238",
    "0xc9f9f694ae147b1333c4f53266c5ccd5c6e4c04f",
    "0x26ca0fea5c32ef8297c0c98d12fd3b41bbf51b03",
    "0xc333e80ef2dec2805f239e3f1e810612d294f771",
    "0x85cedfd30f75a57a59294c9632f2d308c67758d0",
    "0x74aa5387681505c806ff1e972b12cdfd01406828",
    "0x1ca3675407963eafb03701a33825b36cd58cea10",
    "0xbec12bf8e94a6e6a37342a56301d9eb21ee10ee1",
    "0x8e407b22de830e67ac853ce56e131cab039733a7",
]

# ─────────────────────────────────────────────
# 가격 조회 함수 (Coingecko 안정화 버전)
def get_price(symbol="bitcoin"):
    url = "https://api.coingecko.com/api/v3/simple/price"
    params = {
        "ids": symbol,
        "vs_currencies": "usd",
        "include_24hr_change": "true"
    }
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        if symbol in data and "usd" in data[symbol]:
            price = data[symbol]["usd"]
            change = data[symbol]["usd_24h_change"]
            return f"{symbol.upper()} 현재가: ${price:,.2f} (24h: {change:+.2f}%)"
        else:
            return f"{symbol.upper()} 가격 정보가 응답에 없음"
    except Exception as e:
        return f"{symbol.upper()} 가격 조회 실패: {e}"

# ─────────────────────────────────────────────
# 고래 지갑 활동 감시 (ERC-20 기준)
def check_wallet_activity(wallet):
    url = f"https://api.ethplorer.io/getAddressTransactions/{wallet}?apiKey=freekey&limit=5"
    try:
        res = requests.get(url, timeout=10)
        res.raise_for_status()
        txs = res.json()
        if isinstance(txs, list) and len(txs) > 0:
            latest_tx = txs[0]
            timestamp = latest_tx.get("timestamp", 0)
            tx_type = latest_tx.get("type", "")
            value = latest_tx.get("value", 0)
            return f"지갑 {wallet[-6:]} 최근 트랜잭션 → {tx_type.upper()} {value}"
        else:
            return None
    except:
        return None

# ─────────────────────────────────────────────
# 백그라운드 고래 모니터링 루프
def background_monitor():
    while True:
        alert_msgs = []
        for wallet in WATCHED_WALLETS:
            result = check_wallet_activity(wallet)
            if result:
                alert_msgs.append(result)

        if alert_msgs:
            full_msg = "🕵️ 고래 지갑 알림:\n" + "\n".join(alert_msgs)
            requests.post(f"{TELEGRAM_API_URL}/sendMessage", json={
                "chat_id": ADMIN_CHAT_ID,
                "text": full_msg
            })

        time.sleep(1800)  # 30분 간격 체크 (원하면 조정 가능)

# ─────────────────────────────────────────────
# 텔레그램 웹훅 처리
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
        elif text == "/check":
            reply = "📊 시스템 정상 작동 중입니다.\n고래 모니터링 백그라운드 가동 중입니다."
        else:
            reply = f"니안 봇이 받았어! 네가 보낸 메시지: {text}"

        requests.post(f"{TELEGRAM_API_URL}/sendMessage", json={
            "chat_id": chat_id,
            "text": reply
        })

    return "ok", 200

# ─────────────────────────────────────────────
@app.route('/', methods=['GET'])
def index():
    return 'Bot is running!', 200

# ─────────────────────────────────────────────
if __name__ == '__main__':
    threading.Thread(target=background_monitor, daemon=True).start()
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
