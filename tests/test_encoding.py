from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

TEXT_EXTENSIONS = {".bat", ".cmd", ".md", ".py", ".txt", ".yaml", ".yml"}
SKIPPED_PARTS = {
    ".git",
    ".pytest_cache",
    "__pycache__",
    "bin",
    "dist",
    "exe",
    "lists",
    "presets",
    "src/resources",
    "windivert.filter",
}

SUSPICIOUS_CHARS = {
    "\u0403",
    "\u040a",
    "\u040c",
    "\u040e",
    "\u040f",
    "\u201a",
    "\u201e",
    "\u2020",
    "\u2021",
    "\u02c6",
    "\u2030",
    "\u2039",
    "\u0152",
    "\u017d",
}

SUSPICIOUS_SEQUENCE_POINTS = {
    (0x0420, 0x045F),
    (0x0420, 0x2019),
    (0x0420, 0x040C),
    (0x0420, 0x040E),
    (0x0420, 0x00B0),
    (0x0420, 0x00B5),
    (0x0421, 0x0403),
    (0x0421, 0x201A),
    (0x0421, 0x040A),
    (0x0432, 0x045A),
    (0x0432, 0x0459),
    (0x0432, 0x0402),
    (0x0432, 0x2020),
}
SUSPICIOUS_SEQUENCES = {
    "".join(chr(point) for point in points) for points in SUSPICIOUS_SEQUENCE_POINTS
}


def _is_checked_text_file(path: Path) -> bool:
    relative = path.relative_to(REPO_ROOT).as_posix()
    if path.suffix.lower() not in TEXT_EXTENSIONS:
        return False
    return not any(part in relative for part in SKIPPED_PARTS)


def test_user_facing_text_does_not_contain_mojibake():
    offenders: dict[str, list[str]] = {}

    for path in REPO_ROOT.rglob("*"):
        if not path.is_file() or not _is_checked_text_file(path):
            continue

        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError as exc:
            offenders[str(path.relative_to(REPO_ROOT))] = [f"invalid utf-8: {exc}"]
            continue

        bad_chars = sorted({char for char in text if char in SUSPICIOUS_CHARS})
        bad_sequences = sorted(sequence for sequence in SUSPICIOUS_SEQUENCES if sequence in text)
        if bad_chars or bad_sequences:
            offenders[str(path.relative_to(REPO_ROOT))] = bad_chars + bad_sequences

    assert offenders == {}
