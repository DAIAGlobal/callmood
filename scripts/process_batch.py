#!/usr/bin/env python3
"""
Deprecated wrapper for batch processing.
Use: python run_daia.py <carpeta>
"""

import sys

from run_daia import run

if __name__ == "__main__":
    print("'process_batch.py' está deprecado. Usa 'python run_daia.py <carpeta>'", file=sys.stderr)
    sys.exit(run(sys.argv[1:]))
