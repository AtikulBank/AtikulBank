# cython: language_level=3, boundscheck=False, wraparound=False
"""
Raw C-Socket implementation via Cython
Ultra-low-latency TCP connections for FIX protocol
"""

import socket
import time


class SocketError(Exception):
    """Socket operation error"""
    pass


cdef class TcpSocket:
    """
    High-performance TCP socket with minimal Python overhead
    """
    
    cdef:
        object _socket
        str _host
        int _port
        double _timeout
        bint _connected
        
    def __init__(self, host: str, port: int, timeout: float = 30.0):
        self._host = host
        self._port = port
        self._timeout = timeout
        self._connected = False
        self._socket = None
    
    def connect(self) -> None:
        """Establish TCP connection with minimal latency"""
        try:
            # Create socket
            self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            
            # Enable TCP_NODELAY for minimal latency
            self._socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
            
            # Set socket timeout
            self._socket.settimeout(self._timeout)
            
            # Connect to server
            self._socket.connect((self._host, self._port))
            self._connected = True
            
        except Exception as e:
            if self._socket:
                self._socket.close()
                self._socket = None
            raise SocketError(f"Connection failed: {e}")
    
    cpdef int send(self, bytes data: bytes):
        """
        Send data with minimal overhead
        Returns: Number of bytes sent
        """
        if not self._connected:
            raise SocketError("Socket not connected")
        
        cdef int total_sent = 0
        cdef int data_len = len(data)
        
        # Send with retry
        while total_sent < data_len:
            try:
                sent = self._socket.send(data[total_sent:])
                if sent == 0:
                    raise SocketError("Connection closed")
                total_sent += sent
            except socket.timeout:
                time.sleep(0.001)  # 1ms backoff
                continue
            except Exception as e:
                raise SocketError(f"Send error: {e}")
        
        return total_sent
    
    cpdef bytes recv(self, int max_bytes=0):
        """
        Receive data with minimal overhead
        Returns: Received bytes
        """
        if not self._connected:
            raise SocketError("Socket not connected")
        
        cdef int target_bytes = max_bytes if max_bytes > 0 else 65536
        
        try:
            data = self._socket.recv(target_bytes)
            
            if not data:
                # Connection closed
                self._connected = False
                raise SocketError("Connection closed by remote")
            
            return data
            
        except socket.timeout:
            return b''
        except Exception as e:
            if "Connection closed" in str(e):
                raise
            raise SocketError(f"Receive error: {e}")
    
    def close(self) -> None:
        """Close socket connection"""
        if self._connected and self._socket:
            try:
                self._socket.close()
            except:
                pass
            self._connected = False
            self._socket = None
    
    @property
    def is_connected(self) -> bool:
        """Check if socket is connected"""
        return self._connected
    
    def __enter__(self):
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
        return False