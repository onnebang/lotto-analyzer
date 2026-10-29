"""
로또 6/45 AI 분석기 웹 애플리케이션 실행 스크립트
브라우저를 자동으로 띄워 대시보드에 접속합니다.
"""
import webbrowser
import threading
import time
import uvicorn
from web_app import app

def open_browser():
    time.sleep(1.2)
    url = "http://127.0.0.1:8000"
    print(f"\n🚀 웹 브라우저에서 분석기를 실행합니다: {url}")
    webbrowser.open(url)

if __name__ == "__main__":
    threading.Thread(target=open_browser, daemon=True).start()
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="info")
