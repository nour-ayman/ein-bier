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


def convert_ipynb_to_html(notebook_path: str) -> str:
    """
    Converts a Jupyter Notebook (.ipynb) to a standalone HTML string.
    Safely resolves template paths to prevent 'no template sub-directory' errors.
    """
    # 1. Inject JUPYTER_PATH dynamically into the environment
    jupyter_dir = get_jupyter_data_dir()
    if jupyter_dir:
        os.environ["JUPYTER_PATH"] = jupyter_dir

    # 2. Check for explicit template folder
    template_dir = None
    if jupyter_dir:
        cand_templates = os.path.join(jupyter_dir, "nbconvert", "templates")
        if os.path.exists(cand_templates):
            template_dir = cand_templates

    # 3. Read the notebook file
    with open(notebook_path, "r", encoding="utf-8") as f:
        nb = nbformat.read(f, as_version=4)

    # 4. Initialize HTMLExporter with classic template and extra search path
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
        # Fallback to 'basic' template if classic assets have any issue
        print(f"Warning: Falling back to basic template due to: {exc}")
        if template_dir:
            exporter = HTMLExporter(
                template_name="basic",
                extra_template_basedirs=[template_dir]
            )
        else:
            exporter = HTMLExporter(template_name="basic")

        body, _ = exporter.from_notebook_node(nb)
        return body