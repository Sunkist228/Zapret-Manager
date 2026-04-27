from __future__ import annotations

import re
from datetime import datetime, timedelta

from utils import logger as logger_module
from utils.logger import cleanup_old_logs, create_winws2_log_file


def _set_mtime(path, when: datetime):
    timestamp = when.timestamp()
    path.touch()
    path.chmod(0o666)
    import os

    os.utime(path, (timestamp, timestamp))


def test_cleanup_old_logs_keeps_only_recent_two_weeks(tmp_path):
    old_time = datetime.now() - timedelta(days=15)
    recent_time = datetime.now() - timedelta(days=2)

    old_app = tmp_path / "app.log.2026-04-01"
    old_winws = tmp_path / "winws2-20260401-120000.log"
    recent_winws = tmp_path / "winws2-20260426-120000.log"
    unrelated = tmp_path / "notes.txt"

    _set_mtime(old_app, old_time)
    _set_mtime(old_winws, old_time)
    _set_mtime(recent_winws, recent_time)
    _set_mtime(unrelated, old_time)

    cleanup_old_logs(tmp_path, retention_days=14)

    assert not old_app.exists()
    assert not old_winws.exists()
    assert recent_winws.exists()
    assert unrelated.exists()


def test_create_winws2_log_file_uses_timestamped_per_run_name(tmp_path):
    log_file = create_winws2_log_file(tmp_path)

    assert log_file.parent == tmp_path
    assert re.fullmatch(r"winws2-\d{8}-\d{6}\.log", log_file.name)


def test_create_winws2_log_file_does_not_overwrite_same_second_log(monkeypatch, tmp_path):
    class FixedDateTime(datetime):
        @classmethod
        def now(cls):
            return cls(2026, 4, 27, 12, 0, 0)

    monkeypatch.setattr(logger_module, "datetime", FixedDateTime)

    first = create_winws2_log_file(tmp_path)
    first.write_text("first", encoding="utf-8")
    second = create_winws2_log_file(tmp_path)

    assert second != first
    assert second.name == "winws2-20260427-120000-1.log"
