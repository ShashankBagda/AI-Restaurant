import json
import socket
import threading


DISCOVERY_PORT = 37020
DISCOVERY_MESSAGE = "SMART_RESTRO_DISCOVER"


def _get_local_ip():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        sock.connect(("8.8.8.8", 80))
        return sock.getsockname()[0]
    finally:
        sock.close()


def start_discovery_responder(http_port: int, server_name: str = "smart-restaurant"):
    def _serve():
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind(("", DISCOVERY_PORT))
        while True:
            data, addr = sock.recvfrom(1024)
            if not data:
                continue
            try:
                message = data.decode("utf-8").strip()
            except UnicodeDecodeError:
                continue
            if message != DISCOVERY_MESSAGE:
                continue
            payload = {
                "server_name": server_name,
                "ip": _get_local_ip(),
                "http_port": http_port,
            }
            sock.sendto(json.dumps(payload).encode("utf-8"), addr)

    thread = threading.Thread(target=_serve, daemon=True)
    thread.start()
    return thread
