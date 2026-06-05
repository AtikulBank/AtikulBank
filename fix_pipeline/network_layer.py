import socket
import ssl

class SocketError(Exception):
    pass

class TcpSocket:
    def __init__(self):
        self._sock = None
        self._ssl_sock = None

    def connect(self, host: str, port: int, use_ssl: bool = True) -> bool:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
            sock.settimeout(30)
            sock.connect((host, port))
            if use_ssl:
                ctx = ssl.create_default_context()
                self._ssl_sock = ctx.wrap_socket(sock, server_hostname=host)
            else:
                self._ssl_sock = sock
            self._sock = sock
            return True
        except Exception as e:
            raise SocketError(f"Connection failed: {e}")

    def send(self, data: bytes) -> int:
        if not self._ssl_sock:
            raise SocketError("Not connected")
        return self._ssl_sock.send(data)

    def sendall(self, data: bytes) -> None:
        if not self._ssl_sock:
            raise SocketError("Not connected")
        self._ssl_sock.sendall(data)

    def recv(self, size: int = 4096) -> bytes:
        if not self._ssl_sock:
            raise SocketError("Not connected")
        try:
            return self._ssl_sock.recv(size)
        except socket.timeout:
            return b""

    def settimeout(self, timeout: float) -> None:
        if self._ssl_sock:
            self._ssl_sock.settimeout(timeout)

    def close(self) -> None:
        try:
            if self._ssl_sock:
                self._ssl_sock.close()
            if self._sock:
                self._sock.close()
        except:
            pass

    @property
    def is_connected(self) -> bool:
        return self._ssl_sock is not None
