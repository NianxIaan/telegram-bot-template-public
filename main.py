from flask import Flask, request
import requests
import os

app = Flask(__name__)

# 텔레그램 봇 설정
BOT_TOKEN = '7921739120:AAFD5LF8WunXJM96TuBETt6QDuF3bZ0_eWw'
TELEGRAM_API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"

# 가격 조회 함수
def get_price(symbol="bitcoin"):
    url = f"https://api.coingecko.com/api/v3/simple/price?ids={symbol}&vs_currencies=usd&include_24hr_change=true"
    response = requests.get(url)
    data = response.json()
    price = data[symbol]["usd"]
    change = data[symbol]["usd_24h_change"]
    return f"{symbol.upper()} 현재가: ${price:,.2f} (24h: {change:+.2f}%)"

# 텔레그램 웹훅 처리
@app.route('/', methods=['POST'])
def webhook():
    data = request.get_json()

    if "message" in data and "text" in data["message"]:
        chat_id = data["message"]["chat"]["id"]
        text = data["message"]["text"]

        if text.strip() == "/price":
            btc = get_price("bitcoin")
            eth = get_price("ethereum")
            reply_text = f"{btc}\n{eth}"
        else:
            reply_text = f"니안 봇이 받았어! 네가 보낸 메시지: {text}"

        requests.post(
            f"{TELEGRAM_API_URL}/sendMessage",
            json={"chat_id": chat_id, "text": reply_text}
        )

    return "ok", 200

# 헬스체크용 GET 요청 대응
@app.route('/', methods=['GET'])
def index():
    return 'Bot is running!', 200

# 서버 실행
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
