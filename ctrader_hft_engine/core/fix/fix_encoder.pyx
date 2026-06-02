# cython: language_level=3
# cython: boundscheck=False
# cython: wraparound=False
# cython: cdivision=True
"""
High-Performance FIX 4.4 Message Encoder
Zero-overhead message construction with static typing
"""

import time
import random
from libc.string cimport memcpy
from libc.stdlib cimport malloc, free

cdef class FIXEncoder:
    """FIX Message Encoder with zero-overhead construction"""
    cdef:
        str sender_comp_id
        str target_comp_id
        str sender_sub_id
        int sequence_number
        char SOH
    
    def __cinit__(self, str sender_comp_id, str target_comp_id, str sender_sub_id):
        self.sender_comp_id = sender_comp_id
        self.target_comp_id = target_comp_id
        self.sender_sub_id = sender_sub_id
        self.sequence_number = 1
        self.SOH = chr(1)  # FIX delimiter
    
    cpdef str calculate_checksum(self, str message):
        """Calculate FIX checksum"""
        cdef int checksum = 0
        cdef int i
        cdef str msg_without_checksum
        
        # Remove existing checksum if present
        if "10=" in message:
            idx = message.index("10=")
            msg_without_checksum = message[:idx]
        else:
            msg_without_checksum = message
        
        # Calculate sum of bytes
        for i in range(len(msg_without_checksum)):
            checksum += ord(msg_without_checksum[i])
        
        checksum = checksum % 256
        return f"{checksum:03d}"
    
    cpdef str create_logon_message(self, str password):
        """Create FIX Logon message (MsgType=A)"""
        cdef str timestamp = time.strftime("%Y%m%d-%H:%M:%S", time.gmtime())
        
        msg = (
            f"8=FIX.4.4{self.SOH}"
            f"35=A{self.SOH}"
            f"49={self.sender_comp_id}{self.SOH}"
            f"56={self.target_comp_id}{self.SOH}"
            f"57={self.sender_sub_id}{self.SOH}"
            f"34={self.sequence_number}{self.SOH}"
            f"52={timestamp}{self.SOH}"
            f"98=0{self.SOH}"
            f"108=30{self.SOH}"
            f"554={password}{self.SOH}"
            f"10=000{self.SOH}"
        )
        
        # Calculate and insert checksum
        checksum = self.calculate_checksum(msg)
        msg = msg.replace("10=000", f"10={checksum}")
        
        self.sequence_number += 1
        return msg
    
    cpdef str create_heartbeat_message(self):
        """Create FIX Heartbeat message (MsgType=0)"""
        cdef str timestamp = time.strftime("%Y%m%d-%H:%M:%S", time.gmtime())
        
        msg = (
            f"8=FIX.4.4{self.SOH}"
            f"35=0{self.SOH}"
            f"49={self.sender_comp_id}{self.SOH}"
            f"56={self.target_comp_id}{self.SOH}"
            f"57={self.sender_sub_id}{self.SOH}"
            f"34={self.sequence_number}{self.SOH}"
            f"52={timestamp}{self.SOH}"
            f"10=000{self.SOH}"
        )
        
        checksum = self.calculate_checksum(msg)
        msg = msg.replace("10=000", f"10={checksum}")
        
        self.sequence_number += 1
        return msg
    
    cpdef str create_new_order_single(
        self,
        str cl_ord_id,
        str symbol,
        str side,
        double quantity,
        double price,
        str order_type="2",  # Limit
        str time_in_force="0"  # Day
    ):
        """Create FIX New Order Single message (MsgType=D)"""
        cdef str timestamp = time.strftime("%Y%m%d-%H:%M:%S", time.gmtime())
        
        msg = (
            f"8=FIX.4.4{self.SOH}"
            f"35=D{self.SOH}"
            f"49={self.sender_comp_id}{self.SOH}"
            f"56={self.target_comp_id}{self.SOH}"
            f"57={self.sender_sub_id}{self.SOH}"
            f"34={self.sequence_number}{self.SOH}"
            f"52={timestamp}{self.SOH}"
            f"11={cl_ord_id}{self.SOH}"
            f"21=1{self.SOH}"  # HandlInst = AutoPrivate
            f"55={symbol}{self.SOH}"
            f"54={'1' if side.upper() == 'BUY' else '2'}{self.SOH}"
            f"60={timestamp}{self.SOH}"
            f"38={quantity}{self.SOH}"
            f"40={order_type}{self.SOH}"
            f"44={price}{self.SOH}"
            f"59={time_in_force}{self.SOH}"
            f"10=000{self.SOH}"
        )
        
        checksum = self.calculate_checksum(msg)
        msg = msg.replace("10=000", f"10={checksum}")
        
        self.sequence_number += 1
        return msg
    
    cpdef str create_order_cancel_request(
        self,
        str cl_ord_id,
        str orig_cl_ord_id,
        str symbol,
        str side,
        double quantity
    ):
        """Create FIX Order Cancel Request message (MsgType=F)"""
        cdef str timestamp = time.strftime("%Y%m%d-%H:%M:%S", time.gmtime())
        
        msg = (
            f"8=FIX.4.4{self.SOH}"
            f"35=F{self.SOH}"
            f"49={self.sender_comp_id}{self.SOH}"
            f"56={self.target_comp_id}{self.SOH}"
            f"57={self.sender_sub_id}{self.SOH}"
            f"34={self.sequence_number}{self.SOH}"
            f"52={timestamp}{self.SOH}"
            f"11={cl_ord_id}{self.SOH}"
            f"41={orig_cl_ord_id}{self.SOH}"
            f"55={symbol}{self.SOH}"
            f"54={'1' if side.upper() == 'BUY' else '2'}{self.SOH}"
            f"60={timestamp}{self.SOH}"
            f"38={quantity}{self.SOH}"
            f"10=000{self.SOH}"
        )
        
        checksum = self.calculate_checksum(msg)
        msg = msg.replace("10=000", f"10={checksum}")
        
        self.sequence_number += 1
        return msg
    
    cpdef str create_market_data_request(
        self,
        str md_req_id,
        str symbol,
        str subscription_type="1"  # Snapshot
    ):
        """Create FIX Market Data Request message (MsgType=V)"""
        cdef str timestamp = time.strftime("%Y%m%d-%H:%M:%S", time.gmtime())
        
        msg = (
            f"8=FIX.4.4{self.SOH}"
            f"35=V{self.SOH}"
            f"49={self.sender_comp_id}{self.SOH}"
            f"56={self.target_comp_id}{self.SOH}"
            f"57={self.sender_sub_id}{self.SOH}"
            f"34={self.sequence_number}{self.SOH}"
            f"52={timestamp}{self.SOH}"
            f"262={md_req_id}{self.SOH}"
            f"263={subscription_type}{self.SOH}"
            f"264=1{self.SOH}"  # MarketDepth = 1
            f"265=0{self.SOH}"  # MarketDepthType = 0
            f"267=2{self.SOH}"  # MarketDepthSize = 2
            f"269=0{self.SOH}"  # MDEntryType = Bid
            f"269=1{self.SOH}"  # MDEntryType = Offer
            f"146=1{self.SOH}"  # NoRelatedSym = 1
            f"55={symbol}{self.SOH}"
            f"10=000{self.SOH}"
        )
        
        checksum = self.calculate_checksum(msg)
        msg = msg.replace("10=000", f"10={checksum}")
        
        self.sequence_number += 1
        return msg