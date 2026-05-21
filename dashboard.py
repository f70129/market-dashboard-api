#!/usr/bin/env python3
"""
全球市場戰情看板 — 一頁式 · 吉卜力風格
========================================
本機: pip install yfinance matplotlib numpy pandas
      python ghibli_dashboard.py
"""

import io, os, datetime as dt
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Rectangle
from matplotlib.offsetbox import OffsetImage, AnnotationBbox
import matplotlib.patheffects as pe
from matplotlib import font_manager

# ── 字型 ──
CJK_FONT = None
for fp in [
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Medium.ttc",
    "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",
    "/System/Library/Fonts/PingFang.ttc",
    "C:/Windows/Fonts/msjh.ttc",
]:
    if os.path.exists(fp):
        font_manager.fontManager.addfont(fp)
        CJK_FONT = font_manager.FontProperties(fname=fp)
        plt.rcParams["font.family"] = CJK_FONT.get_name()
        break

CJK_BOLD = None
for fp in [
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Medium.ttc",
]:
    if os.path.exists(fp):
        font_manager.fontManager.addfont(fp)
        CJK_BOLD = font_manager.FontProperties(fname=fp)
        break

if CJK_BOLD is None:
    CJK_BOLD = CJK_FONT

plt.rcParams["axes.unicode_minus"] = False

# ── 吉卜力配色 ──
G = {
    "bg":        "#F7F3EB",    # 溫暖米色紙張
    "header":    "#3B6B35",    # 龍貓森林綠
    "header_t":  "#F7F3EB",
    "sub_t":     "#8FA87A",    # 苔蘚綠
    # 區塊配色
    "s1_bg":     "#FAF0E4",    # 原物料 - 大地暖棕
    "s1_bd":     "#A68B6B",
    "s1_title":  "#6B5344",
    "s2_bg":     "#E8F0F2",    # 指數 - 天空藍
    "s2_bd":     "#5A8FA8",
    "s2_title":  "#2E6078",
    "s3_bg":     "#EDE8F2",    # 科技 - 薰衣草
    "s3_bd":     "#7E6B99",
    "s3_title":  "#4A3D5E",
    "s4_bg":     "#F5E8EC",    # 台股 - 櫻花粉
    "s4_bd":     "#C27B8E",
    "s4_title":  "#8B4A5E",
    "sum_bg":    "#E8EDDF",    # 總結 - 草原綠
    "sum_bd":    "#6B8E5A",
    # 漲跌
    "up":        "#C75050",    # 暖紅
    "down":      "#3B7A4A",    # 森林綠
    "flat":      "#9E9E9E",
    "text":      "#3E3832",
    "muted":     "#8A8478",
}


# ============================================================
# 數據層 (同前，精簡)
# ============================================================
def try_yfinance():
    try:
        import yfinance as yf
        t = yf.download("^GSPC", period="5d", progress=False)
        return not t.empty
    except Exception:
        return False

