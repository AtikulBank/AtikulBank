# cython: language_level=3, boundscheck=False, wraparound=False
"""
FIX 4.4 Message Encoder via Cython
High-performance FIX message construction
"""

import time
from datetime import datetime, timezone
from libc.stdlib cimport malloc, free
from libc.string cimport memset, memcpy


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
        char[256] _temp_buffer
        
    def __init__(self, sender_comp_id: str, target_comp_id: str, 
                 sender_sub_id: str, heartbeat_interval: int = 30):
        self._sender_comp_id = sender_comp_id
        self._target_comp_id = target_comp_id
        self._sender_sub_id = sender_sub_id
        self._sequence_number = 0
        self._heartbeat_interval = heartbeat_interval
    
    cpdef str create_logon(self, password, reset=False):
        """
        Create FIX Logon message (MsgType=A)
        """
        self._sequence_number += 1
        
        # Build message
        msg = f"8=FIX.4.4|9=0|35=A|34={self._sequence_number}|"
        msg += f"49={self._sender_comp_id}|56={self._target_comp_id}|"
        
        if self._sender_sub_id:
            msg += f"50={self._sender_sub_id}|"
        
        msg += f"52={self._timestamp()}|"
        msg += f"98=0|108={self._heartbeat_interval}|"
        
        if reset:
            msg += "141=Y|"
        
        msg += f"554={password}|"
        
        # Calculate body length and checksum
        msg = self._add_body_length(msg)
        msg = self._add_checksum(msg)
        
        return msg
    
    cpdef str create_heartbeat(self, test_request_id=None):
        """
        Create FIX Heartbeat message (MsgType=0)
        """
        self._sequence_number += 1
        
        msg = f"8=FIX.4.4|9=0|35=0|34={self._sequence_number}|"
        msg += f"49={self._sender_comp_id}|56={self._target_comp_id}|"
        msg += f"52={self._timestamp()}|"
        
        if test_request_id:
            msg += f"112={test_request_id}|"
        
        msg = self._add_body_length(msg)
        msg = self._add_checksum(msg)
        
        return msg
    
    cpdef str create_test_request(self, test_request_id):
        """
        Create FIX TestRequest message (MsgType=1)
        """
        self._sequence_number += 1
        
        msg = f"8=FIX.4.4|9=0|35=1|34={self._sequence_number}|"
        msg += f"49={self._sender_comp_id}|56={self._target_comp_id}|"
        msg += f"52={self._timestamp()}|112={test_request_id}|"
        
        msg = self._add_body_length(msg)
        msg = self._add_checksum(msg)
        
        return msg
    
    cpdef str create_new_order(self, cl_ord_id, symbol,
                               side, quantity, price,
                               order_type="2", time_in_force="0"):
        """
        Create FIX NewOrderSingle message (MsgType=D)
        
        Args:
            cl_ord_id: Unique client order ID
            symbol: Symbol (e.g., "XAUUSD")
            side: "1" = Buy, "2" = Sell
            quantity: Order quantity
            price: Limit price
            order_type: "2" = Limit, "1" = Market
            time_in_force: "0" = Day, "1" = GTC, "3" = IOC
        """
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
    
    cpdef str create_order_cancel_request(self, cl_ord_id, 
                                          orig_cl_ord_id,
                                          symbol, side,
                                          quantity):
        """
        Create FIX OrderCancelRequest message (MsgType=F)
        """
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
    
    cpdef str create_logout(self, reason=""):
        """
        Create FIX Logout message (MsgType=5)
        """
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
        """Generate FIX timestamp in UTC"""
        return datetime.now(timezone.utc).strftime("%Y%m%d-%H:%M:%S.%f")[:-3]
    
    cdef str _format_price(self, float price):
        """Format price with 5 decimal places"""
        return f"{price:.5f}"
    
    cdef str _format_quantity(self, float quantity):
        """Format quantity with appropriate precision"""
        if quantity == int(quantity):
            return str(int(quantity))
        return f"{quantity:.5f}"
    
    cdef str _add_body_length(self, str msg):
        """Calculate and add body length"""
        # Remove the placeholder "9=0|" from the message
        msg = msg.replace("9=0|", "", 1)
        
        # Calculate body length (everything after "8=FIX.4.4|")
        header = "8=FIX.4.4|"
        body = msg[len(header):]
        body_length = len(body)
        
        # Rebuild message with correct body length
        msg = f"8=FIX.4.4|9={body_length}|{body}"
        
        return msg
    
    cdef str _add_checksum(self, str msg):
        """Calculate and add checksum"""
        # Sum of all bytes in message
        checksum = 0
        for c in msg.encode('ascii'):
            checksum += c
        checksum = checksum % 256
        
        # Add checksum
        msg = f"{msg}10={checksum:03d}|"
        
        return msg
    
    @property
    def sequence_number(self) -> int:
        """Get current sequence number"""
        return self._sequence_number
    
    @sequence_number.setter
    def sequence_number(self, value: int):
        """Set sequence number"""
        self._sequence_number = value