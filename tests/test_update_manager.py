from __future__ import annotations

import hashlib
import json

import pytest

from core.update_manager import UpdateManager, UpdateError
from utils import config as config_module
from utils.versioning import compare_versions, normalize_product_version


class FakeResponse:
    def __init__(self, status_code=200, payload=None, content=b"", raise_json=False):
        self.status_code = status_code
        self._payload = payload
        self._content = content
        self._raise_json = raise_json

    def json(self):
        if self._raise_json:
            raise ValueError("bad json")
        return self._payload

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError(f"http {self.status_code}")

    def iter_content(self, chunk_size=1024):
        for index in range(0, len(self._content), chunk_size):
            yield self._content[index : index + chunk_size]


class FakeSession:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []

    def get(self, url, **kwargs):
        self.calls.append((url, kwargs))
        response = self.responses.pop(0)
        if isinstance(response, Exception):
            raise response
        return response


@pytest.fixture()
def temp_config(monkeypatch, tmp_path):
    monkeypatch.setattr(config_module.Config, "CONFIG_DIR", tmp_path / "config")
    monkeypatch.setattr(
        config_module.Config, "UPDATE_STATE_FILE", tmp_path / "config" / "state.json"
    )
    monkeypatch.setattr(config_module.Config, "UPDATE_DOWNLOAD_DIR", tmp_path / "downloads")
    monkeypatch.setattr(config_module.Config, "VERSION", "1.0.0+build.1")
    monkeypatch.setattr(config_module.Config, "PRODUCT_VERSION", "1.0.0")
    monkeypatch.setattr(config_module.Config, "UPDATE_ENABLED", True)
    monkeypatch.setattr(config_module.Config, "UPDATE_CHECK_INTERVAL_HOURS", 24)
    monkeypatch.setattr(
        config_module.Config,
        "UPDATE_ENDPOINTS",
        ("https://artifact.devflux.ru", "https://update.devflux.ru"),
    )
    monkeypatch.setattr(config_module.Config, "UPDATE_CHECK_PATH", "/api/v1/update/check")
    monkeypatch.setattr(config_module.Config, "UPDATE_ARTIFACT_SLUG", "zapret-manager")
    monkeypatch.setattr(config_module.Config, "UPDATE_CHANNEL", "stable")
    monkeypatch.setattr(config_module.Config, "UPDATE_PLATFORM", "windows")
    monkeypatch.setattr(config_module.Config, "UPDATE_ARCH", "x64")
    monkeypatch.setattr(config_module.Config, "IS_FROZEN", False)


def test_version_comparison_ignores_build_metadata():
    assert normalize_product_version("1.0.0+build.42") == "1.0.0"
    assert compare_versions("1.0.0", "1.0.1") < 0
    assert compare_versions("1.0.0+build.1", "1.0.0+build.999") == 0
    assert compare_versions("1.0.0-dev.1", "1.0.0") < 0


def test_update_check_fails_over_to_second_endpoint(temp_config):
    payload = {
        "update_available": True,
        "latest_version": "1.0.1+build.5",
        "product_version": "1.0.1",
        "channel": "stable",
        "platform": "windows",
        "arch": "x64",
        "mandatory": False,
        "published_at": "2026-04-17T10:00:00Z",
        "download_url": "https://update.devflux.ru/files/update.exe",
        "sha256": "a" * 64,
        "size": 123,
        "release_notes": "notes",
    }
    session = FakeSession([RuntimeError("timeout"), FakeResponse(payload=payload)])
    manager = UpdateManager(session=session)

    result = manager.check_for_updates(force=True)

    assert result.update_available is True
    assert result.release.product_version == "1.0.1"
    assert result.endpoint == "https://update.devflux.ru"
    assert len(session.calls) == 2


def test_update_check_throttles_after_recent_success(temp_config):
    state_file = config_module.Config.UPDATE_STATE_FILE
    state_file.parent.mkdir(parents=True, exist_ok=True)
    state_file.write_text(
        json.dumps({"last_check_at": "2099-01-01T00:00:00+00:00"}), encoding="utf-8"
    )

    manager = UpdateManager(session=FakeSession([]))
    result = manager.check_for_updates(force=False)

    assert result.checked is False
    assert result.message == "Update check throttled"


def test_download_update_verifies_checksum(temp_config):
    payload = b"new version binary"
    digest = hashlib.sha256(payload).hexdigest()
    release_payload = {
        "update_available": True,
        "latest_version": "1.0.1+build.5",
        "product_version": "1.0.1",
        "channel": "stable",
        "platform": "windows",
        "arch": "x64",
        "mandatory": False,
        "published_at": "2026-04-17T10:00:00Z",
        "download_url": "https://update.devflux.ru/files/update.exe",
        "sha256": digest,
        "size": len(payload),
        "release_notes": "notes",
    }
    session = FakeSession([FakeResponse(payload=release_payload), FakeResponse(content=payload)])
    manager = UpdateManager(session=session)

    result = manager.check_for_updates(force=True)
    downloaded = manager.download_update(result.release)

    assert downloaded.file_path.exists()
    assert downloaded.file_path.read_bytes() == payload


def test_download_update_rejects_bad_checksum(temp_config):
    payload = b"new version binary"
    session = FakeSession([FakeResponse(content=payload)])
    manager = UpdateManager(session=session)
    release = manager._parse_release(
        {
            "latest_version": "1.0.1+build.5",
            "product_version": "1.0.1",
            "channel": "stable",
            "platform": "windows",
            "arch": "x64",
            "mandatory": False,
            "published_at": "2026-04-17T10:00:00Z",
            "download_url": "https://update.devflux.ru/files/update.exe",
            "sha256": "0" * 64,
            "size": len(payload),
            "release_notes": "notes",
        },
        "https://update.devflux.ru",
    )

    with pytest.raises(UpdateError):
        manager.download_update(release)


def test_no_update_when_product_version_matches(temp_config):
    payload = {
        "update_available": True,
        "latest_version": "1.0.0+build.99",
        "product_version": "1.0.0",
        "channel": "stable",
        "platform": "windows",
        "arch": "x64",
        "mandatory": False,
        "published_at": "2026-04-17T10:00:00Z",
        "download_url": "https://update.devflux.ru/files/update.exe",
        "sha256": "a" * 64,
        "size": 123,
        "release_notes": "notes",
    }
    manager = UpdateManager(session=FakeSession([FakeResponse(payload=payload)]))

    result = manager.check_for_updates(force=True)

    assert result.update_available is False
    assert result.message == "Current version is up to date"


def test_malformed_json_does_not_crash(temp_config):
    manager = UpdateManager(
        session=FakeSession([FakeResponse(raise_json=True), FakeResponse(status_code=204)])
    )

    result = manager.check_for_updates(force=True)

    assert result.update_available is False
    assert result.message == "No updates available"
