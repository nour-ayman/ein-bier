import io
import os
import sys
import nbformat
from nbconvert import HTMLExporter


def get_jupyter_data_dir():
    """
    Locates the bundled jupyter data directory containing nbconvert templates.
    Works seamlessly both in local development and inside PyInstaller's _internal directory.
    """
    if getattr(sys, "frozen", False):
        base_dir = os.path.join(os.path.dirname(sys.executable), "_internal")
    else:
        base_dir = sys.prefix

    jupyter_dir = os.path.join(base_dir, "share", "jupyter")
    return jupyter_dir if os.path.exists(jupyter_dir) else None


def convert_ipynb_to_html(notebook_bytes=None, notebook_path=None, **kwargs) -> str:
    """
    Converts Jupyter Notebook to standalone HTML.
    Supports either notebook_bytes (from Streamlit uploader) or a local notebook_path.
    """
    # 1. Set environment variable for jupyter templates
    jupyter_dir = get_jupyter_data_dir()
    if jupyter_dir:
        os.environ["JUPYTER_PATH"] = jupyter_dir

    template_dir = None
    if jupyter_dir:
        cand_templates = os.path.join(jupyter_dir, "nbconvert", "templates")
        if os.path.exists(cand_templates):
            template_dir = cand_templates

    # 2. Parse notebook from bytes or file path
    if notebook_bytes is not None:
        if isinstance(notebook_bytes, bytes):
            notebook_str = notebook_bytes.decode("utf-8")
        else:
            notebook_str = str(notebook_bytes)
        nb = nbformat.reads(notebook_str, as_version=4)
    elif notebook_path is not None:
        with open(notebook_path, "r", encoding="utf-8") as f:
            nb = nbformat.read(f, as_version=4)
    else:
        raise ValueError("Either notebook_bytes or notebook_path must be provided.")

    # 3. Export to HTML using classic or fallback to basic
    try:
        if template_dir:
            exporter = HTMLExporter(
                template_name="classic",
                extra_template_basedirs=[template_dir]
            )
        else:
            exporter = HTMLExporter(template_name="classic")

        body, _ = exporter.from_notebook_node(nb)
        return body

    except Exception as exc:
        print(f"Classic template failed ({exc}), falling back to basic template.")
        if template_dir:
            exporter = HTMLExporter(
                template_name="basic",
                extra_template_basedirs=[template_dir]
            )
        else:
            exporter = HTMLExporter(template_name="basic")

        body, _ = exporter.from_notebook_node(nb)
        return body