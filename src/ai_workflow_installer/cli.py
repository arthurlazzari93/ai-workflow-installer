"""Console entrypoint for installing workflow docs into a repository."""

from __future__ import annotations

import runpy
import sys
from importlib.resources import as_file, files


def main() -> int:
    script = files("ai_workflow_installer").joinpath("skill_bundle/scripts/install_ai_workflow.py")
    with as_file(script) as script_path:
        sys.argv = ["ai-workflow", *sys.argv[1:]]
        runpy.run_path(str(script_path), run_name="__main__")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
