# rt
Recommend Tickers
# Recommend Tickers (RT)

A progressive funnel workflow designed for medium-term institutional investors (holding horizon: months & quarters). Built to run natively in Streamlit via browser environment.

## Core Methodology: The Institutional Funnel
1. **Stage 1 (Macro & Relative Strength Ranking):** Scans global macro indexes, asset classes, and thematic ETFs relative to a user-selected benchmark (`SPY`, `QQQ`, `DIA`, `EEM`) to locate active institutional capital rotation.
2. **Stage 2 (Institutional Dip Screener):** Filters Core ETFs or Satellite Stocks for structural bull trends ($\text{Price} > 200\text{ SMA}$ and $50\text{ SMA} > 200\text{ SMA}$) undergoing a high-probability institutional dip (resting near the 50-day SMA with positive up/down volume accumulation).
3. **Stage 3 (Shortlist & Watchlist Docket):** Manages local session state to track filtered candidates across separate **Core ETF** and **Satellite Stock** watchlists.

## How to Run Locally / Streamlit Cloud
1. Ensure all files (`app.py`, `config.json`, `requirements.txt`, `utils/technicals.py`) are in your GitHub repository.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
