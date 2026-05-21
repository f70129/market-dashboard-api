import streamlit as st
import yfinance as yf
import pandas as pd
import datetime

# --- 網頁全域設定 (暗黑科技風) ---
st.set_page_config(
    page_title="車庫財經室",
    page_icon="🛠️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- 隱藏 Streamlit 預設選單與浮水印 ---
hide_streamlit_style = """
<style>
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}
</style>
"""
st.markdown(hide_streamlit_style, unsafe_allow_html=True)

# --- 標的清單 ---
TICKERS = {
    "全球主要股市": {"^DJI": "道瓊", "^GSPC": "S&P 500", "^IXIC": "那斯達克", "^SOX": "費半"},
    "焦點原物料": {"GC=F": "黃金", "SI=F": "白銀", "HG=F": "銅", "BZ=F": "布倫特原油"},
    "核心科技巨頭": {"AMD": "AMD", "NVDA": "NVDA", "TSM": "TSM", "TSLA": "TSLA", "INTC": "INTC", "MU": "MU", "AAPL": "AAPL"},
    "台股與總經": {"^TWII": "加權指數", "2330.TW": "台積電", "TWD=X": "美元/台幣", "^TNX": "美10年期公債"}
}

# --- 抓取數據 (加入快取機制，避免頻繁呼叫 API) ---
@st.cache_data(ttl=300) # 每 5 分鐘自動刷新一次快取
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
                    results[category].append({"name": name, "symbol": tk, "close": last, "chg": chg, "pct": pct})
            except Exception as e:
                pass
    return results

# --- 頁面標題 ---
today = datetime.datetime.now().strftime("%Y年 %m/%d %H:%M")
st.title("🛠️ 車庫財經室 晨間戰情看板")
st.caption(f"數據最後更新時間: {today} (自動緩存 5 分鐘)")
st.divider()

# --- 載入數據 ---
with st.spinner('連線至全球市場獲取即時數據中...'):
    data = fetch_data()

# --- 繪製 Dashboard 版面 ---
for category, items in TICKERS.items():
    st.subheader(f"📌 {category}")
    
    # 根據該分類的標的數量自動生成多欄位佈局
    cols = st.columns(len(items))
    category_data = data.get(category, [])
    
    for i, item_info in enumerate(category_data):
        with cols[i]:
            name = item_info['name']
            c = item_info['close']
            chg = item_info['chg']
            pct = item_info['pct']
            
            # 特殊邏輯處理
            if item_info['symbol'] == 'TWD=X':
                # 匯率：因為小數點較多，特別處理顯示格式
                val_str = f"{c:.3f}"
                delta_str = f"{chg:.3f} ({pct:.2f}%)"
                # Streamlit 預設上漲是綠色，台股習慣上漲是紅色。
                # 匯率數字變大是貶值(負面)，所以我們設定為 inverse。
                st.metric(label=name, value=val_str, delta=delta_str, delta_color="inverse")
            
            elif item_info['symbol'] == '^TNX':
                val_str = f"{c:.3f}%"
                delta_str = f"{chg:.3f} bps ({pct:.2f}%)"
                st.metric(label=name, value=val_str, delta=delta_str, delta_color="inverse")
                
            else:
                # 一般股價
                val_str = f"{c:,.2f}"
                delta_str = f"{chg:.2f} ({pct:.2f}%)"
                # 台股習慣：紅漲綠跌。因此將 delta_color 設為 off，稍後可用 CSS 客製，或使用預設美股邏輯
                st.metric(label=name, value=val_str, delta=delta_str, delta_color="normal")
                
    st.divider()

st.success("量化策略待命。保持紀律，穩穩向前！")
