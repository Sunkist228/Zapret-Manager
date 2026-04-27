# -*- coding: utf-8 -*-
"""Persistent runtime state for Zapret Manager."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

from utils.config import Config
from utils.logger import logger


class RuntimeState:
    """Small JSON-backed store for restore-on-start behavior."""

    DEFAULTS: Dict[str, Any] = {
        "zapret_was_active_on_exit": False,
        "last_active_preset": None,
        "last_shutdown_at": None,
        "last_start_error": None,
    }

    def __init__(self, state_file: Optional[Path] = None):
        self.state_file = state_file or Config.RUNTIME_STATE_FILE

    def read(self) -> Dict[str, Any]:
        data = dict(self.DEFAULTS)
        try:
            if self.state_file.exists():
                loaded = json.loads(self.state_file.read_text(encoding="utf-8-sig"))
                if isinstance(loaded, dict):
                    data.update(loaded)
        except Exception as exc:
            logger.warning("Failed to read runtime state %s: %s", self.state_file, exc)
        return data

    def write(self, **updates: Any) -> None:
        data = self.read()
        data.update(updates)
        try:
            self.state_file.parent.mkdir(parents=True, exist_ok=True)
            self.state_file.write_text(
                json.dumps(data, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
        except Exception as exc:
            logger.error("Failed to write runtime state %s: %s", self.state_file, exc)

    def mark_zapret_active(self, preset_name: Optional[str]) -> None:
        self.write(
            zapret_was_active_on_exit=True,
            last_active_preset=preset_name,
            last_start_error=None,
        )

    def mark_zapret_inactive(self) -> None:
        self.write(zapret_was_active_on_exit=False)

    def mark_shutdown(self, active: bool, preset_name: Optional[str]) -> None:
        self.write(
            zapret_was_active_on_exit=active,
            last_active_preset=preset_name,
            last_shutdown_at=datetime.now(timezone.utc).isoformat(),
        )

    def mark_start_error(self, message: str) -> None:
        self.write(last_start_error=message)

    def should_restore_zapret(self) -> bool:
        return bool(self.read().get("zapret_was_active_on_exit", False))
