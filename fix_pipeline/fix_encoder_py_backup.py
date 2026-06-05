"""
Pure Python FIX 4.4 Message Encoder
Fallback when Cython extensions fail
"""

import time
from datetime import datetime, timezone


class FixEncoder:
    """FIX 4.4 Message Encoder - Pure Python implementation"""
    
    def __init__(self, sender_comp_id: str, target_comp_id: str,
                 sender_sub_id: str, heartbeat_interval: int = 30):
        self._sender_comp_id = sender_comp_id
        self._target_comp_id = target_comp_id
        self._sender_sub_id = sender_sub_id
        self._sequence_number = 0
        self._heartbeat_interval = heartbeat_interval
    
    def _timestamp(self) -> str:
        """Generate FIX timestamp: YYYYMMDD-HH:MM:SS.sss"""
        now = datetime.now(timezone.utc)
        return now.strftime("%Y%m%d-%H:%M:%S.") + f"{now.microsecond // 1000:03d}"
    
    def _add_body_length(self, msg: str) -> str:
        """Calculate and insert body length"""
        # Remove the temporary 9=0| placeholder
        msg = msg.replace("9=0|", "", 1)
        
        # Find where the body starts (after header 8=FIX.4.4|)
        header = "8=FIX.4.4|"
        body = msg[len(header):]
        
        # Body length = from tag 35 to just before tag 10
        # Including the delimiter before tag 10
        body_without_trailing = body.rstrip("|")
        body_length = len(body_without_trailing) + 1
        
        # Replace the body length placeholder
        msg = f"8=FIX.4.4|9={body_length}|{body}"
        return msg
    
    def _add_checksum(self, msg: str) -> str:
        """Calculate and append checksum"""
        # FIX Checksum: sum of all bytes from tag 8 through 10=000\x01
        wire_msg = msg.replace("|", "\x01")
        wire_msg += "10=000\x01"  # Add placeholder for checksum calculation
        checksum = sum(wire_msg.encode('ascii')) % 256
        msg = f"{msg}10={checksum:03d}|"
        return msg
    
    def create_logon(self, password: str, reset: bool = True) -> str:
        """Create FIX Logon message (MsgType=A) for cTrader"""
        self._sequence_number += 1
        # Extract numeric username from SenderCompID
        username = self._sender_comp_id.split(".")[-1] if "." in self._sender_comp_id else self._sender_comp_id
        
        # Match exact order from official cTrader sample
        msg = f"8=FIX.4.4|9=0|35=A|"
        msg += f"49={self._sender_comp_id}|"  # SenderCompID
        msg += f"56=CSERVER|"  # TargetCompID (cTrader requires uppercase)
        msg += f"34={self._sequence_number}|"  # MsgSeqNum
        msg += f"52={self._timestamp()}|"  # SendingTime
        msg += f"57=TRADE|"  # TargetSubID
        msg += f"50={self._sender_sub_id}|"  # SenderSubID
        msg += f"98=0|"  # EncryptMethod
        msg += f"108={self._heartbeat_interval}|"  # HeartBtInt
        if reset:
            msg += "141=Y|"  # ResetSeqNumFlag
        msg += f"553={username}|"  # Username
        msg += f"554={password}|"  # Password
        msg = self._add_body_length(msg)
        msg = self._add_checksum(msg)
        return msg
    
    def create_heartbeat(self, test_request_id: str = None) -> str:
        """Create FIX Heartbeat message"""
        self._sequence_number += 1
        msg = f"8=FIX.4.4|9=0|35=0|34={self._sequence_number}|"
        msg += f"49={self._sender_comp_id}|56={self._target_comp_id}|"
        if self._sender_sub_id:
            msg += f"50={self._sender_sub_id}|"
        msg += f"52={self._timestamp()}|"
        if test_request_id:
            msg += f"112={test_request_id}|"
        msg = self._add_body_length(msg)
        msg = self._add_checksum(msg)
        return msg
    
    def create_market_data_request(self, symbol_id: str, md_request_id: str,
                                     subscription_type: int = 1,
                                     market_depth: int = 1) -> str:
        """Create Market Data Request (MsgType=V)"""
        self._sequence_number += 1
        msg = f"8=FIX.4.4|9=0|35=V|34={self._sequence_number}|"
        msg += f"49={self._sender_comp_id}|56={self._target_comp_id}|"
        if self._sender_sub_id:
            msg += f"50={self._sender_sub_id}|"
        msg += f"52={self._timestamp()}|"
        msg += f"262={md_request_id}|"
        msg += f"263={subscription_type}|"  # 1=Subscribe, 2=Unsubscribe
        msg += f"264={market_depth}|"  # 0=Full, 1=Top of book
        msg += f"267=2|"  # Number of MDEntryTypes
        msg += f"269=0|269=1|"  # Bid, Offer
        msg += f"146=1|"  # Number of symbols
        msg += f"55={symbol_id}|"
        msg = self._add_body_length(msg)
        msg = self._add_checksum(msg)
        return msg
    
    def create_order_single(self, symbol_id: str, client_order_id: str,
                             side: int, order_qty: float, price: float,
                             order_type: int = 2) -> str:
        """Create New Order Single (MsgType=D)"""
        self._sequence_number += 1
        msg = f"8=FIX.4.4|9=0|35=D|34={self._sequence_number}|"
        msg += f"49={self._sender_comp_id}|56={self._target_comp_id}|"
        if self._sender_sub_id:
            msg += f"50={self._sender_sub_id}|"
        msg += f"52={self._timestamp()}|"
        msg += f"11={client_order_id}|"
        msg += f"55={symbol_id}|"
        msg += f"54={side}|"  # 1=Buy, 2=Sell
        msg += f"60={self._timestamp()}|"
        msg += f"40={order_type}|"  # 2=Limit, 1=Market
        msg += f"38={order_qty:.2f}|"
        msg += f"44={price:.5f}|"
        msg += f"59=0|"  # TimeInForce=Day
        msg = self._add_body_length(msg)
        msg = self._add_checksum(msg)
        return msg
    
    def create_order_cancel(self, symbol_id: str, client_order_id: str,
                             orig_client_order_id: str, side: int) -> str:
        """Create Order Cancel Request (MsgType=F)"""
        self._sequence_number += 1
        msg = f"8=FIX.4.4|9=0|35=F|34={self._sequence_number}|"
        msg += f"49={self._sender_comp_id}|56={self._target_comp_id}|"
        if self._sender_sub_id:
            msg += f"50={self._sender_sub_id}|"
        msg += f"52={self._timestamp()}|"
        msg += f"11={client_order_id}|"
        msg += f"41={orig_client_order_id}|"
        msg += f"55={symbol_id}|"
        msg += f"54={side}|"
        msg = self._add_body_length(msg)
        msg = self._add_checksum(msg)
        return msg
    
    def create_logout(self, reason: str = "") -> str:
        """Create Logout message"""
        self._sequence_number += 1
        msg = f"8=FIX.4.4|9=0|35=5|34={self._sequence_number}|"
        msg += f"49={self._sender_comp_id}|56={self._target_comp_id}|"
        if self._sender_sub_id:
            msg += f"50={self._sender_sub_id}|"
        msg += f"52={self._timestamp()}|"
        if reason:
            msg += f"58={reason}|"
        msg = self._add_body_length(msg)
        msg = self._add_checksum(msg)
        return msg
    
    # Alias for compatibility with live_gate.py
    def create_new_order(self, cl_ord_id: str, symbol: str, side: str, 
                         quantity: float, price: float) -> str:
        """Create New Order Single (MsgType=D) - alias for create_order_single"""
        side_int = 1 if side == "1" else 2
        return self.create_order_single(
            symbol_id=symbol,
            client_order_id=cl_ord_id,
            side=side_int,
            order_qty=quantity,
            price=price,
            order_type=2  # Limit order
        )
    
    @property
    def sequence_number(self) -> int:
        return self._sequence_number
    
    @sequence_number.setter
    def sequence_number(self, value: int):
        self._sequence_number = value
