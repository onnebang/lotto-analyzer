"""
FastAPI 기반 로또 AI 분석기 & 스마트 조합 생성기 웹 서버
"""
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List, Optional
import os
import uvicorn
from lotto_engine import LottoAnalyzer
from fetch_lotto_data import fetch_and_enrich_lotto_data, save_all

app = FastAPI(title="Lotto 6/45 AI Analyzer")

# 데이터 및 분석기 초기화
analyzer = LottoAnalyzer()

class GenerateRequest(BaseModel):
    n_games: int = 5
    strategy: str = "golden"
    fixed_nums: Optional[List[int]] = []
    exclude_nums: Optional[List[int]] = []

class BacktestRequest(BaseModel):
    numbers: List[int]

@app.get("/api/summary")
def get_summary():
    return analyzer.get_summary_stats()

@app.get("/api/pairs")
def get_pairs():
    return {
        "pairs": analyzer.get_top_pairs(15),
        "triplets": analyzer.get_top_triplets(10)
    }

@app.get("/api/history")
def get_history(limit: int = 50, page: int = 1, search_round: Optional[int] = None):
    records = analyzer.records
    if search_round:
        filtered = [r for r in records if r["round"] == search_round]
        return {"total": len(filtered), "data": filtered}
    
    # 최신순
    rev = list(reversed(records))
    start = (page - 1) * limit
    end = start + limit
    return {
        "total": len(records),
        "page": page,
        "limit": limit,
        "data": rev[start:end]
    }

@app.post("/api/generate")
def generate_games(req: GenerateRequest):
    games = analyzer.generate_numbers(
        n_games=req.n_games,
        strategy=req.strategy,
        fixed_nums=req.fixed_nums,
        exclude_nums=req.exclude_nums
    )
    return {"games": games, "count": len(games)}

@app.post("/api/backtest")
def run_backtest(req: BacktestRequest):
    if len(req.numbers) != 6:
        return JSONResponse(status_code=400, content={"error": "번호는 정확히 6개여야 합니다."})
    res = analyzer.backtest_combination(req.numbers)
    return res

@app.post("/api/sync")
def sync_latest():
    try:
        df, raw = fetch_and_enrich_lotto_data()
        save_all(df, raw)
        analyzer.load_data()
        latest = analyzer.records[-1]
        return {
            "success": True,
            "message": f"성공적으로 최신 {latest['round']}회차까지 동기화되었습니다!",
            "latest_round": latest['round'],
            "latest_date": latest['date']
        }
    except Exception as e:
        return JSONResponse(status_code=500, content={"success": False, "error": str(e)})

@app.get("/download/excel")
def download_excel():
    excel_path = "lotto_history.xlsx"
    if os.path.exists(excel_path):
        return FileResponse(
            excel_path,
            filename=f"lotto_history_1_{analyzer.records[-1]['round']}회.xlsx",
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    return JSONResponse(status_code=404, content={"error": "파일이 없습니다."})

@app.get("/download/csv")
def download_csv():
    csv_path = "lotto_history.csv"
    if os.path.exists(csv_path):
        return FileResponse(
            csv_path,
            filename=f"lotto_history_1_{analyzer.records[-1]['round']}회.csv",
            media_type="text/csv"
        )
    return JSONResponse(status_code=404, content={"error": "파일이 없습니다."})

@app.get("/", response_class=HTMLResponse)
def index():
    html_path = os.path.join(os.path.dirname(__file__), "templates", "index.html")
    with open(html_path, "r", encoding="utf-8") as f:
        return f.read()

if __name__ == "__main__":
    uvicorn.run("web_app:app", host="127.0.0.1", port=8000, reload=False)
