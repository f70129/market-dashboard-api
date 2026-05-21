"""
戰情看板 API — 部署到 Render / Railway
======================================
GET  /health          → 健康檢查
POST /generate        → 產生 PDF 並回傳
GET  /generate        → 同上 (方便瀏覽器測試)
"""

import os, io, datetime as dt, json, hashlib, hmac
from fastapi import FastAPI, HTTPException, Header, Query
from fastapi.responses import Response, JSONResponse

app = FastAPI(title="Market Dashboard API", version="1.0")

# ── 簡易 API Key 驗證 (選用) ──
API_KEY = os.environ.get("DASHBOARD_API_KEY", "")


def verify_key(x_api_key: str = Header(default="")):
    """如果設了環境變數 DASHBOARD_API_KEY 就驗證, 沒設就跳過"""
    if API_KEY and not hmac.compare_digest(x_api_key, API_KEY):
        raise HTTPException(status_code=401, detail="Invalid API key")


# ── 健康檢查 ──
@app.get("/health")
def health():
    return {"status": "ok", "time": dt.datetime.now().isoformat()}


# ── 產生 PDF ──
@app.api_route("/generate", methods=["GET", "POST"])
def generate_pdf(
    x_api_key: str = Header(default=""),
    format: str = Query(default="pdf", description="pdf or json"),
):
    verify_key(x_api_key)

    try:
        from dashboard import try_yfinance, fetch_live, fetch_mock, build_single_page

        # 抓數據
        if try_yfinance():
            idx, comm, tech, tw = fetch_live()
            source = "live"
        else:
            idx, comm, tech, tw = fetch_mock()
            source = "mock"

        # 產生 PDF 到記憶體
        output_path = f"/tmp/dashboard_{dt.date.today().isoformat()}.pdf"
        build_single_page(idx, comm, tech, tw, output=output_path)

        # 讀取 PDF
        with open(output_path, "rb") as f:
            pdf_bytes = f.read()

        if format == "json":
            import base64
            return JSONResponse({
                "status": "success",
                "source": source,
                "date": dt.date.today().isoformat(),
                "pdf_base64": base64.b64encode(pdf_bytes).decode(),
                "pdf_size": len(pdf_bytes),
            })

        # 直接回傳 PDF binary
        filename = f"dashboard_{dt.date.today().isoformat()}.pdf"
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"',
                "X-Dashboard-Source": source,
                "X-Dashboard-Date": dt.date.today().isoformat(),
            },
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
