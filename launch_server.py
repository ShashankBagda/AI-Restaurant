import os
import socket
import subprocess
import sys
import time
import webbrowser


def ensure_backend_deps(skip_install: bool):
    if skip_install:
        return
    req_path = os.path.join(os.getcwd(), "Backend", "requirements.txt")
    if not os.path.exists(req_path):
        return
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", req_path])


def run_backend():
    backend_dir = os.path.join(os.getcwd(), "Backend")
    return subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"],
        cwd=backend_dir,
    )


def get_local_ip():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        sock.connect(("8.8.8.8", 80))
        return sock.getsockname()[0]
    except OSError:
        return "127.0.0.1"
    finally:
        sock.close()


def main():
    skip_install = "--no-install" in sys.argv
    ensure_backend_deps(skip_install)
    backend_proc = run_backend()
    time.sleep(1.5)

    server_url = "http://127.0.0.1:8000"
    customer_path = os.path.join(os.getcwd(), "Frontend", "customer.html")
    admin_path = os.path.join(os.getcwd(), "Frontend", "admin.html")
    customer_url = f"file:///{customer_path.replace(os.sep, '/')}?server={server_url}"
    admin_url = f"file:///{admin_path.replace(os.sep, '/')}?server={server_url}"
    webbrowser.open(customer_url)
    webbrowser.open(admin_url)

    print("Backend running on http://127.0.0.1:8000")
    print(f"Customer and admin frontends opened with server {server_url}.")
    print("Press Ctrl+C to stop.")

    try:
        backend_proc.wait()
    except KeyboardInterrupt:
        pass
    finally:
        backend_proc.terminate()


if __name__ == "__main__":
    main()
