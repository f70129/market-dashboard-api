import streamlit as st
import yfinance as yf
import datetime

# --- 1. Streamlit 全域設定 ---
st.set_page_config(
    page_title="車庫財經室",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# 隱藏 Streamlit 預設選單，並強制套用純白底極簡風格
st.markdown("""
<style>
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}
.stApp { background-color: #ffffff; }

/* 區塊標題設計 (灰底 + 黑色左邊框) */
.section-title {
    font-size: 14pt;
    font-weight: bold;
    color: #000;
    border-left: 5px solid #000;
    padding-left: 10px;
    margin-bottom: 15px;
    background-color: #f4f4f4;
    padding: 8px 12px;
    border-radius: 4px;
    font-family: 'Microsoft JhengHei', sans-serif;
}

/* 數據表格設計 */
.data-table {
    width: 100%;
    border-collapse: collapse;
    font-family: 'Microsoft JhengHei', sans-serif;
    margin-bottom: 30px;
}
.data-table td {
    padding: 10px 5px;
    font-size: 11.5pt;
    border-bottom: 1px solid #eeeeee;
    color: #000;
}
.text-right { text-align: right; }
.val { font-weight: bold; color: #000; }

/* 紅漲綠跌 */
.up { color: #d32f2f; font-weight: bold; }
.down { color: #2e7d32; font-weight: bold; }
.neutral { color: #666666; }
</style>
""", unsafe_allow_html=True)

# --- 2. 定義追蹤標的 ---
TICKERS = {
    "1. 全球主要股市指數": {"^DJI": "道瓊", "^GSPC": "S&P 500", "^IXIC": "那斯達克", "^SOX": "費半"},
    "2. 焦點原物料 / 能源": {"GC=F": "黃金", "CL=F": "WTI原油", "SI=F": "白銀", "HG=F": "銅"},
    "3. 核心科技巨頭表現": {"AMD": "AMD", "NVDA": "NVDA", "TSM": "TSM", "TSLA": "TSLA", "INTC": "INTC", "MU": "MU", "AAPL": "AAPL"},
    "4. 台股與總經數據觀測": {"^TWII": "加權指數", "2330.TW": "台積電", "TWD=X": "美元/台幣", "^TNX": "美10年期公債"}
}

# --- 3. 抓取資料函數 (快取 5 分鐘) ---
@st.cache_data(ttl=300)
def fetch_data():
    results = {}
    for category, group in TICKERS.items():
        results[category] = []
        for tk, name in group.items():
            try:
                stock = yf.Ticker(tk)
                df = stock.history(period="5d")
                if not df.empty and len(df) >= 2:
                    last = float(df["Close"].iloc[-1])
                    prev = float(df["Close"].iloc[-2])
                    chg = last - prev
                    pct = (chg / prev) * 100
                    results[category].append({
                        "name": name, "symbol": tk, "close": last, "chg": chg, "pct": pct, "has_data": True
                    })
                else:
                    results[category].append({"name": name, "symbol": tk, "close": 0, "chg": 0, "pct": 0, "has_data": False})
            except Exception:
                results[category].append({"name": name, "symbol": tk, "close": 0, "chg": 0, "pct": 0, "has_data": False})
    return results

# --- 4. 將資料轉為單行 HTML 表格列的函數 ---
def build_html_rows(data_list):
    rows = ""
    for item in data_list:
        if not item['has_data']:
            rows += f"<tr><td style='font-weight:bold; color:#000;'>{item['name']} <span style='font-weight:normal; font-size:10.5pt; color:#666;'>({item['symbol']})</span></td><td colspan='2' class='text-right neutral'>暫無報價</td></tr>"
            continue
            
        c = item['close']
        chg = item['chg']
        pct = item['pct']
        
        # 決定顏色與箭頭 (台灣習慣紅漲綠跌)
        color_class = "up" if chg > 0 else "down" if chg < 0 else "neutral"
        sign = "+" if chg > 0 else ""
        arrow = "▲" if chg > 0 else "▼" if chg < 0 else ""
        
        # 特殊邏輯處理
        status_text = ""
        if item['symbol'] == 'TWD=X':
            status_text = f" <span style='font-size:10.5pt; font-weight:normal; color:#666;'>({'貶值' if chg > 0 else '升值' if chg < 0 else '持平'})</span>"
            val_str = f"{c:,.3f}"
            delta_str = f"{abs(chg):,.3f}"
        elif item['symbol'] == '^TNX':
            status_text = f" <span style='font-size:10.5pt; font-weight:normal; color:#666;'>({'升' if chg > 0 else '降' if chg < 0 else '持平'})</span>"
            val_str = f"{c:,.3f}%"
            delta_str = f"{abs(chg):,.3f} bps"
        else:
            val_str = f"{c:,.2f}"
            delta_str = f"{abs(chg):,.2f}"

        # 這裡絕對不加 <br>，保證每一列都在同一行完美對齊
        rows += f"""
        <tr>
            <td style="font-weight:bold; color:#000;">
                {item['name']} <span style="font-size:10.5pt; font-weight:normal; color:#666;">({item['symbol']})</span>
            </td>
            <td class="text-right val">
                {val_str}
            </td>
            <td class="text-right {color_class}">
                {arrow} {delta_str} ({sign}{pct:.2f}%){status_text}
            </td>
        </tr>
        """
    return rows

# --- 5. 渲染主頁面 ---
with st.spinner('獲取即時數據中...'):
    market_data = fetch_data()

today_str = datetime.datetime.now().strftime("%Y年%m/%d %H:%M")

# 頂部 Header
st.markdown(f"""
<div style="text-align:center; padding:10px 0 20px 0; border-bottom:3px solid #000; margin-bottom:30px;">
    <div style="font-size:14pt; font-weight:bold; color:#666; margin-bottom:5px;">{today_str}</div>
    <h1 style="margin:0; font-size:26pt; font-weight:900; letter-spacing:2px; color:#000;">車庫財經室 晨間戰情看板</h1>
</div>
""", unsafe_allow_html=True)

# 兩欄式排版
col1, col2 = st.columns(2, gap="large")

with col1:
    st.markdown('<div class="section-title">| 1. 全球主要股市指數</div>', unsafe_allow_html=True)
    st.markdown(f"<table class='data-table'><tbody>{build_html_rows(market_data.get('1. 全球主要股市指數', []))}</tbody></table>", unsafe_allow_html=True)
    
    st.markdown('<div class="section-title">| 3. 核心科技巨頭表現</div>', unsafe_allow_html=True)
    st.markdown(f"<table class='data-table'><tbody>{build_html_rows(market_data.get('3. 核心科技巨頭表現', []))}</tbody></table>", unsafe_allow_html=True)

with col2:
    st.markdown('<div class="section-title">| 2. 焦點原物料 / 能源</div>', unsafe_allow_html=True)
    st.markdown(f"<table class='data-table'><tbody>{build_html_rows(market_data.get('2. 焦點原物料 / 能源', []))}</tbody></table>", unsafe_allow_html=True)
    
    st.markdown('<div class="section-title">| 4. 台股與總經數據觀測</div>', unsafe_allow_html=True)
    st.markdown(f"<table class='data-table'><tbody>{build_html_rows(market_data.get('4. 台股與總經數據觀測', []))}</tbody></table>", unsafe_allow_html=True)

# --- 6. 底部分析與建議區塊 ---
st.markdown('<div class="section-title" style="margin-top: 20px;">| 5. 戰情分析與投資建議</div>', unsafe_allow_html=True)

st.markdown("""
<div style="padding: 10px 20px; font-family: 'Microsoft JhengHei', sans-serif;">
    <ul style="margin:0; padding-left:20px; color:#333; line-height:2.0; font-size:11.5pt;">
        <li><strong style="color:#000;">量化思維：</strong> 讓客觀數據說話，摒除主觀情緒與市場雜訊，嚴格執行交易策略。</li>
        <li><strong style="color:#000;">風險控管：</strong> 每日追蹤美元匯率與美債殖利率，作為資金流向的領先指標；堅守預設的停損與停利點。</li>
        <li><strong style="color:#000;">自動化進化：</strong> 持續優化量化交易系統，讓機器處理重複性勞動，將專注力保留給核心策略研發。</li>
        <li><strong style="color:#000;">系統狀態：</strong> 數據流連線正常，交易模組待命。準備迎接開盤，紀律是獲利的唯一法則。</li>
    </ul>
</div>
""", unsafe_allow_html=True)
