import os
import sys
import ctypes
import time
import base64
import subprocess
from PIL import Image
import streamlit as st
import streamlit.components.v1 as components
from core.converter import convert_ipynb_to_html


def resource_path(*parts):
    """Resolve a path in dev mode and inside a PyInstaller bundle (_internal / _MEIPASS)."""
    base = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, *parts)


def ask_save_path(initial_filename: str):
    """
    Returns the chosen save path, or None if cancelled. Raises RuntimeError on failure.
    1) pywebview's native dialog (same window as the app, so it can't open behind it)
    2) PowerShell + .NET SaveFileDialog as a fallback
    """
    downloads = os.path.join(os.path.expanduser("~"), "Downloads")
    if not os.path.isdir(downloads):
        downloads = os.path.expanduser("~")

    # 1) pywebview dialog (works because Streamlit runs in the same process as the window)
    try:
        import webview
        if webview.windows:
            save_type = webview.FileDialog.SAVE if hasattr(webview, "FileDialog") else webview.SAVE_DIALOG
            result = webview.windows[0].create_file_dialog(
                save_type,
                directory=downloads,
                save_filename=initial_filename,
                file_types=("HTML files (*.html)", "All files (*.*)"),
            )
            if not result:
                return None  # user cancelled
            return result if isinstance(result, str) else result[0]
    except Exception as e:
        print(f"pywebview dialog failed, falling back to PowerShell: {e}")

    if sys.platform != "win32":
        return os.path.join(downloads, initial_filename)

    # 2) PowerShell fallback
    ps_script = r"""
Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$owner = New-Object System.Windows.Forms.Form
$owner.TopMost = $true
$owner.ShowInTaskbar = $false
$owner.StartPosition = 'Manual'
$owner.Location = New-Object System.Drawing.Point(-32000, -32000)
$owner.Size = New-Object System.Drawing.Size(1, 1)
$owner.Show()
$owner.Activate()
$dlg = New-Object System.Windows.Forms.SaveFileDialog
$dlg.Title = 'Choose where to save your brew'
$dlg.Filter = 'HTML files (*.html)|*.html|All files (*.*)|*.*'
$dlg.DefaultExt = 'html'
$dlg.AddExtension = $true
$dlg.OverwritePrompt = $true
$dlg.FileName = $env:BREW_FILENAME
if (Test-Path $env:BREW_DIR) { $dlg.InitialDirectory = $env:BREW_DIR }
if ($dlg.ShowDialog($owner) -eq [System.Windows.Forms.DialogResult]::OK) {
    Write-Output $dlg.FileName
}
$owner.Close()
$owner.Dispose()
"""
    encoded = base64.b64encode(ps_script.encode("utf-16-le")).decode("ascii")
    env = os.environ.copy()
    env["BREW_FILENAME"] = initial_filename
    env["BREW_DIR"] = downloads

    result = subprocess.run(
        ["powershell", "-NoProfile", "-NonInteractive", "-STA",
         "-ExecutionPolicy", "Bypass", "-EncodedCommand", encoded],
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=env,
        creationflags=subprocess.CREATE_NO_WINDOW,
        timeout=600,
    )
    if result.returncode != 0:
        err = result.stderr.decode("utf-8", errors="ignore").strip()
        raise RuntimeError(err or f"PowerShell exited with code {result.returncode}")

    path = result.stdout.decode("utf-8", errors="ignore").strip().lstrip("\ufeff")
    return path or None


# Fix Windows Taskbar grouping to display custom app icon instead of default Python console
if sys.platform == "win32":
    try:
        myappid = "einbier.rpg.converter.1.0"
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
    except Exception:
        pass

# Resolve absolute path for the desktop/app icon
icon_path = resource_path("static", "img", "wenz.ico")
app_icon = icon_path if os.path.exists(icon_path) else "🍺"

st.set_page_config(
    page_title="ein Bier",
    page_icon=app_icon,
    layout="centered"
)

