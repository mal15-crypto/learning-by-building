"""
data_collection.py
──────────────────
Fetches live data from:
  • CoinGecko  → crypto metadata + 1-year daily prices (top 3 by market cap)
  • GitHub     → WTI crude oil daily prices (2020-2026)
  • Yahoo Finance (yfinance) → S&P 500, NASDAQ, NIFTY daily prices (2020-2026)

Run this file once (or on a schedule) to populate / refresh the SQLite database.
"""

import requests
import pandas as pd
import yfinance as yf
from datetime import datetime
import database  # our local database.py module


# ─── 1. COINGECKO — COIN METADATA ──────────────────────────────────────────────
def fetch_crypto_metadata() -> pd.DataFrame:
    """
    Hits the CoinGecko /coins/markets endpoint (page 1, 250 coins).
    Returns a cleaned DataFrame ready for the 'cryptocurrencies' table.
    """
    url = (
        "https://api.coingecko.com/api/v3/coins/markets"
        "?vs_currency=usd"
        "&per_page=250"
        "&order=market_cap_desc"
        "&page=1"
        "&sparkline=false"
    )
    resp = requests.get(url)
    resp.raise_for_status()
    raw = resp.json()                          # list of dicts

    keep = [
        "id", "symbol", "name", "current_price", "market_cap",
        "market_cap_rank", "total_volume", "circulating_supply",
        "total_supply", "ath", "atl", "last_updated"
    ]
    df = pd.DataFrame(raw)[keep]
    df["last_updated"] = pd.to_datetime(df["last_updated"]).dt.strftime("%Y-%m-%d")
    df.dropna(subset=["id"], inplace=True)
    print(f"[CoinGecko] Fetched metadata for {len(df)} coins.")
    return df


# ─── 2. COINGECKO — HISTORICAL PRICES (top 3 coins) ───────────────────────────
def fetch_crypto_historical(coin_id: str, symbol: str, name: str, days: int = 365) -> pd.DataFrame:
    """
    Downloads daily price history for a single coin.
    Returns DataFrame with columns: coin_id, symbol, name, date, price_usd
    """
    url = (
        f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart"
        f"?vs_currency=usd&days={days}"
    )
    resp = requests.get(url)
    resp.raise_for_status()
    prices = resp.json().get("prices", [])      # [[timestamp_ms, price], ...]

    df = pd.DataFrame(prices, columns=["timestamp", "price_usd"])
    df["date"]      = pd.to_datetime(df["timestamp"], unit="ms").dt.strftime("%Y-%m-%d")
    df["coin_id"]   = coin_id
    df["symbol"]    = symbol.upper()
    df["name"]      = name
    df             = df[["coin_id", "symbol", "name", "date", "price_usd"]].drop_duplicates(subset="date")
    print(f"[CoinGecko] Fetched {len(df)} daily prices for {name}.")
    return df


def collect_top3_historical(meta_df: pd.DataFrame) -> pd.DataFrame:
    """
    Picks the top 3 coins by market_cap_rank from the metadata DataFrame
    and fetches one year of daily prices for each.
    """
    top3 = meta_df.nsmallest(3, "market_cap_rank")[["id", "symbol", "name"]]
    frames = []
    for _, row in top3.iterrows():
        frames.append(fetch_crypto_historical(row["id"], row["symbol"], row["name"]))
    return pd.concat(frames, ignore_index=True)


# ─── 3. OIL PRICES (WTI) FROM GITHUB CSV ──────────────────────────────────────
def fetch_oil_prices() -> pd.DataFrame:
    """
    Reads the public WTI daily CSV from GitHub.
    Filters for Jan 2020 – Jan 2026.
    Returns DataFrame: date, price_usd
    """
    url = "https://raw.githubusercontent.com/datasets/oil-prices/main/data/wti-daily.csv"
    df  = pd.read_csv(url, parse_dates=["Date"])
    df.columns = df.columns.str.strip().str.lower()          # normalise headers
    df.rename(columns={"date": "date", "price": "price_usd"}, inplace=True)
    df  = df[["date", "price_usd"]]
    df  = df[(df["date"] >= "2020-01-01") & (df["date"] <= "2026-01-31")]
    df["date"] = df["date"].dt.strftime("%Y-%m-%d")
    df.dropna(subset=["price_usd"], inplace=True)
    print(f"[Oil] Fetched {len(df)} daily WTI prices.")
    return df


# ─── 4. STOCK PRICES (Yahoo Finance) ──────────────────────────────────────────
TICKERS = ["^GSPC", "^IXIC", "^NSEI"]          # S&P 500, NASDAQ, NIFTY

def fetch_stock_prices() -> pd.DataFrame:
    """
    Downloads daily OHLCV for each ticker via yfinance.
    Returns a long-format DataFrame: date, open, high, low, close, volume, ticker
    """
    frames = []
    for ticker in TICKERS:
        raw = yf.download(
            ticker,
            start="2020-01-01",
            end="2025-09-30",
            auto_adjust=True,
            progress=False
        )
        raw.reset_index(inplace=True)
        raw.columns = [c[0] if isinstance(c, tuple) else c for c in raw.columns]
        raw.rename(columns={"Date": "date", "Open": "open", "High": "high",
                            "Low": "low", "Close": "close", "Volume": "volume"}, inplace=True)
        raw = raw[["date", "open", "high", "low", "close", "volume"]]
        raw["ticker"] = ticker
        raw["date"]   = pd.to_datetime(raw["date"]).dt.strftime("%Y-%m-%d")
        frames.append(raw)
        print(f"[Yahoo] Fetched {len(raw)} days for {ticker}.")
    return pd.concat(frames, ignore_index=True)


# ─── 5. MASTER PIPELINE ────────────────────────────────────────────────────────
def run_pipeline():
    """
    Orchestrates the full ETL:
      1. Create SQLite tables (idempotent)
      2. Fetch every dataset
      3. Insert into the database
    """
    # 1. Ensure tables exist
    database.create_tables()

    # 2a. Crypto metadata
    meta_df = fetch_crypto_metadata()
    database.insert_cryptocurrencies(meta_df)

    # 2b. Top-3 historical crypto prices
    hist_df = collect_top3_historical(meta_df)
    database.insert_crypto_prices(hist_df)

    # 2c. Oil
    oil_df  = fetch_oil_prices()
    database.insert_oil_prices(oil_df)

    # 2d. Stocks
    stock_df = fetch_stock_prices()
    database.insert_stock_prices(stock_df)

    print("\n✅ Pipeline complete — all data is in crossmarket.db")


# ─── ENTRY POINT ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    run_pipeline()
