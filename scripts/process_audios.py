#!/usr/bin/env python
"""
Deprecated wrapper kept for backward compatibility.

Use:
    python run_daia.py <audio_file_or_directory>
"""

import sys

from run_daia import run


if __name__ == "__main__":
    print("'process_audios.py' está deprecado. Usa 'python run_daia.py <audio>'", file=sys.stderr)
    sys.exit(run(sys.argv[1:]))