# Custom animation function: Completely random toss (across the entire bottom width)
def toss_lingerie():
    components.html("""
    <script>
    (function() {
        const parentDoc = window.parent.document;

        if (!parentDoc.getElementById('lingerie-toss-keyframes')) {
            const style = parentDoc.createElement('style');
            style.id = 'lingerie-toss-keyframes';
            style.innerHTML = `
                @keyframes continuousArc {
                    0% {
                        transform: translate3d(0, 0, 0) rotate(0deg);
                        opacity: 0;
                    }
                    10% {
                        opacity: 1;
                    }
                    40% {
                        transform: translate3d(var(--fly-x-mid), var(--fly-y-peak), 0) rotate(var(--rot-mid));
                    }
                    90% {
                        opacity: 1;
                    }
                    100% {
                        transform: translate3d(var(--fly-x-end), 125vh, 0) rotate(var(--rot-end));
                        opacity: 0;
                    }
                }
            `;
            parentDoc.head.appendChild(style);
        }

        const container = parentDoc.createElement('div');
        container.style.position = 'fixed';
        container.style.top = '0';
        container.style.left = '0';
        container.style.width = '100vw';
        container.style.height = '100vh';
        container.style.pointerEvents = 'none';
        container.style.zIndex = '9999999';
        container.style.overflow = 'hidden';
        parentDoc.body.appendChild(container);

        const images = [
            '/app/static/img/panty%201.png',
            '/app/static/img/panty%202.png',
            '/app/static/img/panty%203.png',
            '/app/static/img/bra%201.jpg',
            '/app/static/img/bra%202.png',
            '/app/static/img/bra%203.png'
        ];

        const totalItems = 16; // زودنا العدد شوية عشان الانتشار يبان أغنى

        for (let i = 0; i < totalItems; i++) {
            const img = parentDoc.createElement('img');
            img.src = images[Math.floor(Math.random() * images.length)];
            img.style.position = 'absolute';

            img.style.width = (Math.random() * 15 + 60) + 'px';
            img.style.height = 'auto';
            img.style.imageRendering = 'pixelated';

            // بداية عشوائية تماماً تغطي كامل عرض الشاشة من تحت (من 2vw لـ 98vw) لضمان الرمي من كل حتة
            const spawnX = Math.random() * 96 + 2;
            img.style.left = spawnX + 'vw';
            img.style.bottom = '-100px';

            // ارتفاعات متنوعة ومختلفة لكل رمية
            const peakY = -(Math.random() * 30 + 40) + 'vh';
            
            // انحراف أفقي عشوائي واسع (يتحذف يمين أو شمال أو يطلع مستقيم) بناءً على نقطة البداية
            const midX = (Math.random() - 0.5) * 300 + 'px';
            const endX = (Math.random() - 0.5) * 500 + 'px';
            
            // درجات لف ودوران عشوائية لإعطاء حركة طبيعية في الهواء
            const midRot = (Math.random() - 0.5) * 360 + 'deg';
            const endRot = (Math.random() - 0.5) * 720 + 'deg';

            // سرعات مختلفة لعمل فوضى بصرية ممتعة
            const duration = (Math.random() * 0.8 + 2.0) + 's';

            img.style.setProperty('--fly-y-peak', peakY);
            img.style.setProperty('--fly-x-mid', midX);
            img.style.setProperty('--fly-x-end', endX);
            img.style.setProperty('--rot-mid', midRot);
            img.style.setProperty('--rot-end', endRot);

            img.style.animation = `continuousArc ${duration} ease-in-out forwards`;
            
            // تأخير عشوائي متباعد عشان الرمي يحصل ورا بعضه مش كله في نفس اللحظة
            const randomDelay = Math.random() * 1200;
            img.style.animationDelay = randomDelay + 'ms';

            container.appendChild(img);
        }

        setTimeout(() => {
            container.remove();
        }, 5200);
    })();
    </script>
    """, height=0, width=0)

