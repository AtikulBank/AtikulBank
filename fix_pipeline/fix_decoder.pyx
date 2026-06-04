# cython: language_level=3, boundscheck=False, wraparound=False
"""
FIX Message Decoder - Parse incoming FIX 4.4 messages from cTrader
Decodes MarketData, ExecutionReport, and other response messages
"""

from dataclasses import dataclass
from typing import Dict, Optional, List
from enum import Enum
from datetime import datetime, timezone


class FixMsgType(Enum):
    """FIX Message Types"""
    HEARTBEAT = "0"
    TEST_REQUEST = "1"
    RESEND_REQUEST = "2"
    REJECT = "3"
    SEQUENCE_RESET = "4"
    LOGOUT = "5"
    LOGON = "A"
    MARKET_DATA_REQUEST = "V"
    MARKET_DATA_SNAPSHOT = "W"
    MARKET_DATA_INCREMENTAL = "X"
    MARKET_DATA_REQUEST_REJECT = "Y"
    EXECUTION_REPORT = "8"
    ORDER_CANCEL_REJECT = "9"
    BUSINESS_MESSAGE_REJECT = "j"


@dataclass
class MarketDataTick:
    """Parsed market data tick from FIX stream"""
    symbol: str = ""
    bid_price: float = 0.0
    ask_price: float = 0.0
    bid_size: float = 0.0
    ask_size: float = 0.0
    timestamp: str = ""
    msg_seq_num: int = 0


@dataclass
class ExecutionReport:
    """Parsed execution report from FIX stream"""
    order_id: str = ""
    cl_ord_id: str = ""
    exec_id: str = ""
    exec_type: str = ""
    ord_status: str = ""
    symbol: str = ""
    side: str = ""
    order_qty: float = 0.0
    price: float = 0.0
    leaves_qty: float = 0.0
    cum_qty: float = 0.0
    avg_px: float = 0.0
    timestamp: str = ""


