import os
import datetime
import yfinance as yf
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from weasyprint import HTML

app = FastAPI(title="車庫財經室戰情看板 API")

# 完整載入你指定的追蹤標的清單
TICKERS = {
    "indices": {"^DJI":"道瓊","^GSPC":"S&P500","^IXIC":"那斯達克","^SOX":"費半"},
    "commodities": {"GC=F":"黃金","CL=F":"WTI原油","SI=F":"白銀"},
    "tech": {"AMD":"AMD","NVDA":"NVDA","TSM":"TSM","TSLA":"TSLA","INTC":"INTC","MU":"MU","AAPL":"AAPL"},
    "tw": {"^TWII":"加權指數","2330.TW":"台積電"}
}

def fetch_real_market_data():
    results = {}
    for category, group in TICKERS.items():
        results[category] = []
        for tk, name in group.items():
            try:
                df = yf.download(tk, period="5d", interval="1d", progress=False)
                if hasattr(df.columns, 'levels'):
                    df.columns = df.columns.get_level_values(0)
                if not df.empty and len(df) > 1:
                    last = float(df["Close"].iloc[-1])
                    prev = float(df["Close"].iloc[-2])
                    chg = last - prev
                    chg_pct = (chg / prev) * 100
                    results[category].append({
                        "name": name, "symbol": tk, "close": last, "chg": chg, "chg_pct": chg_pct
                    })
            except Exception as e:
                print(f"Error fetching {tk}: {e}")
    return results

def generate_html_rows(data_list):
    html_rows = ""
    for item in data_list:
        c = item['close']
        chg = item['chg']
        pct = item['chg_pct']
        color_class = "up" if chg > 0 else "down" if chg < 0 else "neutral"
        sign = "+" if chg > 0 else ""
        arrow = "▲" if chg > 0 else "▼" if chg < 0 else "-"
        html_rows += f"""
        <tr>
            <td>{item['name']} ({item['symbol']})</td>
            <td class="text-right val">{c:,.2f}</td>
            <td class="text-right {color_class}">{arrow} {abs(chg):,.2f} ({sign}{pct:.2f}%)</td>
        </tr>
        """
    return html_rows

@app.get("/generate_report")
def generate_report():
    try:
        market_data = fetch_real_market_data()

        idx_html = generate_html_rows(market_data.get("indices", []))
        cmd_html = generate_html_rows(market_data.get("commodities", []))
        stk_html = generate_html_rows(market_data.get("tech", []))
        tw_html = generate_html_rows(market_data.get("tw", []))

        today_str = datetime.datetime.now().strftime("%Y年 %m/%d")
        current_time_str = datetime.datetime.now().strftime("%H:%M")

        html_template = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                @page {{ size: A4; margin: 12mm 10mm; background-color: #121212; }}
                body {{ font-family: 'Noto Sans CJK TC', 'Microsoft JhengHei', sans-serif; color: #e0e0e0; margin: 0; }}
                .header {{ background: linear-gradient(135deg, #1a1a1a, #2d3748); border-bottom: 2px solid #f6ad55; padding: 16px 20px; text-align: center; position: relative; }}
                .header h1 {{ margin: 0; font-size: 20pt; color: #f6ad55; }}
                .header .date-badge {{ position: absolute; top: 16px; left: 20px; background: #2d3748; border: 1px solid #4a5568; padding: 4px 10px; border-radius: 4px; font-weight: bold; color: #edf2f7; }}
                .layout-table {{ width: 100%; border-collapse: separate; border-spacing: 12px; }}
                .layout-cell {{ background: rgba(26, 26, 26, 0.95); border-radius: 8px; padding: 15px; border: 1px solid #4a5568; }}
                .section-title {{ font-size: 12pt; font-weight: bold; color: #e2e8f0; border-left: 5px solid #f6ad55; padding-left: 10px; margin-bottom: 12px; }}
                .data-table {{ width: 100%; border-collapse: collapse; }}
                .data-table td {{ padding: 8px 0; border-bottom: 1px dashed #2d3748; font-size: 10pt; }}
                .text-right {{ text-align: right; }}
                .up {{ color: #fc8181; font-weight: bold; }}
                .down {{ color: #68d391; font-weight: bold; }}
                .val {{ color: #fff; font-weight: bold; }}
                .footer-cell {{ background: rgba(26, 26, 26, 0.95); border-radius: 8px; padding: 15px; border: 1px solid #4a5568; margin: 12px; }}
            </style>
        </head>
        <body>
            <div class="header"><div class="date-badge">{today_str}</div><h1>🛠️ 車庫財經室 晨間戰情看板</h1></div>
            <table class="layout-table">
                <tr>
                    <td class="layout-cell">
                        <div class="section-title">1. 全球主要股市指數</div>
                        <table class="data-table"><tbody>{idx_html}</tbody></table>
                    </td>
                    <td class="layout-cell">
                        <div class="section-title">2. 焦點原物料 / 能源</div>
                        <table class="data-table"><tbody>{cmd_html}</tbody></table>
                    </td>
                </tr>
                <tr>
                    <td class="layout-cell">
                        <div class="section-title">3. 核心科技巨頭表現</div>
                        <table class="data-table"><tbody>{stk_html}</tbody></table>
                    </td>
                    <td class="layout-cell">
                        <div class="section-title">4. 台股市場觀測</div>
                        <table class="data-table"><tbody>{tw_html}</tbody></table>
                    </td>
                </tr>
            </table>
            <div class="footer-cell">
                <div class="section-title">📊 系統自動化狀態</div>
                <div style="color: #68d391; font-family: monospace;">> DATA_FETCH: SUCCESS (yfinance API)<br>> GENERATE_TIME: {today_str} {current_time_str} CST</div>
            </div>
        </body>
        </html>
        """
        output_pdf = "/tmp/garage_report.pdf"
        HTML(string=html_template).write_pdf(output_pdf)
        return FileResponse(output_pdf, media_type="application/pdf", filename="garage_report.pdf")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
