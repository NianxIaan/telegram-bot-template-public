from flask import Flask, request
import requests
import os
import threading
import time

app = Flask(__name__)

# === 기본 설정 ===
BOT_TOKEN = '7921739120:AAFD5LF8WunXJM96TuBETt6QDuF3bZ0_eWw'
TELEGRAM_API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"
ADMIN_CHAT_ID = 5845150582  # 니안 텔레그램 ID 숫자만

# === 고래 지갑 목록 ===
WATCHED_WALLETS = {
    "0xc9f9f694ae147b1333c4f53266c5ccd5c6e4c04f": "메인 고래 지갑",
    "0xd32fa356b235430df8fa53c851388d2c30b6119a": "보조 고래 1",
    "0x61fbf5140a5bf3770d0305fce2c6f84f7c218bd4": "117K USDT 수신",
    "0xd2e281bdf6a2a89b8004a10de76f32803f667238": "USDC 대량 출금",
    "0xc333e80ef2dec2805f239e3f1e810612d294f771": "관측 대상",
    "0x26ca0fea5c32ef8297c0c98d12fd3b41bbf51b03": "50만 USDC 수신",
    "0xbec12bf8e94a6e6a37342a56301d9eb21ee10ee1": "보조 지갑",
    "0x8e407b22de830e67ac853ce56e131cab039733a7": "관측 지갑",
    "0x74aa5387681505c806ff1e972b12cdfd01406828": "고래-74aa",
    "0x1ca3675407963eafb03701a33825b36cd58cea10": "보조-1ca3"
    # ...필요시 계속 추가 가능
}

# === 가격 조회 함수 ===
def get_price(symbol="bitcoin"):
    try:
        url = f"https://api.coingecko.com/api/v3/simple/price?ids={symbol}&vs_currencies=usd&include_24hr_change=true"
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        data = response.json()
        price = data[symbol]["usd"]
        change = data[symbol]["usd_24h_change"]
        return f"{symbol.upper()} 현재가: ${price:,.2f} (24h: {change:+.2f}%)"
    except Exception as e:
        return f"{symbol.upper()} 가격 조회 실패: {str(e)}"

# === 웹훅 수신 핸들러 ===
@app.route('/', methods=['POST'])
def webhook():
    data = request.get_json()
    message = data.get("message") or data.get("channel_post")

    if message and "text" in message:
        chat_id = message["chat"]["id"]
        text = message["text"].strip()

        if text == "/price":
            btc = get_price("bitcoin")
            eth = get_price("ethereum")
            reply_text = f"{btc}\n{eth}"
        elif text == "/check":
            reply_text = "\ud83d\udcc8 시스템 정상 작동 중입니다.\n고래 모니터링 백그라운드 가동 중입니다."
        else:
            reply_text = f"니안 봇이 받았어! 네가 보낸 메시지: {text}"

        requests.post(
            f"{TELEGRAM_API_URL}/sendMessage",
            json={"chat_id": chat_id, "text": reply_text}
        )

    return "ok", 200

# === 헬스체크용 ===
@app.route('/', methods=['GET'])
def index():
    return 'Bot is running!', 200

# === 고래 트랜잭션 감시 쓰레드 ===
def whale_watcher():
    while True:
        try:
            for address, label in WATCHED_WALLETS.items():
                url = f"https://api.etherscan.io/api?module=account&action=txlist&address={address}&sort=desc&apikey=YourAPIKey"
                res = requests.get(url)
                if res.status_code == 200:
                    txs = res.json().get("result", [])
                    if txs:
                        tx = txs[0]
                        value = int(tx['value']) / 1e18
                        time_str = tx['timeStamp']
                        tx_hash = tx['hash'][:10] + "..."
                        msg = f"\u26a1️ {label} 지갑 활동 감지!\n최근 TX: {value:.2f} ETH\nHash: {tx_hash}"
                        requests.post(
                            f"{TELEGRAM_API_URL}/sendMessage",
                            json={"chat_id": ADMIN_CHAT_ID, "text": msg}
                        )
        except Exception as e:
            print(f"[Watcher Error] {e}")

        time.sleep(3600)  # 1시간마다 확인

# === 메인 ===
if __name__ == '__main__':
    threading.Thread(target=whale_watcher, daemon=True).start()
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
