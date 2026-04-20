from __future__ import annotations

from pathlib import Path

from utils.validators import Validators

ROOT = Path(__file__).resolve().parents[1]

TELEGRAM_DOMAINS = {
    "telegram.org",
    "t.me",
    "web.telegram.org",
    "api.telegram.org",
    "telegramusercontent.com",
    "telegram-cdn.org",
}

TELEGRAM_CIDRS = {
    "91.108.56.0/22",
    "91.108.4.0/22",
    "91.108.8.0/22",
    "91.108.16.0/22",
    "91.108.12.0/22",
    "149.154.160.0/20",
    "91.105.192.0/23",
    "91.108.20.0/22",
    "185.76.151.0/24",
    "2001:b28:f23d::/48",
    "2001:b28:f23f::/48",
    "2001:67c:4e8::/48",
    "2001:b28:f23c::/48",
    "2a0a:f280::/32",
}


def _entries(path: Path) -> set[str]:
    return {
        line.strip()
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.strip().startswith("#")
    }


def test_telegram_lists_are_available_in_runtime_and_bat_trees():
    for lists_dir in (ROOT / "lists", ROOT / "src" / "resources" / "lists"):
        telegram_domains = _entries(lists_dir / "telegram.txt")
        telegram_cidrs = _entries(lists_dir / "ipset-telegram.txt")
        general_domains = _entries(lists_dir / "list-general.txt")
        all_cidrs = _entries(lists_dir / "ipset-all.txt")

        assert TELEGRAM_DOMAINS <= telegram_domains
        assert TELEGRAM_DOMAINS <= general_domains
        assert TELEGRAM_CIDRS <= telegram_cidrs
        assert TELEGRAM_CIDRS <= all_cidrs


def test_telegram_presets_reference_existing_lists_and_are_valid():
    for presets_dir in (ROOT / "presets", ROOT / "src" / "resources" / "presets"):
        for preset_name in (
            "Telegram Direct.txt",
            "Default (Discord, YouTube, Telegram).txt",
            "YouTube Telegram Minimal.txt",
        ):
            preset_path = presets_dir / preset_name
            content = preset_path.read_text(encoding="utf-8")

            assert Validators.validate_preset_file(preset_path)
            assert "--hostlist=lists/telegram.txt" in content
            assert "--ipset=lists/ipset-telegram.txt" in content
            assert "--filter-tcp=80,443,5222,5223" in content
