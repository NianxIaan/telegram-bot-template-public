# main.py
from flask import Flask
import os

app = Flask(__name__)

@app.route('/')
def hello():
    return '안녕 니안의 텔레그램 봇이야! 잘 작동 중이야 ✨'

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))  # Render는 PORT 환경변수를 사용
    app.run(host='0.0.0.0', port=port)
