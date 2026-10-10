import os
import sys
import html
import base64
import nbformat
from nbconvert import HTMLExporter

def get_template_dirs():
    dirs = []
    if getattr(sys, "frozen", False):
        base_dir = os.path.join(os.path.dirname(sys.executable), "_internal")
    else:
        base_dir = sys.prefix

    cand = os.path.join(base_dir, "share", "jupyter", "nbconvert", "templates")
    if os.path.exists(cand):
        dirs.append(cand)
    return dirs

def render_fallback_html(nb) -> str:
    """Built-in basic renderer if nbconvert templates fail completely."""
    parts = ["<!DOCTYPE html><html><head><meta charset='utf-8'><title>Notebook</title>",
             "<style>body{font-family:sans-serif;margin:40px;line-height:1.6}pre{background:#f4f4f4;padding:10px;border-radius:4px;overflow-x:auto}img{max-width:100%}</style></head><body>"]
    for cell in nb.get("cells", []):
        cell_type = cell.get("cell_type", "")
        source = "".join(cell.get("source", ""))
        if cell_type == "markdown":
            parts.append(f"<div>{html.escape(source)}</div>")
        elif cell_type == "code":
            parts.append(f"<pre><code>{html.escape(source)}</code></pre>")
            for out in cell.get("outputs", []):
                data = out.get("data", {})
                if "text/plain" in data:
                    parts.append(f"<pre style='color:#555'>{html.escape(''.join(data['text/plain']))}</pre>")
                if "image/png" in data:
                    parts.append(f"<img src='data:image/png;base64,{data['image/png']}' />")
    parts.append("</body></html>")
    return "\n".join(parts)

def convert_ipynb_to_html(notebook_bytes=None, notebook_path=None, **kwargs) -> str:
    if notebook_bytes is not None:
        nb_str = notebook_bytes.decode("utf-8") if isinstance(notebook_bytes, bytes) else str(notebook_bytes)
        nb = nbformat.reads(nb_str, as_version=4)
    elif notebook_path is not None:
        with open(notebook_path, "r", encoding="utf-8") as f:
            nb = nbformat.read(f, as_version=4)
    else:
        raise ValueError("Either notebook_bytes or notebook_path must be provided.")

    template_dirs = get_template_dirs()
    for tpl in ["lab", "classic", "basic"]:
        try:
            kwargs_exp = {"template_name": tpl}
            if template_dirs:
                kwargs_exp["extra_template_basedirs"] = template_dirs
            exporter = HTMLExporter(**kwargs_exp)
            body, _ = exporter.from_notebook_node(nb)
            return body
        except Exception:
            continue

    return render_fallback_html(nb)