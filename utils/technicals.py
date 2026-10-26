import numpy as np
import pandas as pd
import yfinance as yf


def rank_macro_universe(universe_dict: dict, benchmark: str = "SPY") -> pd.DataFrame:
  """Downloads 6m data for global/sector ETFs and ranks them by multi-month relative performance against a chosen benchmark."""
  tickers = list(universe_dict.values())
  if benchmark not in tickers:
    tickers.append(benchmark)

  # Fetch close prices safely
  data = yf.download(tickers, period="6m", progress=False)["Close"]

  if isinstance(data, pd.Series):
    data = data.to_frame()

  if benchmark not in data.columns:
    return pd.DataFrame()

  # Calculate 3-month (63 trading days) and 6-month returns
  returns_3m = (data.iloc[-1] - data.iloc[-min(63, len(data) - 1)]) / data.iloc[
      -min(63, len(data) - 1)
  ]
  returns_6m = (data.iloc[-1] - data.iloc[0]) / data.iloc[0]

  benchmark_3m = returns_3m[benchmark]
  benchmark_6m = returns_6m[benchmark]

  results = []
  for name, symbol in universe_dict.items():
    if symbol in data.columns:
      rel_3m = returns_3m[symbol] - benchmark_3m
      rel_6m = returns_6m[symbol] - benchmark_6m
      composite_score = (rel_3m * 0.6) + (rel_6m * 0.4)

      results.append({
          "Asset / Sector": name,
          "Ticker": symbol,
          "3M Return": f"{returns_3m[symbol]:.1%}",
          "6M Return": f"{returns_6m[symbol]:.1%}",
          "3M Rel vs {benchmark}": f"{rel_3m:+.1%}",
          "Score": round(composite_score, 4),
      })

  df_ranked = pd.DataFrame(results).sort_values(by="Score", ascending=False)
  return df_ranked


def screen_institutional_dip(ticker: str, period: str = "1y") -> dict:
  """Evaluates structural uptrend and institutional dip criteria for a given ticker."""
  df = yf.download(ticker, period=period, progress=False)

  if df.empty or len(df) < 200:
    return {"pass": False, "reason": "Insufficient historical data"}

  if isinstance(df.columns, pd.MultiIndex):
    df.columns = df.columns.get_level_values(0)

  df["SMA_200"] = df["Close"].rolling(window=200).mean()
  df["SMA_50"] = df["Close"].rolling(window=50).mean()

  latest = df.iloc[-1]
  close_price = latest["Close"]
  sma_50 = latest["SMA_50"]
  sma_200 = latest["SMA_200"]

  # 1. Structural Uptrend Check
  in_uptrend = (close_price > sma_200) and (sma_50 > sma_200)

  # 2. Buy-the-Dip Check (Near 50 SMA or healthy pullback from highs)
  dist_from_50 = (close_price - sma_50) / sma_50
  high_52w = df["High"].tail(252).max()
  pullback_from_high = (high_52w - close_price) / high_52w

  is_dip_zone = (-0.04 <= dist_from_50 <= 0.03) or (
      0.05 <= pullback_from_high <= 0.12
  )

  # 3. Institutional Accumulation (Up vs Down Volume Ratio over 50 days)
  recent_df = df.tail(50).copy()
  up_vol = recent_df[recent_df["Close"] > recent_df["Open"]]["Volume"].sum()
  down_vol = recent_df[recent_df["Close"] < recent_df["Open"]]["Volume"].sum()
  ud_ratio = (up_vol / down_vol) if down_vol > 0 else 1.0
  is_accumulating = ud_ratio >= 1.15

  passed = in_uptrend and is_dip_zone and is_accumulating

  return {
      "pass": passed,
      "price": round(close_price, 2),
      "sma_50": round(sma_50, 2),
      "sma_200": round(sma_200, 2),
      "dist_50sma": f"{round(dist_from_50 * 100, 1)}%",
      "pullback_high": f"{round(pullback_from_high * 100, 1)}%",
      "vol_ratio": round(ud_ratio, 2),
  }
