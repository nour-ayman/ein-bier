import os
import sys
import time
import socket
import threading
import signal
import multiprocessing
import webview
import streamlit.web.cli as stcli


# --- LOGGING SETUP ---
def setup_logging():
    if getattr(sys, "frozen", False):
        base_dir = os.path.dirname(sys.executable)
    else:
        base_dir = os.path.dirname(os.path.abspath(__file__))

    log_path = os.path.join(base_dir, "app_debug.log")
    log_file = open(log_path, "w", encoding="utf-8", buffering=1)

    sys.stdout = log_file
    sys.stderr = log_file
    print(f"App started. Python executable: {sys.executable}")
    print(f"Base dir: {base_dir}")


def is_server_ready(host="127.0.0.1", port=8501):
    """Check if the Streamlit server socket is actively listening."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(0.3)
            return s.connect_ex((host, port)) == 0
    except Exception as e:
        print(f"Socket probe error: {e}")
        return False


def resolve_app_path():
    """
    Locate app.py reliably and switch the working directory to
    ensure Streamlit finds its internal assets and bundled core modules.
    """
    if getattr(sys, "frozen", False):
        base_dir = getattr(sys, "_MEIPASS", os.path.dirname(sys.executable))
        internal_dir = os.path.join(os.path.dirname(sys.executable), "_internal")

        # PyInstaller --onedir mode places bundled files inside _internal
        if os.path.exists(internal_dir):
            os.chdir(internal_dir)
            candidate = os.path.join(internal_dir, "app.py")
            if os.path.exists(candidate):
                return os.path.abspath(candidate)
        else:
            os.chdir(base_dir)
            candidate = os.path.join(base_dir, "app.py")
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
        "--server.enableStaticServing=true",   # NEW: serves /app/static/*
        "--server.fileWatcherType=none",       # NEW: no file watcher needed in a frozen app
        "--browser.gatherUsageStats=false",    # NEW: no telemetry prompt
    ]
    try:
        print(f"Starting Streamlit CLI with app: {app_path}")
        stcli.main()
    except SystemExit as e:
        print(f"Streamlit stopped with exit code: {e}")
    except Exception as e:
        print(f"Streamlit server encountered error: {e}")


if __name__ == "__main__":
    # Prevent Windows PyInstaller subprocess infinite loop
    multiprocessing.freeze_support()

    # Initialize file logging
    setup_logging()

    app_path = resolve_app_path()
    print(f"Resolved app path: {app_path}")
    print(f"Current working directory: {os.getcwd()}")

    # Start Streamlit in a daemon thread
    server_thread = threading.Thread(
        target=start_streamlit_server,
        args=(app_path,),
        daemon=True
    )
    server_thread.start()

    # Wait for the local server port to open
    start_time = time.time()
    while time.time() - start_time < 25:
        if is_server_ready("127.0.0.1", 8501):
            print("Streamlit server is ready on 127.0.0.1:8501.")
            break
        time.sleep(0.1)
    else:
        print("Warning: Timed out waiting for Streamlit server.")

    # Create and start the webview window
    print("Launching pywebview window...")
    window = webview.create_window(
        title="ein Bier 🍺",
        url="http://127.0.0.1:8501",
        width=850,
        height=650,
        resizable=False,
        fullscreen=False
    )
    webview.start()
    print("Webview closed. Terminating.")

    sys.exit(0)