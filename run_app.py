import os
import sys
import time
import socket
import threading
import signal
import multiprocessing
import ctypes
from ctypes import wintypes

# 1. Must be the very first call before any imports that spawn processes
if __name__ == "__main__":
    multiprocessing.freeze_support()

# 2. Windows Mutex to guarantee only ONE instance runs
MUTEX_NAME = "Local\\EinBierSingleInstanceMutex_v1"
kernel32 = ctypes.windll.kernel32
user32 = ctypes.windll.user32

mutex = kernel32.CreateMutexW(None, wintypes.BOOL(True), wintypes.LPCWSTR(MUTEX_NAME))
last_error = kernel32.GetLastError()
ERROR_ALREADY_EXISTS = 183

if last_error == ERROR_ALREADY_EXISTS:
    # Another instance is already open: bring it to front and exit immediately
    hwnd = user32.FindWindowW(None, wintypes.LPCWSTR("ein Bier 🍺"))
    if hwnd:
        user32.ShowWindow(hwnd, 9)  # SW_RESTORE
        user32.SetForegroundWindow(hwnd)
    sys.exit(0)

# Hide console window if visible
if sys.platform == "win32":
    console_hwnd = kernel32.GetConsoleWindow()
    if console_hwnd != 0:
        user32.ShowWindow(console_hwnd, 0)  # SW_HIDE

# 3. Setup Logging
def setup_logging():
    if getattr(sys, "frozen", False):
        base_dir = os.path.dirname(sys.executable)
    else:
        base_dir = os.path.dirname(os.path.abspath(__file__))
    log_path = os.path.join(base_dir, "app_debug.log")
    try:
        log_file = open(log_path, "w", encoding="utf-8", buffering=1)
        sys.stdout = log_file
        sys.stderr = log_file
    except Exception:
        pass

setup_logging()

# 4. Set JUPYTER_PATH explicitly in frozen environment
if getattr(sys, "frozen", False):
    internal_dir = os.path.join(os.path.dirname(sys.executable), "_internal")
    bundled_jupyter = os.path.join(internal_dir, "share", "jupyter")
    if os.path.exists(bundled_jupyter):
        os.environ["JUPYTER_PATH"] = bundled_jupyter

# Imports after guards
import webview
import streamlit.web.cli as stcli

def is_server_ready(host="127.0.0.1", port=8501):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(0.3)
            return s.connect_ex((host, port)) == 0
    except Exception:
        return False

def resolve_app_path():
    if getattr(sys, "frozen", False):
        base_dir = getattr(sys, "_MEIPASS", os.path.dirname(sys.executable))
        internal_dir = os.path.join(os.path.dirname(sys.executable), "_internal")
        target_dir = internal_dir if os.path.exists(internal_dir) else base_dir
        os.chdir(target_dir)
        candidate = os.path.join(target_dir, "app.py")
        if os.path.exists(candidate):
            return os.path.abspath(candidate)
    return os.path.abspath("app.py")

def start_streamlit_server(app_path):
    orig_signal = signal.signal
    def dummy_signal(sig, handler):
        try:
            return orig_signal(sig, handler)
        except ValueError:
            return None
    signal.signal = dummy_signal

    sys.argv = [
        "streamlit",
        "run",
        app_path,
        "--global.developmentMode=false",
        "--server.headless=true",
        "--server.port=8501",
        "--server.address=127.0.0.1",
        "--browser.serverAddress=127.0.0.1",
        "--server.enableCORS=false",
        "--server.enableXsrfProtection=false",
        "--server.enableStaticServing=true",
        "--server.fileWatcherType=none",
        "--browser.gatherUsageStats=false",
    ]
    try:
        stcli.main()
    except (SystemExit, Exception):
        pass

if __name__ == "__main__":
    app_path = resolve_app_path()
    server_thread = threading.Thread(
        target=start_streamlit_server,
        args=(app_path,),
        daemon=True
    )
    server_thread.start()

    start_time = time.time()
    while time.time() - start_time < 30:
        if is_server_ready("127.0.0.1", 8501):
            break
        time.sleep(0.1)

    window = webview.create_window(
        title="ein Bier 🍺",
        url="http://127.0.0.1:8501",
        width=850,
        height=650,
        resizable=False,
        fullscreen=False
    )
    webview.start()
    
    # Hard exit to cleanly kill all background threads
    os._exit(0)