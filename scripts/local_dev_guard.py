#!/usr/bin/env python3
"""doraemon-local-dev-guard: read-only local environment guard.

Responsibilities (and ONLY these):
  1. lightweight environment audit
  2. smart path discovery / recommendation
  3. minimal risk pre-check

It never executes delivery work, never retries loops, never modifies the
environment, and never makes network or model calls. If this guard is absent,
a task may proceed under its own hard rules. Delivery / scheduling /
acceptance belongs to doraemon-goal-driven-delivery.

Standard library only. Cross-platform (Windows / macOS / Linux).
"""
from __future__ import annotations

import argparse
import json
import os
import platform
import posixpath
import re
import shutil
import subprocess
import sys

# Only run version probes for caller-supplied "tool --version" style commands.
_SAFE_VERSION_CMD = re.compile(r"^[A-Za-z0-9_.-]+\s+--version\s*$")


def probe_drives() -> dict:
    """Map available drives (Windows) or the POSIX data dir to their status."""
    if platform.system() == "Windows":
        out = {}
        for letter in "CDEF":
            root = letter + ":\\"
            if os.path.exists(root):
                try:
                    free = shutil.disk_usage(root).free
                except OSError:
                    free = -1
                out[letter] = {
                    "exists": True,
                    "writable": os.access(root, os.W_OK),
                    "free_bytes": free,
                    "root": root,
                }
        return out
    home = os.environ.get("HOME", "")
    if home:
        return {"data": {"exists": True, "writable": os.access(home, os.W_OK),
                         "free_bytes": -1, "root": home}}
    return {}


def recommend_path(project_name, *, existing_project_path=None, drives=None,
                   is_windows=True, projects_root="Projects",
                   min_free_bytes=1_000_000_000, data_dir=None) -> dict:
    """Pick a project location. Existing projects are never migrated."""
    if existing_project_path:
        return {
            "status": "USE_EXISTING",
            "path": existing_project_path,
            "reason": "existing project kept in place; no migration performed",
            "auto_fallback": False,
        }
    if not project_name:
        return {"status": "INVALID", "reason": "project_name is required"}

    if is_windows:
        d = (drives or {}).get("D")
        if not d or not d.get("exists"):
            return _blocked("NO_D_DRIVE",
                            "No D drive; C-drive fallback requires explicit authorization",
                            True)
        if not d.get("writable"):
            return _blocked("D_NOT_WRITABLE",
                            "D drive not writable; C-drive fallback requires explicit authorization",
                            True)
        if d.get("free_bytes", -1) < min_free_bytes:
            return _blocked("D_LOW_SPACE",
                            "Insufficient free space on D; C-drive fallback requires explicit authorization",
                            True)
        return {
            "status": "RECOMMEND",
            "path": "D:\\" + projects_root + "\\" + project_name,
            "reason": "prefer D drive for new projects",
            "auto_fallback": False,
        }

    dd = data_dir or (drives or {}).get("data", {}).get("root")
    if not dd:
        return _blocked("NO_DATA_DIR", "No writable data directory available", False)
    if not os.access(dd, os.W_OK):
        return _blocked("DATA_DIR_NOT_WRITABLE", "Data directory is not writable", False)
    return {
        "status": "RECOMMEND",
        "path": posixpath.join(dd, project_name),
        "reason": "use the actual writable data directory on POSIX",
        "auto_fallback": False,
    }


def _blocked(code, reason, needs_authorization) -> dict:
    return {
        "status": "BLOCKED",
        "code": code,
        "reason": reason,
        "auto_fallback": False,
        "needs_authorization": needs_authorization,
    }


def detect_risks(state: dict) -> list:
    """Return a minimal risk list. Every risk is report-only: no auto-fix."""
    risks = []
    if state.get("dirty_workspace"):
        risks.append(_risk("UNCOMMITTED_CHANGES", "high",
                           "existing workspace has uncommitted changes; will not overwrite"))
    if state.get("path_conflict"):
        risks.append(_risk("PATH_CONFLICT", "high",
                           "target path collides with existing content"))
    if state.get("insufficient_permission"):
        risks.append(_risk("PERMISSION", "medium", "insufficient permission"))
    if state.get("env_mismatch"):
        risks.append(_risk("ENV_MISMATCH", "medium", "environment / version mismatch"))
    for dep in state.get("missing_dep", []):
        risks.append(_risk("MISSING_DEP", "high", "missing required dependency: " + dep))
    return risks


def _risk(code, severity, detail) -> dict:
    return {"code": code, "severity": severity, "detail": detail,
            "auto_fix_allowed": False}


