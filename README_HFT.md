# cTrader HFT Engine

Ultra-Low-Latency Cython-based FIX API implementation for cTrader.

## Features

- **Ultra-Low Latency**: Pure Cython implementation with static type binding
- **TCP_NODELAY**: Optimized for minimal network latency
- **FIX 4.4 Protocol**: Full support for FIX 4.4 messages
- **SSL/TLS Security**: Encrypted connections to cTrader
- **Zero-Copy Optimization**: Memory-efficient buffer management

## Architecture

```
ctrader_hft_engine/
├── __init__.py
├── config/
│   └── __init__.py          # Environment configuration
├── core/
│   ├── __init__.py
│   ├── network/
│   │   ├── __init__.py
│   │   └── hft_socket.pyx   # Ultra-fast TCP socket
│   └── fix/
│       ├── __init__.py
│       ├── fix_encoder.pyx   # FIX message encoder
│       └── fix_decoder.pyx   # FIX message decoder
└── utils/
    └── __init__.py
```

## Installation

### Prerequisites

- Python 3.8+
- Cython 0.29+
- NumPy 1.21+

### Build Cython Extensions

```bash
# Install dependencies
pip install numpy cython

# Build extensions
python setup.py build_ext --inplace
```

## Configuration

### Environment Variables

Create a `.env` file with your cTrader FIX credentials:

```bash
FIX_HOST=live-uk-eqx-01.p.c-trader.com
FIX_PORT=5212
SENDER_COMP_ID=your_sender_comp_id
TARGET_COMP_ID=cServer
SENDER_SUB_ID=TRADE
FIX_PASSWORD=your_fix_password
```

**⚠️ SECURITY WARNING**: Never commit your `.env` file to version control!

### Load Configuration

```python
from ctrader_hft_engine.config import get_fix_config

config = get_fix_config()
print(f"Connecting to {config.FIX_HOST}:{config.FIX_PORT}")
```

## Usage

### Basic Connection

```python
from ctrader_hft_engine.core.network.hft_socket import HFTSocket
from ctrader_hft_engine.core.fix.fix_encoder import FIXEncoder

# Create encoder
encoder = FIXEncoder(
    sender_comp_id="your_sender",
    target_comp_id="cServer",
    sender_sub_id="TRADE"
)

# Create socket
socket = HFTSocket(
    host="live-uk-eqx-01.p.c-trader.com",
    port=5212,
    use_ssl=True
)

# Connect and send logon
socket.connect()
logon_msg = encoder.create_logon_message("your_password")
socket.send_fix_message(logon_msg)
```

### Create Orders

```python
# New Order Single
order_msg = encoder.create_new_order_single(
    cl_ord_id="ORDER001",
    symbol="XAUUSD",
    side="BUY",
    quantity=0.1,
    price=2413.50
)

# Cancel Order
cancel_msg = encoder.create_order_cancel_request(
    cl_ord_id="CANCEL001",
    orig_cl_ord_id="ORDER001",
    symbol="XAUUSD",
    side="BUY",
    quantity=0.1
)
```

### Parse Messages

```python
from ctrader_hft_engine.core.fix.fix_decoder import FIXDecoder

decoder = FIXDecoder()

# Parse received message
parsed = decoder.parse_message(raw_fix_message)
if parsed:
    print(f"Message Type: {parsed.get('MsgType')}")
    print(f"Order ID: {parsed.get('OrderID')}")
```

## Performance Optimization

### Cython Compiler Directives

The following optimizations are enabled:

- `boundscheck=False`: Disable array bounds checking
- `wraparound=False`: Disable negative index wrapping
- `cdivision=True`: Use C-style division
- `nonecheck=False`: Disable None checking
- `overflowcheck=False`: Disable integer overflow checking

### Compilation Flags

```
-O3                    # Maximum optimization
-march=native          # Optimize for current CPU
-mtune=native          # Tune for current CPU
```

## FIX Protocol Support

### Message Types

- **A**: Logon
- **0**: Heartbeat
- **D**: New Order Single
- **F**: Order Cancel Request
- **V**: Market Data Request
- **8**: Execution Report
- **W**: Market Data Snapshot

## Security

### Credential Management

- Use environment variables for credentials
- Never hardcode credentials in source code
- Use `.env` files for local development
- Use secrets managers for production

### Network Security

- SSL/TLS encryption enabled by default
- Certificate verification can be configured
- TCP_NODELAY for low latency

## Development

### Build from Source

```bash
git clone https://github.com/your-repo/ctrader-hft-engine.git
cd ctrader-hft-engine
pip install -e .
python setup.py build_ext --inplace
```

### Run Tests

```bash
python -m pytest tests/
```

## License

This project is proprietary software. All rights reserved.

## Disclaimer

This software is provided for educational purposes only. Trading involves significant risk of financial loss. The authors are not responsible for any losses incurred from using this software.