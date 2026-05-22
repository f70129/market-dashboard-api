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

# 隱藏 Streamlit 預設選單，並套用你截圖中的深黑風格
st.markdown("""
<style>
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}

/* 整體背景色 */
.stApp {
    background-color: #0e1117; /* Streamlit 預設深色背景 */
    color: #ffffff;
}

/* 自訂區塊標題：黃色漸層左邊框 */
.custom-section-title {
    font-size: 16px;
    font-weight: 600;
    color: #ffffff;
    border-left: 4px solid #f6ad55; /* 橘黃色左邊框 */
    padding-left: 10px;
    margin-bottom: 10px;
    margin-top: 20px;
    letter-spacing: 1px;
}

/* 數據表格設計 */
.data-table {
    width: 100%;
    border-collapse: collapse;
    font-size: 15px;
    margin-bottom: 20px;
}
.data-table td {
    padding: 8px 0;
    border-bottom: 1px dashed #333333; /* 暗色虛線分隔 */
}

/* 左側標的名稱：稍微偏灰 */
.data-table td:first-child { 
    color: #cccccc; 
}

/* 數值靠右 */
.text-right { 
    text-align: right; 
}

/* 價格數值：純白加粗 */
.val { 
    color: #ffffff; 
    font-weight: 500; 
}

/* 漲跌幅顏色 */
.up { color: #ff4b4b; font-weight: 500; } /* 紅色 */
.down { color: #00e676; font-weight: 500; } /* 綠色 */
.neutral { color: #aaaaaa; }

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

# --- 4. 將資料轉為 HTML 表格的函數 ---
def build_html_rows(data_list):
    rows = ""
    for item in data_list:
        if not item['has_data']:
            rows += f"<tr><td>{item['name']} <span style='font-size:12px;'>({item['symbol']})</span></td><td colspan='2' class='text-right neutral'>暫無報價</td></tr>"
            continue
            
        c = item['close']
        chg = item['chg']
        pct = item['pct']
        
        # 決定顏色與符號 (台灣習慣紅漲綠跌)
        color_class = "up" if chg > 0 else "down" if chg < 0 else "neutral"
        sign = "+" if chg > 0 else ""
        arrow = "▲" if chg > 0 else "▼" if chg < 0 else "-"
        
        # 數值格式化處理
        status_text = ""
        if item['symbol'] == 'TWD=X':
            status_text = f" <span style='font-size:12px; color:#aaa;'>({'貶' if chg > 0 else '升' if chg < 0 else '-'})</span>"
            val_str = f"{c:,.3f}"
            delta_str = f"{abs(chg):,.3f}"
        elif item['symbol'] == '^TNX':
            status_text = f" <span style='font-size:12px; color:#aaa;'>({'升' if chg > 0 else '降' if chg < 0 else '-'})</span>"
            val_str = f"{c:,.3f}%"
            delta_str = f"{abs(chg):,.3f} bps"
        else:
            val_str = f"{c:,.2f}"
            delta_str = f"{abs(chg):,.2f}"

        rows += f"""
        <tr>
            <td>
                {item['name']} <br>
                <span style="font-size:12px; color:#777;">{item['symbol']}</span>
            </td>
            <td class="text-right val">
                {val_str}
            </td>
            <td class="text-right {color_class}">
                {arrow} {delta_str} <br>
                <span style="font-size:13px;">({sign}{pct:.2f}%){status_text}</span>
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
<div style="padding-bottom:10px; margin-bottom:20px;">
    <div style="font-size:14px; color:#aaa; margin-bottom:5px;">{today_str}</div>
    <h1 style="margin:0; font-size:24px; font-weight:700; color:#fff;">車庫財經室 晨間戰情看板</h1>
</div>
""", unsafe_allow_html=True)

# 兩欄式排版
col1, col2 = st.columns(2, gap="large")

with col1:
    st.markdown('<div class="custom-section-title">1. 全球主要股市指數</div>', unsafe_allow_html=True)
    st.markdown(f"<table class='data-table'><tbody>{build_html_rows(market_data.get('1. 全球主要股市指數', []))}</tbody></table>", unsafe_allow_html=True)
    
    st.markdown('<div class="custom-section-title">3. 核心科技巨頭表現</div>', unsafe_allow_html=True)
    st.markdown(f"<table class='data-table'><tbody>{build_html_rows(market_data.get('3. 核心科技巨頭表現', []))}</tbody></table>", unsafe_allow_html=True)

with col2:
    st.markdown('<div class="custom-section-title">2. 焦點原物料 / 能源</div>', unsafe_allow_html=True)
    st.markdown(f"<table class='data-table'><tbody>{build_html_rows(market_data.get('2. 焦點原物料 / 能源', []))}</tbody></table>", unsafe_allow_html=True)
    
    st.markdown('<div class="custom-section-title">4. 台股與總經數據觀測</div>', unsafe_allow_html=True)
    st.markdown(f"<table class='data-table'><tbody>{build_html_rows(market_data.get('4. 台股與總經數據觀測', []))}</tbody></table>", unsafe_allow_html=True)

# --- 6. 底部分析與建議區塊 ---
st.markdown('<div class="custom-section-title">5. 戰情分析與投資建議</div>', unsafe_allow_html=True)

st.markdown("""
<div style="padding: 10px; border-radius: 5px; background-color: rgba(255,255,255,0.05); border: 1px solid #333;">
    <ul style="margin:0; padding-left:20px; color:#ccc; line-height:1.8; font-size:14px;">
        <li><span style="color:#fff; font-weight:bold;">量化思維：</span> 讓客觀數據說話，摒除主觀情緒與市場雜訊，嚴格執行交易策略。</li>
        <li><span style="color:#fff; font-weight:bold;">風險控管：</span> 每日追蹤美元匯率與美債殖利率，作為資金流向的領先指標；堅守預設的停損與停利點。</li>
        <li><span style="color:#fff; font-weight:bold;">自動化進化：</span> 持續優化量化交易系統，讓機器處理重複性勞動，將專注力保留給核心策略研發。</li>
        <li><span style="color:#fff; font-weight:bold;">系統狀態：</span> 數據流連線正常，交易模組待命。準備迎接開盤，紀律是獲利的唯一法則。</li>
    </ul>
</div>
""", unsafe_allow_html=True)