def _in_git_repo(cwd: str) -> bool:
    try:
        r = subprocess.run(["git", "-C", cwd, "rev-parse", "--is-inside-work-tree"],
                           capture_output=True, text=True, timeout=10)
        return r.returncode == 0 and r.stdout.strip() == "true"
    except Exception:
        return False


def _git_status(cwd: str) -> dict:
    try:
        r = subprocess.run(["git", "-C", cwd, "status", "--porcelain"],
                           capture_output=True, text=True, timeout=15)
        lines = [ln for ln in r.stdout.splitlines() if ln.strip()]
        return {"clean": len(lines) == 0, "changed": len(lines)}
    except Exception as exc:  # noqa: BLE001
        return {"error": str(exc)}


def audit_env(required_tools=(), version_commands=None, *, include_git=True,
              cwd=None, anonymize=True) -> dict:
    """Read-only environment snapshot. Writes nothing."""
    system = platform.system()
    is_windows = system == "Windows"
    cwd = cwd or os.getcwd()
    user = os.environ.get("USERNAME") or os.environ.get("USER") or "unknown"
    if anonymize:
        user = "<user>"
    tools = {}
    for name in required_tools:
        found = shutil.which(name)
        entry = {"available": bool(found)}
        if version_commands and name in version_commands:
            cmd = version_commands[name]
            if isinstance(cmd, str) and _SAFE_VERSION_CMD.match(cmd):
                try:
                    pr = subprocess.run(cmd, shell=True, capture_output=True,
                                        text=True, timeout=10)
                    entry["version"] = pr.stdout.strip().splitlines()[0] if pr.stdout else None
                except Exception:
                    entry["version"] = None
        tools[name] = entry
    env = {
        "os_family": "windows" if is_windows else ("macos" if system == "Darwin" else "linux"),
        "os_release": platform.release(),
        "arch": platform.machine(),
        "user": user,
        "shell": os.environ.get("SHELL", "unknown"),
        "cwd": cwd,
        "cwd_writable": os.access(cwd, os.W_OK),
        "is_windows": is_windows,
        "tools": tools,
    }
    if include_git and _in_git_repo(cwd):
        env["git"] = _git_status(cwd)
    return env


def run(payload: dict) -> dict:
    """Full read-only pre-flight report from a JSON payload.

    payload keys:
      project_name, existing_project_path, required_tools, version_commands,
      is_windows, drives, data_dir, risk_state
    """
    is_windows = payload.get("is_windows", platform.system() == "Windows")
    drives = payload.get("drives", probe_drives())
    env = audit_env(
        payload.get("required_tools", []),
        payload.get("version_commands"),
        include_git=bool(payload.get("include_git", True)),
        cwd=payload.get("cwd"),
        anonymize=bool(payload.get("anonymize", True)),
    )
    env["is_windows"] = is_windows
    if payload.get("existing_project_path"):
        rec = recommend_path(
            payload.get("project_name", ""),
            existing_project_path=payload["existing_project_path"],
            is_windows=is_windows,
        )
    else:
        rec = recommend_path(
            payload.get("project_name", ""),
            drives=drives,
            is_windows=is_windows,
            projects_root=payload.get("projects_root", "Projects"),
            min_free_bytes=payload.get("min_free_bytes", 1_000_000_000),
            data_dir=payload.get("data_dir"),
        )
    risk_state = dict(payload.get("risk_state", {}))
    if env.get("git") is not None:
        risk_state.setdefault("dirty_workspace", not env["git"].get("clean", True))
    return {
        "env": env,
        "path": rec,
        "risks": detect_risks(risk_state),
        "guard": "doraemon-local-dev-guard",
        "version": "2.0.0",
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="read-only local dev guard")
    parser.add_argument("--project-name")
    parser.add_argument("--existing")
    parser.add_argument("--tools", default="")
    parser.add_argument("--version-cmd", default="")
    parser.add_argument("--from-stdin", action="store_true")
    parser.add_argument("--no-anonymize", action="store_true")
    args = parser.parse_args(argv)

    if args.from_stdin:
        payload = json.load(sys.stdin)
    else:
        payload = {"project_name": args.project_name,
                   "existing_project_path": args.existing,
                   "anonymize": not args.no_anonymize}
        if args.tools:
            payload["required_tools"] = [t for t in args.tools.split(",") if t]
        if args.version_cmd:
            vc = {}
            for pair in args.version_cmd.split(","):
                if "=" in pair:
                    k, v = pair.split("=", 1)
                    vc[k] = v
            payload["version_commands"] = vc

    print(json.dumps(run(payload), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