def fetch_live():
    import yfinance as yf
    def dl(tk, period="6mo"):
        df = yf.download(tk, period=period, interval="1d", progress=False)
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        return df

    def extract(df):
        last, prev = float(df["Close"].iloc[-1]), float(df["Close"].iloc[-2]) if len(df)>1 else float(df["Close"].iloc[-1])
        return last, last-prev, ((last-prev)/prev)*100, df["Close"].values[-60:].astype(float)

    idx = {}
    for tk, nm in {"^DJI":"道瓊指數","^GSPC":"S&P 500","^IXIC":"那斯達克","^SOX":"費半"}.items():
        df = dl(tk)
        if not df.empty:
            c, ch, cp, h = extract(df)
            idx[tk] = {"n":nm,"c":c,"ch":ch,"cp":cp,"h":h}

    comm = {}
    for tk, nm in {"GC=F":"黃金","SI=F":"白銀","CL=F":"WTI原油","BZ=F":"布倫特","NG=F":"天然氣","HG=F":"銅"}.items():
        df = dl(tk, "5d")
        if not df.empty:
            c, ch, cp, _ = extract(df)
            comm[tk] = {"n":nm,"p":c,"ch":ch,"cp":cp}

    tech = {}
    for tk, nm in {"AMD":"AMD","INTC":"INTC","MU":"MU","TSLA":"TSLA","TSM":"TSM","NVDA":"NVDA","AAPL":"AAPL"}.items():
        df = dl(tk, "5d")
        if not df.empty:
            c, ch, cp, _ = extract(df)
            tech[tk] = {"n":nm,"p":c,"cp":cp}

    tw = {}
    for tk, nm in {"^TWII":"加權指數","2330.TW":"台積電"}.items():
        df = dl(tk)
        if not df.empty:
            c, ch, cp, h = extract(df)
            tw[tk] = {"n":nm,"c":c,"ch":ch,"cp":cp,"h":h}

    return idx, comm, tech, tw

def fetch_mock():
    np.random.seed(42)
    def gh(b, n=60, v=0.008):
        return (b * np.cumprod(1 + np.random.normal(0.0003, v, n))).astype(float)

    idx = {
        "^DJI":  {"n":"道瓊指數","c":50009.35,"ch":645.47,"cp":1.31,"h":gh(48000)},
        "^GSPC": {"n":"S&P 500","c":7432.97,"ch":79.36,"cp":1.08,"h":gh(7100)},
        "^IXIC": {"n":"那斯達克","c":26270.36,"ch":399.65,"cp":1.54,"h":gh(25000)},
        "^SOX":  {"n":"費半","c":11813.29,"ch":507.79,"cp":4.49,"h":gh(10500)},
    }
    comm = {
        "GC=F": {"n":"黃金","p":4539.55,"ch":-4.07,"cp":-0.09},
        "HG=F": {"n":"銅","p":6.32,"ch":-0.01,"cp":-0.18},
        "SI=F": {"n":"白銀","p":75.45,"ch":-0.37,"cp":-0.49},
        "BZ=F": {"n":"布倫特","p":105.15,"ch":-0.29,"cp":-0.28},
        "CL=F": {"n":"WTI原油","p":99.13,"ch":0.12,"cp":0.12},
        "NG=F": {"n":"天然氣","p":3.01,"ch":0.0,"cp":0.0},
        "RB=F": {"n":"汽油","p":1158.12,"ch":-65.0,"cp":-5.31},
    }
    tech = {
        "AMD":  {"n":"AMD 超微","p":447.58,"cp":8.10},
        "INTC": {"n":"INTC 英特爾","p":118.96,"cp":7.36},
        "MU":   {"n":"MU 美光","p":731.99,"cp":4.76},
        "TSLA": {"n":"TSLA 特斯拉","p":417.26,"cp":3.25},
        "GLW":  {"n":"GLW 康寧","p":180.69,"cp":2.76},
        "STX":  {"n":"STX Seagate","p":751.07,"cp":2.42},
        "TSM":  {"n":"TSM 台積電","p":401.62,"cp":2.29},
    }
    tw = {
        "^TWII":   {"n":"加權指數","c":40020.82,"ch":-154.74,"cp":-0.39,"h":gh(39500)},
        "2330.TW": {"n":"台積電","c":1085.0,"ch":15.0,"cp":1.40,"h":gh(1000)},
    }
    return idx, comm, tech, tw


# ============================================================
# 繪圖引擎 — 單頁 A4 matplotlib
# ============================================================
def color_of(val):
    return G["up"] if val > 0 else (G["down"] if val < 0 else G["flat"])

def sign_of(val):
    return "+" if val > 0 else ""

def arrow_of(val):
    return "\u25B2" if val > 0 else ("\u25BC" if val < 0 else "\u25AC")


