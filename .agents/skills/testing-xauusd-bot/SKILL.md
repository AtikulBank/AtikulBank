---
name: testing-xauusd-bot
description: Test the XAUUSD GOD BOT trading system. Use when verifying bot initialization, backtest execution, model ensemble, risk management, or any of the 24 subsections.
---

# Testing XAUUSD GOD BOT

## Overview
`xauusd_god_bot.py` is a single-file Python CLI app with a Rich TUI dashboard. All testing is shell-based — no browser or GUI recording needed.

## Prerequisites
- Python 3.10+
- No credentials needed for demo/backtest mode
- Dependencies auto-install on first import (numpy, pandas, torch, xgboost, lightgbm, catboost, rich, etc.) — first run may take 1-2 minutes

## How to Run

### Quick syntax check
```bash
python -m py_compile xauusd_god_bot.py
```

### Import test
The module prints a banner and runs `auto_install_packages()` on import. Suppress stdout if testing programmatically:
```python
import sys, io
old_stdout = sys.stdout
sys.stdout = io.StringIO()
from xauusd_god_bot import *
sys.stdout = old_stdout
```

### Backtest mode
The startup wizard reads from stdin. Pipe "backtest" to run non-interactively:
```bash
echo "backtest" | timeout 120 python xauusd_god_bot.py
```
Note: output may go to `logs/xauusd_bot.log` rather than stdout.

### Programmatic testing (recommended)
Import the module and test subsystems directly:
```python
config = BotConfig(mode="backtest")
config.ensure_dirs()
fetcher = DataFetcher(config)
df = fetcher.fetch_historical("1h", 5)  # ~13k bars synthetic data
feat_eng = FeatureEngineer(config)
features = feat_eng.generate_all_features(df)  # 120+ features
ensemble = EnsembleOrchestrator(config)  # 29 models + 5 RL agents
```

## Key Test Areas

### Ensemble weight adaptation
- `EnsembleOrchestrator.update_weights(model_name, correct)` only accepts model names from `self.weights.keys()`
- Passing arbitrary strings (e.g., trade IDs) is a silent no-op — verify weights actually change

### Risk management
- `RiskManager.check_limits()` daily drawdown check only triggers on negative `daily_pnl`
- Positive P&L should never block trading regardless of magnitude

### Config persistence
- `BotConfig.to_yaml()` saves credentials in plaintext (not redacted)
- Verify round-trip: `to_yaml()` → `from_yaml()` preserves `telegram_token` and `mt5_password`

### Data cleaning
- `DataFetcher._clean()` uses `pct_change().abs().fillna(0)` to preserve the first row
- Verify row count is unchanged after cleaning valid data

### Label generation
- Both `initialize()` and `_retrain()` must use `np.diff(c, prepend=c[0])` for consistent labels
- First label should be 2 (HOLD), not 0 (BUY)

## Devin Secrets Needed
None for demo/backtest testing. Live trading would require MT5 credentials and optionally Telegram bot token.
