import json
import os
import pandas as pd
import streamlit as st
from utils.technicals import rank_macro_universe, screen_institutional_dip

# Page Configuration for Chromebook Browser
st.set_page_config(
    page_title="Recommend Tickers (RT)", page_icon="🎯", layout="wide"
)

# Load Configuration
CONFIG_PATH = "config.json"


@st.cache_data
def load_config():
  if os.path.exists(CONFIG_PATH):
    with open(CONFIG_PATH, "r") as f:
      return json.load(f)
  return {}


config = load_config()

# Initialize Session State for Watchlists (Core ETF vs Satellite Stock)
if "core_watchlist" not in st.session_state:
  st.session_state.core_watchlist = []
if "stock_watchlist" not in st.session_state:
  st.session_state.stock_watchlist = []

# --- Title & Help / Criteria Panel ---
st.title("🎯 Recommend Tickers (RT)")
st.markdown(
    "**Institutional Capital Flow & Medium-Term Dip-Buying Framework**"
)

with st.expander(
    "📖 How to Use & Criteria for Success (Click to Expand)", expanded=False
):
  st.markdown("""
    ### Objective
    Build and maintain a rock-solid **Core ETF Portfolio** while opportunistically deploying **10-20% into Individual Stocks (Satellite)** using institutional accumulation signals over a multi-month/quarter horizon.
    
    ### The 3-Stage Funnel Workflow
    1. **Stage 1 (Macro Relative Strength):** Scans global asset classes and sectors relative to your chosen benchmark (`SPY`, `QQQ`, `DIA`, `EEM`) over a 3 to 6-month lookback to locate active institutional capital.
    2. **Stage 2 (Institutional Dip Screener):** Evaluates tickers for structural bull trends and high-probability dip entries.
    3. **Stage 3 (Shortlist & Watchlist Docket):** Pushes qualified candidates directly into persistent session-state watchlists for precise entry tracking.
    
    ### Criteria for Success (The Institutional Filters)
    * **Structural Uptrend:** $\\text{Price} > 200\\text{ SMA}$ and $50\\text{ SMA} > 200\\text{ SMA}$.
    * **The Dip Zone:** Price is resting near the 50-day moving average ($\le 4\%$ away) or undergoing a controlled $5\\text{--}12\%$ pullback from 52-week highs.
    * **Volume Footprint:** 50-day Up/Down Volume Ratio $\ge 1.15$, proving institutional accumulation on rallies and calm support during pullbacks.
    """)

# --- Sidebar Controls ---
st.sidebar.header("Funnel Navigation")
funnel_stage = st.sidebar.radio(
    "Select Funnel Stage",
    [
        "Stage 1: Macro & Sector Heatmap",
        "Stage 2: Institutional Dip Screener",
        "Stage 3: Research Docket & Watchlist",
    ],
)

# --- STAGE 1: Macro & Sector Heatmap ---
if funnel_stage == "Stage 1: Macro & Sector Heatmap":
  st.header("Stage 1: Global Macro & Sector Capital Flow")
  st.markdown(
      "Ranking global asset classes and sectors by persistent multi-month"
      " momentum."
  )

  benchmarks = config.get("benchmarks", ["SPY"])
  selected_benchmark = st.selectbox(
      "Select Benchmark for Relative Strength Comparison", benchmarks
  )

  universe = config.get("global_macro_universe", {})

  if st.button("Run Macro Heatmap Scan", type="primary"):
    with st.spinner("Downloading historical data & calculating momentum..."):
      df_ranked = rank_macro_universe(universe, benchmark=selected_benchmark)

      if not df_ranked.empty:
        st.success("Macro scan complete!")
        st.dataframe(df_ranked, use_container_width=True)
      else:
        st.error(
            "Unable to retrieve data. Please check your network connection."
        )

