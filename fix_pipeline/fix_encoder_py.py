"""
Pure Python FIX 4.4 Message Encoder
Fallback when Cython extensions fail
"""

from datetime import datetime, timezone


class FixEncoder:
    """FIX 4.4 Message Encoder - Pure Python implementation"""

    def __init__(self, sender_comp_id: str, target_comp_id: str,
                 sender_sub_id: str, target_sub_id: str = "TRADE",
                 heartbeat_interval: int = 30):
        self._sender_comp_id = sender_comp_id
        self._target_comp_id = target_comp_id.upper()
        self._sender_sub_id = sender_sub_id
        self._target_sub_id = target_sub_id
        self._sequence_number = 0
        self._heartbeat_interval = heartbeat_interval

    def _timestamp(self) -> str:
        """Generate FIX timestamp: YYYYMMDD-HH:MM:SS.sss"""
        now = datetime.now(timezone.utc)
        return now.strftime("%Y%m%d-%H:%M:%S.") + f"{now.microsecond // 1000:03d}"

    def _build_message(self, body_fields: str) -> str:
        """Build complete FIX message with correct BodyLength and Checksum.

        body_fields: pipe-delimited tags from 35= through the last tag,
                     ending with a trailing ``|``.
        """
        body_wire = body_fields.replace("|", "\x01")
        body_length = len(body_wire)
        msg = f"8=FIX.4.4|9={body_length}|{body_fields}"
        wire = msg.replace("|", "\x01")
        checksum = sum(wire.encode('latin-1')) % 256
        msg += f"10={checksum:03d}|"
        return msg

    def to_wire(self, msg: str) -> bytes:
        """Convert pipe-delimited FIX message to SOH wire format."""
        wire = msg.replace("|", "\x01")
        return wire.encode('latin-1')

    def create_logon(self, password: str, reset: bool = True) -> str:
        """Create FIX Logon message (MsgType=A) for cTrader"""
        self._sequence_number += 1
        username = self._sender_comp_id.split(".")[-1] if "." in self._sender_comp_id else self._sender_comp_id

        body = f"35=A|"
        body += f"49={self._sender_comp_id}|"
        body += f"56={self._target_comp_id}|"
        body += f"34={self._sequence_number}|"
        body += f"52={self._timestamp()}|"
        body += f"57={self._target_sub_id}|"
        body += f"50={self._sender_sub_id}|"
        body += f"98=0|"
        body += f"108={self._heartbeat_interval}|"
        if reset:
            body += "141=Y|"
        body += f"553={username}|"
        body += f"554={password}|"
        return self._build_message(body)

    def create_heartbeat(self, test_request_id: str = None) -> str:
        """Create FIX Heartbeat message"""
        self._sequence_number += 1
        body = f"35=0|"
        body += f"49={self._sender_comp_id}|"
        body += f"56={self._target_comp_id}|"
        if self._sender_sub_id:
            body += f"50={self._sender_sub_id}|"
        body += f"52={self._timestamp()}|"
        if test_request_id:
            body += f"112={test_request_id}|"
        return self._build_message(body)

    def create_market_data_request(self, symbol_id: str, md_request_id: str,
                                     subscription_type: int = 1,
                                     market_depth: int = 1) -> str:
        """Create Market Data Request (MsgType=V)"""
        self._sequence_number += 1
        body = f"35=V|"
        body += f"49={self._sender_comp_id}|"
        body += f"56={self._target_comp_id}|"
        if self._sender_sub_id:
            body += f"50={self._sender_sub_id}|"
        body += f"52={self._timestamp()}|"
        body += f"262={md_request_id}|"
        body += f"263={subscription_type}|"
        body += f"264={market_depth}|"
        body += f"267=2|"
        body += f"269=0|269=1|"
        body += f"146=1|"
        body += f"55={symbol_id}|"
        return self._build_message(body)

    def create_order_single(self, symbol_id: str, client_order_id: str,
                             side: int, order_qty: float, price: float,
                             order_type: int = 2) -> str:
        """Create New Order Single (MsgType=D)"""
        self._sequence_number += 1
        body = f"35=D|"
        body += f"49={self._sender_comp_id}|"
        body += f"56={self._target_comp_id}|"
        if self._sender_sub_id:
            body += f"50={self._sender_sub_id}|"
        body += f"52={self._timestamp()}|"
        body += f"11={client_order_id}|"
        body += f"55={symbol_id}|"
        body += f"54={side}|"
        body += f"60={self._timestamp()}|"
        body += f"40={order_type}|"
        body += f"38={order_qty:.2f}|"
        body += f"44={price:.5f}|"
        body += f"59=0|"
        return self._build_message(body)

    def create_order_cancel(self, symbol_id: str, client_order_id: str,
                             orig_client_order_id: str, side: int) -> str:
        """Create Order Cancel Request (MsgType=F)"""
        self._sequence_number += 1
        body = f"35=F|"
        body += f"49={self._sender_comp_id}|"
        body += f"56={self._target_comp_id}|"
        if self._sender_sub_id:
            body += f"50={self._sender_sub_id}|"
        body += f"52={self._timestamp()}|"
        body += f"11={client_order_id}|"
        body += f"41={orig_client_order_id}|"
        body += f"55={symbol_id}|"
        body += f"54={side}|"
        return self._build_message(body)

    def create_logout(self, reason: str = "") -> str:
        """Create Logout message"""
        self._sequence_number += 1
        body = f"35=5|"
        body += f"49={self._sender_comp_id}|"
        body += f"56={self._target_comp_id}|"
        if self._sender_sub_id:
            body += f"50={self._sender_sub_id}|"
        body += f"52={self._timestamp()}|"
        if reason:
            body += f"58={reason}|"
        return self._build_message(body)

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
            order_type=2
        )

    @property
    def sequence_number(self) -> int:
        return self._sequence_number

    @sequence_number.setter
    def sequence_number(self, value: int):
        self._sequence_number = value
