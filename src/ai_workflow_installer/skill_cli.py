"""Install bundled Codex skills into CODEX_HOME."""

from __future__ import annotations

import argparse
import os
import shutil
from importlib.resources import files
from pathlib import Path
from typing import Iterable

SKILL_NAME = "ai-workflow-installer"


def default_codex_home() -> Path:
    return Path(os.environ.get("CODEX_HOME", Path.home() / ".codex")).expanduser()


def copy_resource_tree(resource, destination: Path) -> None:
    destination.mkdir(parents=True, exist_ok=True)
    for child in resource.iterdir():
        target = destination / child.name
        if child.is_dir():
            copy_resource_tree(child, target)
        else:
            target.write_bytes(child.read_bytes())


def install_skill(codex_home: Path, *, force: bool) -> Path:
    skills_dir = codex_home.expanduser() / "skills"
    target = skills_dir / SKILL_NAME
    if target.exists():
        if not force:
            raise SystemExit(f"Skill already installed at {target}. Use --force to replace it.")
        shutil.rmtree(target)
    bundle = files("ai_workflow_installer").joinpath("skill_bundle")
    copy_resource_tree(bundle, target)
    return target


def list_skills(codex_home: Path) -> Iterable[str]:
    skills_dir = codex_home.expanduser() / "skills"
    if not skills_dir.exists():
        return []
    return sorted(path.name for path in skills_dir.iterdir() if path.is_dir())


def main() -> int:
    parser = argparse.ArgumentParser(prog="ai-skills", description="Manage bundled AI workflow skills.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    install = subparsers.add_parser("install", help="Install a bundled skill into Codex.")
    install.add_argument("name", choices=[SKILL_NAME])
    install.add_argument("--codex-home", type=Path, default=default_codex_home())
    install.add_argument("--force", action="store_true")

    list_cmd = subparsers.add_parser("list", help="List skills in CODEX_HOME.")
    list_cmd.add_argument("--codex-home", type=Path, default=default_codex_home())

    path_cmd = subparsers.add_parser("path", help="Print the Codex skills directory.")
    path_cmd.add_argument("--codex-home", type=Path, default=default_codex_home())

    args = parser.parse_args()

    if args.command == "install":
        target = install_skill(args.codex_home, force=args.force)
        print(f"Installed {SKILL_NAME} at {target}")
        return 0

    if args.command == "list":
        for name in list_skills(args.codex_home):
            print(name)
        return 0

    if args.command == "path":
        print(args.codex_home.expanduser() / "skills")
        return 0

    parser.error("unknown command")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