# --- STAGE 2: Institutional Dip Screener ---
elif funnel_stage == "Stage 2: Institutional Dip Screener":
  st.header("Stage 2: Institutional Dip Screener")
  st.markdown(
      "Scan either your **Core ETFs** or **Satellite Stocks** for high-conviction"
      " pullback entries."
  )

  scan_target = st.radio(
      "Choose Universe to Scan",
      ["Core ETFs (Global & Sectors)", "Satellite Stocks (Individual Equities)"],
  )

  if scan_target.startswith("Core"):
    target_dict = config.get("global_macro_universe", {})
    universe_tickers = list(target_dict.values())
  else:
    universe_tickers = config.get("default_stock_universe", [])

  if st.button("Run Dip Screener", type="primary"):
    results = []
    progress_bar = st.progress(0)
    total = len(universe_tickers)

    for i, ticker in enumerate(universe_tickers):
      res = screen_institutional_dip(ticker)
      if res.get("pass"):
        results.append({"Ticker": ticker, **res})
      progress_bar.progress((i + 1) / total)

    progress_bar.empty()

    if results:
      st.session_state.last_scan_results = results
      st.session_state.last_scan_target = scan_target
    else:
      st.session_state.last_scan_results = []
      st.session_state.last_scan_target = scan_target

  # Display persistent scan results if available
  if (
      "last_scan_results" in st.session_state
      and st.session_state.last_scan_results
  ):
    res_df = pd.DataFrame(st.session_state.last_scan_results)
    st.success(
        f"Found {len(res_df)} candidates meeting institutional dip criteria!"
    )
    st.dataframe(res_df, use_container_width=True)

    st.subheader("Add to Watchlist")
    selected_to_add = st.multiselect(
        "Select Tickers to Save",
        options=res_df["Ticker"].tolist(),
        default=res_df["Ticker"].tolist(),
    )

    if st.session_state.get("last_scan_target", "").startswith("Core"):
      if st.button("Add Selected to Core ETF Watchlist", type="primary"):
        added = 0
        for t in selected_to_add:
          if t not in st.session_state.core_watchlist:
            st.session_state.core_watchlist.append(t)
            added += 1
        if added > 0:
          st.success(f"Added {added} ticker(s) to Core ETF Watchlist!")
        else:
          st.info("Selected tickers are already in your Core Watchlist.")
    else:
      if st.button("Add Selected to Satellite Stock Watchlist", type="primary"):
        added = 0
        for t in selected_to_add:
          if t not in st.session_state.stock_watchlist:
            st.session_state.stock_watchlist.append(t)
            added += 1
        if added > 0:
          st.success(f"Added {added} ticker(s) to Satellite Stock Watchlist!")
        else:
          st.info(
              "Selected tickers are already in your Satellite Stock Watchlist."
          )
  elif "last_scan_results" in st.session_state:
    st.warning(
        "No tickers passed the strict institutional dip criteria in this run."
        " Markets may be extended."
    )

# --- STAGE 3: Research Docket & Watchlist ---
elif funnel_stage == "Stage 3: Research Docket & Watchlist":
  st.header("Stage 3: Shortlist & 200-Day Triggers Watchlist")
  st.markdown(
      "Manage your core portfolio allocations and tactical satellite triggers."
  )

  col1, col2 = st.columns(2)

  with col1:
    st.subheader("🛡️ Core ETF Watchlist")
    if st.session_state.core_watchlist:
      for t in list(st.session_state.core_watchlist):
        c1, c2, c3 = st.columns([2, 2, 1])
        with c1:
          st.code(t)
        with c2:
          st.markdown(f"[Chart ↗](https://finance.yahoo.com/quote/{t})")
        with c3:
          if st.button("❌", key=f"del_core_{t}"):
            st.session_state.core_watchlist.remove(t)
            st.rerun()

      if st.button("Clear Core Watchlist", key="clear_core"):
        st.session_state.core_watchlist = []
        st.rerun()
    else:
      st.info("No Core ETFs saved yet.")

  with col2:
    st.subheader("🚀 Satellite Stock Watchlist (10-20% Allocation)")
    if st.session_state.stock_watchlist:
      for t in list(st.session_state.stock_watchlist):
        c1, c2, c3 = st.columns([2, 2, 1])
        with c1:
          st.code(t)
        with c2:
          st.markdown(f"[Chart ↗](https://finance.yahoo.com/quote/{t})")
        with c3:
          if st.button("❌", key=f"del_stock_{t}"):
            st.session_state.stock_watchlist.remove(t)
            st.rerun()

      if st.button("Clear Stock Watchlist", key="clear_stock"):
        st.session_state.stock_watchlist = []
        st.rerun()

      st.divider()
      # Bridge link to open watchlist in your 200 Day Triggers app
      tickers_string = ",".join(st.session_state.stock_watchlist)
      target_200day_url = f"https://your-200-day-triggers-app.streamlit.app/?preset=Watching&tickers={tickers_string}"
      st.markdown(
          f"🔗 **[Open Watchlist in 200 Day Triggers App ↗]({target_200day_url})**"
      )
    else:
      st.info("No Satellite Stocks saved yet.")
