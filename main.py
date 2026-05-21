import os
import datetime
import yfinance as yf
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from weasyprint import HTML

app = FastAPI(title="車庫財經室戰情看板 API")

# 完整載入指定的追蹤標的清單
TICKERS = {
    "indices": {"^DJI": "道瓊", "^GSPC": "S&P 500", "^IXIC": "那斯達克", "^SOX": "費半"},
    "commodities": {"GC=F": "黃金", "SI=F": "白銀", "HG=F": "銅", "BZ=F": "布倫特原油"},
    "tech": {"AMD": "AMD", "NVDA": "NVDA", "TSM": "TSM", "TSLA": "TSLA", "INTC": "INTC", "MU": "MU", "AAPL": "AAPL"},
    "macro": {"^TWII": "加權指數", "2330.TW": "台積電", "TWD=X": "美元 / 台幣", "^TNX": "美10年期公債"}
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
                        "name": name, "symbol": tk, "close": last, "chg": chg, "chg_pct": chg_pct
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

def generate_macro_rows(data_list):
    """專門處理台股與總經(匯率、美債)的特殊排版與邏輯"""
    html_rows = ""
    if not data_list: return "<tr><td colspan='3'>無資料</td></tr>"
        
    for item in data_list:
        c = item['close']
        chg = item['chg']
        pct = item['chg_pct']
        
        color_class = "up" if chg > 0 else "down" if chg < 0 else "neutral"
        sign = "+" if chg > 0 else ""
        arrow = "▲" if chg > 0 else "▼" if chg < 0 else "-"
        
        if item['symbol'] == 'TWD=X':
            status = "台幣貶值" if chg > 0 else "台幣升值" if chg < 0 else "持平"
            html_rows += f"""
            <tr>
                <td>{item['name']}</td>
                <td class="text-right val">{c:,.3f}</td>
                <td class="text-right {color_class}">{arrow} {abs(chg):,.3f} <span style="font-size:8.5pt;">({status})</span></td>
            </tr>
            """
        elif item['symbol'] == '^TNX':
            status = "殖利率升" if chg > 0 else "殖利率降" if chg < 0 else "持平"
            html_rows += f"""
            <tr>
                <td>{item['name']}</td>
                <td class="text-right val">{c:,.3f}%</td>
                <td class="text-right {color_class}">{arrow} {abs(chg):,.3f} <span style="font-size:8.5pt;">({status})</span></td>
            </tr>
            """
        else:
            html_rows += f"""
            <tr>
                <td>{item['name']}</td>
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
        macro_html = generate_macro_rows(market_data.get("macro", []))
        
        today_str = datetime.datetime.now().strftime("%Y年 %m/%d")
        
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
                *, *::before, *::after {{ box-sizing: border-box; }}
                body {{
                    font-family: "Noto Sans CJK TC", "Noto Sans CJK JP", "Microsoft JhengHei", sans-serif;
                    color: #e0e0e0;
                    margin: 0; padding: 0;
                    font-size: 10pt; line-height: 1.5;
                    background-image: 
                        linear-gradient(rgba(255,255,255,0.02) 1px, transparent 1px),
                        linear-gradient(90deg, rgba(255,255,255,0.02) 1px, transparent 1px);
                    background-size: 20px 20px;
                }}
                .header {{
                    background: linear-gradient(135deg, #1a1a1a, #2d3748);
                    border-bottom: 2px solid #f6ad55;
                    padding: 16px 20px; text-align: center; position: relative; border-radius: 8px; margin-bottom: 15px;
                }}
                .header h1 {{ margin: 0; font-size: 20pt; font-weight: 900; letter-spacing: 2px; color: #f6ad55; }}
                .header .subtitle {{ margin-top: 4px; font-size: 11pt; color: #a0aec0; }}
                .header .date-badge {{
                    position: absolute; top: 16px; left: 20px; background: #2d3748; border: 1px solid #4a5568; 
                    padding: 4px 10px; border-radius: 4px; font-weight: bold; font-size: 10pt; color: #edf2f7;
                }}
                .layout-table {{ width: 100%; border-collapse: separate; border-spacing: 12px; margin-bottom: 5px; }}
                .layout-cell {{
                    display: table-cell; width: 50%; vertical-align: top; background: rgba(26, 26, 26, 0.95);
                    border-radius: 8px; padding: 15px; border: 1px solid #4a5568;
                }}
                .section-title {{
                    font-size: 12pt; font-weight: bold; color: #e2e8f0; border-left: 5px solid #f6ad55;
                    padding-left: 10px; margin-top: 0; margin-bottom: 12px; letter-spacing: 1px;
                }}
                .data-table {{ width: 100%; border-collapse: collapse; }}
                .data-table th {{ font-size: 9pt; color: #a0aec0; text-align: left; padding-bottom: 8px; border-bottom: 1px solid #4a5568; }}
                .data-table td {{ padding: 10px 0; font-size: 10.5pt; border-bottom: 1px dashed #2d3748; }}
                .text-right {{ text-align: right; }}
                .up {{ color: #fc8181; font-weight: bold; }}
                .down {{ color: #68d391; font-weight: bold; }}
                .neutral {{ color: #a0aec0; }}
                .val {{ color: #fff; font-weight: bold; }}
                .footer-cell {{
                    background: rgba(26, 26, 26, 0.95); border-radius: 8px; padding: 15px; border: 1px solid #4a5568; margin: 0 12px;
                }}
                .summary-list {{ margin: 0; padding-left: 20px; color: #cbd5e0; line-height: 1.8; }}
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
                        <table class="data-table"><tbody>{idx_html}</tbody></table>
                    </td>
                    <td class="layout-cell">
                        <div class="section-title">2. 焦點原物料 / 能源</div>
                        <table class="data-table"><tbody>{cmd_html}</tbody></table>
                    </td>
                </tr>
            </table>

            <table class="layout-table">
                <tr>
                    <td class="layout-cell">
                        <div class="section-title">3. 核心科技巨頭表現</div>
                        <table class="data-table"><tbody>{stk_html}</tbody></table>
                    </td>
                    <td class="layout-cell">
                        <div class="section-title">4. 台股與總經數據觀測</div>
                        <table class="data-table"><tbody>{macro_html}</tbody></table>
                    </td>
                </tr>
            </table>
            
            <div class="footer-cell">
                <div class="section-title">📊 核心投資紀律</div>
                <ul class="summary-list">
                    <li><strong>量化思維：</strong> 排除市場雜訊，讓客觀數據引導每一步策略。</li>
                    <li><strong>風險控管：</strong> 匯率與公債為資金流向領先指標，務必堅守停損停利點。</li>
                    <li><strong>自動化營運：</strong> 減少手動重覆勞動，將精力專注於策略研發。</li>
                </ul>
            </div>
        </body>
        </html>
        """
        output_pdf = "/tmp/garage_report.pdf"
        HTML(string=html_template).write_pdf(output_pdf)
        return FileResponse(output_pdf, media_type="application/pdf", filename="garage_report.pdf")
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
