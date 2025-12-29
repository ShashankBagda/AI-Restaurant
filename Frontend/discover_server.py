import json
import socket


DISCOVERY_PORT = 37020
DISCOVERY_MESSAGE = "SMART_RESTRO_DISCOVER"


def discover(timeout=3.0):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    sock.settimeout(timeout)
    sock.sendto(DISCOVERY_MESSAGE.encode("utf-8"), ("<broadcast>", DISCOVERY_PORT))
    try:
        data, _ = sock.recvfrom(1024)
    except socket.timeout:
        return None
    finally:
        sock.close()
    try:
        return json.loads(data.decode("utf-8"))
    except json.JSONDecodeError:
        return None


if __name__ == "__main__":
    info = discover()
    if not info:
        print("No server found")
    else:
        print(f"Server: {info['server_name']} at {info['ip']}:{info['http_port']}")
