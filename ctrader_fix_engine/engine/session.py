"""
FIX Session Manager
Handles FIX protocol session lifecycle
"""

import asyncio
import time
from datetime import datetime, timezone
from enum import Enum, auto
from typing import Optional, Callable

from ..network.socket import TcpSocket, SocketError
from ..protocol.encoder import FixEncoder
from ..protocol.decoder import FixDecoder, FixMessage
from ..config.loader import FixConfig


class SessionState(Enum):
    """FIX Session States"""
    DISCONNECTED = auto()
    CONNECTING = auto()
    LOGON_SENT = auto()
    LOGGED_ON = auto()
    LOGOUT_SENT = auto()
    ERROR = auto()


class FixSession:
    """
    FIX 4.4 Session Manager
    Manages connection, logon, heartbeats, and message routing
    """
    
    def __init__(self, config: FixConfig):
        self.config = config
        self.state = SessionState.DISCONNECTED
        
        # Network layer
        self._socket: Optional[TcpSocket] = None
        
        # Protocol layer
        self._encoder = FixEncoder(
            sender_comp_id=config.sender_comp_id,
            target_comp_id=config.target_comp_id,
            sender_sub_id=config.sender_sub_id,
            heartbeat_interval=config.heartbeat_interval
        )
        self._decoder = FixDecoder(
            sender_comp_id=config.sender_comp_id,
            target_comp_id=config.target_comp_id
        )
        
        # Session state
        self._last_heartbeat_time: float = 0.0
        self._last_recv_time: float = 0.0
        self._test_request_id: Optional[str] = None
        
        # Message callbacks
        self._on_message: Optional[Callable[[FixMessage], None]] = None
        self._on_execution_report: Optional[Callable[[FixMessage], None]] = None
        self._on_disconnect: Optional[Callable[[], None]] = None
        
        # Running flag
        self._running = False
    
    def connect(self) -> None:
        """Establish connection to FIX server"""
        self.state = SessionState.CONNECTING
        
        try:
            self._socket = TcpSocket(
                host=self.config.host,
                port=self.config.port,
                timeout=self.config.timeout
            )
            self._socket.connect()
            self.state = SessionState.CONNECTING
            
        except SocketError as e:
            self.state = SessionState.ERROR
            raise
    
    def logon(self, password: str) -> str:
        """
        Send Logon message
        Returns: Logon message
        """
        if self.state != SessionState.CONNECTING:
            raise RuntimeError("Must connect before logon")
        
        self.state = SessionState.LOGON_SENT
        logon_msg = self._encoder.create_logon(password)
        self._send(logon_msg)
        
        return logon_msg
    
    def send_heartbeat(self, test_request_id: str = None) -> str:
        """Send Heartbeat message"""
        heartbeat_msg = self._encoder.create_heartbeat(test_request_id)
        self._send(heartbeat_msg)
        self._last_heartbeat_time = time.time()
        
        return heartbeat_msg
    
    def send_test_request(self) -> str:
        """Send TestRequest message"""
        self._test_request_id = f"TR-{int(time.time())}"
        test_msg = self._encoder.create_test_request(self._test_request_id)
        self._send(test_msg)
        
        return test_msg
    
    def send_new_order(self, cl_ord_id: str, symbol: str,
                       side: str, quantity: float, price: float,
                       order_type: str = "2", time_in_force: str = "0") -> str:
        """
        Send NewOrderSingle message
        
        Args:
            cl_ord_id: Unique client order ID
            symbol: Symbol (e.g., "XAUUSD")
            side: "1" = Buy, "2" = Sell
            quantity: Order quantity
            price: Limit price
            order_type: "2" = Limit, "1" = Market
            time_in_force: "0" = Day, "1" = GTC, "3" = IOC
            
        Returns:
            Sent message
        """
        if self.state != SessionState.LOGGED_ON:
            raise RuntimeError("Must be logged on to send orders")
        
        order_msg = self._encoder.create_new_order(
            cl_ord_id=cl_ord_id,
            symbol=symbol,
            side=side,
            quantity=quantity,
            price=price,
            order_type=order_type,
            time_in_force=time_in_force
        )
        self._send(order_msg)
        
        return order_msg
    
    def send_cancel_request(self, cl_ord_id: str, orig_cl_ord_id: str,
                           symbol: str, side: str, quantity: float) -> str:
        """Send OrderCancelRequest message"""
        if self.state != SessionState.LOGGED_ON:
            raise RuntimeError("Must be logged on to cancel orders")
        
        cancel_msg = self._encoder.create_order_cancel_request(
            cl_ord_id=cl_ord_id,
            orig_cl_ord_id=orig_cl_ord_id,
            symbol=symbol,
            side=side,
            quantity=quantity
        )
        self._send(cancel_msg)
        
        return cancel_msg
    
    def logout(self, reason: str = "") -> str:
        """Send Logout message"""
        self.state = SessionState.LOGOUT_SENT
        logout_msg = self._encoder.create_logout(reason)
        self._send(logout_msg)
        
        return logout_msg
    
    def disconnect(self) -> None:
        """Disconnect from FIX server"""
        self._running = False
        
        if self._socket and self._socket.is_connected:
            try:
                self.logout("Client disconnect")
            except Exception:
                pass
            
            try:
                self._socket.close()
            except Exception:
                pass
        
        self.state = SessionState.DISCONNECTED
        self._socket = None
    
    def receive_message(self, timeout: float = None) -> Optional[FixMessage]:
        """
        Receive and decode a FIX message
        
        Args:
            timeout: Receive timeout in seconds
            
        Returns:
            Decoded FixMessage or None if timeout
        """
        if not self._socket or not self._socket.is_connected:
            return None
        
        try:
            # Set socket timeout
            if timeout is not None:
                self._socket._timeout = timeout
            
            # Receive raw data
            raw_data = self._socket.recv(self.config.buffer_size)
            
            if not raw_data:
                return None
            
            # Update last receive time
            self._last_recv_time = time.time()
            
            # Decode message
            message = self._decoder.decode(raw_data)
            
            if message.is_valid:
                self._handle_message(message)
            
            return message
            
        except SocketError:
            self.state = SessionState.ERROR
            if self._on_disconnect:
                self._on_disconnect()
            return None
    
    def _handle_message(self, message: FixMessage) -> None:
        """Handle incoming FIX message"""
        msg_type = message.msg_type
        
        # Handle specific message types
        if msg_type == "0":  # Heartbeat
            pass
        
        elif msg_type == "1":  # TestRequest
            # Respond with Heartbeat
            test_id = message.get(112)
            if test_id:
                self.send_heartbeat(test_id)
        
        elif msg_type == "3":  # Reject
            # Log rejection
            reason = message.get(58, "Unknown")
            print(f"Message rejected: {reason}")
        
        elif msg_type == "5":  # Logout
            self.state = SessionState.DISCONNECTED
        
        elif msg_type == "8":  # ExecutionReport
            if self._on_execution_report:
                self._on_execution_report(message)
        
        # Call general message handler
        if self._on_message:
            self._on_message(message)
    
    def check_heartbeat_timeout(self) -> bool:
        """Check if heartbeat timeout occurred"""
        if self._last_recv_time == 0:
            return False
        
        elapsed = time.time() - self._last_recv_time
        return elapsed > (self.config.heartbeat_interval * 1.5)
    
    def _send(self, message: str) -> None:
        """Send raw message"""
        if not self._socket or not self._socket.is_connected:
            raise SocketError("Not connected")
        
        # Convert to bytes and send
        data = message.replace("|", "\x01").encode('ascii')
        self._socket.send(data)
    
    def set_message_handler(self, handler: Callable[[FixMessage], None]) -> None:
        """Set message callback"""
        self._on_message = handler
    
    def set_execution_report_handler(self, handler: Callable[[FixMessage], None]) -> None:
        """Set execution report callback"""
        self._on_execution_report = handler
    
    def set_disconnect_handler(self, handler: Callable[[], None]) -> None:
        """Set disconnect callback"""
        self._on_disconnect = handler
    
    @property
    def is_connected(self) -> bool:
        """Check if session is connected"""
        return (self._socket is not None and 
                self._socket.is_connected and 
                self.state == SessionState.LOGGED_ON)