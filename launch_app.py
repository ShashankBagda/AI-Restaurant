import os
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


def main():
    skip_install = "--no-install" in sys.argv
    ensure_backend_deps(skip_install)
    backend_proc = run_backend()
    time.sleep(1.5)

    server_url = "http://127.0.0.1:8000"
    cache_bust = int(time.time())
    landing_url = f"{server_url}/app/?v={cache_bust}#/landing"
    webbrowser.open(landing_url)

    print("Backend running on http://127.0.0.1:8000")
    print(f"Landing page: {landing_url}")
    print("Press Ctrl+C to stop.")

    try:
        backend_proc.wait()
    except KeyboardInterrupt:
        pass
    finally:
        backend_proc.terminate()


if __name__ == "__main__":
    main()
