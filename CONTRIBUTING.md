# Contributing

## Setup

Create a branch, then run from the repository root:

```sh
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt pre-commit
pre-commit install
```

## Validate changes

Run checks on the files you changed:

```sh
pre-commit run --files path/to/changed_file.py
git diff --check
```

For integration changes, copy `custom_components/crestron_home` into a test Home Assistant configuration, restart HA, and verify affected entities and logs.

For direct API troubleshooting, see the [debug script instructions](README.md#debug-script):

```sh
python scripts/crestron_debug.py --help
```

## Pull requests

Keep each change focused. Describe its effect and how you verified it. Use clear names, type hints, and comments only where the logic needs explanation.

For bug reports, include reproduction steps, Home Assistant and Crestron versions, and relevant logs without credentials.

Contributions are covered by the [MIT license](LICENSE).
