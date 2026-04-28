from __future__ import annotations

import json

from core.runtime_state import RuntimeState
from main import should_restore_zapret_on_start


def test_runtime_state_tracks_start_stop_and_shutdown(tmp_path):
    state = RuntimeState(tmp_path / "runtime-state.json")

    state.mark_zapret_active("Default")
    data = state.read()
    assert data["zapret_was_active_on_exit"] is True
    assert data["last_active_preset"] == "Default"
    assert data["last_start_error"] is None

    state.mark_zapret_inactive()
    assert state.read()["zapret_was_active_on_exit"] is False

    state.mark_shutdown(True, "Default")
    data = state.read()
    assert data["zapret_was_active_on_exit"] is True
    assert data["last_active_preset"] == "Default"
    assert data["last_shutdown_at"]


def test_restore_start_enabled_only_when_last_exit_was_active(tmp_path):
    state_file = tmp_path / "runtime-state.json"
    state_file.write_text(
        json.dumps({"zapret_was_active_on_exit": True}),
        encoding="utf-8",
    )
    assert should_restore_zapret_on_start(RuntimeState(state_file)) is True

    state_file.write_text(
        json.dumps({"zapret_was_active_on_exit": False}),
        encoding="utf-8",
    )
    assert should_restore_zapret_on_start(RuntimeState(state_file)) is False