# Initialize Session State across reruns
if "brewed_html" not in st.session_state:
    st.session_state.brewed_html = None
if "output_filename" not in st.session_state:
    st.session_state.output_filename = None

# 1. Inject Local RPGUI Stylesheet & Fixes for Streamlit
st.markdown("""
<link href="/app/static/rpgui.min.css" rel="stylesheet" type="text/css">

<style>
    /* Hide default Streamlit headers, menu, and footers */
    header[data-testid="stHeader"] {
        display: none !important;
    }

    [data-testid="stToolbar"] {
        display: none !important;
        visibility: hidden !important;
    }

    #MainMenu {
        visibility: hidden !important;
    }

    footer {
        visibility: hidden !important;
    }

    /* Global RPG pixel cursors */
    html, body, .stApp, * {
        cursor: url('/app/static/img/cursor/default.png'), auto !important;
    }

    button, input, label, a, [role="button"], [data-testid="stFileUploader"], .stCheckbox {
        cursor: url('/app/static/img/cursor/point.png') 10 0, pointer !important;
    }

    /* Atmospheric Tavern Background image with gradient overlay */
    .stApp {
        background-color: #0e0704;
        background-image: 
            linear-gradient(rgba(14, 7, 4, 0.78), rgba(8, 4, 2, 0.88)), 
            url('/app/static/img/tavern-bg.jpg') !important;
        background-size: cover !important;
        background-position: center !important;
        background-attachment: fixed !important;
        image-rendering: pixelated;
        font-family: 'Press Start 2P', cursive !important;
    }

    /* Constrain window width for retro arcade look */
    .block-container {
        max-width: 580px !important;
        min-width: 560px !important;
        padding-top: 2rem !important;
        padding-bottom: 2rem !important;
        margin: 0 auto !important;
    }

    @media (min-width: 768px) {
        .block-container {
            width: 580px !important;
        }
    }

    .rpgui-container {
        position: relative !important;
        width: 100% !important;
        margin: 0 auto 25px auto !important;
    }

    .quest-board {
        padding: 25px 20px !important;
    }

    /* Styled file uploader Parchment box */
    [data-testid="stFileUploader"] {
        background: rgba(20, 12, 8, 0.75) !important;
        border: 4px solid #5a3818 !important;
        border-radius: 4px !important;
        padding: 15px !important;
        box-shadow: inset 0 0 10px #000000 !important;
    }

    [data-testid="stFileUploader"] section {
        background-color: transparent !important;
    }

    [data-testid="stFileUploader"] span, 
    [data-testid="stFileUploader"] small, 
    [data-testid="stFileUploader"] label {
        color: #e6c280 !important;
        text-shadow: 1px 1px 0px #000 !important;
    }

    /* Wooden Dropzone Upload Button */
    [data-testid="stFileUploaderDropzone"] button {
        background: url('/app/static/img/button.png') no-repeat center center !important;
        background-size: 100% 100% !important;
        border: none !important;
        font-family: 'Press Start 2P', cursive !important;
        font-size: 0.65rem !important;
        color: #ffffff !important;
        height: 44px !important;
        min-width: 120px !important;
        padding: 0 16px !important;
        text-shadow: 1px 1px 0px #000 !important;
        image-rendering: pixelated;
        display: inline-flex !important;
        align-items: center !important;
        justify-content: center !important;
        line-height: normal !important;
        cursor: pointer !important;
    }

    [data-testid="stFileUploaderDropzone"] button:hover {
        background-image: url('/app/static/img/button-hover.png') !important;
        color: #ffe066 !important;
    }

    [data-testid="stFileUploaderDropzone"] button:active {
        background-image: url('/app/static/img/button-down.png') !important;
    }

    [data-testid="stFileUploaderDropzone"] button svg {
        display: none !important;
    }

    [data-testid="stFileUploaderDropzone"] button > div {
        display: inline-block !important;
    }

    /* Crimson Clear Button */
    button[data-testid="stBaseButton-minimal"] {
        background: #501010 !important;
        border: 2px solid #ff4d4d !important;
        box-shadow: inset -2px -2px 0px 0px #200000, inset 2px 2px 0px 0px #aa2020 !important;
        border-radius: 0px !important;
        width: 30px !important;
        min-width: 30px !important;
        max-width: 30px !important;
        height: 30px !important;
        padding: 0 !important;
        margin: 0 0 0 10px !important;
        display: inline-flex !important;
        align-items: center !important;
        justify-content: center !important;
        position: relative !important;
        image-rendering: pixelated !important;
        cursor: pointer !important;
    }

    button[data-testid="stBaseButton-minimal"] svg,
    button[data-testid="stBaseButton-minimal"] * {
        display: none !important;
    }

    button[data-testid="stBaseButton-minimal"]::after {
        content: "✕" !important;
        display: block !important;
        font-family: 'Press Start 2P', monospace !important;
        font-size: 0.7rem !important;
        color: #ffffff !important;
        text-shadow: 1px 1px 0px #000000 !important;
        line-height: 1 !important;
    }

    button[data-testid="stBaseButton-minimal"]:hover {
        background: #801818 !important;
        border-color: #ff7777 !important;
    }

    button[data-testid="stBaseButton-minimal"]:active {
        box-shadow: inset 2px 2px 0px 0px #200000, inset -2px -2px 0px 0px #aa2020 !important;
    }

    /* Primary Action Button (Wooden RPG Style) */
    div.stButton > button:first-child {
        background: url('/app/static/img/button.png') no-repeat center !important;
        background-size: 100% 100% !important;
        border: none !important;
        color: #ffffff !important;
        font-family: 'Press Start 2P', cursive !important;
        font-size: 0.95rem !important;
        height: 60px !important;
        padding: 0 25px !important;
        text-shadow: 2px 2px 0px #000 !important;
        box-shadow: none !important;
        image-rendering: pixelated;
    }

    div.stButton > button:first-child:hover {
        background-image: url('/app/static/img/button-hover.png') !important;
        color: #ffe066 !important;
    }

    div.stButton > button:first-child:active {
        background-image: url('/app/static/img/button-down.png') !important;
    }

    /* Golden Action Button (Used for Download/Save) */
    .golden-button div.stButton > button:first-child {
        background: url('/app/static/img/button-golden.png') no-repeat center !important;
        background-size: 100% 100% !important;
        border: none !important;
        color: #ffeaa7 !important;
        font-family: 'Press Start 2P', cursive !important;
        font-size: 0.82rem !important;
        height: 60px !important;
        padding: 0 20px !important;
        text-shadow: 2px 2px 0px #000 !important;
        image-rendering: pixelated;
    }

    .golden-button div.stButton > button:first-child:hover {
        background-image: url('/app/static/img/button-golden-hover.png') !important;
    }

    .stCheckbox label span {
        color: #eeddcc !important;
        font-size: 0.85rem !important;
        text-shadow: 1px 1px 0px #000 !important;
    }

    /* Retro RPG Saved notification container using border-image */
    .rpg-saved-box {
        border-style: solid !important;
        border-width: 16px !important;
        border-image: url('/app/static/img/border-image.png') 16 16 16 16 repeat !important;
        background: rgba(14, 7, 4, 0.92) !important;
        padding: 12px 14px !important;
        margin-top: 15px !important;
        image-rendering: pixelated;
        word-break: break-all;
        box-sizing: border-box;
    }

    .rpg-saved-title {
        color: #ffcc66 !important;
        font-family: 'Press Start 2P', cursive !important;
        font-size: 0.72rem !important;
        text-shadow: 1px 1px 0px #000 !important;
        margin-bottom: 8px !important;
    }

    .rpg-saved-path {
        color: #e6c280 !important;
        font-family: 'Press Start 2P', monospace !important;
        font-size: 0.55rem !important;
        line-height: 1.4 !important;
        text-shadow: 1px 1px 0px #000 !important;
    }
</style>
""", unsafe_allow_html=True)

