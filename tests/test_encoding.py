from __future__ import annotations

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def test_tray_ui_text_does_not_contain_mojibake():
    text = (REPO_ROOT / "src" / "gui" / "tray_icon.py").read_text(encoding="utf-8")
    suspicious_chars = {
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

    offenders = sorted({char for char in text if char in suspicious_chars})

    assert offenders == []
