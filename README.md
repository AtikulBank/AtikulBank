# cTrader FIX 4.4 High-Frequency Trading Engine

Ultra-low-latency trading engine for cTrader FIX API using pure Cython and raw C-sockets.

## Architecture

```
ctrader_fix_engine/
├── config/          # Configuration loader
├── network/         # Raw C-socket implementation (Cython)
├── protocol/        # FIX 4.4 encoder/decoder (Cython)
├── engine/          # FIX session manager
├── utils/           # Helper functions
└── main.py          # Entry point
```

## Features

- **Pure Cython**: All critical paths compiled to C for maximum performance
- **Raw C-Sockets**: Bypasses Python's socket overhead
- **FIX 4.4 Protocol**: Full implementation of FIX 4.4 messaging
- **Secure Configuration**: Credentials loaded from `.env` files
- **Zero Hardcoded Secrets**: All sensitive data externalized

## Requirements

- Python 3.8+
- Cython
- GCC or compatible C compiler

## Installation

```bash
# Install dependencies
pip install cython setuptools

# Build Cython extensions
python setup.py build_ext --inplace
```

## Configuration

Create a `.env` file in the project root:

```env
FIX_HOST=live.ctrader.com
FIX_PORT=5222
SENDER_COMP_ID=YOUR_SENDER_ID
TARGET_COMP_ID=cServer
SENDER_SUB_ID=TRADE
FIX_PASSWORD=YOUR_PASSWORD
```

## Usage

```python
from ctrader_fix_engine.config import load_config
from ctrader_fix_engine.engine import FixSession

# Load configuration
config = load_config()

# Create session
session = FixSession(config)

# Connect and logon
session.connect()
session.logon(config.password)

# Send order
session.send_new_order(
    cl_ord_id="ORD-001",
    symbol="XAUUSD",
    side="1",  # Buy
    quantity=1.0,
    price=2350.50
)
```

## Security

- **Never commit `.env` files** to version control
- Use environment variables in production
- Rotate credentials regularly
- Monitor connection logs

## Performance

- Cython compilation with `-O3` optimization
- Native CPU architecture tuning
- Minimal memory allocation in hot paths
- TCP_NODELAY for minimal latency

## License

MIT License