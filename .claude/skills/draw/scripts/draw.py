"""Draw a cartoon architecture diagram: python draw.py spec.yaml  ->  spec.html, spec.svg, spec.png"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from archdraw.cli import main  # noqa: E402

if __name__ == "__main__":
    sys.exit(main())
