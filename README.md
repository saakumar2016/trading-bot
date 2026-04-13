# Nifty Trading Bot 🚀

Smart real-time trading bot for NSE Nifty 50 index using technical analysis and Telegram alerts.

## Features

- 📊 **Real-time Market Analysis**: Continuous monitoring with configurable timeframes
- 🎯 **Smart Signal Generation**: Liquidity sweep + fake breakout pattern detection
- 📈 **Trend Detection**: UP, DOWN, SIDEWAYS analysis
- 💰 **Level Calculation**: Dynamic support/resistance based on recent price action
- 📱 **Telegram Alerts**: Instant notifications on trading signals
- 💾 **Trade Persistence**: All trades saved to CSV for analysis
- 📝 **Comprehensive Logging**: Full audit trail of bot operations
- ⚙️ **Configurable Settings**: Environment-based configuration with .env file
- **✨ NEW: Multi-Timeframe Support**: Trade on 1m, 5m, 15m, 1h, or 1d
- **✨ NEW: Backtesting Engine**: Validate strategy on historical data with performance metrics
- **✨ NEW: Risk/Reward Analysis**: Detailed metrics for every signal (R/R ratio, win probability, quality score)

## Strategy Logic

**Trading Pattern**: Liquidity Sweep + Fake Breakout

### BUY Signal
- Trend is UP or SIDEWAYS
- 3rd candle dips below support (-5 buffer)
- 3rd candle closes above support
- Lower wick > 80% of candle body
- Confirmation candle closes up

### SELL Signal
- Trend is DOWN or SIDEWAYS
- 3rd candle spikes above resistance (+5 buffer)
- 3rd candle closes below resistance
- Upper wick > 80% of candle body
- Confirmation candle closes down

## Installation

```bash
# Clone repository
git clone <repo-url>
cd trading-bot

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Configuration

1. **Copy .env template**:
   ```bash
   cp .env.example .env
   ```

2. **Update .env with your settings**:
   ```env
   # Telegram Configuration
   TELEGRAM_TOKEN=your_bot_token_here
   CHAT_ID=your_chat_id_here
   
   # Trading Configuration
   SYMBOL=^NSEI
   TIMEFRAME=1m
   REFRESH_INTERVAL=10
   
   # Logging Configuration
   LOG_LEVEL=INFO
   ```

3. **Get Telegram Bot Token**:
   - Talk to [@BotFather](https://t.me/botfather) on Telegram
   - Create new bot and get the token
   - Message your bot once
   - Get your Chat ID from [@userinfobot](https://t.me/userinfobot)

### Supported Timeframes

| Timeframe | Candle Size | Data Period | Best For |
|-----------|------------|-------------|----------|
| 1m | 1 minute | Last 1 day | Scalping, high frequency |
| 5m | 5 minutes | Last 2 days | Active day trading |
| 15m | 15 minutes | Last 5 days | Day/swing trading |
| 1h | 1 hour | Last 30 days | Swing trading |
| 1d | 1 day | Last 1 year | Position trading |

## Running the Bot

```bash
# Activate virtual environment
source venv/bin/activate

# Start Streamlit app
streamlit run app.py
```

Open browser to: `http://localhost:8501`

### Pages Available

- **🤖 Home (Main Dashboard)** - Real-time trading with current signals and risk/reward analysis
- **📊 Backtest** - Validate strategy on historical data with performance metrics
- **📈 Analysis** - Analyze signals with detailed risk/reward breakdown
- **⚙️ Settings** - Configure parameters and view current settings

## Architecture

```
trading-bot/
├── app.py                    # Main Streamlit dashboard
├── config.py                 # Configuration management (.env based)
├── pages/                    # Streamlit multi-page app
│   ├── 1_Backtest.py        # Backtesting engine
│   ├── 2_Analysis.py        # Signal analysis page
│   └── 3_Settings.py        # Settings configuration
├── core/                     # Trading logic
│   ├── trend.py             # Trend detection
│   ├── strategy.py          # Signal generation
│   └── levels.py            # Support/Resistance calculation
├── services/                # External integrations
│   ├── data_service.py      # yfinance data fetching (multi-timeframe)
│   └── telegram_service.py  # Telegram alerts
├── ui/                      # Streamlit UI components
│   ├── dashboard.py         # Layout and controls
│   └── components.py        # Market & signal panels
├── utils/                   # Utilities
│   ├── helpers.py           # Type conversion utility
│   ├── logger.py            # Logging configuration
│   ├── trade_storage.py     # CSV trade persistence
│   ├── analysis.py          # Risk/reward calculations ✨ NEW
│   ├── backtest.py          # Backtesting engine ✨ NEW
│   └── timeframe.py         # Timeframe management ✨ NEW
├── data/                    # Generated data
│   └── trades.csv           # Trade history
├── logs/                    # Application logs
├── .env.example             # Environment template
└── .gitignore               # Git ignore rules
```

