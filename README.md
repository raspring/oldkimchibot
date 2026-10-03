# oldkimchibot

A 2022 hobby project that tracks the **"kimchi premium"** on Bitcoin. That's the gap between the BTC price on the Korean exchange [Bithumb](https://www.bithumb.com) (in KRW) and on [Kraken](https://www.kraken.com) (in USD), once KRW is converted to USD.

> **Status:** unfinished and experimental. **Trading is simulated.** The bot only changes balances held in memory and never places orders. The REST clients do include real order methods, so be careful before connecting them to anything.

## How it works

```
premium = (bithumb_best_bid / usd_krw_rate - kraken_best_ask) / kraken_best_ask
```

1. **At startup**, the bot downloads recent price candles (OHLC data) from both exchanges and the USD/KRW rate. From these it builds a premium history and its rolling medians (1 hour, 12 hours, day, week, month).
2. **Live prices** come in over websockets: Kraken's ticker and Bithumb's order book snapshots. Each Kraken update recalculates the premium.
3. **Simulated trades**: when the premium is more than 0.5% above the 1-hour median, the bot "opens" a trade: it buys BTC on Kraken and sells it on Bithumb. When the premium is 0.5% below the median, it "closes" by doing the reverse. Medians are recalculated every 15 minutes.

| File | Role |
| --- | --- |
| `arbitrage.py` | Entry point. Holds the central state, the premium calculation and the simulated trading. |
| `kraken_ws_classes_1.py`, `bithumb_ws_class_1.py` | Websocket price feeds |
| `kraken_api_1.py`, `bithumb_api_1.py` | REST clients (public and signed private calls) |
| `FX_Rates_2.py` | USD/KRW rate from [exchangerate-api.com](https://www.exchangerate-api.com) |
| `kimchi_GUI.py` | Tkinter dashboard (not working yet, see Known issues) |
| `load_keys.py`, `data_paths.py` | API keys and data file locations |

## Setup

Requires Python 3 and these packages:

```
pip install pandas numpy scipy requests pycurl websocket-client
```

Set the API keys as environment variables:

| Variable | Required | Purpose |
| --- | --- | --- |
| `EXCHANGERATE_API_KEY` | yes | USD/KRW exchange rate |
| `KRAKEN_API_KEY`, `KRAKEN_API_SECRET` | no | Kraken account balance |
| `BITHUMB_API_KEY`, `BITHUMB_API_SECRET` | no | Bithumb account balance |
| `KRAKEN_JK_API_KEY`, `KRAKEN_JK_API_SECRET` | no | Second Kraken account (`K_API(user='JK')`) |

The exchange keys are optional. Without them the bot skips the balance checks and runs on public market data only.

## Running

```
export EXCHANGERATE_API_KEY=...
python3 arbitrage.py
```

The bot runs until you stop it.

## Data files

The bot reads and writes CSV files in a data folder. It chooses the folder in this order:

1. `$KIMCHI_DATA_DIR`, if set
2. the iCloud Drive `Crypto` folder, if it can be read
3. `./data`

Two files live there:

- `New Arb/krw_usd_historical.csv`: every USD/KRW rate the bot fetches gets added as a row. It's used to rebuild the premium history.
- `errors.csv`: errors from the REST clients.

## Known issues

- The simulated trade size in `update_premium` divides the wrong way round (`kraken_best_ask / kraken_usd` should be `kraken_usd / kraken_best_ask`, and the same for KRW).
- The Kraken ticker websocket doesn't reconnect if it drops.
- Data from the websockets is shared between threads without locks.
- The Tkinter dashboard isn't working. `arbitrage(GUI='Yes')` creates the window, but nothing runs its event loop, and `update_gui()` is called from websocket threads, which Tkinter doesn't allow on macOS.
