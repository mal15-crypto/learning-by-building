"""
sql_queries.py
──────────────
All predefined SQL queries for the "SQL Query Runner" page.
Each entry is a dict with:
    group   → tab / category label
    label   → human-readable title shown in the dropdown
    sql     → the actual SQL string executed against crossmarket.db
"""

QUERIES = [
    # ──────────────── CRYPTOCURRENCIES ────────────────────────────────────────
    {
        "group": "Cryptocurrencies",
        "label": "1. Top 3 cryptocurrencies by market cap",
        "sql": """
SELECT id, name, symbol, current_price, market_cap
FROM cryptocurrencies
ORDER BY market_cap DESC
LIMIT 3;
        """
    },
    {
        "group": "Cryptocurrencies",
        "label": "2. Coins where circulating supply > 90 % of total supply",
        "sql": """
SELECT id, name, circulating_supply, total_supply,
       ROUND(circulating_supply * 100.0 / total_supply, 2) AS supply_pct
FROM cryptocurrencies
WHERE total_supply IS NOT NULL
  AND total_supply > 0
  AND (circulating_supply * 1.0 / total_supply) > 0.9;
        """
    },
    {
        "group": "Cryptocurrencies",
        "label": "3. Coins within 10 % of their all-time high (ATH)",
        "sql": """
SELECT id, name, current_price, ath,
       ROUND((ath - current_price) * 100.0 / ath, 2) AS pct_below_ath
FROM cryptocurrencies
WHERE ath IS NOT NULL
  AND ath > 0
  AND ((ath - current_price) * 1.0 / ath) <= 0.10;
        """
    },
    {
        "group": "Cryptocurrencies",
        "label": "4. Average market-cap rank (volume > $1 B)",
        "sql": """
SELECT ROUND(AVG(market_cap_rank), 2) AS avg_rank
FROM cryptocurrencies
WHERE total_volume > 1000000000;
        """
    },
    {
        "group": "Cryptocurrencies",
        "label": "5. Most recently updated coin",
        "sql": """
SELECT id, name, symbol, last_updated
FROM cryptocurrencies
ORDER BY last_updated DESC
LIMIT 1;
        """
    },

    # ──────────────── CRYPTO PRICES ───────────────────────────────────────────
    {
        "group": "Crypto Prices",
        "label": "1. Highest daily Bitcoin price (last 365 days)",
        "sql": """
SELECT MAX(price_usd) AS highest_price
FROM crypto_prices
WHERE coin_id = 'bitcoin'
  AND date >= date('now', '-365 days');
        """
    },
    {
        "group": "Crypto Prices",
        "label": "2. Average daily Ethereum price (past 1 year)",
        "sql": """
SELECT ROUND(AVG(price_usd), 2) AS avg_price
FROM crypto_prices
WHERE coin_id = 'ethereum'
  AND date >= date('now', '-365 days');
        """
    },
    {
        "group": "Crypto Prices",
        "label": "3. Bitcoin daily price trend – January 2025",
        "sql": """
SELECT date, price_usd
FROM crypto_prices
WHERE coin_id  = 'bitcoin'
  AND date BETWEEN '2025-01-01' AND '2025-01-31'
ORDER BY date;
        """
    },
    {
        "group": "Crypto Prices",
        "label": "4. Coin with the highest average price over 1 year",
        "sql": """
SELECT coin_id, name,
       ROUND(AVG(price_usd), 2) AS avg_price
FROM crypto_prices
WHERE date >= date('now', '-365 days')
GROUP BY coin_id, name
ORDER BY avg_price DESC
LIMIT 1;
        """
    },
    {
        "group": "Crypto Prices",
        "label": "5. % change in Bitcoin price – Sep 2024 vs Sep 2025",
        "sql": """
SELECT
    sep24.avg_price                                          AS sep_2024_avg,
    sep25.avg_price                                          AS sep_2025_avg,
    ROUND((sep25.avg_price - sep24.avg_price) * 100.0
          / sep24.avg_price, 2)                              AS pct_change
FROM
    (SELECT AVG(price_usd) AS avg_price FROM crypto_prices
      WHERE coin_id = 'bitcoin'
        AND date BETWEEN '2024-09-01' AND '2024-09-30') sep24,
    (SELECT AVG(price_usd) AS avg_price FROM crypto_prices
      WHERE coin_id = 'bitcoin'
        AND date BETWEEN '2025-09-01' AND '2025-09-30') sep25;
        """
    },

    # ──────────────── OIL PRICES ──────────────────────────────────────────────
    {
        "group": "Oil Prices",
        "label": "1. Highest oil price in the last 5 years",
        "sql": """
SELECT MAX(price_usd) AS highest_oil_price
FROM oil_prices
WHERE date >= '2021-01-01';
        """
    },
    {
        "group": "Oil Prices",
        "label": "2. Average oil price per year",
        "sql": """
SELECT
    CAST(strftime('%Y', date) AS INTEGER) AS year,
    ROUND(AVG(price_usd), 2)             AS avg_price
FROM oil_prices
GROUP BY year
ORDER BY year;
        """
    },
    {
        "group": "Oil Prices",
        "label": "3. Oil prices during COVID crash (Mar–Apr 2020)",
        "sql": """
SELECT date, price_usd
FROM oil_prices
WHERE date BETWEEN '2020-03-01' AND '2020-04-30'
ORDER BY date;
        """
    },
    {
        "group": "Oil Prices",
        "label": "4. Lowest oil price in the last 10 years",
        "sql": """
SELECT date, MIN(price_usd) AS lowest_oil_price
FROM oil_prices
WHERE date >= '2016-01-01';
        """
    },
    {
        "group": "Oil Prices",
        "label": "5. Yearly oil-price volatility (max – min per year)",
        "sql": """
SELECT
    CAST(strftime('%Y', date) AS INTEGER) AS year,
    ROUND(MAX(price_usd) - MIN(price_usd), 2) AS volatility
FROM oil_prices
GROUP BY year
ORDER BY year;
        """
    },

    # ──────────────── STOCK PRICES ────────────────────────────────────────────
    {
        "group": "Stock Prices",
        "label": "1. All stock prices for S&P 500 (^GSPC)",
        "sql": """
SELECT date, open, high, low, close, volume
FROM stock_prices
WHERE ticker = '^GSPC'
ORDER BY date DESC
LIMIT 30;
        """
    },
    {
        "group": "Stock Prices",
        "label": "2. Highest closing price – NASDAQ (^IXIC)",
        "sql": """
SELECT MAX(close) AS highest_close
FROM stock_prices
WHERE ticker = '^IXIC';
        """
    },
    {
        "group": "Stock Prices",
        "label": "3. Top 5 days with highest intra-day range – S&P 500",
        "sql": """
SELECT date, high, low,
       ROUND(high - low, 2) AS intraday_range
FROM stock_prices
WHERE ticker = '^GSPC'
ORDER BY intraday_range DESC
LIMIT 5;
        """
    },
    {
        "group": "Stock Prices",
        "label": "4. Monthly average closing price – all tickers",
        "sql": """
SELECT
    ticker,
    strftime('%Y-%m', date)       AS month,
    ROUND(AVG(close), 2)          AS avg_close
FROM stock_prices
GROUP BY ticker, month
ORDER BY ticker, month DESC;
        """
    },
    {
        "group": "Stock Prices",
        "label": "5. Average trading volume – NIFTY (^NSEI) in 2024",
        "sql": """
SELECT ROUND(AVG(volume), 0) AS avg_volume
FROM stock_prices
WHERE ticker = '^NSEI'
  AND date BETWEEN '2024-01-01' AND '2024-12-31';
        """
    },

    # ──────────────── CROSS-MARKET (JOIN) QUERIES ─────────────────────────────
    {
        "group": "Cross-Market Joins",
        "label": "1. Bitcoin vs Oil – average price in 2025",
        "sql": """
SELECT
    ROUND(AVG(cp.price_usd), 2)  AS btc_avg_2025,
    ROUND(AVG(op.price_usd), 2)  AS oil_avg_2025
FROM crypto_prices cp
JOIN oil_prices    op  ON cp.date = op.date
WHERE cp.coin_id = 'bitcoin'
  AND cp.date BETWEEN '2025-01-01' AND '2025-12-31';
        """
    },
    {
        "group": "Cross-Market Joins",
        "label": "2. Bitcoin vs S&P 500 – daily prices 2025",
        "sql": """
SELECT
    cp.date,
    cp.price_usd  AS btc_price,
    sp.close      AS sp500_close
FROM crypto_prices cp
JOIN stock_prices  sp  ON cp.date = sp.date AND sp.ticker = '^GSPC'
WHERE cp.coin_id = 'bitcoin'
  AND cp.date BETWEEN '2025-01-01' AND '2025-12-31'
ORDER BY cp.date;
        """
    },
    {
        "group": "Cross-Market Joins",
        "label": "3. Ethereum vs NASDAQ – daily prices 2025",
        "sql": """
SELECT
    cp.date,
    cp.price_usd  AS eth_price,
    sp.close      AS nasdaq_close
FROM crypto_prices cp
JOIN stock_prices  sp  ON cp.date = sp.date AND sp.ticker = '^IXIC'
WHERE cp.coin_id = 'ethereum'
  AND cp.date BETWEEN '2025-01-01' AND '2025-12-31'
ORDER BY cp.date;
        """
    },
    {
        "group": "Cross-Market Joins",
        "label": "4. Oil-spike days vs Bitcoin price change",
        "sql": """
WITH oil_spikes AS (
    SELECT
        o1.date,
        o1.price_usd                                          AS oil_price,
        ROUND((o1.price_usd - o0.price_usd) * 100.0
              / o0.price_usd, 2)                              AS oil_chg_pct
    FROM oil_prices o1
    JOIN oil_prices o0
        ON o0.date = (SELECT MAX(date) FROM oil_prices
                      WHERE date < o1.date)
)
SELECT
    os.date,
    os.oil_price,
    os.oil_chg_pct,
    cp.price_usd  AS btc_price
FROM oil_spikes   os
JOIN crypto_prices cp ON os.date = cp.date AND cp.coin_id = 'bitcoin'
WHERE os.oil_chg_pct > 3          -- spike = >3 %  daily rise
ORDER BY os.oil_chg_pct DESC
LIMIT 10;
        """
    },
    {
        "group": "Cross-Market Joins",
        "label": "5. Top-3 coins vs NIFTY – daily 2025",
        "sql": """
SELECT
    cp.date,
    cp.coin_id,
    cp.price_usd        AS crypto_price,
    sp.close            AS nifty_close
FROM crypto_prices cp
JOIN stock_prices  sp ON cp.date = sp.date AND sp.ticker = '^NSEI'
WHERE cp.date BETWEEN '2025-01-01' AND '2025-12-31'
ORDER BY cp.date, cp.coin_id;
        """
    },
    {
        "group": "Cross-Market Joins",
        "label": "6. S&P 500 vs Crude Oil – same dates",
        "sql": """
SELECT
    sp.date,
    sp.close      AS sp500_close,
    op.price_usd  AS oil_price
FROM stock_prices sp
JOIN oil_prices   op ON sp.date = op.date
WHERE sp.ticker = '^GSPC'
ORDER BY sp.date DESC
LIMIT 30;
        """
    },
    {
        "group": "Cross-Market Joins",
        "label": "7. Bitcoin ↔ Oil correlation (same-date prices)",
        "sql": """
SELECT
    cp.date,
    cp.price_usd  AS btc_price,
    op.price_usd  AS oil_price
FROM crypto_prices cp
JOIN oil_prices    op ON cp.date = op.date
WHERE cp.coin_id = 'bitcoin'
ORDER BY cp.date;
        """
    },
    {
        "group": "Cross-Market Joins",
        "label": "8. NASDAQ vs Ethereum price trends",
        "sql": """
SELECT
    cp.date,
    cp.price_usd  AS eth_price,
    sp.close      AS nasdaq_close
FROM crypto_prices cp
JOIN stock_prices  sp ON cp.date = sp.date AND sp.ticker = '^IXIC'
WHERE cp.coin_id = 'ethereum'
ORDER BY cp.date;
        """
    },
    {
        "group": "Cross-Market Joins",
        "label": "9. Top-5 crypto coins + stock indices – 2024",
        "sql": """
SELECT
    cp.date,
    cp.coin_id,
    cp.price_usd        AS crypto_price,
    sp.ticker           AS stock_ticker,
    sp.close            AS stock_close
FROM crypto_prices cp
JOIN stock_prices  sp ON cp.date = sp.date
WHERE cp.date BETWEEN '2024-01-01' AND '2024-12-31'
ORDER BY cp.date LIMIT 50;
        """
    },
    {
        "group": "Cross-Market Joins",
        "label": "10. Multi-join: BTC + Oil + S&P 500 daily",
        "sql": """
SELECT
    cp.date,
    cp.price_usd  AS btc_price,
    op.price_usd  AS oil_price,
    sp.close      AS sp500_close
FROM crypto_prices cp
JOIN oil_prices    op ON cp.date = op.date
JOIN stock_prices  sp ON cp.date = sp.date AND sp.ticker = '^GSPC'
WHERE cp.coin_id = 'bitcoin'
ORDER BY cp.date DESC
LIMIT 30;
        """
    },
]