class FixDecoder:
    """
    FIX 4.4 Message Decoder
    Parses incoming FIX messages from cTrader into structured data
    """

    def __init__(self):
        self._buffer = ""
        self._sequence_number = 0

    def decode_message(self, raw_message: str):
        """Decode a raw FIX message string"""
        msg = raw_message.replace("\\x01", "|").replace("\x01", "|")

        # Parse tags preserving order for repeating groups
        tag_list = []
        for tag_pair in msg.split("|"):
            if "=" in tag_pair:
                tag_num, tag_val = tag_pair.split("=", 1)
                tag_list.append((tag_num, tag_val))

        # Also build a dict for quick lookup of single-value tags
        tags = dict(tag_list)

        msg_type = tags.get("35", "")

        if msg_type == FixMsgType.MARKET_DATA_SNAPSHOT.value:
            return self._parse_market_data_snapshot(tags, tag_list)
        elif msg_type == FixMsgType.MARKET_DATA_INCREMENTAL.value:
            return self._parse_market_data_incremental(tags, tag_list)
        elif msg_type == FixMsgType.EXECUTION_REPORT.value:
            return self._parse_execution_report(tags)
        elif msg_type == FixMsgType.LOGON.value:
            return self._parse_logon(tags)
        elif msg_type == FixMsgType.HEARTBEAT.value:
            return {"type": "heartbeat", "tags": tags}
        elif msg_type == FixMsgType.LOGOUT.value:
            return {"type": "logout", "tags": tags}
        elif msg_type == FixMsgType.REJECT.value:
            return {"type": "reject", "tags": tags, "text": tags.get("58", "")}
        else:
            return {"type": "unknown", "msg_type": msg_type, "tags": tags}

    def _parse_market_data_snapshot(self, tags: dict, tag_list: list):
        """Parse MarketDataSnapshot (MsgType=W) - tag 270=MdEntryPx, tag 271=MdEntrySize"""
        tick = MarketDataTick()
        tick.symbol = tags.get("55", "")
        tick.timestamp = tags.get("52", "")
        tick.msg_seq_num = int(tags.get("34", "0"))

        num_entries = int(tags.get("268", "0"))

        # FIX repeating groups: tags appear sequentially in the tag_list
        # e.g., [("268","2"), ("269","0"), ("270","4472.50"), ("271","1.5"),
        #         ("269","1"), ("270","4472.97"), ("271","2.0")]
        # Find the position of tag 268 (NoMDEntries) and parse from there

        start_idx = 0
        for i, (tag_num, tag_val) in enumerate(tag_list):
            if tag_num == "268":
                start_idx = i + 1
                break

        # Parse entries sequentially from the tag_list
        current_entry = {"type": None, "price": 0.0, "size": 0.0}
        entries = []

        for i in range(start_idx, len(tag_list)):
            tag_num, tag_val = tag_list[i]

            # Stop if we hit a non-market-data tag (like checksum 10)
            if tag_num not in ("269", "270", "271", "280", "279"):
                if current_entry["type"] is not None:
                    entries.append(current_entry.copy())
                break

            if tag_num == "269":
                # Save previous entry if we have one
                if current_entry["type"] is not None:
                    entries.append(current_entry.copy())
                # Start new entry
                current_entry = {"type": tag_val, "price": 0.0, "size": 0.0}
            elif tag_num == "270":
                current_entry["price"] = float(tag_val) if tag_val else 0.0
            elif tag_num == "271":
                current_entry["size"] = float(tag_val) if tag_val else 0.0

        # Don't forget the last entry
        if current_entry["type"] is not None:
            entries.append(current_entry)

        # Process the parsed entries
        for entry in entries:
            if entry["type"] == "0":  # Bid
                tick.bid_price = entry["price"]
                tick.bid_size = entry["size"]
            elif entry["type"] in ("1", "2"):  # Offer/Ask or Trade
                tick.ask_price = entry["price"]
                tick.ask_size = entry["size"]

        # Fallback: direct tag 270/271
        if tick.bid_price == 0.0 and tick.ask_price == 0.0:
            if "270" in tags:
                tick.bid_price = float(tags["270"])
            if "271" in tags:
                tick.ask_price = float(tags["271"])

        return {"type": "market_data_snapshot", "tick": tick}

    def _parse_market_data_incremental(self, tags: dict, tag_list: list):
        """Parse MarketDataIncrementalRefresh (MsgType=X)"""
        tick = MarketDataTick()
        tick.symbol = tags.get("55", "")
        tick.timestamp = tags.get("52", "")
        tick.msg_seq_num = int(tags.get("34", "0"))

        num_entries = int(tags.get("268", "0"))

        # Find the position of tag 268 and parse from there
        start_idx = 0
        for i, (tag_num, tag_val) in enumerate(tag_list):
            if tag_num == "268":
                start_idx = i + 1
                break

        # Parse entries sequentially
        current_entry = {"type": None, "price": 0.0, "size": 0.0}
        entries = []

        for i in range(start_idx, len(tag_list)):
            tag_num, tag_val = tag_list[i]

            if tag_num not in ("269", "270", "271", "279", "280"):
                if current_entry["type"] is not None:
                    entries.append(current_entry.copy())
                break

            if tag_num == "269":
                if current_entry["type"] is not None:
                    entries.append(current_entry.copy())
                current_entry = {"type": tag_val, "price": 0.0, "size": 0.0}
            elif tag_num == "270":
                current_entry["price"] = float(tag_val) if tag_val else 0.0
            elif tag_num == "271":
                current_entry["size"] = float(tag_val) if tag_val else 0.0

        if current_entry["type"] is not None:
            entries.append(current_entry)

        for entry in entries:
            if entry["type"] == "0":
                tick.bid_price = entry["price"]
                tick.bid_size = entry["size"]
            elif entry["type"] in ("1", "2"):
                tick.ask_price = entry["price"]
                tick.ask_size = entry["size"]

        return {"type": "market_data_incremental", "tick": tick}

    def _parse_execution_report(self, tags: dict):
        """Parse ExecutionReport (MsgType=8)"""
        report = ExecutionReport()
        report.order_id = tags.get("37", "")
        report.cl_ord_id = tags.get("11", "")
        report.exec_id = tags.get("17", "")
        report.exec_type = tags.get("150", "")
        report.ord_status = tags.get("39", "")
        report.symbol = tags.get("55", "")
        report.side = tags.get("54", "")

        try:
            report.order_qty = float(tags.get("38", "0"))
            report.price = float(tags.get("44", "0"))
            report.leaves_qty = float(tags.get("151", "0"))
            report.cum_qty = float(tags.get("14", "0"))
            report.avg_px = float(tags.get("6", "0"))
        except ValueError:
            pass

        report.timestamp = tags.get("52", "")
        return {"type": "execution_report", "report": report}

    def _parse_logon(self, tags: dict):
        """Parse Logon message"""
        return {
            "type": "logon",
            "encrypt_method": tags.get("98", ""),
            "heartbeat_interval": int(tags.get("108", "0")),
            "tags": tags
        }

    def create_market_data_request(self, symbol: str, sender: str, target: str,
                                    sub_id: str = "", request_id: str = "MD_REQ_1"):
        """Create MarketDataRequest (MsgType=V) to subscribe to live prices"""
        self._sequence_number += 1
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H:%M:%S.%f")[:-3]

        msg = f"8=FIX.4.4|9=0|35=V|34={self._sequence_number}|"
        msg += f"49={sender}|56={target}|"
        if sub_id:
            msg += f"50={sub_id}|"
        msg += f"52={timestamp}|"
        msg += f"262={request_id}|"
        msg += f"263=1|"
        msg += f"264=1|"
        msg += f"265=0|"
        msg += f"266=Y|"
        msg += f"146=1|"
        msg += f"55={symbol}|"
        msg += f"267=2|"
        msg += f"269=0|269=1|"

        msg = self._add_body_length(msg)
        msg = self._add_checksum(msg)
        return msg

    def _add_body_length(self, msg):
        msg = msg.replace("9=0|", "", 1)
        header = "8=FIX.4.4|"
        body = msg[len(header):]
        body_length = len(body)
        msg = f"8=FIX.4.4|9={body_length}|{body}"
        return msg

    def _add_checksum(self, msg):
        checksum = 0
        for c in msg.encode('ascii'):
            checksum += c
        checksum = checksum % 256
        msg = f"{msg}10={checksum:03d}|"
        return msg
