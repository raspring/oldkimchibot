# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

An unfinished 2022 hobby bot that watches the "kimchi premium" on BTC: the spread between Bithumb (BTC/KRW) and Kraken (BTC/USD) after converting KRW to USD. It is a loose set of Python scripts. There is no package layout, build, test suite, linter, requirements file or git history.

## Running

```
python3 arbitrage.py
```

This runs at import time: the bottom of `arbitrage.py` builds `arbitrage(GUI='No')`, opens the websockets and starts a thread that recomputes the medians every 15 minutes. The websocket threads are not daemons, so the process runs until it is killed.

- `load_keys.load_key()` reads API keys from the environment: `KRAKEN_API_KEY`/`KRAKEN_API_SECRET`, `BITHUMB_API_KEY`/`BITHUMB_API_SECRET` and `KRAKEN_JK_API_KEY`/`KRAKEN_JK_API_SECRET`. A missing key is `None`. With no keys, the clients skip their startup balance query and the bot runs on public data only. `EXCHANGERATE_API_KEY` is required: `FX_Rates_2.FX_rates` raises without it.
- `data_paths.py` decides where the CSVs go: `$KIMCHI_DATA_DIR` if set, otherwise the iCloud `Crypto` folder if it can be read (macOS privacy settings can block it for terminal apps), otherwise `./data`.

Third-party dependencies (inferred from imports): `pandas`, `numpy`, `scipy`, `requests`, `pycurl`, `websocket-client`, plus `tkinter` for the GUI.

## Architecture

`arbitrage` (in `arbitrage.py`) is the central state object. The other modules feed it:

- **Websocket feeds** (`kraken_ws_classes_1.py`, `bithumb_ws_class_1.py`) take the `arbitrage` instance as `arb_class`/`parent_class`. Each runs `websocket.WebSocketApp.run_forever` on its own thread and **writes directly to attributes on that instance** (`kraken_best_bid`, `kraken_best_ask_vol`, `kraken_timestamp`, …). Each Kraken ticker update calls `arb.update_premium()` and, when a GUI exists, `arb.update_gui()`. All of this runs on websocket threads, without locks.
- **REST clients**: `kraken_api_1.K_API` and `bithumb_api_1.XCoinAPI` handle signed private and public calls (HMAC-SHA512). Bithumb uses `pycurl`; Kraken uses `requests`. `arbitrage.__init__` uses them only to fetch OHLC data and seed `historical_prem`. `update_assets()` reads real balances, but nothing calls it.
- **FX** (`FX_Rates_2.FX_rates`) pulls USD→KRW from exchangerate-api.com and **appends every fetch to a CSV**. `fx_Rates_Auto_Update` busy-polls until `next_update` arrives.
- **GUI** (`kimchi_GUI.visual`): a Tkinter grid of `Entry` widgets that `arbitrage.update_gui()` fills by attribute name. It is optional (`GUI='Yes'`).

Premium = `(bithumb_best_bid / krw_rate - kraken_best_ask) / kraken_best_ask`. `update_premium()` "trades" when the premium moves more than `target_spread` (0.5%) away from the rolling 1-hour median. **Trading is simulated**: it only adjusts the in-memory test balances set at the end of `__init__` (`kraken_usd = 10000`, `bithumb_btc = 0.22`) and adds entries to `self.trade`. No orders are placed. `K_API` and `XCoinAPI` do contain real order methods (`cash_limit`, `margin_limit`, `buy_market`, `limit_order`, …), so take care before wiring them in.

## Environment assumptions

- Data files, relative to `data_paths.DATA_DIR`: `New Arb/krw_usd_historical.csv` (no header; rows are `Unix, rate, date`; the FX module appends a row on every fetch and `arbitrage.load_hist_fx` reads it) and `errors.csv` (the REST clients' error log).
- The Bithumb price feed is `bithumb_ws_class_1.Bithumb_WS`, which uses the `orderbooksnapshot` channel. Only Kraken ticker updates trigger `update_premium()`, and it does nothing until both books have a price.
- `K_API(user=...)` chooses between two credential sets: `'rs'` (the default) or the `jk_*` keys.
- Bithumb trade-websocket timestamps get a hard-coded `-3600` offset to align them with Kraken.
- Module filenames carry version suffixes (`_1`, `_2`), so check which version is actually imported before editing.