## File Outputs

- **logs/bot.log**: Complete bot operation log
- **data/trades.csv**: All generated trades with timestamps

## Priority 2 Features Implemented

### 🎯 Multi-Timeframe Support
Trade on your preferred timeframe, not just 1-minute candles:
- Configure via `TIMEFRAME` in .env (1m, 5m, 15m, 1h, 1d)
- Each timeframe fetches appropriate historical data
- Fewer signals on higher timeframes = potentially higher quality

### 📊 Backtesting Engine
Validate the strategy on historical data before trading:
- Access via **Backtest** page in the app
- Analyze performance metrics: Win rate, profit factor, average win/loss
- View all generated trades with outcomes
- Download trades as CSV for further analysis
- Test different timeframes and symbols

### 💰 Risk/Reward Analysis
Every signal includes detailed risk/reward metrics:
- **Risk/Reward Ratio**: Expected reward vs actual risk
- **Breakeven Win Rate**: What win % is needed to break even
- **Quality Score**: 0-100 rating based on setup quality
- **Position Rating**: Excellent/Good/Fair/Poor
- View in real-time on main dashboard and **Analysis** page

## Usage Tips

1. **First Run**: Start the bot with a small position size to test
2. **Monitor Logs**: Check `logs/bot.log` for any issues
3. **Backtest First**: Use the Backtest page to validate on historical data
4. **Check Metrics**: Review Risk/Reward Analysis before taking trades
5. **Verify Signals**: Review generated trades in the dashboard
6. **Adjust Parameters**: Modify thresholds if needed based on backtest results
7. **Backup Trades**: Regularly backup `data/trades.csv`

### Backtesting Workflow

1. Go to **Backtest** page
2. Select your preferred symbol and timeframe
3. Click "Run Backtest"
4. Review performance metrics
5. Download trades for further analysis
6. Adjust parameters if needed
7. Run on live market if satisfied with results

## Configuration Parameters

Tune these in respective modules:

**Trend Detection** (`core/trend.py`):
- `MIN_DATA_POINTS`: 20 candles
- `LOOKBACK_CANDLES`: 16 candles
- `THRESHOLD`: ±10 points

**Support/Resistance** (`core/levels.py`):
- `LOOKBACK_PERIODS`: 80 candles
- `SAMPLE_SIZE`: 5 extremes

**Signal Generation** (`core/strategy.py`):
- `SUPPORT_BUFFER`: ±5 points
- `WICK_RATIO`: 0.8 (80% of body)
- `TARGET_MULTIPLIER`: 0.6 (60% of range)
- `SL_BUFFER`: 10 points

## Troubleshooting

**No data available**
- Check internet connection
- Verify `SYMBOL` in .env is correct
- yfinance may be rate-limited (wait 5 minutes)

**Telegram not sending**
- Verify `TELEGRAM_TOKEN` is correct
- Check `CHAT_ID` format
- Ensure bot token is still valid
- Check `logs/bot.log` for errors

**Errors in trading logic**
- Check `logs/bot.log` for detailed error stack trace
- Verify data quality (use market hours)
- Ensure sufficient data points (minimum 80 candles)

## Priority 3 - Future Enhancements

- [ ] Database integration (SQLite)
- [ ] Web dashboard (FastAPI + React)
- [ ] Performance statistics & equity curve
- [ ] Monte Carlo simulation
- [ ] Machine learning signal validation
- [ ] Multi-symbol portfolio management

## Disclaimer

⚠️ **USE AT YOUR OWN RISK**

This bot is provided for educational purposes only. Always test thoroughly before live trading.

## License

MIT License - See LICENSE file for details
