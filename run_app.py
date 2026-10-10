import os
import sys
import time
import socket
import threading
import signal
import multiprocessing
import ctypes
import webview
import streamlit.web.cli as stcli

# --- إخفاء نافذة الـ Console فوراً إذا كانت مفتوحة ---
if sys.platform == "win32":
    hwnd = ctypes.windll.kernel32.GetConsoleWindow()
    if hwnd != 0:
        ctypes.windll.user32.ShowWindow(hwnd, 0)  # 0 = SW_HIDE


# --- LOGGING SETUP ---
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


def is_server_ready(host="127.0.0.1", port=8501):
    """Check if the Streamlit server socket is actively listening."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(0.3)
            return s.connect_ex((host, port)) == 0
    except Exception:
        return False


def resolve_app_path():
    """
    Locate app.py reliably and switch the working directory to
    ensure Streamlit finds its internal assets and bundled core modules.
    Also inject JUPYTER_PATH so nbconvert finds bundled templates.
    """
    if getattr(sys, "frozen", False):
        base_dir = getattr(sys, "_MEIPASS", os.path.dirname(sys.executable))
        internal_dir = os.path.join(os.path.dirname(sys.executable), "_internal")

        target_dir = internal_dir if os.path.exists(internal_dir) else base_dir
        os.chdir(target_dir)

        # حل مشكلة قوالب nbconvert (lab template) بتحديد مسار jupyter المدمج
        bundled_jupyter = os.path.join(target_dir, "share", "jupyter")
        if os.path.exists(bundled_jupyter):
            os.environ["JUPYTER_PATH"] = bundled_jupyter

        candidate = os.path.join(target_dir, "app.py")
        if os.path.exists(candidate):
            return os.path.abspath(candidate)

    return os.path.abspath("app.py")


def start_streamlit_server(app_path):
    """Run Streamlit in a thread without crashing Windows signals."""
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
    # منع التكرار اللانهائي للعمليات في Windows PyInstaller
    multiprocessing.freeze_support()

    setup_logging()

    app_path = resolve_app_path()

    # تشغيل سيرفر Streamlit في Daemon Thread
    server_thread = threading.Thread(
        target=start_streamlit_server,
        args=(app_path,),
        daemon=True
    )
    server_thread.start()

    # انتظار فتح بورت السيرفر محلياً
    start_time = time.time()
    while time.time() - start_time < 25:
        if is_server_ready("127.0.0.1", 8501):
            break
        time.sleep(0.1)

    # فتح نافذة التطبيق الرسومية فقط
    window = webview.create_window(
        title="ein Bier 🍺",
        url="http://127.0.0.1:8501",
        width=850,
        height=650,
        resizable=False,
        fullscreen=False
    )
    webview.start()

    sys.exit(0)