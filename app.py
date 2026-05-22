import streamlit as st
import yfinance as yf
import pandas as pd
import altair as alt
import datetime

# ==========================================
# 1. 網頁全域設定
# ==========================================
st.set_page_config(
    page_title="全球市場戰情看板",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# 隱藏預設選單，調整版面間距
st.markdown("""
<style>
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}
.block-container { padding-top: 2rem; padding-bottom: 2rem; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. 標的清單設定
# ==========================================
TICKERS = {
    "commodities": {
        "GC=F": "GOLD 黃金", "SI=F": "SILVER 白銀", "HG=F": "HGCOP 銅", 
        "BZ=F": "BRENT 布倫特原油", "CL=F": "OIL WTI原油", "NG=F": "NGAS 天然氣", 
        "PA=F": "PALL 鈀", "PL=F": "PLAT 鉑"
    },
    "indices": {
        "^DJI": "道瓊工業指數", "^GSPC": "S&P 500", 
        "^IXIC": "那斯達克", "^SOX": "費城半導體"
    },
    "tech": {
        "AMD": "AMD", "NVDA": "NVDA", "TSM": "TSM", 
        "TSLA": "TSLA", "INTC": "INTC", "MU": "MU", "AAPL": "AAPL"
    },
    "tw": {
        "^TWII": "加權指數", "2330.TW": "台積電"
    },
    "fx": {
        "TWD=X": "美元/台幣", "DX-Y.NYB": "DXY 美元指數"
    },
    "yields": {
        "^IRX": "3M 公債", "^FVX": "5Y 公債", 
        "^TNX": "10Y 公債", "^TYX": "30Y 公債"
    }
}

# ==========================================
# 3. 獲取資料函數 (快取 5 分鐘，抓取近一個月以繪製走勢圖)
# ==========================================
@st.cache_data(ttl=300)
def fetch_all_data():
    results = {}
    for cat, group in TICKERS.items():
        cat_data = {}
        for tk, name in group.items():
            try:
                stock = yf.Ticker(tk)
                # 抓取 1 個月的歷史數據以供 Altair 畫走勢圖
                df = stock.history(period="1mo")
                if not df.empty and len(df) >= 2:
                    cat_data[tk] = {'name': name, 'df': df}
            except Exception:
                pass
        results[cat] = cat_data
    return results

# ==========================================
# 4. 輔助繪圖函數 (Altair 迷你走勢圖 Sparkline)
# ==========================================
def make_sparkline(df, color):
    df_reset = df.reset_index()
    # 畫出極簡線圖，隱藏 X/Y 軸標籤與網格線
    chart = alt.Chart(df_reset).mark_line(strokeWidth=2).encode(
        x=alt.X('Date:T', axis=None),
        y=alt.Y('Close:Q', scale=alt.Scale(zero=False), axis=None),
        color=alt.value(color),
        tooltip=['Date:T', 'Close:Q']
    ).properties(height=60)
    return chart

# ==========================================
# 5. 主頁面渲染
# ==========================================
with st.spinner('連線至全球市場獲取即時數據中...'):
    data = fetch_all_data()

# --- 頁首 ---
now_str = datetime.datetime.now().strftime("%Y年%m月%d日 %H:%M")
st.title("🌍 全球市場戰情看板 Streamlit")
st.markdown(f"**全球市場 & 台股電子盤 最新數據總整理！** (資料更新時間: `{now_str}`)")
st.info("💡 波動是日常，紀律是勝利。數據看仔細，投資不怕怕！")
st.divider()

# --- 兩欄排版 (上半部) ---
col_left, col_right = st.columns([1, 1.2], gap="large")

with col_left:
    st.subheader("🛢️ 1. 焦點原物料 / 能源價格")
    # 將原物料轉換為 DataFrame 並顯示
    comm_list = []
    for tk, info in data.get('commodities', {}).items():
        df = info['df']
        c = df['Close'].iloc[-1]
        p = df['Close'].iloc[-2]
        chg = c - p
        pct = (chg / p) * 100
        comm_list.append({
            "★商品": info['name'], "價格": c, "漲跌": chg, "漲跌(%)": pct
        })
    
    if comm_list:
        df_comm = pd.DataFrame(comm_list)
        # 設定 Pandas DataFrame 樣式，加入顏色邏輯 (台灣習慣紅漲綠跌)
        def color_rule(val):
            if isinstance(val, float):
                color = '#ff4b4b' if val > 0 else '#00e676' if val < 0 else 'gray'
                return f'color: {color}; font-weight: bold;'
            return ''
        
        st.dataframe(
            df_comm.style.format({"價格": "{:,.2f}", "漲跌": "{:+.2f}", "漲跌(%)": "{:+.2f}%"})
                         .map(color_rule, subset=['漲跌', '漲跌(%)']),
            use_container_width=True, hide_index=True
        )

with col_right:
    st.subheader("📈 2. 全球主要股市指數表現")
    idx_cols = st.columns(4)
    indices_data = data.get('indices', {})
    
    for i, (tk, info) in enumerate(indices_data.items()):
        with idx_cols[i % 4]:
            df = info['df']
            c = df['Close'].iloc[-1]
            p = df['Close'].iloc[-2]
            chg = c - p
            pct = (chg / p) * 100
            
            st.metric(label=info['name'], value=f"{c:,.2f}", delta=f"{chg:+.2f} ({pct:+.2f}%)")
            # 依據今日漲跌決定走勢圖顏色
            line_color = '#ff4b4b' if chg >= 0 else '#00e676' 
            st.altair_chart(make_sparkline(df, line_color), use_container_width=True)

st.divider()

# --- 兩欄排版 (中半部：科技Top7 vs 台股雙線圖) ---
col_tech, col_tw = st.columns([1, 1], gap="large")

with col_tech:
    st.subheader("🔥 3. 美股科技巨頭漲跌幅 (Top 7)")
    tech_list = []
    for tk, info in data.get('tech', {}).items():
        df = info['df']
        c = df['Close'].iloc[-1]
        p = df['Close'].iloc[-2]
        pct = ((c - p) / p) * 100
        tech_list.append({"代號": tk, "最新價格": c, "漲跌幅(%)": pct})
    
    if tech_list:
        df_tech = pd.DataFrame(tech_list).sort_values(by="漲跌幅(%)", ascending=False)
        
        # 繪製 Altair 水平柱狀條 (視覺化)
        bars = alt.Chart(df_tech).mark_bar().encode(
            x=alt.X('漲跌幅(%):Q', title='日漲跌幅 (%)'),
            y=alt.Y('代號:N', sort='-x', title=None),
            color=alt.condition(
                alt.datum['漲跌幅(%)'] > 0,
                alt.value('#ff4b4b'),  # 正值為紅
                alt.value('#00e676')   # 負值為綠
            ),
            tooltip=['代號', '最新價格', '漲跌幅(%)']
        )
        # 在柱子旁加上數字標籤
        text = bars.mark_text(
            align='left', baseline='middle', dx=3, color='white'
        ).encode(text=alt.Text('漲跌幅(%):Q', format='+.2f'))
        
        st.altair_chart((bars + text).properties(height=250), use_container_width=True)

with col_tw:
    st.subheader("🇹🇼 4. 台股市場表現 (大盤 vs 台積電)")
    tw_data = data.get('tw', {})
    
    # 顯示兩張 Metric 卡片
    m_cols = st.columns(2)
    for i, (tk, info) in enumerate(tw_data.items()):
        df = info['df']
        c = df['Close'].iloc[-1]
        chg = c - df['Close'].iloc[-2]
        pct = (chg / df['Close'].iloc[-2]) * 100
        m_cols[i].metric(label=info['name'], value=f"{c:,.2f}", delta=f"{chg:+.2f} ({pct:+.2f}%)")
        
    # 製作台股大盤與台積電的「雙線比較圖」(比較近一個月基準績效)
    if '^TWII' in tw_data and '2330.TW' in tw_data:
        df_twii = tw_data['^TWII']['df'][['Close']].copy().rename(columns={'Close':'大盤(^TWII)'})
        df_tsmc = tw_data['2330.TW']['df'][['Close']].copy().rename(columns={'Close':'台積電(2330)'})
        
        # 合併數據並計算「累積報酬率 (%)」以利在同一個 Y 軸比較
        df_merge = pd.merge(df_twii, df_tsmc, left_index=True, right_index=True)
        df_merge['大盤(^TWII)'] = (df_merge['大盤(^TWII)'] / df_merge['大盤(^TWII)'].iloc[0] - 1) * 100
        df_merge['台積電(2330)'] = (df_merge['台積電(2330)'] / df_merge['台積電(2330)'].iloc[0] - 1) * 100
        
        st.line_chart(df_merge, height=180)

st.divider()

# --- 三欄排版 (下半部：匯率、殖利率、分析總結) ---
col_fx, col_yield, col_summary = st.columns([1, 1, 1.5], gap="large")

with col_fx:
    st.subheader("💵 5. 美元匯率指標")
    for tk, info in data.get('fx', {}).items():
        df = info['df']
        c = df['Close'].iloc[-1]
        p = df['Close'].iloc[-2]
        chg = c - p
        pct = (chg / p) * 100
        
        # 匯率升貶判斷
        status = ""
        if tk == 'TWD=X':
            status = " (貶值)" if chg > 0 else " (升值)" if chg < 0 else ""
            st.metric(label=info['name'], value=f"{c:,.3f}", delta=f"{chg:+.3f} {status}", delta_color="inverse")
        else:
            st.metric(label=info['name'], value=f"{c:,.2f}", delta=f"{chg:+.2f} ({pct:+.2f}%)")

with col_yield:
    st.subheader("🏛️ 6. 美國公債殖利率")
    y_cols = st.columns(2)
    for i, (tk, info) in enumerate(data.get('yields', {}).items()):
        with y_cols[i % 2]:
            df = info['df']
            c = df['Close'].iloc[-1]
            p = df['Close'].iloc[-2]
            chg = c - p
            
            # 殖利率升降判斷
            status = "升" if chg > 0 else "降" if chg < 0 else "平"
            st.metric(label=info['name'], value=f"{c:,.3f}%", delta=f"{chg:+.3f} bps ({status})", delta_color="inverse")

with col_summary:
    st.subheader("📊 戰情分析與投資建議")
    st.success("""
    **💡 核心投資紀律：**
    * **量化思維：** 排除市場雜訊，讓客觀數據引導每一步策略。
    * **風險控管：** 匯率與公債為資金流向領先指標，務必堅守停損停利點。
    * **自動化營運：** 減少手動重覆勞動，將精力專注於策略研發。
    
    *(註：系統模組連線正常，請留意科技股板塊的相對強弱與美元強弱指數之變化。)*
    """)
