"""
Thin backwards-compatible entry point: `python3 ynified_cli.py ...`
The real CLI lives in ynified.cli (also installed as the `ynified`
console script, see pyproject.toml).
"""
import sys

from ynified.cli import main

if __name__ == "__main__":
    sys.exit(main())
