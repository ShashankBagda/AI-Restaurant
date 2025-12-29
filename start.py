import subprocess
import sys
import time


def run(cmd):
    return subprocess.Popen([sys.executable, cmd])


def main():
    server = run("launch_server.py")

    print("Started server launcher for local testing.")
    print("Press Ctrl+C to stop.")

    try:
        server.wait()
    except KeyboardInterrupt:
        pass
    finally:
        if server.poll() is None:
            server.terminate()


if __name__ == "__main__":
    main()
