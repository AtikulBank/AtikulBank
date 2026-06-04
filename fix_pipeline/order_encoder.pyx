# cython: language_level=3, boundscheck=False, wraparound=False
"""
Order Encoder - FIX 4.4 Message Generator
Eye-blink speed FIX message construction
"""

import time
from datetime import datetime, timezone


cdef class FixEncoder:
    """
    FIX 4.4 Message Encoder
    Constructs FIX protocol messages with minimal overhead
    """

    cdef:
        str _sender_comp_id
        str _target_comp_id
        str _sender_sub_id
        int _sequence_number
        int _heartbeat_interval

    def __init__(self, str sender_comp_id, str target_comp_id,
                 str sender_sub_id, int heartbeat_interval=30):
        self._sender_comp_id = sender_comp_id
        self._target_comp_id = target_comp_id
        self._sender_sub_id = sender_sub_id
        self._sequence_number = 0
        self._heartbeat_interval = heartbeat_interval

    cpdef str create_logon(self, str password, bint reset=False):
        """Create FIX Logon message (MsgType=A)"""
        self._sequence_number += 1
        msg = f"8=FIX.4.4|9=0|35=A|34={self._sequence_number}|"
        msg += f"49={self._sender_comp_id}|56={self._target_comp_id}|"
        if self._sender_sub_id:
            msg += f"50={self._sender_sub_id}|"
        msg += f"52={self._timestamp()}|"
        msg += f"98=0|108={self._heartbeat_interval}|"
        if reset:
            msg += "141=Y|"
        msg += f"554={password}|"
        msg = self._add_body_length(msg)
        msg = self._add_checksum(msg)
        return msg

    cpdef str create_heartbeat(self, str test_request_id=None):
        """Create FIX Heartbeat message (MsgType=0)"""
        self._sequence_number += 1
        msg = f"8=FIX.4.4|9=0|35=0|34={self._sequence_number}|"
        msg += f"49={self._sender_comp_id}|56={self._target_comp_id}|"
        msg += f"52={self._timestamp()}|"
        if test_request_id:
            msg += f"112={test_request_id}|"
        msg = self._add_body_length(msg)
        msg = self._add_checksum(msg)
        return msg

    cpdef str create_test_request(self, str test_request_id):
        """Create FIX TestRequest message (MsgType=1)"""
        self._sequence_number += 1
        msg = f"8=FIX.4.4|9=0|35=1|34={self._sequence_number}|"
        msg += f"49={self._sender_comp_id}|56={self._target_comp_id}|"
        msg += f"52={self._timestamp()}|112={test_request_id}|"
        msg = self._add_body_length(msg)
        msg = self._add_checksum(msg)
        return msg

    cpdef str create_new_order(self, str cl_ord_id, str symbol,
                               str side, double quantity, double price,
                               str order_type="2", str time_in_force="0"):
        """Create FIX NewOrderSingle message (MsgType=D)"""
        self._sequence_number += 1
        msg = f"8=FIX.4.4|9=0|35=D|34={self._sequence_number}|"
        msg += f"49={self._sender_comp_id}|56={self._target_comp_id}|"
        msg += f"52={self._timestamp()}|"
        msg += f"11={cl_ord_id}|21=1|55={symbol}|"
        msg += f"54={side}|38={self._format_quantity(quantity)}|"
        msg += f"40={order_type}|44={self._format_price(price)}|"
        msg += f"59={time_in_force}|"
        msg = self._add_body_length(msg)
        msg = self._add_checksum(msg)
        return msg

    cpdef str create_order_cancel_request(self, str cl_ord_id, str orig_cl_ord_id,
                                          str symbol, str side, double quantity):
        """Create FIX OrderCancelRequest message (MsgType=F)"""
        self._sequence_number += 1
        msg = f"8=FIX.4.4|9=0|35=F|34={self._sequence_number}|"
        msg += f"49={self._sender_comp_id}|56={self._target_comp_id}|"
        msg += f"52={self._timestamp()}|"
        msg += f"11={cl_ord_id}|41={orig_cl_ord_id}|"
        msg += f"55={symbol}|54={side}|"
        msg += f"38={self._format_quantity(quantity)}|"
        msg = self._add_body_length(msg)
        msg = self._add_checksum(msg)
        return msg

    cpdef str create_logout(self, str reason=""):
        """Create FIX Logout message (MsgType=5)"""
        self._sequence_number += 1
        msg = f"8=FIX.4.4|9=0|35=5|34={self._sequence_number}|"
        msg += f"49={self._sender_comp_id}|56={self._target_comp_id}|"
        msg += f"52={self._timestamp()}|"
        if reason:
            msg += f"58={reason}|"
        msg = self._add_body_length(msg)
        msg = self._add_checksum(msg)
        return msg

    cdef str _timestamp(self):
        return datetime.now(timezone.utc).strftime("%Y%m%d-%H:%M:%S.%f")[:-3]

    cdef str _format_price(self, double price):
        return f"{price:.5f}"

    cdef str _format_quantity(self, double quantity):
        if quantity == int(quantity):
            return str(int(quantity))
        return f"{quantity:.5f}"

    cdef str _add_body_length(self, str msg):
        msg = msg.replace("9=0|", "", 1)
        header = "8=FIX.4.4|"
        body = msg[len(header):]
        body_length = len(body)
        msg = f"8=FIX.4.4|9={body_length}|{body}"
        return msg

    cdef str _add_checksum(self, str msg):
        checksum = 0
        for c in msg.encode('ascii'):
            checksum += c
        checksum = checksum % 256
        msg = f"{msg}10={checksum:03d}|"
        return msg

    @property
    def sequence_number(self) -> int:
        return self._sequence_number

    @sequence_number.setter
    def sequence_number(self, value: int):
        self._sequence_number = value
