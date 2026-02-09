"""
database.py
───────────
All SQLite3 logic lives here:
  • create_tables()          – idempotent DDL
  • insert_*()               – bulk-upsert helpers (called by data_collection.py)
  • run_query(sql)           – generic SELECT executor (used by the SQL runner page)
  • Helper functions used by the Streamlit pages to pull specific data.
"""

import sqlite3
import pandas as pd

DB_PATH = "crossmarket.db"


# ─── CONNECTION HELPER ─────────────────────────────────────────────────────────
def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row          # dict-like access
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


# ─── 1. TABLE CREATION (idempotent) ────────────────────────────────────────────
DDL = """
-- 1. Cryptocurrencies (metadata snapshot)
CREATE TABLE IF NOT EXISTS cryptocurrencies (
    id                  VARCHAR(50)     PRIMARY KEY,
    symbol              VARCHAR(10),
    name                VARCHAR(100),
    current_price       DECIMAL(18, 6),
    market_cap          BIGINT,
    market_cap_rank     INT,
    total_volume        BIGINT,
    circulating_supply  DECIMAL(20, 6),
    total_supply        DECIMAL(20, 6),
    ath                 DECIMAL(18, 6),
    atl                 DECIMAL(18, 6),
    last_updated        DATE
);

-- 2. Crypto daily prices (top coins, 1 year)
CREATE TABLE IF NOT EXISTS crypto_prices (
    coin_id     VARCHAR(50),
    symbol      VARCHAR(10),
    name        VARCHAR(100),
    date        DATE,
    price_usd   DECIMAL(18, 6),
    PRIMARY KEY (coin_id, date),
    FOREIGN KEY (coin_id) REFERENCES cryptocurrencies(id)
);

-- 3. Oil prices (WTI)
CREATE TABLE IF NOT EXISTS oil_prices (
    date        DATE            PRIMARY KEY,
    price_usd   DECIMAL(18, 6)
);

-- 4. Stock prices (S&P 500, NASDAQ, NIFTY)
CREATE TABLE IF NOT EXISTS stock_prices (
    date        DATE,
    open        DECIMAL(18, 6),
    high        DECIMAL(18, 6),
    low         DECIMAL(18, 6),
    close       DECIMAL(18, 6),
    volume      BIGINT,
    ticker      VARCHAR(20),
    PRIMARY KEY (date, ticker)
);
"""


def create_tables():
    conn = get_connection()
    conn.executescript(DDL)
    conn.commit()
    conn.close()
    print("[DB] Tables created / verified.")


# ─── 2. INSERT HELPERS ─────────────────────────────────────────────────────────
def insert_cryptocurrencies(df: pd.DataFrame):
    conn = get_connection()
    df.to_sql("cryptocurrencies", conn, if_exists="replace", index=False)
    conn.commit()
    conn.close()
    print(f"[DB] Inserted {len(df)} rows → cryptocurrencies")


def insert_crypto_prices(df: pd.DataFrame):
    conn = get_connection()
    df.to_sql("crypto_prices", conn, if_exists="replace", index=False)
    conn.commit()
    conn.close()
    print(f"[DB] Inserted {len(df)} rows → crypto_prices")


def insert_oil_prices(df: pd.DataFrame):
    conn = get_connection()
    df.to_sql("oil_prices", conn, if_exists="replace", index=False)
    conn.commit()
    conn.close()
    print(f"[DB] Inserted {len(df)} rows → oil_prices")


def insert_stock_prices(df: pd.DataFrame):
    conn = get_connection()
    df.to_sql("stock_prices", conn, if_exists="replace", index=False)
    conn.commit()
    conn.close()
    print(f"[DB] Inserted {len(df)} rows → stock_prices")


# ─── 3. GENERIC QUERY RUNNER ──────────────────────────────────────────────────
def run_query(sql: str) -> pd.DataFrame:
    """Execute any SELECT and return a pandas DataFrame."""
    conn = get_connection()
    try:
        df = pd.read_sql_query(sql, conn)
    finally:
        conn.close()
    return df


# ─── 4. PAGE-1 HELPERS (Filters & Data Exploration) ──────────────────────────
def get_btc_avg(start: str, end: str) -> float:
    sql = """
        SELECT AVG(price_usd) AS avg_price
        FROM crypto_prices
        WHERE coin_id = 'bitcoin'
          AND date BETWEEN :start AND :end
    """
    conn = get_connection()
    row  = conn.execute(sql, {"start": start, "end": end}).fetchone()
    conn.close()
    return row["avg_price"] or 0.0


def get_oil_avg(start: str, end: str) -> float:
    sql = """
        SELECT AVG(price_usd) AS avg_price
        FROM oil_prices
        WHERE date BETWEEN :start AND :end
    """
    conn = get_connection()
    row  = conn.execute(sql, {"start": start, "end": end}).fetchone()
    conn.close()
    return row["avg_price"] or 0.0


def get_stock_avg(ticker: str, start: str, end: str) -> float:
    sql = """
        SELECT AVG(close) AS avg_close
        FROM stock_prices
        WHERE ticker = :ticker
          AND date  BETWEEN :start AND :end
    """
    conn = get_connection()
    row  = conn.execute(sql, {"ticker": ticker, "start": start, "end": end}).fetchone()
    conn.close()
    return row["avg_close"] or 0.0


def get_daily_snapshot(start: str, end: str) -> pd.DataFrame:
    """
    JOIN query: Bitcoin price + Oil price + S&P 500 close + NIFTY close
    on the same date.  Only returns dates where ALL four have data.
    """
    sql = """
        SELECT
            cp.date                         AS date,
            cp.price_usd                    AS bitcoin_price,
            op.price_usd                    AS oil_price,
            sp.close                        AS sp500_close,
            ni.close                        AS nifty_close
        FROM crypto_prices   cp
        JOIN oil_prices      op  ON cp.date = op.date
        JOIN stock_prices    sp  ON cp.date = sp.date  AND sp.ticker = '^GSPC'
        JOIN stock_prices    ni  ON cp.date = ni.date  AND ni.ticker = '^NSEI'
        WHERE cp.coin_id = 'bitcoin'
          AND cp.date BETWEEN :start AND :end
        ORDER BY cp.date
    """
    conn = get_connection()
    df   = pd.read_sql_query(sql, conn, params={"start": start, "end": end})
    conn.close()
    return df


# ─── 5. PAGE-3 HELPERS (Top-3 Crypto) ─────────────────────────────────────────
def get_available_coins() -> list[dict]:
    """Return the top 3 coins stored in crypto_prices (distinct)."""
    sql = """
        SELECT DISTINCT coin_id, symbol, name
        FROM crypto_prices
        ORDER BY coin_id
    """
    conn = get_connection()
    rows = conn.execute(sql).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_coin_prices(coin_id: str, start: str, end: str) -> pd.DataFrame:
    sql = """
        SELECT date, price_usd
        FROM crypto_prices
        WHERE coin_id = :coin_id
          AND date BETWEEN :start AND :end
        ORDER BY date
    """
    conn = get_connection()
    df   = pd.read_sql_query(sql, conn, params={"coin_id": coin_id, "start": start, "end": end})
    conn.close()
    return df
