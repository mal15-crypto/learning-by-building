"""
app.py
──────
Streamlit front-end — 3 pages as specified in the project.

Run:
    streamlit run app.py

Pre-requisite:
    python data_collection.py      ← populates crossmarket.db first
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import date, timedelta

import database
from sql_queries import QUERIES          # predefined SQL list


# ─── PAGE CONFIG ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Cross-Market Analysis – Crypto, Oil & Stocks",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ─── CUSTOM CSS (dark financial-dashboard theme) ──────────────────────────────
st.markdown("""
<style>
    /* dark background */
    .stApp                          { background-color: #0f172a; color: #f1f5f9; }
    .stApp *                        { font-family: 'Segoe UI', sans-serif; }

    /* sidebar */
    .css-1aumxhk                    { background-color: #1e293b !important; }

    /* KPI cards helper class */
    .kpi-card {
        background: linear-gradient(135deg, #1e293b, #0f172a);
        border-radius: 12px;
        padding: 16px;
        text-align: center;
        border: 1px solid #334155;
    }
    .kpi-card .label               { color: #94a3b8; font-size: 13px; }
    .kpi-card .value               { color: #f1f5f9; font-size: 22px; font-weight: 700; }
    .kpi-card .change              { font-size: 13px; font-weight: 600; }

    /* dataframe styling */
    .stDataFrame                    { border-radius: 10px; overflow: hidden; }

    /* tab styling */
    .stTabs [data-basedclient="true"] { color: #f1f5f9; }
    .stTabs [role="tablist"]        { border-bottom: 2px solid #334155; }
    .stTabs [role="tab"]            { color: #94a3b8; font-weight: 600; }
    .stTabs [role="tab"][aria-selected="true"] { color: #3b82f6; border-bottom: 3px solid #3b82f6; }

    /* button */
    .stButton>button                { background: linear-gradient(135deg,#3b82f6,#6366f1); color:#fff; border:none; border-radius:8px; font-weight:700; }
    .stButton>button:hover          { opacity:0.88; }

    /* code block (SQL preview) */
    .stCode                         { background: #0a0e1a !important; border: 1px solid #1e293b; border-radius:10px; }
</style>
""", unsafe_allow_html=True)


# ─── SHARED COLOUR MAP ─────────────────────────────────────────────────────────
COLORS = {
    "bitcoin":  "#f7931a",
    "ethereum": "#627eea",
    "tether":   "#26a17b",
    "BTC":      "#f7931a",
    "ETH":      "#627eea",
    "OIL":      "#22c55e",
    "SP500":    "#3b82f6",
    "NASDAQ":   "#a855f7",
    "NIFTY":    "#f59e0b",
}


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE 1 — FILTERS & DATA EXPLORATION
# ═══════════════════════════════════════════════════════════════════════════════
def page_filters():
    st.markdown("## 📊 Filters & Data Exploration")
    st.markdown("Select a date range to explore average prices and the daily market snapshot.")

    # ── date picker ─────────────────────────────────────────────────────────
    col_l, col_r = st.columns(2)
    start_date = col_l.date_input("📅 Start Date", value=date(2025, 1, 1), min_value=date(2020, 1, 1))
    end_date   = col_r.date_input("📅 End Date",   value=date.today(),     min_value=start_date)

    start_str = start_date.strftime("%Y-%m-%d")
    end_str   = end_date.strftime("%Y-%m-%d")

    # ── KPI cards ───────────────────────────────────────────────────────────
    btc_avg   = database.get_btc_avg(start_str, end_str)
    oil_avg   = database.get_oil_avg(start_str, end_str)
    sp500_avg = database.get_stock_avg("^GSPC", start_str, end_str)
    nifty_avg = database.get_stock_avg("^NSEI", start_str, end_str)

    c1, c2, c3, c4 = st.columns(4)
    for col, label, val, symbol in [
        (c1, "Bitcoin (BTC)",  btc_avg,   "$"),
        (c2, "WTI Oil",        oil_avg,   "$"),
        (c3, "S&P 500",        sp500_avg, ""),
        (c4, "NIFTY 50",       nifty_avg, ""),
    ]:
        col.markdown(f"""
        <div class="kpi-card">
            <div class="label">{label} — Avg Price</div>
            <div class="value">{symbol}{val:,.2f}</div>
        </div>""", unsafe_allow_html=True)

    st.divider()

    # ── daily snapshot JOIN table ───────────────────────────────────────────
    st.markdown("### 📋 Daily Market Snapshot (SQL JOIN)")
    snapshot = database.get_daily_snapshot(start_str, end_str)

    if snapshot.empty:
        st.warning("No overlapping data for the selected range. Try widening the dates.")
    else:
        # round for display
        snapshot["bitcoin_price"] = snapshot["bitcoin_price"].round(2)
        snapshot["oil_price"]     = snapshot["oil_price"].round(2)
        snapshot["sp500_close"]   = snapshot["sp500_close"].round(2)
        snapshot["nifty_close"]   = snapshot["nifty_close"].round(2)

        st.dataframe(snapshot, width='stretch', hide_index=True)

        # ── line chart of the snapshot ────────────────────────────────────
        st.markdown("### 📈 Cross-Market Trend")
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=snapshot["date"], y=snapshot["bitcoin_price"],
                                  name="Bitcoin",  line=dict(color=COLORS["BTC"])))
        fig.add_trace(go.Scatter(x=snapshot["date"], y=snapshot["oil_price"],
                                  name="WTI Oil",   line=dict(color=COLORS["OIL"]),
                                  yaxis="y2"))
        fig.add_trace(go.Scatter(x=snapshot["date"], y=snapshot["sp500_close"],
                                  name="S&P 500",   line=dict(color=COLORS["SP500"]),
                                  yaxis="y3"))
        fig.add_trace(go.Scatter(x=snapshot["date"], y=snapshot["nifty_close"],
                                  name="NIFTY 50",   line=dict(color=COLORS["NIFTY"]),
                                  yaxis="y4"))

        fig.update_layout(
            height=420,
            paper_bgcolor="#0f172a",
            plot_bgcolor="#1e293b",
            font=dict(color="#94a3b8"),
            legend=dict(orientation="h", yanchor="bottom", y=-0.25),
            yaxis  =dict(title=dict(text="Bitcoin ($)", font=dict(color=COLORS["BTC"])),  tickfont=dict(color="#94a3b8"), showgrid=False),
            yaxis2 =dict(title=dict(text="Oil ($/bbl)", font=dict(color=COLORS["OIL"])),  tickfont=dict(color="#94a3b8"), overlaying="y", side="right", showgrid=False),
            yaxis3 =dict(title=dict(text="S&P 500",     font=dict(color=COLORS["SP500"])),tickfont=dict(color="#94a3b8"), overlaying="y", side="left",  showgrid=False, anchor="free", position=0.05),
            yaxis4 =dict(title=dict(text="NIFTY",       font=dict(color=COLORS["NIFTY"])),tickfont=dict(color="#94a3b8"), overlaying="y", side="right", showgrid=False, anchor="free", position=0.95),
            xaxis  =dict(showgrid=False),
        )
        st.plotly_chart(fig, use_container_width=True)


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE 2 — SQL QUERY RUNNER
# ═══════════════════════════════════════════════════════════════════════════════
def page_sql_runner():
    st.markdown("## 🔎 SQL Query Runner")
    st.markdown("Pick a predefined query, preview the SQL, then hit **Run Query**.")

    # ── group selector → query selector ─────────────────────────────────────
    groups = list(dict.fromkeys(q["group"] for q in QUERIES))          # ordered unique
    chosen_group = st.selectbox("📂 Query Group", groups)

    group_queries = [q for q in QUERIES if q["group"] == chosen_group]
    chosen_label  = st.selectbox("📝 Select Query", [q["label"] for q in group_queries])
    chosen_query  = next(q for q in group_queries if q["label"] == chosen_label)

    # ── SQL preview ─────────────────────────────────────────────────────────
    st.markdown("#### SQL Preview")
    st.code(chosen_query["sql"].strip(), language="sql")

    # ── Run ─────────────────────────────────────────────────────────────────
    if st.button("▶  Run Query", width='stretch'):
        with st.spinner("Executing…"):
            try:
                result_df = database.run_query(chosen_query["sql"])
                st.success(f"✅ {len(result_df)} row(s) returned")
                st.dataframe(result_df, width='stretch', hide_index=True)
            except Exception as exc:
                st.error(f"❌ Query error: {exc}")


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE 3 — TOP-3 CRYPTO ANALYSIS
# ═══════════════════════════════════════════════════════════════════════════════
def page_crypto():
    st.markdown("## 🪙 Top 3 Crypto Analysis")

    # ── load available coins ────────────────────────────────────────────────
    coins = database.get_available_coins()
    if not coins:
        st.warning("No crypto price data found. Run `data_collection.py` first.")
        return

    coin_labels = {c["coin_id"]: f"{c['symbol'].upper()} – {c['name']}" for c in coins}
    chosen_id   = st.selectbox("🪙 Select Cryptocurrency",
                               options=list(coin_labels.keys()),
                               format_func=lambda x: coin_labels[x])

    # ── date range ──────────────────────────────────────────────────────────
    col_l, col_r = st.columns(2)
    start_date = col_l.date_input("📅 Start Date", value=date.today() - timedelta(days=90), min_value=date(2024, 1, 1))
    end_date   = col_r.date_input("📅 End Date",   value=date.today(),                      min_value=start_date)

    start_str = start_date.strftime("%Y-%m-%d")
    end_str   = end_date.strftime("%Y-%m-%d")

    # ── fetch prices ────────────────────────────────────────────────────────
    df = database.get_coin_prices(chosen_id, start_str, end_str)
    if df.empty:
        st.warning("No price data in this range. Adjust the dates.")
        return

    # ── summary KPIs ────────────────────────────────────────────────────────
    high = df["price_usd"].max()
    low  = df["price_usd"].min()
    avg  = df["price_usd"].mean()
    latest = df["price_usd"].iloc[-1]

    k1, k2, k3, k4 = st.columns(4)
    for col, lbl, val in [(k1,"Current Price", latest),
                          (k2,"Highest",       high),
                          (k3,"Lowest",        low),
                          (k4,"Average",       avg)]:
        col.markdown(f"""
        <div class="kpi-card">
            <div class="label">{lbl}</div>
            <div class="value" style="color:{COLORS.get(chosen_id,'#f1f5f9')}">${val:,.2f}</div>
        </div>""", unsafe_allow_html=True)

    st.divider()

    # ── line chart ──────────────────────────────────────────────────────────
    st.markdown(f"### 📈 {coin_labels[chosen_id]} – Daily Price Trend")
    
    # Convert hex color to rgba for fill
    color = COLORS.get(chosen_id, "#3b82f6")
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df["date"], y=df["price_usd"],
        mode="lines",
        name=chosen_id.capitalize(),
        line=dict(color=color, width=2.5),
        fill="tozeroy",
        fillcolor=f"rgba({int(color[1:3],16)},{int(color[3:5],16)},{int(color[5:7],16)},0.08)",
    ))
    fig.update_layout(
        height=350,
        paper_bgcolor="#0f172a",
        plot_bgcolor="#1e293b",
        font=dict(color="#94a3b8"),
        yaxis=dict(title="Price (USD)", showgrid=True, gridcolor="#1e293b"),
        xaxis=dict(showgrid=False),
        showlegend=False,
    )
    st.plotly_chart(fig, use_container_width=True)

    # ── daily price table ───────────────────────────────────────────────────
    st.markdown("### 📋 Daily Price Table")
    df_display = df.copy()
    df_display["price_usd"]  = df_display["price_usd"].round(2)
    df_display["daily_chg_%"] = df_display["price_usd"].pct_change().mul(100).round(2)
    st.dataframe(df_display, width='stretch', hide_index=True)


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN — TAB NAVIGATION
# ═══════════════════════════════════════════════════════════════════════════════
def main():
    # Header
    st.markdown("""
    <div style="text-align:center; padding:12px 0 4px;">
        <h1 style="margin:0; font-size:28px; background:linear-gradient(90deg,#f7931a,#627eea,#22c55e);
            -webkit-background-clip:text; -webkit-text-fill-color:transparent;">
            💰 🛢 📈 Cross-Market Analysis
        </h1>
        <p style="color:#64748b; margin:4px 0 0; font-size:13px;">
            Crypto · Oil · Stocks — SQL-Powered Dashboard (SQLite3 + Streamlit)
        </p>
    </div>
    """, unsafe_allow_html=True)

    # Tabs (Streamlit native)
    tab1, tab2, tab3 = st.tabs([
        "📊  Filters & Data Exploration",
        "🔎  SQL Query Runner",
        "🪙  Top 3 Crypto Analysis",
    ])

    with tab1:
        page_filters()
    with tab2:
        page_sql_runner()
    with tab3:
        page_crypto()


if __name__ == "__main__":
    main()
