# cython: language_level=3, boundscheck=False, wraparound=False
"""
FIX 4.4 Message Decoder via Cython
High-performance FIX message parsing
"""

from libc.stdlib cimport malloc, free


cdef class FixMessage:
    """
    FIX Message container
    Stores parsed FIX tags as key-value pairs
    """
    
    cdef:
        dict _tags
        str _raw_message
        bint _valid
        
    def __init__(self):
        self._tags = {}
        self._raw_message = ""
        self._valid = False
    
    cpdef bint parse(self, str message):
        """
        Parse FIX message string
        Returns: True if parsing successful
        """
        self._raw_message = message
        self._tags.clear()
        
        try:
            # Split by field separator
            fields = message.split("|")
            
            for field in fields:
                if not field:
                    continue
                
                # Split tag=value
                if "=" in field:
                    tag, _, value = field.partition("=")
                    try:
                        tag_num = int(tag)
                        self._tags[tag_num] = value
                    except ValueError:
                        continue
            
            # Validate basic FIX structure
            if 8 in self._tags and 35 in self._tags:
                self._valid = True
                return True
            
            return False
            
        except Exception:
            self._valid = False
            return False
    
    cpdef str get(self, int tag, str default=""):
        """
        Get tag value
        Args:
            tag: FIX tag number
            default: Default value if tag not found
        Returns:
            Tag value or default
        """
        return self._tags.get(tag, default)
    
    cpdef int get_int(self, int tag, int default=0):
        """Get tag value as integer"""
        value = self._tags.get(tag, "")
        try:
            return int(value)
        except (ValueError, TypeError):
            return default
    
    cpdef float get_float(self, int tag, float default=0.0):
        """Get tag value as float"""
        value = self._tags.get(tag, "")
        try:
            return float(value)
        except (ValueError, TypeError):
            return default
    
    @property
    def msg_type(self) -> str:
        """Get message type (Tag 35)"""
        return self.get(35)
    
    @property
    def sequence_number(self) -> int:
        """Get sequence number (Tag 34)"""
        return self.get_int(34)
    
    @property
    def sender_comp_id(self) -> str:
        """Get sender comp ID (Tag 49)"""
        return self.get(49)
    
    @property
    def target_comp_id(self) -> str:
        """Get target comp ID (Tag 56)"""
        return self.get(56)
    
    @property
    def timestamp(self) -> str:
        """Get timestamp (Tag 52)"""
        return self.get(52)
    
    @property
    def body_length(self) -> int:
        """Get body length (Tag 9)"""
        return self.get_int(9)
    
    @property
    def checksum(self) -> int:
        """Get checksum (Tag 10)"""
        return self.get_int(10)
    
    @property
    def is_valid(self) -> bool:
        """Check if message is valid"""
        return self._valid
    
    @property
    def raw_message(self) -> str:
        """Get raw message"""
        return self._raw_message
    
    def __repr__(self) -> str:
        if self._valid:
            return f"FixMessage(type={self.msg_type}, seq={self.sequence_number})"
        return "FixMessage(invalid)"


cdef class FixDecoder:
    """
    FIX 4.4 Message Decoder
    Parses incoming FIX messages with minimal overhead
    """
    
    cdef:
        str _sender_comp_id
        str _target_comp_id
        dict _message_handlers
    
    def __init__(self, sender_comp_id: str, target_comp_id: str):
        self._sender_comp_id = sender_comp_id
        self._target_comp_id = target_comp_id
        self._message_handlers = {}
    
    cpdef FixMessage decode(self, bytes raw_data):
        """
        Decode raw bytes into FixMessage
        Args:
            raw_data: Raw bytes from socket
        Returns:
            Parsed FixMessage
        """
        cdef FixMessage msg = FixMessage()
        
        try:
            # Convert bytes to string
            message = raw_data.decode('ascii')
            
            # Remove SOH characters if present (some implementations use \x01)
            message = message.replace('\x01', '|')
            
            # Parse the message
            if msg.parse(message):
                # Validate message structure
                if self._validate_message(msg):
                    return msg
            
            return msg
            
        except Exception:
            return msg
    
    cpdef bint validate_checksum(self, str message):
        """
        Validate message checksum
        Returns: True if checksum is valid
        """
        # Find checksum position
        checksum_pos = message.rfind("10=")
        if checksum_pos == -1:
            return False
        
        # Extract checksum value
        try:
            received_checksum = int(message[checksum_pos+3:checksum_pos+6])
        except ValueError:
            return False
        
        # Calculate checksum of message before checksum field
        message_body = message[:checksum_pos-1]  # Remove trailing |
        
        # Sum of all bytes
        calculated_checksum = 0
        for c in message_body.encode('ascii'):
            calculated_checksum += c
        calculated_checksum = calculated_checksum % 256
        
        return received_checksum == calculated_checksum
    
    cdef bint _validate_message(self, FixMessage msg):
        """Validate basic message structure"""
        # Check required tags
        required_tags = [8, 9, 35, 34, 49, 56, 52]
        for tag in required_tags:
            if tag not in msg._tags:
                return False
        
        # Validate version
        if msg.get(8) != "FIX.4.4":
            return False
        
        # Validate target comp ID
        if msg.sender_comp_id != self._target_comp_id:
            return False
        
        return True
    
    cpdef str get_message_type_name(self, str msg_type):
        """Convert message type code to name"""
        message_types = {
            "0": "Heartbeat",
            "1": "TestRequest",
            "2": "ResendRequest",
            "3": "Reject",
            "4": "SequenceReset",
            "5": "Logout",
            "6": "IOI",
            "7": "Advertisement",
            "8": "ExecutionReport",
            "9": "OrderCancelReject",
            "A": "Logon",
            "B": "NewOrderList",
            "C": "OrderCancelReplaceRequest",
            "D": "NewOrderSingle",
            "E": "NewOrderCross",
            "F": "OrderCancelRequest",
            "G": "OrderCancelReplaceRequest",
            "H": "OrderStatusRequest",
            "J": "Allocation",
            "K": "AllocationACK",
            "L": "DontKnowTrade",
            "M": "RequestForPositions",
            "N": "RequestForPositionsACK",
            "P": "PositionReport",
            "Q": "TradeCaptureReport",
            "R": "TradeCaptureReportACK",
            "S": "MarketDataRequest",
            "T": "MarketDataSnapshotFullRefresh",
            "U": "MarketDataIncrementalRefresh",
            "V": "MarketDataRequestReject",
            "W": "QuoteRequestReject",
            "X": "RFQRequest",
            "Y": "Quote",
            "Z": "QuoteCancel",
        }
        return message_types.get(msg_type, f"Unknown({msg_type})")