# cython: language_level=3
# cython: boundscheck=False
# cython: wraparound=False
# cython: cdivision=True
# cython: nonecheck=False
# cython: overflowcheck=False
"""
Ultra-Low-Latency Cython TCP Socket for FIX Protocol
High-performance network layer with static type binding
"""

import socket
import ssl
import time
import sys
from libc.string cimport memcpy, strlen
from libc.stdlib cimport malloc, free
from libc.math cimport pow, log, exp, sin

cdef class HFTSocket:
    """High-Performance TCP Socket with TCP_NODELAY"""
    cdef:
        object sock
        object ssl_sock
        str host
        int port
        bint connected
        bint use_ssl
        double timeout
        char* send_buffer
        char* recv_buffer
        size_t buffer_size
    
    def __cinit__(self, str host, int port, bint use_ssl=True, double timeout=5.0):
        self.host = host
        self.port = port
        self.use_ssl = use_ssl
        self.timeout = timeout
        self.connected = False
        self.buffer_size = 65536  # 64KB buffer
        
        # Allocate buffers
        self.send_buffer = <char*>malloc(self.buffer_size)
        self.recv_buffer = <char*>malloc(self.buffer_size)
        
        if not self.send_buffer or not self.recv_buffer:
            raise MemoryError("Failed to allocate socket buffers")
    
    def __dealloc__(self):
        """Clean up buffers"""
        if self.send_buffer:
            free(self.send_buffer)
        if self.recv_buffer:
            free(self.recv_buffer)
    
    cpdef bint connect(self):
        """Establish TCP connection with TCP_NODELAY"""
        try:
            # Create socket
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            
            # Enable TCP_NODELAY for low latency
            self.sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
            
            # Set timeout
            self.sock.settimeout(self.timeout)
            
            # Connect
            self.sock.connect((self.host, self.port))
            
            # Wrap with SSL if needed
            if self.use_ssl:
                context = ssl.create_default_context()
                context.check_hostname = False
                context.verify_mode = ssl.CERT_NONE
                self.ssl_sock = context.wrap_socket(self.sock, server_hostname=self.host)
            
            self.connected = True
            return True
            
        except Exception as e:
            print(f"[HFT] Connection failed: {e}")
            self.connected = False
            return False
    
    cpdef void disconnect(self):
        """Close connection"""
        try:
            if self.ssl_sock:
                self.ssl_sock.close()
            if self.sock:
                self.sock.close()
        except:
            pass
        self.connected = False
    
    cpdef int send_data(self, bytes data):
        """Send data with zero-copy optimization"""
        cdef:
            size_t data_len
            int sent
            char* c_data
        
        if not self.connected:
            return -1
        
        data_len = len(data)
        if data_len > self.buffer_size:
            return -1
        
        # Copy data to buffer
        c_data = <char*>data
        memcpy(self.send_buffer, c_data, data_len)
        
        try:
            if self.use_ssl:
                sent = self.ssl_sock.sendall(self.send_buffer[:data_len])
            else:
                sent = self.sock.sendall(self.send_buffer[:data_len])
            return 0
        except Exception as e:
            print(f"[HFT] Send failed: {e}")
            return -1
    
    cpdef bytes recv_data(self, size_t max_size=4096):
        """Receive data with zero-copy optimization"""
        cdef:
            size_t received
            bytes result
        
        if not self.connected:
            return b''
        
        try:
            if self.use_ssl:
                result = self.ssl_sock.recv(min(max_size, self.buffer_size))
            else:
                result = self.sock.recv(min(max_size, self.buffer_size))
            return result
        except socket.timeout:
            return b''
        except Exception as e:
            print(f"[HFT] Receive failed: {e}")
            return b''
    
    cpdef bint send_fix_message(self, str message):
        """Send FIX message with proper encoding"""
        cdef bytes encoded = message.encode('ascii')
        return self.send_data(encoded) == 0
    
    cpdef str recv_fix_message(self):
        """Receive FIX message"""
        cdef bytes data = self.recv_data()
        if data:
            return data.decode('ascii')
        return ''