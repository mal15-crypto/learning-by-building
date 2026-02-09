## 💰🛢📈 Cross-Market Analysis — Crypto, Oil & Stocks

A SQL-powered analytics dashboard built with **Python · SQLite3 · Streamlit**.

---

### 📂 File Structure

```
project/
├── app.py                 ← Streamlit app (3 pages)
├── database.py            ← SQLite3 table creation, inserts, all query helpers
├── data_collection.py     ← ETL: fetches data from APIs & CSV → inserts into DB
├── sql_queries.py         ← All 30 predefined SQL queries for the Runner page
├── requirements.txt       ← pip dependencies
└── README.md              ← this file
```

---

### ⚡ How to Run (step by step)

**1. Install dependencies**
```bash
pip install -r requirements.txt
```

**2. Collect data & build the database**
```bash
python data_collection.py
```
This will:
- Fetch top-250 crypto metadata from CoinGecko
- Download 1-year daily prices for the top 3 coins (by market cap)
- Pull WTI oil prices (2020–2026) from the GitHub dataset
- Download S&P 500, NASDAQ, NIFTY prices (2020–2025) via Yahoo Finance
- Create `crossmarket.db` (SQLite3) and insert everything

**3. Launch the Streamlit dashboard**
```bash
streamlit run app.py
```
Open the URL shown in the terminal (usually `http://localhost:8501`).

---

### 📊 What's Inside the App

| Page | Description |
|---|---|
| **Filters & Data Exploration** | Date-range picker → live KPIs (BTC / Oil / S&P 500 / NIFTY averages) + a JOIN snapshot table + multi-axis trend chart |
| **SQL Query Runner** | Pick any of the 30 predefined queries by group, preview the SQL, hit Run, see results in a table |
| **Top 3 Crypto Analysis** | Select a coin → date range → price trend chart + daily table with % change |

---

### 🗄 Database Tables

| Table | Key Columns |
|---|---|
| `cryptocurrencies` | id (PK), symbol, name, current_price, market_cap, market_cap_rank, total_volume, circulating_supply, total_supply, ath, atl, last_updated |
| `crypto_prices` | coin_id (FK), symbol, name, date, price_usd |
| `oil_prices` | date (PK), price_usd |
| `stock_prices` | date, open, high, low, close, volume, ticker |

---

### 🔗 Data Sources

| Source | What it provides |
|---|---|
| CoinGecko API | Crypto metadata + historical daily prices |
| GitHub (datasets/oil-prices) | WTI crude oil daily prices |
| Yahoo Finance (yfinance) | S&P 500 (`^GSPC`), NASDAQ (`^IXIC`), NIFTY (`^NSEI`) |
