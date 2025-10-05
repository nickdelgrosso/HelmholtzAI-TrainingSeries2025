"""
This script converts Jupyter notebooks (.ipynb) from the 'notebooks' directory into Markdown files for a static site.
It processes each notebook, extracting markdown, code, and output cells, and writes them as Markdown files to the
'site/content' directory, preserving the directory structure. ANSI color codes in error tracebacks are removed.
Special handling is provided for 'index' notebooks, renaming them to '_index.md' for site compatibility.
Workflow:
- Recursively find all .ipynb files in the source directory.
- For each notebook:
    - Parse notebook JSON.
    - For each cell:
        - Markdown cells: append as-is.
        - Code cells: format code blocks and outputs, handling errors and execution results.
        - Raw cells: append as-is.
        - Unimplemented cell/output types are reported.
    - Write the processed content to a Markdown file in the destination directory.


Todo:
  - Export images from markdown cells, so they render both in VSCode's Notebook viewer and in the hugo site as Assets
  - Export images from output cells (basically, matplotlib plots).
"""

import json
import re
from pathlib import Path

src = Path("notebooks")
dst = Path("site/content/docs")

ansi_escape = re.compile(
    r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])"
)  # for getting rid of ansi color codes in error tracebacks


for nb_path in src.rglob("*.ipynb"):
    rel = nb_path.relative_to(src)
    outdir = dst / rel.parent
    outdir.mkdir(parents=True, exist_ok=True)

    # # Load notebook (with outputs already inside)
    data = json.loads(nb_path.read_text())

    out_sections = []

    for cell in data["cells"]:
        match cell["cell_type"]:
            case "raw":
                out = "".join(cell["source"])
                out_sections.append(out)

            case "markdown":
                source = cell["source"]
                out_sections.append("".join(source))

            case "code":
                source = cell["source"]
                language = data["metadata"]["kernelspec"]["language"]
                source_text = f"```{language}\n{''.join(s for s in source)}\n```"
                out_sections.append(source_text)
                for output in cell["outputs"]:
                    match output["output_type"]:
                        case "execute_result":
                            out = f"```\n{''.join(output['data']['text/plain'])}\n```"
                            out_sections.append(out)
                        case "error":
                            out = f"```\n{''.join(ansi_escape.sub('', o) + '\n' for o in output['traceback'])}\n```"
                            out_sections.append(out)
                        case other:
                            print(f"Output Type Not Implemeneted: {other}")

            case other:
                print(f"Not yet implemented cell type: {other}")

    # Fix Page Bundle Indices
    if rel.stem == "index":
        rel = rel.with_stem("_index")

    out_md = outdir / rel.with_suffix(".md").name
    print(out_md)
    out_md.write_text("\n\n".join(out_sections))
