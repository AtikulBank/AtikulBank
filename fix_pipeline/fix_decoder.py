"""
Pure Python FIX 4.4 Decoder for cTrader
Fallback when Cython extensions fail
"""

from enum import Enum
from dataclasses import dataclass
from typing import Optional


class FixMsgType(Enum):
    """FIX Message Types"""
    LOGON = "A"
    LOGOUT = "5"
    HEARTBEAT = "0"
    MARKET_DATA = "W"
    EXECUTION_REPORT = "8"
    REJECT = "3"


@dataclass
class MarketDataTick:
    """Market Data Tick"""
    symbol: str
    bid: float
    ask: float
    timestamp: str


@dataclass
class ExecutionReport:
    """Execution Report"""
    order_id: str
    symbol: str
    side: str
    qty: float
    price: float
    status: str


class FixDecoder:
    """FIX 4.4 Message Decoder - Pure Python implementation"""

    def __init__(self):
        self._last_seq_num = 0

    def decode_message(self, raw: str) -> dict:
        """
        Decode a FIX message string.
        Handles both SOH-delimited and pipe-delimited messages.
        Returns dict with 'type' key.
        """
        # Normalize: replace SOH with pipe if needed
        if "\x01" in raw:
            msg = raw.replace("\x01", "|")
        else:
            msg = raw

        # Remove trailing pipe if present
        if msg.endswith("|"):
            msg = msg[:-1]

        # Parse all tags - store as ordered list for duplicate tag handling
        tags = {}
        tag_list = []  # preserves order including duplicates
        for field in msg.split("|"):
            if "=" in field:
                key, _, value = field.partition("=")
                key = key.strip()
                value = value.strip()
                tags[key] = value
                tag_list.append((key, value))

        msg_type = tags.get("35", "")

        # Update sequence number
        try:
            seq = int(tags.get("34", "0"))
            if seq > self._last_seq_num:
                self._last_seq_num = seq
        except ValueError:
            pass

        # Handle different message types
        if msg_type == FixMsgType.LOGON.value:
            return {"type": "logon", "tags": tags}

        elif msg_type == FixMsgType.LOGOUT.value:
            return {
                "type": "logout",
                "text": tags.get("58", ""),
                "tags": tags
            }

        elif msg_type == FixMsgType.HEARTBEAT.value:
            return {"type": "heartbeat", "tags": tags}

        elif msg_type == "1":  # TestRequest
            return {"type": "test_request", "tags": tags}

        elif msg_type == FixMsgType.REJECT.value:
            return {
                "type": "reject",
                "text": tags.get("58", ""),
                "tags": tags
            }

        elif msg_type == FixMsgType.MARKET_DATA.value:
            return self._parse_market_data(tags, tag_list)

        elif msg_type == FixMsgType.EXECUTION_REPORT.value:
            return self._parse_execution_report(tags)

        else:
            return {"type": "unknown", "msg_type": msg_type, "tags": tags}

    def _parse_market_data(self, tags: dict, tag_list: list) -> dict:
        """Parse Market Data Snapshot (MsgType=W)"""
        symbol = tags.get("55", "")
        bid = 0.0
        ask = 0.0

        # Walk tag_list in order to find 269/270 pairs
        for i, (key, val) in enumerate(tag_list):
            if key == "269" and i + 1 < len(tag_list):
                next_key, next_val = tag_list[i + 1]
                if next_key == "270":
                    try:
                        price = float(next_val)
                    except ValueError:
                        price = 0.0
                    if val == "0":
                        bid = price
                    elif val == "1":
                        ask = price

        timestamp = tags.get("52", "")

        return {
            "type": "market_data",
            "symbol": symbol,
            "bid": bid,
            "ask": ask,
            "timestamp": timestamp,
            "tags": tags
        }

    def _parse_execution_report(self, tags: dict) -> dict:
        """Parse Execution Report (MsgType=8)"""
        order_id = tags.get("17", tags.get("11", ""))
        symbol = tags.get("55", "")
        side = tags.get("54", "")
        try:
            qty = float(tags.get("38", "0"))
        except ValueError:
            qty = 0.0
        try:
            price = float(tags.get("44", "0"))
        except ValueError:
            price = 0.0

        # Map ord status code to text
        status_map = {
            "0": "New",
            "1": "Partially Filled",
            "2": "Filled",
            "4": "Cancelled",
            "8": "Rejected"
        }
        raw_status = tags.get("39", "")
        status = status_map.get(raw_status, raw_status)

        return {
            "type": "execution_report",
            "order_id": order_id,
            "symbol": symbol,
            "side": side,
            "qty": qty,
            "price": price,
            "status": status,
            "tags": tags
        }

    def create_market_data_request(self, symbol: str, sender: str,
                                    target: str, sub_id: str,
                                    request_id: str) -> str:
        """
        Create Market Data Request (MsgType=V) as pipe-delimited string.
        symbol: numeric FIX symbol ID (e.g., "14" for XAUUSD on IC Markets)
        """
        self._last_seq_num += 1
        body = f"35=V|"
        body += f"49={sender}|"
        body += f"56={target}|"
        body += f"34={self._last_seq_num}|"
        body += f"52={self._current_timestamp()}|"
        body += f"50={sub_id}|"
        body += f"262={request_id}|"
        body += f"263=1|"
        body += f"264=1|"
        body += f"267=2|"
        body += f"269=0|269=1|"
        body += f"146=1|"
        body += f"55={symbol}|"

        # Build complete message with BodyLength and Checksum
        body_wire = body.replace("|", "\x01")
        body_length = len(body_wire)
        msg = f"8=FIX.4.4|9={body_length}|{body}"
        wire = msg.replace("|", "\x01")
        checksum = sum(wire.encode("latin-1")) % 256
        msg += f"10={checksum:03d}|"
        return msg

    def _current_timestamp(self) -> str:
        """Generate FIX timestamp"""
        from datetime import datetime, timezone
        now = datetime.now(timezone.utc)
        return now.strftime("%Y%m%d-%H:%M:%S.") + f"{now.microsecond // 1000:03d}"
