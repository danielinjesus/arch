"""Pictures from a short spec: python vis.py spec.yaml. The spec's `kind:` picks arch, xref, mindmap or graph."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from visdraw.cli import main  # noqa: E402

if __name__ == "__main__":
    sys.exit(main())
