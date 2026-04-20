#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Generate CHANGELOG.md from conventional commits.

Usage:
    python scripts/generate_changelog.py [--version VERSION]

Examples:
    python scripts/generate_changelog.py --version 1.1.0
    python scripts/generate_changelog.py  # Auto-detect from VERSION file
"""

import argparse
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Tuple


CONVENTIONAL_COMMIT_RE = re.compile(
    r"^(?P<type>feat|fix|docs|style|refactor|perf|test|chore|build|ci|revert)"
    r"(?:\((?P<scope>[^\)]+)\))?"
    r"(?P<breaking>!)?"
    r": (?P<description>.+)$"
)

BREAKING_CHANGE_RE = re.compile(r"BREAKING[- ]CHANGE:\s*(.+)", re.MULTILINE | re.IGNORECASE)


def get_git_commits_since_last_tag() -> List[Tuple[str, str]]:
    """
    Get all commits since the last tag.

    Returns:
        List of (commit_hash, commit_message) tuples
    """
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

        # Get commit hashes and messages
        result = subprocess.run(
            ["git", "log", commit_range, "--pretty=format:%H|||%s%n%b%n---COMMIT---"],
            capture_output=True,
            text=True,
            check=True
        )

        commits = []
        for commit_block in result.stdout.split("---COMMIT---"):
            commit_block = commit_block.strip()
            if not commit_block:
                continue

            parts = commit_block.split("|||", 1)
            if len(parts) == 2:
                commit_hash = parts[0].strip()
                commit_msg = parts[1].strip()
                commits.append((commit_hash, commit_msg))

        return commits

    except subprocess.CalledProcessError as e:
        print(f"Error getting git commits: {e}", file=sys.stderr)
        return []


def parse_commits(commits: List[Tuple[str, str]]) -> Dict[str, List[Dict]]:
    """
    Parse commits and group by type.

    Returns:
        Dict with keys: 'breaking', 'features', 'fixes', 'other'
    """
    grouped = {
        'breaking': [],
        'features': [],
        'fixes': [],
        'other': []
    }

    for commit_hash, commit_msg in commits:
        short_hash = commit_hash[:7]

        # Check for BREAKING CHANGE in body
        breaking_match = BREAKING_CHANGE_RE.search(commit_msg)
        if breaking_match:
            description = breaking_match.group(1).strip()
            grouped['breaking'].append({
                'hash': short_hash,
                'description': description,
                'full_msg': commit_msg
            })
            continue

        # Parse conventional commit
        lines = commit_msg.split('\n')
        first_line = lines[0]

        match = CONVENTIONAL_COMMIT_RE.match(first_line)
        if not match:
            # Non-conventional commit, skip or add to other
            continue

        commit_type = match.group("type")
        scope = match.group("scope")
        breaking_marker = match.group("breaking")
        description = match.group("description")

        # Format description with scope
        if scope:
            formatted_desc = f"**{scope}:** {description}"
        else:
            formatted_desc = description

        commit_info = {
            'hash': short_hash,
            'description': formatted_desc,
            'type': commit_type,
            'scope': scope
        }

        if breaking_marker:
            grouped['breaking'].append(commit_info)
        elif commit_type == "feat":
            grouped['features'].append(commit_info)
        elif commit_type == "fix":
            grouped['fixes'].append(commit_info)
        else:
            # chore, docs, style, refactor, etc.
            grouped['other'].append(commit_info)

    return grouped


def generate_changelog_entry(version: str, grouped_commits: Dict[str, List[Dict]]) -> str:
    """Generate changelog entry for a version."""
    today = datetime.now().strftime("%Y-%m-%d")

    lines = [
        f"## [{version}] - {today}",
        ""
    ]

    # Breaking Changes
    if grouped_commits['breaking']:
        lines.append("### ⚠ BREAKING CHANGES")
        lines.append("")
        for commit in grouped_commits['breaking']:
            lines.append(f"- {commit['description']} ({commit['hash']})")
        lines.append("")

    # Features
    if grouped_commits['features']:
        lines.append("### Features")
        lines.append("")
        for commit in grouped_commits['features']:
            lines.append(f"- {commit['description']} ({commit['hash']})")
        lines.append("")

    # Bug Fixes
    if grouped_commits['fixes']:
        lines.append("### Bug Fixes")
        lines.append("")
        for commit in grouped_commits['fixes']:
            lines.append(f"- {commit['description']} ({commit['hash']})")
        lines.append("")

    # Other changes (optional, usually not included)
    # if grouped_commits['other']:
    #     lines.append("### Other Changes")
    #     lines.append("")
    #     for commit in grouped_commits['other']:
    #         lines.append(f"- {commit['description']} ({commit['hash']})")
    #     lines.append("")

    return "\n".join(lines)


def update_changelog(version: str, new_entry: str, changelog_path: Path):
    """Update CHANGELOG.md with new entry."""
    if changelog_path.exists():
        existing_content = changelog_path.read_text(encoding="utf-8")

        # Find where to insert (after header, before first version)
        lines = existing_content.split("\n")
        insert_index = 0

        for i, line in enumerate(lines):
            if line.startswith("## ["):
                insert_index = i
                break
            elif line.strip() and not line.startswith("#"):
                insert_index = i
                break

        if insert_index > 0:
            # Insert after header
            new_lines = lines[:insert_index] + [""] + new_entry.split("\n") + [""] + lines[insert_index:]
        else:
            # No existing versions, append
            new_lines = lines + ["", ""] + new_entry.split("\n")

        new_content = "\n".join(new_lines)
    else:
        # Create new CHANGELOG
        header = [
            "# Changelog",
            "",
            "All notable changes to this project will be documented in this file.",
            "",
            "The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),",
            "and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).",
            "",
            ""
        ]
        new_content = "\n".join(header) + new_entry + "\n"

    changelog_path.write_text(new_content, encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description="Generate CHANGELOG from conventional commits")
    parser.add_argument(
        "--version",
        help="Version for the changelog entry (default: read from VERSION file)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print changelog entry without writing to file"
    )

    args = parser.parse_args()

    # Determine version
    if args.version:
        version = args.version
    else:
        version_file = Path(__file__).parent.parent / "VERSION"
        if not version_file.exists():
            print("ERROR: VERSION file not found and --version not specified", file=sys.stderr)
            sys.exit(1)
        version = version_file.read_text(encoding="utf-8").strip()

    # Get commits
    commits = get_git_commits_since_last_tag()
    if not commits:
        print("No commits found since last tag", file=sys.stderr)
        sys.exit(1)

    # Parse and group commits
    grouped = parse_commits(commits)

    # Check if there are any relevant commits
    total_relevant = len(grouped['breaking']) + len(grouped['features']) + len(grouped['fixes'])
    if total_relevant == 0:
        print("No relevant commits found (feat, fix, or breaking changes)", file=sys.stderr)
        sys.exit(1)

    # Generate changelog entry
    entry = generate_changelog_entry(version, grouped)

    if args.dry_run:
        print(entry)
    else:
        changelog_path = Path(__file__).parent.parent / "CHANGELOG.md"
        update_changelog(version, entry, changelog_path)
        print(f"Updated CHANGELOG.md with version {version}", file=sys.stderr)
        print(f"  Breaking changes: {len(grouped['breaking'])}", file=sys.stderr)
        print(f"  Features: {len(grouped['features'])}", file=sys.stderr)
        print(f"  Bug fixes: {len(grouped['fixes'])}", file=sys.stderr)

    sys.exit(0)


if __name__ == "__main__":
    main()
