#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Automatic version bumping based on conventional commits.

Usage:
    python scripts/bump_version.py [--type auto|major|minor|patch] [--dry-run]

Examples:
    python scripts/bump_version.py                    # Auto-detect from commits
    python scripts/bump_version.py --type patch       # Force patch bump
    python scripts/bump_version.py --dry-run          # Preview without writing

Returns:
    Prints new version to stdout
    Exit code 0 if version changed, 1 if no change needed
"""

import argparse
import re
import subprocess
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

try:
    from utils.versioning import parse_version, SemVer
except ImportError:
    # Fallback if versioning module not available
    class SemVer:
        def __init__(self, major, minor, patch):
            self.major = major
            self.minor = minor
            self.patch = patch

        def __str__(self):
            return f"{self.major}.{self.minor}.{self.patch}"

    def parse_version(version_str):
        parts = version_str.strip().split('.')
        if len(parts) != 3:
            raise ValueError(f"Invalid version: {version_str}")
        return SemVer(int(parts[0]), int(parts[1]), int(parts[2]))


CONVENTIONAL_COMMIT_RE = re.compile(
    r"^(?P<type>feat|fix|docs|style|refactor|perf|test|chore|build|ci|revert)"
    r"(?:\((?P<scope>[^\)]+)\))?"
    r"(?P<breaking>!)?"
    r": (?P<description>.+)$",
    re.MULTILINE
)

BREAKING_CHANGE_RE = re.compile(r"BREAKING[- ]CHANGE:\s*(.+)", re.MULTILINE | re.IGNORECASE)


def get_git_commits_since_last_tag():
    """Get all commits since the last tag."""
    try:
        # Get the last tag
        result = subprocess.run(
            ["git", "describe", "--tags", "--abbrev=0"],
            capture_output=True,
            text=True,
            check=False
        )

        if result.returncode == 0:
            last_tag = result.stdout.strip()
            commit_range = f"{last_tag}..HEAD"
        else:
            # No tags yet, get all commits
            commit_range = "HEAD"

        # Get commit messages
        result = subprocess.run(
            ["git", "log", commit_range, "--pretty=format:%B%n---COMMIT---"],
            capture_output=True,
            text=True,
            check=True
        )

        commits = [c.strip() for c in result.stdout.split("---COMMIT---") if c.strip()]
        return commits

    except subprocess.CalledProcessError as e:
        print(f"Error getting git commits: {e}", file=sys.stderr)
        return []


def analyze_commits(commits):
    """
    Analyze commits and determine bump type.

    Returns:
        str: 'major', 'minor', 'patch', or 'none'
    """
    has_breaking = False
    has_feat = False
    has_fix = False

    for commit in commits:
        # Check for BREAKING CHANGE in body
        if BREAKING_CHANGE_RE.search(commit):
            has_breaking = True
            continue

        # Parse conventional commit
        match = CONVENTIONAL_COMMIT_RE.match(commit)
        if not match:
            continue

        commit_type = match.group("type")
        breaking_marker = match.group("breaking")

        if breaking_marker:
            has_breaking = True
        elif commit_type == "feat":
            has_feat = True
        elif commit_type == "fix":
            has_fix = True

    if has_breaking:
        return "major"
    elif has_feat:
        return "minor"
    elif has_fix:
        return "patch"
    else:
        return "none"


def bump_version(current_version: str, bump_type: str) -> str:
    """
    Bump version according to bump_type.

    Args:
        current_version: Current version string (e.g., "1.0.0")
        bump_type: 'major', 'minor', or 'patch'

    Returns:
        New version string
    """
    ver = parse_version(current_version)

    if bump_type == "major":
        new_ver = SemVer(major=ver.major + 1, minor=0, patch=0)
    elif bump_type == "minor":
        new_ver = SemVer(major=ver.major, minor=ver.minor + 1, patch=0)
    elif bump_type == "patch":
        new_ver = SemVer(major=ver.major, minor=ver.minor, patch=ver.patch + 1)
    else:
        raise ValueError(f"Invalid bump type: {bump_type}")

    return str(new_ver)


def main():
    parser = argparse.ArgumentParser(description="Bump version based on conventional commits")
    parser.add_argument(
        "--type",
        choices=["auto", "major", "minor", "patch"],
        default="auto",
        help="Version bump type (default: auto - analyze commits)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print new version without writing to file"
    )

    args = parser.parse_args()

    # Read current version
    version_file = Path(__file__).parent.parent / "VERSION"
    if not version_file.exists():
        print("ERROR: VERSION file not found", file=sys.stderr)
        sys.exit(1)

    current_version = version_file.read_text(encoding="utf-8").strip()

    try:
        parse_version(current_version)  # Validate current version
    except ValueError as e:
        print(f"ERROR: Invalid current version: {e}", file=sys.stderr)
        sys.exit(1)

    # Determine bump type
    if args.type == "auto":
        commits = get_git_commits_since_last_tag()
        if not commits:
            print(f"No commits since last tag, keeping version {current_version}", file=sys.stderr)
            print(current_version)
            sys.exit(1)

        bump_type = analyze_commits(commits)

        if bump_type == "none":
            print(f"No version-bumping commits found, keeping version {current_version}", file=sys.stderr)
            print(current_version)
            sys.exit(1)
    else:
        bump_type = args.type

    # Bump version
    new_version = bump_version(current_version, bump_type)

    print(f"Bumping version: {current_version} → {new_version} ({bump_type})", file=sys.stderr)

    # Write new version
    if not args.dry_run:
        version_file.write_text(new_version + "\n", encoding="utf-8")
        print(f"Updated VERSION file", file=sys.stderr)

    # Output new version to stdout (for use in CI)
    print(new_version)
    sys.exit(0)


if __name__ == "__main__":
    main()
