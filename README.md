# XAUUSD GOD BOT

Autonomous AI Trading System for XAUUSD (Gold) trading with 28 ML models, 5 RL agents, and 800+ features.

## Features

- **28 ML Models**: LSTM, Transformer, XGBoost, LightGBM, CatBoost, and more
- **5 RL Trading Agents**: PPO, SAC, TD3, A3C, Dreamer V3
- **800+ Features**: Price action, technical indicators, macro, sentiment
- **12 Panel TUI Dashboard**: Real-time monitoring with Rich library
- **Self-Learning**: Online learning with River, drift detection
- **Self-Evolution**: DARTS, genetic algorithms, AutoML
- **Signal Scoring**: 0-1000 points system

## Quick Start

```bash
# Install dependencies (auto-installed on first run)
pip install -r requirements.txt

# Run in demo mode (paper trading)
python xauusd_god_bot.py

# Run backtest
python xauusd_god_bot.py --mode backtest

# Live trading (requires MetaTrader 5)
python xauusd_god_bot.py --mode live
```

## Requirements

- Python 3.9+
- numpy, pandas, scipy
- pytorch >= 2.0
- xgboost, lightgbm, catboost
- rich >= 13.0
- See `REQUIRED_PACKAGES` in code for full list

## Project Structure

```
xauusd_god_bot.py     # Main bot file (all-in-one)
├── ML Models (28 total)
├── RL Agents (5 total)
├── Feature Engineering (800+ features)
├── Risk Management
├── TUI Dashboard (12 panels)
└── Self-Learning System
```

## ⚠️ Disclaimer

This software is for **educational purposes only**. Trading financial instruments involves **substantial risk of loss**. Past performance does not guarantee future results. Use at your own risk.

## License

MIT License
