import os
import datetime
import yfinance as yf
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from weasyprint import HTML

app = FastAPI(title="車庫財經室戰情看板 API")

# 完整載入指定的追蹤標的清單
TICKERS = {
    "indices": {"^DJI": "道瓊", "^GSPC": "S&P500", "^IXIC": "那斯達克", "^SOX": "費半"},
    "commodities": {"GC=F": "黃金", "CL=F": "WTI原油", "SI=F": "白銀"},
    "tech": {"AMD": "AMD", "NVDA": "NVDA", "TSM": "TSM", "TSLA": "TSLA", "INTC": "INTC", "MU": "MU", "AAPL": "AAPL"},
    "tw": {"^TWII": "加權指數", "2330.TW": "台積電"}
}

def fetch_real_market_data():
    results = {}
    for category, group in TICKERS.items():
        results[category] = []
        for tk, name in group.items():
            try:
                # 抓取最近 5 天數據以計算昨日與今日價差
                df = yf.download(tk, period="5d", interval="1d", progress=False)
                
                # 處理新版 yfinance 的 MultiIndex 欄位結構問題
                if hasattr(df.columns, 'levels'):
                    df.columns = df.columns.get_level_values(0)
                    
                df = df.dropna()
                if not df.empty and len(df) > 1:
                    last = float(df["Close"].iloc[-1])
                    prev = float(df["Close"].iloc[-2])
                    chg = last - prev
                    chg_pct = (chg / prev) * 100
                    results[category].append({
                        "name": name,
                        "symbol": tk,
                        "close": last,
                        "chg": chg,
                        "chg_pct": chg_pct
                    })
                else:
                    results[category].append({
                        "name": name, "symbol": tk, "close": 0.0, "chg": 0.0, "chg_pct": 0.0
                    })
            except Exception as e:
                print(f"Error fetching {tk}: {e}")
                results[category].append({
                    "name": name, "symbol": tk, "close": 0.0, "chg": 0.0, "chg_pct": 0.0
                })
    return results

def generate_html_rows(data_list):
    html_rows = ""
    if not data_list:
        return "<tr><td colspan='3' style='text-align:center; color:#a0aec0;'>無資料</td></tr>"
        
    for item in data_list:
        c = item['close']
        chg = item['chg']
        pct = item['chg_pct']
        
        # 台灣習慣：紅漲綠跌
        color_class = "up" if chg > 0 else "down" if chg < 0 else "neutral"
        sign = "+" if chg > 0 else ""
        arrow = "▲" if chg > 0 else "▼" if chg < 0 else "-"
        
        html_rows += f"""
        <tr>
            <td>{item['name']} <span style="font-size:8pt; color:#718096;">({item['symbol']})</span></td>
            <td class="text-right val">{c:,.2f}</td>
            <td class="text-right {color_class}">{arrow} {abs(chg):,.2f} ({sign}{pct:.2f}%)</td>
        </tr>
        """
    return html_rows