# 2. Hero Header & Board
st.markdown("""
<div class="rpgui-content" style="position: relative; overflow: visible; height: auto;">
    <div class="rpgui-container framed-golden quest-board">
        <h1 style="color: #f7d070; font-size: 1.4rem; text-shadow: 2px 2px #000; margin-bottom: 12px; text-align: center;">
            🍺 ein Bier 🍺
        </h1>
        <p style="font-size: 0.65rem; color: #ffb84d; text-align: center; margin-top: 8px;">
            Brewing raw notebooks (.ipynb) into crisp HTML reports.
        </p>
        <hr class="golden">
    </div>
</div>
""", unsafe_allow_html=True)

# 3. Main Action Container
st.markdown("""
<div class="rpgui-content" style="position: relative; overflow: visible; height: auto;">
    <div class="rpgui-container framed" style="padding: 15px;">
        <p style="font-size: 0.75rem; color: #ffcc66; text-shadow: 1px 1px #000; margin-bottom: 10px;">
            Insert (.ipynb)
        </p>
    </div>
</div>
""", unsafe_allow_html=True)

uploaded_file = st.file_uploader(
    "Drop your spellbook (.ipynb)",
    type=["ipynb"],
    label_visibility="collapsed",
    help="Upload your notebook file to start brewing."
)

