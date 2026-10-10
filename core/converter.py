import nbformat
from nbconvert import HTMLExporter

def convert_ipynb_to_html(notebook_bytes: bytes, exclude_code: bool = False) -> str:
    """
    Takes raw notebook bytes and converts them into standalone HTML string.
    """
    # 1. Parse the notebook JSON from bytes
    nb = nbformat.reads(notebook_bytes.decode("utf-8"), as_version=4)

    # 2. Configure the HTML exporter
    html_exporter = HTMLExporter()
    if exclude_code:
        html_exporter.exclude_input = True

    # 3. Export to HTML string
    body, _ = html_exporter.from_notebook_node(nb)
    return body