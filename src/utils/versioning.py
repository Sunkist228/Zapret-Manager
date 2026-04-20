# -*- coding: utf-8 -*-
"""
Utilities for reading and comparing application versions.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


SEMVER_RE = re.compile(
    r"^\s*"
    r"(?P<major>0|[1-9]\d*)\."
    r"(?P<minor>0|[1-9]\d*)\."
    r"(?P<patch>0|[1-9]\d*)"
    r"(?:-(?P<prerelease>[0-9A-Za-z.-]+))?"
    r"(?:\+(?P<build>[0-9A-Za-z.-]+))?"
    r"\s*$"
)


@dataclass(frozen=True)
class SemVer:
    major: int
    minor: int
    patch: int
    prerelease: Optional[str] = None
    build: Optional[str] = None

    @property
    def product_version(self) -> str:
        return f"{self.major}.{self.minor}.{self.patch}"

    def __str__(self) -> str:
        value = self.product_version
        if self.prerelease:
            value += f"-{self.prerelease}"
        if self.build:
            value += f"+{self.build}"
        return value


def parse_version(value: str) -> SemVer:
    """Parse a SemVer-like version string."""
    match = SEMVER_RE.match((value or "").strip())
    if not match:
        raise ValueError(f"Invalid version: {value!r}")

    return SemVer(
        major=int(match.group("major")),
        minor=int(match.group("minor")),
        patch=int(match.group("patch")),
        prerelease=match.group("prerelease"),
        build=match.group("build"),
    )


def compare_versions(left: str, right: str) -> int:
    """
    Compare versions ignoring build metadata.

    Returns:
        -1 if left < right
         0 if left == right
         1 if left > right
    """
    left_ver = parse_version(left)
    right_ver = parse_version(right)

    left_core = (left_ver.major, left_ver.minor, left_ver.patch)
    right_core = (right_ver.major, right_ver.minor, right_ver.patch)

    if left_core < right_core:
        return -1
    if left_core > right_core:
        return 1

    return _compare_prerelease(left_ver.prerelease, right_ver.prerelease)


def normalize_product_version(value: str) -> str:
    """Return MAJOR.MINOR.PATCH from a version string."""
    return parse_version(value).product_version


def read_version_file(path: Path, default: str = "0.0.0") -> str:
    """Read version from a file and fall back to default on failure."""
    try:
        raw = path.read_text(encoding="utf-8").strip()
        return str(parse_version(raw))
    except Exception:
        return default


def _compare_prerelease(left: Optional[str], right: Optional[str]) -> int:
    if left == right:
        return 0
    if left is None:
        return 1
    if right is None:
        return -1

    left_parts = left.split(".")
    right_parts = right.split(".")

    for left_part, right_part in zip(left_parts, right_parts):
        if left_part == right_part:
            continue

        left_numeric = left_part.isdigit()
        right_numeric = right_part.isdigit()

        if left_numeric and right_numeric:
            left_value = int(left_part)
            right_value = int(right_part)
            if left_value < right_value:
                return -1
            if left_value > right_value:
                return 1
            continue

        if left_numeric != right_numeric:
            return -1 if left_numeric else 1

        if left_part < right_part:
            return -1
        if left_part > right_part:
            return 1

    if len(left_parts) < len(right_parts):
        return -1
    if len(left_parts) > len(right_parts):
        return 1
    return 0
