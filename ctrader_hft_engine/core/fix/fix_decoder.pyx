# cython: language_level=3
# cython: boundscheck=False
# cython: wraparound=False
# cython: cdivision=True
"""
High-Performance FIX 4.4 Message Decoder
Zero-overhead message parsing with static typing
"""

from libc.string cimport strcmp, strcpy, strncpy
from libc.stdlib cimport atoi, atof

cdef class FIXDecoder:
    """FIX Message Decoder with zero-overhead parsing"""
    cdef:
        str last_error
        dict tag_map
    
    def __cinit__(self):
        self.last_error = ""
        self.tag_map = {
            "8": "BeginString",
            "9": "BodyLength",
            "35": "MsgType",
            "49": "SenderCompID",
            "56": "TargetCompID",
            "57": "SenderSubID",
            "34": "MsgSeqNum",
            "52": "SendingTime",
            "11": "ClOrdID",
            "21": "HandlInst",
            "55": "Symbol",
            "54": "Side",
            "60": "TransactTime",
            "38": "OrderQty",
            "40": "OrdType",
            "44": "Price",
            "59": "TimeInForce",
            "10": "CheckSum",
            "37": "OrderID",
            "17": "ExecID",
            "150": "ExecType",
            "39": "OrdStatus",
            "14": "CumQty",
            "151": "LeavesQty",
            "32": "LastQty",
            "31": "LastPx",
            "146": "NoRelatedSym",
            "262": "MDReqID",
            "263": "MDUpdateAction",
            "264": "MarketDepth",
            "265": "MDUpdateType",
            "267": "NoMDEntryTypes",
            "269": "MDEntryType",
            "270": "MDEntryPx",
            "271": "MDEntrySize",
            "272": "MDEntryDate",
            "273": "MDEntryTime",
            "274": "MDEntryPosition",
            "275": "MDEntryPositionDate",
            "554": "Password",
            "98": "EncryptMethod",
            "108": "HeartBtInt",
        }
    
    cpdef dict parse_message(self, str message):
        """Parse FIX message into dictionary"""
        cdef:
            dict result = {}
            list tags
            str tag
            str value
            int eq_idx
        
        if not message:
            self.last_error = "Empty message"
            return None
        
        # Split by SOH (ASCII 1)
        tags = message.split(chr(1))
        
        for tag in tags:
            if '=' in tag:
                eq_idx = tag.index('=')
                tag_id = tag[:eq_idx]
                value = tag[eq_idx + 1:]
                
                # Map to readable name
                tag_name = self.tag_map.get(tag_id, tag_id)
                result[tag_name] = value
        
        return result
    
    cpdef str get_msg_type(self, dict parsed_message):
        """Extract message type from parsed message"""
        return parsed_message.get("MsgType", "")
    
    cpdef bint is_logon(self, dict parsed_message):
        """Check if message is Logon"""
        return self.get_msg_type(parsed_message) == "A"
    
    cpdef bint is_heartbeat(self, dict parsed_message):
        """Check if message is Heartbeat"""
        return self.get_msg_type(parsed_message) == "0"
    
    cpdef bint is_execution_report(self, dict parsed_message):
        """Check if message is Execution Report"""
        return self.get_msg_type(parsed_message) == "8"
    
    cpdef bint is_market_data(self, dict parsed_message):
        """Check if message is Market Data"""
        return self.get_msg_type(parsed_message) in ["W", "X", "Y"]
    
    cpdef bint is_reject(self, dict parsed_message):
        """Check if message is Reject"""
        return self.get_msg_type(parsed_message) == "3"
    
    cpdef str get_last_error(self):
        """Get last parsing error"""
        return self.last_error