hide_code = st.checkbox("Hide spells code (outputs & charts only)")

# Reset session state whenever uploader is cleared
if uploaded_file is None:
    st.session_state.brewed_html = None
    st.session_state.output_filename = None

action_slot = st.empty()

# Execute conversion routine
if uploaded_file is not None and st.session_state.brewed_html is None:
    with action_slot.container():
        if st.button("🍻 sip", type="primary", use_container_width=True):
            try:
                action_slot.empty()
                with action_slot.container():
                    progress_bar = st.progress(0, text="Fermenting your notebook... Wenz: 0%")
                    for percent_complete in range(1, 101):
                        time.sleep(0.012)
                        progress_bar.progress(
                            percent_complete,
                            text=f"Wenz: {percent_complete}%"
                        )
                    time.sleep(0.15)
                    progress_bar.empty()

                    # Cache output inside session state
                    st.session_state.brewed_html = convert_ipynb_to_html(
                        notebook_bytes=uploaded_file.getvalue(),
                        exclude_code=hide_code
                    )
                    st.session_state.output_filename = uploaded_file.name.replace(".ipynb", ".html")
                    st.rerun()
            except Exception as e:
                st.error(f"The brew spoiled: {e}")

# Save section using native Windows file dialog (PowerShell + .NET SaveFileDialog, no tkinter)
if st.session_state.brewed_html is not None:
    st.markdown('<div class="golden-button">', unsafe_allow_html=True)
    if st.button("atmnalk shantafa lazeza 🍺", use_container_width=True):
        try:
            file_path = ask_save_path(st.session_state.output_filename)
        except Exception as e:
            file_path = None
            st.error(f"Could not open the save dialog: {e}")

        # pywebview doesn't always append the extension
        if file_path and not os.path.splitext(file_path)[1]:
            file_path += ".html"

        if file_path:
            content = st.session_state.brewed_html
            content_to_write = content if isinstance(content, str) else content.decode("utf-8")
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content_to_write)

            # Fire the fluid arc toss animation across full bottom width
            toss_lingerie()

            # Render custom RPG border-image container with "etlatsh?"
            st.markdown(f"""
            <div class="rpgui-content" style="position: relative; overflow: visible;">
                <div class="rpg-saved-box">
                    <div class="rpg-saved-title" style="color: #66ff66 !important; font-size: 0.85rem !important; margin-bottom: 10px;">
                        🍻 etlatsh?
                    </div>
                    <div class="rpg-saved-title">Saved to:</div>
                    <div class="rpg-saved-path">{file_path}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)