def draw_rounded_box(ax, x, y, w, h, bg, bd, radius=0.008):
    """在 fig 座標上畫圓角框"""
    box = FancyBboxPatch((x, y), w, h,
                         boxstyle=f"round,pad=0,rounding_size={radius}",
                         facecolor=bg, edgecolor=bd, linewidth=1.2,
                         transform=ax.figure.transFigure, clip_on=False)
    ax.add_patch(box)
    return box


def draw_section_title(fig, x, y, text, color, icon=""):
    """繪製區塊標題"""
    fig.text(x, y, f"{icon} {text}", fontsize=9, fontweight="bold",
             color=color, fontproperties=CJK_BOLD,
             va="center", ha="left")


def draw_mini_sparkline(fig, ax_pos, history, color):
    """在指定位置畫迷你折線"""
    ax = fig.add_axes(ax_pos, frameon=False)
    x = np.arange(len(history))
    is_up = history[-1] >= history[0]
    lc = G["up"] if is_up else G["down"]
    fc = "#F5CACA" if is_up else "#C5E0C5"
    ax.plot(x, history, color=lc, linewidth=1.0)
    ax.fill_between(x, history, history.min()*0.999, alpha=0.25, color=fc)
    ax.set_xlim(0, len(history)-1)
    ax.set_ylim(history.min()*0.998, history.max()*1.002)
    ax.set_xticks([])
    ax.set_yticks([])
    for spine in ax.spines.values():
        spine.set_visible(False)
    return ax


