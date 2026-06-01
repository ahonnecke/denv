#!/usr/bin/env python3
"""
Check git status across multiple crewcapableai working directories.
Provides a summary of changes with special focus on requirements directory.
Creates symlinks for easy navigation (~/src/cc.<taskname>).

Usage:
    crew-claude-summary.py           # Show status of all workspaces
    crew-claude-summary.py --find-empty  # Find first empty workspace and print path
"""

import subprocess
import sys
import os
import re
import argparse
from pathlib import Path
from collections import defaultdict


def run_git_command(cwd, *args):
    """Run a git command and return output."""
    try:
        result = subprocess.run(
            ["git"] + list(args),
            cwd=cwd,
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError:
        return None


def get_status_summary(directory):
    """Get git status summary for a directory."""
    status_output = run_git_command(directory, "status", "--porcelain")

    if not status_output:
        return None

    summary = {
        "modified": [],
        "added": [],
        "deleted": [],
        "untracked": [],
        "requirements": []
    }

    for line in status_output.split("\n"):
        if not line:
            continue

        status_code = line[:2]
        filepath = line[3:]

        # Check if it's in requirements directory
        is_requirements = filepath.startswith("requirements/") or filepath == "requirements.txt"

        if is_requirements:
            summary["requirements"].append((status_code, filepath))

        # Categorize by status
        if status_code.strip() == "M" or status_code[0] == "M":
            summary["modified"].append(filepath)
        elif status_code.strip() == "A" or status_code[0] == "A":
            summary["added"].append(filepath)
        elif status_code.strip() == "D" or status_code[0] == "D":
            summary["deleted"].append(filepath)
        elif status_code == "??":
            summary["untracked"].append(filepath)

    return summary


def get_current_branch(directory):
    """Get the current branch name."""
    return run_git_command(directory, "rev-parse", "--abbrev-ref", "HEAD")


def extract_task_name(branch_name):
    """Extract a clean task name from branch name for symlink."""
    if not branch_name:
        return None
    # Remove common prefixes and convert to lowercase
    task = re.sub(r'^(TASK|FEATURE|BUGFIX|FIX|HOTFIX)/', '', branch_name, flags=re.IGNORECASE)
    # Replace slashes and spaces with hyphens
    task = task.replace('/', '-').replace('_', '-').lower()
    return task


def check_local_server(directory):
    """Check if this directory is running a local server on common dev ports."""
    try:
        # Check for common dev server ports: 3000, 8000, 8080, 5000, 4200
        ports = [3000, 8000, 8080, 5000, 4200]

        for port in ports:
            # Use lsof to find processes listening on these ports
            result = subprocess.run(
                ["lsof", "-ti", f":{port}"],
                capture_output=True,
                text=True
            )

            if result.stdout.strip():
                pids = result.stdout.strip().split('\n')
                for pid in pids:
                    # Get the cwd of the process
                    try:
                        proc_cwd = subprocess.run(
                            ["readlink", "-f", f"/proc/{pid}/cwd"],
                            capture_output=True,
                            text=True
                        )
                        if proc_cwd.returncode == 0:
                            cwd = proc_cwd.stdout.strip()
                            if cwd.startswith(str(directory)):
                                return port
                    except (subprocess.CalledProcessError, FileNotFoundError):
                        continue
    except Exception:
        pass

    return None


def create_symlink(src_dir, crew_dir, task_name):
    """Create a symlink ~/src/cc.<taskname> -> ~/src/crewcapableai.X"""
    if not task_name:
        return False

    symlink_path = src_dir / f"cc.{task_name}"

    try:
        # Clean up any old symlinks pointing to this crew directory
        for potential_link in src_dir.glob("cc.*"):
            if potential_link.is_symlink():
                try:
                    if potential_link.resolve() == crew_dir.resolve():
                        # This symlink points to our crew_dir, remove it if it's not the one we want
                        if potential_link != symlink_path:
                            potential_link.unlink()
                except (OSError, RuntimeError):
                    # Broken symlink or other issue, skip it
                    pass

        # Remove old symlink if it exists at our target path
        if symlink_path.is_symlink() or symlink_path.exists():
            # Only update if it's different
            if symlink_path.is_symlink() and symlink_path.resolve() == crew_dir.resolve():
                return False  # Already correct
            symlink_path.unlink()

        # Create new symlink
        symlink_path.symlink_to(crew_dir)
        return True
    except Exception as e:
        print(f"Warning: Could not create symlink {symlink_path}: {e}", file=sys.stderr)
        return False


def find_empty_workspace(crew_dirs):
    """Find the first workspace with a clean working directory."""
    for crew_dir in crew_dirs:
        if not crew_dir.is_dir():
            continue

        summary = get_status_summary(crew_dir)

        # If summary is None, the working directory is clean
        if summary is None:
            return crew_dir

    return None


def main():
    parser = argparse.ArgumentParser(
        description="Check status of crewcapableai working directories"
    )
    parser.add_argument(
        "--find-empty",
        action="store_true",
        help="Find and print path to first empty workspace"
    )
    args = parser.parse_args()

    src_dir = Path.home() / "src"

    # Find all crewcapableai.* directories
    crew_dirs = sorted(src_dir.glob("crewcapableai.*"))

    if not crew_dirs:
        print("No crewcapableai.* directories found in ~/src", file=sys.stderr)
        return 1

    # Handle --find-empty flag
    if args.find_empty:
        empty_workspace = find_empty_workspace(crew_dirs)
        if empty_workspace:
            print(empty_workspace)
            return 0
        else:
            print("No empty workspace found", file=sys.stderr)
            return 1

    print("=" * 80)
    print("CREW CAPABLE AI - PARALLEL WORKING DIRECTORIES STATUS")
    print("=" * 80)
    print()

    any_changes = False
    symlinks_created = []

    for crew_dir in crew_dirs:
        if not crew_dir.is_dir():
            continue

        dir_name = crew_dir.name
        branch = get_current_branch(crew_dir)
        summary = get_status_summary(crew_dir)
        server_port = check_local_server(crew_dir)

        # Create symlink for this directory
        task_name = extract_task_name(branch)
        if task_name:
            if create_symlink(src_dir, crew_dir, task_name):
                symlinks_created.append(f"cc.{task_name}")

        # Build header with server indicator
        header = f"📁 {dir_name} (branch: {branch or 'unknown'})"
        if server_port:
            header += f" 🚀 SERVER:PORT-{server_port}"
        if task_name:
            header += f" → ~/src/cc.{task_name}"

        if summary is None:
            print(header)
            print("   ✓ Clean working directory")
            print()
            continue

        any_changes = True

        print(header)
        print("-" * 80)

        # Show requirements changes first if any
        if summary["requirements"]:
            print("   🔥 REQUIREMENTS CHANGES:")
            for status_code, filepath in summary["requirements"]:
                status_symbol = {
                    "M ": "📝",
                    " M": "📝",
                    "MM": "📝",
                    "A ": "➕",
                    " A": "➕",
                    "D ": "➖",
                    " D": "➖",
                    "??": "❓"
                }.get(status_code, "  ")
                print(f"      {status_symbol} {filepath}")
            print()

        # Show other changes
        if summary["modified"]:
            req_modified = [f for f in summary["modified"] if not any(
                f.startswith("requirements/") or f == "requirements.txt" for f in [f]
            )]
            if req_modified:
                print(f"   Modified: {len(req_modified)} file(s)")
                for f in req_modified[:5]:  # Show first 5
                    print(f"      📝 {f}")
                if len(req_modified) > 5:
                    print(f"      ... and {len(req_modified) - 5} more")
                print()

        if summary["added"]:
            req_added = [f for f in summary["added"] if not any(
                f.startswith("requirements/") or f == "requirements.txt" for f in [f]
            )]
            if req_added:
                print(f"   Added: {len(req_added)} file(s)")
                for f in req_added[:5]:
                    print(f"      ➕ {f}")
                if len(req_added) > 5:
                    print(f"      ... and {len(req_added) - 5} more")
                print()

        if summary["deleted"]:
            req_deleted = [f for f in summary["deleted"] if not any(
                f.startswith("requirements/") or f == "requirements.txt" for f in [f]
            )]
            if req_deleted:
                print(f"   Deleted: {len(req_deleted)} file(s)")
                for f in req_deleted[:5]:
                    print(f"      ➖ {f}")
                if len(req_deleted) > 5:
                    print(f"      ... and {len(req_deleted) - 5} more")
                print()

        if summary["untracked"]:
            req_untracked = [f for f in summary["untracked"] if not any(
                f.startswith("requirements/") or f == "requirements.txt" for f in [f]
            )]
            if req_untracked:
                print(f"   Untracked: {len(req_untracked)} file(s)")
                for f in req_untracked[:5]:
                    print(f"      ❓ {f}")
                if len(req_untracked) > 5:
                    print(f"      ... and {len(req_untracked) - 5} more")
                print()

        print()

    if not any_changes:
        print("✓ All directories have clean working trees")

    print("=" * 80)

    # Show symlink summary if any were created
    if symlinks_created:
        print()
        print("📎 Symlinks created/updated:")
        for link in symlinks_created:
            print(f"   ~/src/{link}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