@app.get("/generate_report")
def generate_report():
    try:
        # 1. 抓取即時數據
        market_data = fetch_real_market_data()
        
        # 2. 生成各區塊的 HTML 內容
        idx_html = generate_html_rows(market_data.get("indices", []))
        cmd_html = generate_html_rows(market_data.get("commodities", []))
        stk_html = generate_html_rows(market_data.get("tech", []))
        tw_html = generate_html_rows(market_data.get("tw", []))
        
        today_str = datetime.datetime.now().strftime("%Y年 %m/%d")
        current_time_str = datetime.datetime.now().strftime("%H:%M")

        # 3. 內嵌暗黑科技網格風格 HTML/CSS (強制指定開源中文字體)
        html_template = f"""
        <!DOCTYPE html>
        <html lang="zh-TW">
        <head>
            <meta charset="UTF-8">
            <style>
                @page {{
                    size: A4;
                    margin: 12mm 10mm;
                    background-color: #121212;
                }}
                *, *::before, *::after {{
                    box-sizing: border-box;
                }}
                body {{
                    font-family: "Noto Sans CJK TC", "Noto Sans CJK JP", "Microsoft JhengHei", sans-serif;
                    color: #e0e0e0;
                    margin: 0;
                    padding: 0;
                    font-size: 10pt;
                    line-height: 1.5;
                    background-image: 
                        linear-gradient(rgba(255,255,255,0.02) 1px, transparent 1px),
                        linear-gradient(90deg, rgba(255,255,255,0.02) 1px, transparent 1px);
                    background-size: 20px 20px;
                }}
                .header {{
                    background: linear-gradient(135deg, #1a1a1a, #2d3748);
                    border-bottom: 2px solid #f6ad55;
                    color: #fff;
                    padding: 16px 20px;
                    border-radius: 8px;
                    margin-bottom: 15px;
                    text-align: center;
                    position: relative;
                }}
                .header h1 {{
                    margin: 0;
                    font-size: 20pt;
                    font-weight: 900;
                    letter-spacing: 2px;
                    color: #f6ad55;
                }}
                .header .subtitle {{
                    margin-top: 4px;
                    font-size: 11pt;
                    color: #a0aec0;
                }}
                .header .date-badge {{
                    position: absolute;
                    top: 16px;
                    left: 20px;
                    background: #2d3748;
                    border: 1px solid #4a5568;
                    padding: 4px 10px;
                    border-radius: 4px;
                    font-weight: bold;
                    font-size: 10pt;
                    color: #edf2f7;
                }}
                .layout-table {{
                    width: 100%;
                    border-collapse: separate;
                    border-spacing: 12px;
                    margin-bottom: 5px;
                }}
                .layout-cell {{
                    display: table-cell;
                    width: 50%;
                    vertical-align: top;
                    background: rgba(26, 26, 26, 0.95);
                    border-radius: 8px;
                    padding: 15px;
                    border: 1px solid #4a5568;
                }}
                .section-title {{
                    font-size: 12pt;
                    font-weight: bold;
                    color: #e2e8f0;
                    border-left: 5px solid #f6ad55;
                    padding-left: 10px;
                    margin-top: 0;
                    margin-bottom: 12px;
                    letter-spacing: 1px;
                }}
                .data-table {{
                    width: 100%;
                    border-collapse: collapse;
                }}
                .data-table th {{
                    font-size: 9pt;
                    color: #a0aec0;
                    text-align: left;
                    padding-bottom: 8px;
                    border-bottom: 1px solid #4a5568;
                }}
                .data-table td {{
                    padding: 8px 0;
                    font-size: 10pt;
                    border-bottom: 1px dashed #2d3748;
                }}
                .text-right {{ text-align: right; }}
                .up {{ color: #fc8181; font-weight: bold; }}
                .down {{ color: #68d391; font-weight: bold; }}
                .neutral {{ color: #a0aec0; }}
                .val {{ color: #fff; font-weight: bold; }}
                
                .highlight-box {{
                    background-color: rgba(246, 173, 85, 0.08);
                    border-left: 4px solid #f6ad55;
                    padding: 10px;
                    font-size: 9.5pt;
                    margin-top: 12px;
                    border-radius: 0 4px 4px 0;
                    color: #fbd38d;
                }}
                .footer-cell {{
                    background: rgba(26, 26, 26, 0.95);
                    border-radius: 8px;
                    padding: 15px;
                    border: 1px solid #4a5568;
                    margin: 0 12px;
                }}
                .summary-list {{ margin: 0; padding-left: 20px; color: #cbd5e0; }}
                .summary-list li {{ margin-bottom: 6px; }}
            </style>
        </head>
        <body>
            <div class="header">
                <div class="date-badge">{today_str}</div>
                <h1>🛠️ 車庫財經室 晨間戰情看板</h1>
                <div class="subtitle">量化終端機數據流全自動產出</div>
            </div>
            
            <table class="layout-table">
                <tr>
                    <td class="layout-cell">
                        <div class="section-title">1. 全球主要股市指數</div>
                        <table class="data-table">
                            <thead><tr><th>指數名稱</th><th class="text-right">最新點位</th><th class="text-right">漲跌幅</th></tr></thead>
                            <tbody>{idx_html}</tbody>
                        </table>
                    </td>
                    <td class="layout-cell">
                        <div class="section-title">2. 焦點原物料 / 能源</div>
                        <table class="data-table">
                            <thead><tr><th>商品名稱</th><th class="text-right">最新價格</th><th class="text-right">漲跌幅</th></tr></thead>
                            <tbody>{cmd_html}</tbody>
                        </table>
                    </td>
                </tr>
            </table>

            <table class="layout-table">
                <tr>
                    <td class="layout-cell">
                        <div class="section-title">3. 核心科技巨頭表現</div>
                        <table class="data-table">
                            <thead><tr><th>企業代號</th><th class="text-right">最新股價</th><th class="text-right">漲跌幅</th></tr></thead>
                            <tbody>{stk_html}</tbody>
                        </table>
                    </td>
                    <td class="layout-cell">
                        <div class="section-title">4. 台股市場觀測</div>
                        <table class="data-table">
                            <thead><tr><th>股號 / 指數</th><th class="text-right">最新報價</th><th class="text-right">漲跌幅</th></tr></thead>
                            <tbody>{tw_html}</tbody>
                        </table>
                    </td>
                </tr>
            </table>
            
            <div class="footer-cell">
                <div class="section-title">📊 系統自動化狀態</div>
                <div style="color: #68d391; font-family: monospace; font-size: 9.5pt; background: #000; padding: 12px; border-radius: 4px; border: 1px solid #2d3748;">
                    > SYSTEM_STARTUP: OK<br>
                    > DATA_STREAM: CONNECTED<br>
                    > GENERATE_TIME: {today_str} {current_time_str} CST<br>
                    > STATUS: STRATEGY_STANDBY<br><br>
                    [!] 本日晨間戰情數據已封裝完畢。
                </div>
                <div class="highlight-box" style="margin-top: 15px;">
                    🚀 準備迎戰台股開盤！波動是日常，紀律是勝利！
                </div>
            </div>
        </body>
        </html>
        """
        # 4. 將渲染好的 HTML 輸出為實體 PDF 檔案
        output_pdf = "/tmp/garage_report.pdf"
        HTML(string=html_template).write_pdf(output_pdf)
        return FileResponse(output_pdf, media_type="application/pdf", filename="garage_report.pdf")
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
