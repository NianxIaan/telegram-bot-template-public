from flask import Flask
import os

app = Flask(__name__)

@app.route('/')
def home():
    return '니안 봇이 Render에 잘 배포됐어요! 🎉'

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))  # Render가 자동으로 설정하는 포트 사용
    app.run(host='0.0.0.0', port=port)
