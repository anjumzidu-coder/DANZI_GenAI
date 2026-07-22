from __future__ import annotations

import os
import socket
import sys
import threading
import time
import webbrowser
from pathlib import Path

from streamlit.web import bootstrap


HOST = "127.0.0.1"
PORT = 8501


def _is_port_open(host: str, port: int) -> bool:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(0.5)
    try:
        return sock.connect_ex((host, port)) == 0
    finally:
        sock.close()


def _resolve_app_root() -> Path:
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS)
    return Path(__file__).resolve().parent


def _open_browser_when_ready(url: str, host: str, port: int, retries: int = 90) -> None:
    for _ in range(retries):
        if _is_port_open(host, port):
            webbrowser.open(url)
            return
        time.sleep(1)


def main() -> None:
    app_root = _resolve_app_root()
    app_path = app_root / "app.py"

    if not app_path.exists():
        raise FileNotFoundError(f"Could not find app.py at {app_path}")

    os.chdir(app_root)

    os.environ.setdefault("STREAMLIT_GLOBAL_DEVELOPMENT_MODE", "false")
    os.environ.setdefault("STREAMLIT_SERVER_HEADLESS", "true")
    os.environ.setdefault("STREAMLIT_BROWSER_GATHER_USAGE_STATS", "false")

    local_url = f"http://{HOST}:{PORT}"
    print("Starting HPE S&S Tool...")
    print(f"Local URL: {local_url}")

    threading.Thread(
        target=_open_browser_when_ready,
        args=(local_url, HOST, PORT),
        daemon=True,
    ).start()

    flag_options = {
        "global_developmentMode": False,
        "server_headless": True,
        "server_address": "0.0.0.0",
        "server_port": PORT,
        "browser_gatherUsageStats": False,
    }

    # Streamlit bootstrap runs the app in-process so this can be packaged as one EXE.
    bootstrap.run(str(app_path), False, [], flag_options)


if __name__ == "__main__":
    main()