def build_single_page(idx, comm, tech, tw, output="ghibli_dashboard.pdf"):
    today = dt.date.today()
    wd_zh = ["一","二","三","四","五","六","日"][today.weekday()]

    # A4 比例: 210 x 297 mm ≈ 8.27 x 11.69 in
    fig = plt.figure(figsize=(8.27, 11.69), dpi=150)
    fig.patch.set_facecolor(G["bg"])

    # 用一個隱形 ax 做底
    ax = fig.add_axes([0, 0, 1, 1], frameon=False)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.set_xticks([])
    ax.set_yticks([])

    M = 0.035  # margin
    CW = (1 - 3*M) / 2  # column width

    # ══════════════════════════════════════════════
    # HEADER
    # ══════════════════════════════════════════════
    hdr_y = 0.935
    hdr_h = 0.050
    draw_rounded_box(ax, M, hdr_y, 1-2*M, hdr_h, G["header"], G["header"], 0.008)

    fig.text(0.5, hdr_y + hdr_h*0.62, "\u2605 全球市場 & 台股 每日戰情看板 \u2605",
             fontsize=15, fontweight="bold", color=G["header_t"],
             fontproperties=CJK_BOLD, ha="center", va="center")
    fig.text(0.5, hdr_y + hdr_h*0.22,
             f"{today.year}/{today.month}/{today.day}（{wd_zh}）",
             fontsize=8, color="#C5DBBA", fontproperties=CJK_FONT,
             ha="center", va="center")

    # ── 裝飾線 ──
    fig.text(M, hdr_y - 0.006,
             "\u2500" * 90,
             fontsize=5, color=G["sub_t"], ha="left", va="top")

    # ══════════════════════════════════════════════
    # ROW 1: 原物料 (左) + 全球指數 (右)
    # ══════════════════════════════════════════════
    r1_y = 0.590
    r1_h = 0.330

    # ── S1: 原物料 ──
    s1_x = M
    draw_rounded_box(ax, s1_x, r1_y, CW, r1_h, G["s1_bg"], G["s1_bd"])
    draw_section_title(fig, s1_x+0.012, r1_y+r1_h-0.018, "國際原物料 / 能源", G["s1_title"], "\u25C9")

    # 表頭
    ty = r1_y + r1_h - 0.048
    for j, hdr in enumerate(["商品", "價格", "漲跌幅"]):
        ha = "left" if j==0 else "right"
        x_off = s1_x + [0.015, 0.22, CW-0.015][j]
        fig.text(x_off, ty, hdr, fontsize=6.5, color=G["muted"],
                 fontproperties=CJK_BOLD, ha=ha, va="center")

    sorted_comm = sorted(comm.values(), key=lambda x: x["cp"])
    for i, d in enumerate(sorted_comm):
        cy = ty - 0.035 - i * 0.034
        fig.text(s1_x+0.015, cy, d["n"], fontsize=7, color=G["text"],
                 fontproperties=CJK_FONT, va="center")
        fig.text(s1_x+0.22, cy, f"{d['p']:,.2f}", fontsize=7, color=G["text"],
                 fontproperties=CJK_FONT, ha="right", va="center")
        s = sign_of(d["cp"])
        cc = color_of(d["cp"])
        fig.text(s1_x+CW-0.015, cy, f"{s}{d['ch']:,.2f} ({s}{d['cp']:.2f}%)",
                 fontsize=6.5, color=cc, fontproperties=CJK_FONT,
                 ha="right", va="center")

    # 小結
    worst = min(comm.values(), key=lambda x: x["cp"])
    note = f"\u2606 {worst['n']}跌幅最大 {worst['cp']:.2f}%" if worst["cp"] < -1 else "\u2606 原物料價格整體平穩"
    fig.text(s1_x+0.012, r1_y+0.012, note, fontsize=6, color=G["s1_bd"],
             fontproperties=CJK_FONT, style="italic", va="center")

    # ── S2: 全球指數 ──
    s2_x = M + CW + M
    draw_rounded_box(ax, s2_x, r1_y, CW, r1_h, G["s2_bg"], G["s2_bd"])
    draw_section_title(fig, s2_x+0.012, r1_y+r1_h-0.018, "全球主要股市指數", G["s2_title"], "\u2191")

    idx_list = list(idx.values())
    card_h = 0.070
    card_gap = 0.006
    start_y = r1_y + r1_h - 0.050

    for i, d in enumerate(idx_list):
        cy = start_y - i * (card_h + card_gap)
        cc = color_of(d["cp"])
        s = sign_of(d["cp"])
        ar = arrow_of(d["cp"])

        # 名稱
        fig.text(s2_x+0.012, cy - 0.005, d["n"],
                 fontsize=8, fontweight="bold", color=G["s2_title"],
                 fontproperties=CJK_BOLD, va="top")
        # 收盤價
        fig.text(s2_x+0.012, cy - 0.025,
                 f"{d['c']:,.2f}", fontsize=9, fontweight="bold",
                 color=G["text"], fontproperties=CJK_BOLD, va="top")
        # 漲跌
        fig.text(s2_x+0.012, cy - 0.043,
                 f"{ar}{s}{d['ch']:,.2f} ({s}{d['cp']:.2f}%)",
                 fontsize=7, color=cc, fontproperties=CJK_FONT, va="top")

        # 迷你走勢圖
        if "h" in d:
            sp_x = s2_x + 0.19
            sp_w = CW - 0.21
            sp_y_fig = cy - card_h + 0.008
            draw_mini_sparkline(fig, [sp_x, sp_y_fig, sp_w, card_h-0.010], d["h"], cc)

    # 指數小結
    best = max(idx.values(), key=lambda x: x["cp"])
    up_n = sum(1 for d in idx.values() if d["cp"] > 0)
    note2 = f"\u2606 {'全面收紅' if up_n==len(idx) else '漲跌互見'}！{best['n']}領漲 +{best['cp']:.2f}%"
    fig.text(s2_x+0.012, r1_y+0.012, note2, fontsize=6, color=G["s2_bd"],
             fontproperties=CJK_FONT, style="italic", va="center")

    # ══════════════════════════════════════════════
    # ROW 2: 科技 Top7 (左) + 台股 (右)
    # ══════════════════════════════════════════════
    r2_y = 0.195
    r2_h = 0.380

    # ── S3: 科技 Top7 ──
    s3_x = M
    draw_rounded_box(ax, s3_x, r2_y, CW, r2_h, G["s3_bg"], G["s3_bd"])
    draw_section_title(fig, s3_x+0.012, r2_y+r2_h-0.018, "美股科技巨頭 Top 7", G["s3_title"], "\u2606")

    sorted_tech = sorted(tech.items(), key=lambda x: x[1]["cp"], reverse=True)[:7]

    bar_start_y = r2_y + r2_h - 0.055
    bar_h = 0.042
    max_pct = max(abs(d["cp"]) for _, d in sorted_tech) if sorted_tech else 1

    for i, (tk, d) in enumerate(sorted_tech):
        by = bar_start_y - i * bar_h
        cc = color_of(d["cp"])
        s = sign_of(d["cp"])

        # 排名
        rank_c = "#D4A03C" if i < 3 else G["muted"]
        medal = [" 1."," 2."," 3."][i] if i < 3 else f" {i+1}."
        fig.text(s3_x+0.012, by, medal, fontsize=7, color=rank_c, va="center")

        # 名稱
        fig.text(s3_x+0.048, by, d["n"], fontsize=7, color=G["text"],
                 fontproperties=CJK_FONT, va="center")

        # 價格
        fig.text(s3_x+0.22, by, f"${d['p']:,.2f}", fontsize=7, color=G["text"],
                 fontproperties=CJK_FONT, ha="right", va="center")

        # 百分比
        fig.text(s3_x+0.29, by, f"{s}{d['cp']:.2f}%", fontsize=7.5,
                 fontweight="bold", color=cc, fontproperties=CJK_BOLD,
                 ha="right", va="center")

        # 水平柱狀
        bar_w_max = CW - 0.31
        bw = (abs(d["cp"]) / max_pct) * bar_w_max if max_pct > 0 else 0
        bar_rect = FancyBboxPatch(
            (s3_x+0.30, by-0.009), bw, 0.018,
            boxstyle="round,pad=0,rounding_size=0.004",
            facecolor=cc, alpha=0.35,
            transform=fig.transFigure, clip_on=False
        )
        ax.add_patch(bar_rect)

    # 科技小結
    t1 = sorted_tech[0][1]["n"] if sorted_tech else ""
    note3 = f"\u2606 {t1} 領漲！AI/半導體族群全面走強"
    fig.text(s3_x+0.012, r2_y+0.012, note3, fontsize=6, color=G["s3_bd"],
             fontproperties=CJK_FONT, style="italic", va="center")

    # ── S4: 台股 ──
    s4_x = M + CW + M
    draw_rounded_box(ax, s4_x, r2_y, CW, r2_h, G["s4_bg"], G["s4_bd"])
    draw_section_title(fig, s4_x+0.012, r2_y+r2_h-0.018, "台股市場表現", G["s4_title"], "TW")

    # 台股數據卡片
    tw_card_y = r2_y + r2_h - 0.060
    for i, (tk, d) in enumerate(tw.items()):
        cy = tw_card_y - i * 0.065
        cc = color_of(d["cp"])
        s = sign_of(d["cp"])
        ar = arrow_of(d["cp"])

        # 內框
        inner_w = CW - 0.024
        inner_box = FancyBboxPatch(
            (s4_x+0.012, cy-0.035), inner_w, 0.055,
            boxstyle="round,pad=0,rounding_size=0.005",
            facecolor="white", edgecolor=G["s4_bd"], alpha=0.5, linewidth=0.6,
            transform=fig.transFigure, clip_on=False
        )
        ax.add_patch(inner_box)

        fig.text(s4_x+0.022, cy+0.008, d["n"], fontsize=8, fontweight="bold",
                 color=G["s4_title"], fontproperties=CJK_BOLD, va="center")
        fig.text(s4_x+0.022, cy-0.012, f"{d['c']:,.2f}",
                 fontsize=11, fontweight="bold", color=G["text"],
                 fontproperties=CJK_BOLD, va="center")
        fig.text(s4_x+0.20, cy-0.012,
                 f"{ar} {s}{d['ch']:,.2f}  ({s}{d['cp']:.2f}%)",
                 fontsize=8, color=cc, fontproperties=CJK_BOLD, va="center")

    # 台股雙軸走勢圖
    chart_y = r2_y + 0.045
    chart_h = r2_h - 0.230
    chart_x = s4_x + 0.012
    chart_w = CW - 0.024

    ax_tw = fig.add_axes([chart_x, chart_y, chart_w, chart_h])
    ax_tw.set_facecolor("#FFFAFA")

    twii = tw.get("^TWII", {})
    tsmc = tw.get("2330.TW", {})

    if "h" in twii:
        h1 = twii["h"]
        x1 = np.arange(len(h1))
        ax_tw.plot(x1, h1, color=G["s4_bd"], linewidth=1.2, label="加權指數")
        ax_tw.fill_between(x1, h1, h1.min()*0.999, alpha=0.12, color=G["s4_bd"])
        ax_tw.set_ylabel("加權", fontsize=6, color=G["s4_bd"], fontproperties=CJK_FONT)
        ax_tw.tick_params(axis="y", labelsize=5, labelcolor=G["s4_bd"])

    if "h" in tsmc:
        ax_r = ax_tw.twinx()
        h2 = tsmc["h"]
        x2 = np.arange(len(h2))
        ax_r.plot(x2, h2, color=G["s2_bd"], linewidth=1.2, linestyle="--", label="台積電")
        ax_r.set_ylabel("台積電", fontsize=6, color=G["s2_bd"], fontproperties=CJK_FONT)
        ax_r.tick_params(axis="y", labelsize=5, labelcolor=G["s2_bd"])

    ax_tw.tick_params(axis="x", labelsize=5)
    ax_tw.set_xlabel("近60交易日", fontsize=5.5, fontproperties=CJK_FONT)
    ax_tw.grid(axis="y", alpha=0.2, linewidth=0.5)

    lines1, labels1 = ax_tw.get_legend_handles_labels()
    if "h" in tsmc:
        lines2, labels2 = ax_r.get_legend_handles_labels()
        ax_tw.legend(lines1+lines2, labels1+labels2, fontsize=5.5,
                     loc="upper left", framealpha=0.7, prop=CJK_FONT)
    else:
        ax_tw.legend(fontsize=5.5, loc="upper left", framealpha=0.7, prop=CJK_FONT)

    for spine in ax_tw.spines.values():
        spine.set_linewidth(0.5)
        spine.set_color(G["s4_bd"])

    # 台股小結
    td = tw.get("^TWII", {"ch":0, "cp":0})
    dire = "上漲" if td.get("ch",0)>0 else "下跌"
    note4 = f"\u2606 加權{dire} {abs(td.get('ch',0)):,.0f}點 ({td.get('cp',0):+.2f}%)"
    fig.text(s4_x+0.012, r2_y+0.012, note4, fontsize=6, color=G["s4_bd"],
             fontproperties=CJK_FONT, style="italic", va="center")

    # ══════════════════════════════════════════════
    # FOOTER: 總結
    # ══════════════════════════════════════════════
    ft_y = 0.025
    ft_h = 0.155
    draw_rounded_box(ax, M, ft_y, 1-2*M, ft_h, G["sum_bg"], G["sum_bd"])

    fig.text(M+0.012, ft_y+ft_h-0.018, "\u2022 今日總結",
             fontsize=9, fontweight="bold", color=G["sum_bd"],
             fontproperties=CJK_BOLD, va="center")

    # 自動摘要
    summaries = []
    worst_c = min(comm.values(), key=lambda x: x["cp"])
    if worst_c["cp"] < -1:
        summaries.append(f"\u25CB 原物料震盪，{worst_c['n']}跌 {worst_c['cp']:.2f}%，能源族群承壓")
    else:
        summaries.append("\u25CB 國際原物料整體平穩")

    best_i = max(idx.values(), key=lambda x: x["cp"])
    up_cnt = sum(1 for d in idx.values() if d["cp"] > 0)
    if up_cnt == len(idx):
        summaries.append(f"\u25CB 美股四大指數全面收紅，{best_i['n']}漲 +{best_i['cp']:.2f}% 領軍")
    else:
        summaries.append(f"\u25CB 美股漲跌互見，{best_i['n']}表現最佳 +{best_i['cp']:.2f}%")

    t1n = sorted_tech[0][1]["n"] if sorted_tech else ""
    t1p = sorted_tech[0][1]["cp"] if sorted_tech else 0
    summaries.append(f"\u25CB 科技巨頭 {t1n} 領漲 +{t1p:.2f}%，AI晶片族群全面走強")

    twii_d = tw.get("^TWII", {})
    summaries.append(f"\u25CB 台股加權收 {twii_d.get('c',0):,.0f}，{dire} {abs(twii_d.get('ch',0)):,.0f} 點")

    for i, s in enumerate(summaries):
        fig.text(M+0.015, ft_y+ft_h-0.042 - i*0.025, s,
                 fontsize=7, color="#3E5B2F", fontproperties=CJK_FONT, va="center")

    # 投資提醒
    fig.text(0.5, ft_y+0.015,
             "\u2606 市場永遠在變，數據會說話，保持紀律，穩穩向前 \u2606",
             fontsize=6, color=G["muted"], fontproperties=CJK_FONT,
             ha="center", va="center", style="italic")

    # 生成時間
    fig.text(0.98, 0.008,
             f"Generated {dt.datetime.now().strftime('%Y-%m-%d %H:%M')}  |  Python + yfinance",
             fontsize=4.5, color="#C0B8A8", ha="right", va="bottom")

    # 吉卜力裝飾 — 角落小圖案 (用文字符號)
    fig.text(0.04, 0.96, "\u2022", fontsize=14, va="center", alpha=0.4)
    fig.text(0.94, 0.96, "\u2022", fontsize=14, va="center", alpha=0.4)
    fig.text(0.04, 0.008, "\u2022", fontsize=10, va="center", alpha=0.3)
    fig.text(0.94, 0.008, "\u2022", fontsize=10, va="center", alpha=0.3)

    # ── 輸出 ──
    fig.savefig(output, format="pdf", facecolor=G["bg"],
                bbox_inches="tight", pad_inches=0.05)
    plt.close(fig)
    import sys as _sys
    print(f"\n>> 一頁式 PDF 已產生: {output}", file=_sys.stderr)
    return output


# ============================================================
def main():
    import sys, json as _json

    # 支援命令列參數: python n8n_dashboard.py [output_path]
    output_path = sys.argv[1] if len(sys.argv) > 1 else "/tmp/ghibli_dashboard.pdf"

    try:
        if try_yfinance():
            idx, comm, tech, tw = fetch_live()
            source = "live"
        else:
            idx, comm, tech, tw = fetch_mock()
            source = "mock"

        build_single_page(idx, comm, tech, tw, output=output_path)

        # 輸出 JSON 供 n8n 解析
        result = {
            "status": "success",
            "source": source,
            "pdf_path": output_path,
            "date": dt.date.today().isoformat(),
            "timestamp": dt.datetime.now().isoformat(),
        }
        # 最後一行輸出 JSON (n8n 用)
        print(_json.dumps(result, ensure_ascii=False))
        sys.exit(0)

    except Exception as e:
        result = {"status": "error", "error": str(e)}
        print(_json.dumps(result, ensure_ascii=False))
        sys.exit(1)

if __name__ == "__main__":
    main()
