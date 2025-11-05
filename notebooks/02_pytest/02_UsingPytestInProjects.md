# Exercise — convert notebook to a proper package + tests

Goal: take the code and tests from the notebook `01_xxx.ipynb` and turn them into a small git repository with a src/ layout and runnable tests.

Tasks
1. Create a new repo (git init) and project layout:
    - src/<your_pkg>/...  (move library code here)
    - tests/...           (move test cells here as regular .py test files)
    - pyproject.toml
    - README.md, .gitignore

2. Extract code/tests from the notebook:
    - open the notebook, copy library-code cells into modules under src/<your_pkg>/ (e.g. src/<your_pkg>/module.py).
    - copy test cells into tests/test_*.py files, adapt imports to use your package (from <your_pkg> import ...).

3. Minimal pyproject.toml (supports editable install with pip install -e .)
    - Example:
      ```
      [build-system]
      requires = ["setuptools>=61.0", "wheel"]
      build-backend = "setuptools.build_meta"

      [project]
      name = "hhai-workshop"
      version = "0.0.0"
      requires-python = ">=3.8"
      dependencies = []

      [project.optional-dependencies]
      test = ["pytest"]
      
      [tool.setuptools.packages.find]
      where = ["src"]
      ```
    - Install for development: python -m pip install -e ".[test]"

4. Verify
    - Activate your venv, install editable package as above.
    - Run pytest at repo root: pytest
    - All tests should run and pass.

Concise notes
- Use src/ layout so tests import the installed package instead of relative file paths.
- setuptools >= 61 implements PEP 660 editable installs; the pyproject example above is enough for pip install -e .
- To convert many notebook cells quickly, nbconvert/export or manual copy/paste are common.

References
- Packaging docs (pyproject / project metadata): https://packaging.python.org/en/latest/
- PEP 621 (project metadata in pyproject.toml): https://peps.python.org/pep-0621/
- Editable installs (PEP 660): https://peps.python.org/pep-0660/

Deliverable
- A git repo with src/, tests/, pyproject.toml, and instructions in README.md showing how to install and run pytest.

GitHub Copilot