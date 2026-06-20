#!/usr/bin/env python3
"""SmartStudy RAG Windows installer — standalone console exe."""
from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import tempfile
import urllib.request
import zipfile
from pathlib import Path

VERSION = "1.0.0"
DEFAULT_BASE = Path(r"C:\SmartStudy_RAG")
COMPOSE_URL = "https://raw.githubusercontent.com/Ffgags13/SmartStudy_RAG/main/docker-compose.pull.yml"
ZIP_URL = "https://github.com/Ffgags13/SmartStudy_RAG/archive/refs/heads/main.zip"
BACKEND_IMAGE = "ghcr.io/ffgags13/smartstudy-rag-backend:latest"


def log(msg: str) -> None:
    print(f"\n==> {msg}")


def run(cmd: list[str], cwd: Path | None = None) -> int:
    print(f"$ {' '.join(cmd)}")
    return subprocess.call(cmd, cwd=cwd, shell=False)


def docker_ok() -> bool:
    return run(["docker", "info"]) == 0


def download(url: str, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    with urllib.request.urlopen(url, timeout=120) as resp, open(dest, "wb") as f:
        shutil.copyfileobj(resp, f)


def install_pull(base: Path) -> None:
    log("Pull-only: docker-compose + GHCR images")
    compose = base / "docker-compose.yml"
    download(COMPOSE_URL, compose)
    env = os.environ.copy()
    env["COMPOSE_BAKE"] = "false"
    subprocess.check_call(["docker", "compose", "pull"], cwd=base, env=env)
    subprocess.check_call(["docker", "compose", "up", "-d"], cwd=base, env=env)


def install_zip(base: Path) -> Path:
    log("Download ZIP from GitHub")
    with tempfile.TemporaryDirectory() as td:
        zpath = Path(td) / "repo.zip"
        download(ZIP_URL, zpath)
        target = base / "SmartStudy_RAG-main"
        if target.exists():
            shutil.rmtree(target)
        with zipfile.ZipFile(zpath) as zf:
            zf.extractall(base)
    return target


def install_local(src: Path, base: Path) -> Path:
    log(f"Copy local repo: {src}")
    if not (src / "docker-compose.yml").exists():
        raise SystemExit(f"Not a SmartStudy repo: {src}")
    target = base / "SmartStudy_RAG-main"
    if target.exists():
        shutil.rmtree(target)
    shutil.copytree(src, target)
    return target


def compose_build(project: Path) -> None:
    env = os.environ.copy()
    env["COMPOSE_BAKE"] = "false"
    subprocess.check_call(["docker", "compose", "up", "--build", "-d"], cwd=project, env=env)


def try_pull() -> bool:
    log("Try GHCR backend image")
    return run(["docker", "pull", BACKEND_IMAGE]) == 0


def main() -> int:
    parser = argparse.ArgumentParser(description="SmartStudy RAG Setup")
    parser.add_argument("--base", type=Path, default=DEFAULT_BASE)
    parser.add_argument("--local", type=Path, default=None, help="Local repo path (no GitHub)")
    parser.add_argument("--build-only", action="store_true")
    parser.add_argument("--pull-only", action="store_true")
    parser.add_argument("--version", action="version", version=f"SmartStudy Setup {VERSION}")
    args = parser.parse_args()

    print(f"\n SmartStudy RAG Setup v{VERSION}\n Base: {args.base}\n")

    if shutil.which("docker") is None:
        print("ERROR: Docker not found. Install Docker Desktop.", file=sys.stderr)
        return 1

    if not docker_ok():
        print("ERROR: Docker Engine not running.", file=sys.stderr)
        return 1

    args.base.mkdir(parents=True, exist_ok=True)
    local = args.local or (Path(os.environ["SMARTSTUDY_LOCAL_REPO"]) if os.environ.get("SMARTSTUDY_LOCAL_REPO") else None)

    try:
        if args.pull_only:
            install_pull(args.base)
        elif not args.build_only and try_pull():
            install_pull(args.base)
        else:
            if local and local.exists():
                project = install_local(local, args.base)
            else:
                try:
                    project = install_zip(args.base)
                except Exception as e:
                    print("\nGitHub unavailable. Use --local C:\\path\\to\\SmartStudy_RAG", file=sys.stderr)
                    print(f"  ({e})", file=sys.stderr)
                    return 1
            compose_build(project)
    except subprocess.CalledProcessError as e:
        print(f"\nERROR: command failed (exit {e.returncode})", file=sys.stderr)
        return e.returncode or 1

    print("\n Done.\n   UI:  http://localhost:8501\n   API: http://localhost:8000/docs\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
