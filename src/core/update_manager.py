# -*- coding: utf-8 -*-
"""
Auto-update client for Zapret Manager.
"""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import tempfile
import textwrap
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.parse import urljoin

import requests

try:
    from utils.config import Config
    from utils.logger import logger
    from utils.versioning import compare_versions, normalize_product_version
except ImportError:
    from ..utils.config import Config
    from ..utils.logger import logger
    from ..utils.versioning import compare_versions, normalize_product_version


class UpdateError(Exception):
    """Raised when update operations fail."""


@dataclass
class UpdateRelease:
    version: str
    product_version: str
    channel: str
    platform: str
    arch: str
    mandatory: bool
    published_at: Optional[str]
    download_url: str
    sha256: str
    size: Optional[int]
    release_notes: str
    source_endpoint: str


@dataclass
class DownloadedUpdate:
    release: UpdateRelease
    file_path: Path
    downloaded_at: str


@dataclass
class UpdateCheckResult:
    checked: bool
    update_available: bool
    current_version: str
    current_product_version: str
    release: Optional[UpdateRelease] = None
    downloaded_update: Optional[DownloadedUpdate] = None
    message: str = ""
    endpoint: Optional[str] = None


class UpdateManager:
    """Client-side update manager with endpoint failover."""

    def __init__(self, session: Optional[requests.Session] = None):
        self.session = session or requests.Session()
        self.config = Config
        self.state_file = self.config.UPDATE_STATE_FILE
        self.download_dir = self.config.UPDATE_DOWNLOAD_DIR

    def check_for_updates(self, force: bool = False) -> UpdateCheckResult:
        """Check update endpoint(s) for a newer release."""
        self._ensure_paths()
        state = self._load_state()

        if not force and not self._should_check(state):
            return UpdateCheckResult(
                checked=False,
                update_available=False,
                current_version=self.config.VERSION,
                current_product_version=self.config.PRODUCT_VERSION,
                downloaded_update=self.get_downloaded_update(),
                message="Update check throttled",
                endpoint=state.get("last_successful_endpoint"),
            )

        last_error = None
        endpoints = self._ordered_endpoints(state)

        for endpoint in endpoints:
            try:
                result = self._check_endpoint(endpoint)
                state["last_check_at"] = _utcnow_iso()
                # Store the URL for preference tracking
                endpoint_url = endpoint.get("url") if isinstance(endpoint, dict) else endpoint
                state["last_successful_endpoint"] = endpoint_url
                self._save_state(state)
                return result
            except Exception as exc:
                last_error = str(exc)
                endpoint_url = endpoint.get("url") if isinstance(endpoint, dict) else endpoint
                logger.warning("Update endpoint %s failed: %s", endpoint_url, exc)

        state["last_check_at"] = _utcnow_iso()
        self._save_state(state)
        return UpdateCheckResult(
            checked=True,
            update_available=False,
            current_version=self.config.VERSION,
            current_product_version=self.config.PRODUCT_VERSION,
            downloaded_update=self.get_downloaded_update(),
            message=last_error or "No update endpoints available",
        )

    def download_update(self, release: UpdateRelease) -> DownloadedUpdate:
        """Download and verify an update package."""
        self._ensure_paths()
        response = self.session.get(release.download_url, stream=True, timeout=60)
        response.raise_for_status()

        target_path = self.download_dir / f"ZapretManager-{release.product_version}.exe"
        hasher = hashlib.sha256()

        with target_path.open("wb") as handle:
            for chunk in response.iter_content(chunk_size=1024 * 256):
                if not chunk:
                    continue
                handle.write(chunk)
                hasher.update(chunk)

        digest = hasher.hexdigest().lower()
        if digest != release.sha256.lower():
            target_path.unlink(missing_ok=True)
            raise UpdateError("Downloaded update checksum mismatch")

        downloaded = DownloadedUpdate(
            release=release,
            file_path=target_path,
            downloaded_at=_utcnow_iso(),
        )

        state = self._load_state()
        state["downloaded_update"] = self._serialize_downloaded_update(downloaded)
        self._save_state(state)
        return downloaded

    def install_update(self, downloaded: DownloadedUpdate) -> None:
        """Launch helper process that swaps the EXE after shutdown."""
        if not self.config.IS_FROZEN:
            raise UpdateError("Auto-install is supported only for frozen EXE builds")

        if not downloaded.file_path.exists():
            raise UpdateError("Downloaded update file is missing")

        target_exe = Path(sys.executable).resolve()
        script_path = self._write_helper_script(downloaded, target_exe)

        subprocess.Popen(
            [
                "powershell",
                "-NoProfile",
                "-ExecutionPolicy",
                "Bypass",
                "-File",
                str(script_path),
            ],
            creationflags=subprocess.CREATE_NO_WINDOW,
        )

    def get_downloaded_update(self) -> Optional[DownloadedUpdate]:
        """Return cached verified download if still present."""
        state = self._load_state()
        payload = state.get("downloaded_update")
        if not isinstance(payload, dict):
            return None

        try:
            downloaded = self._deserialize_downloaded_update(payload)
        except Exception:
            return None

        if not downloaded.file_path.exists():
            state.pop("downloaded_update", None)
            self._save_state(state)
            return None

        return downloaded

    def clear_downloaded_update(self) -> None:
        """Remove cached downloaded update metadata."""
        state = self._load_state()
        state.pop("downloaded_update", None)
        self._save_state(state)

    def _check_endpoint(self, endpoint: str) -> UpdateCheckResult:
        """Check a single endpoint for updates."""
        # Handle both old string format and new dict format
        if isinstance(endpoint, dict):
            endpoint_type = endpoint.get("type", "artifact_server")
            endpoint_url = endpoint.get("url")
        else:
            # Legacy string format
            endpoint_type = "artifact_server"
            endpoint_url = endpoint

        if endpoint_type == "github":
            return self._check_github_releases(endpoint_url)
        else:
            return self._check_artifact_server(endpoint_url)

    def _check_github_releases(self, api_base: str) -> UpdateCheckResult:
        """Check GitHub Releases for updates."""
        current_version = self.config.VERSION
        current_product_version = self.config.PRODUCT_VERSION

        # Build GitHub API URL
        owner = self.config.GITHUB_REPO_OWNER
        repo = self.config.GITHUB_REPO_NAME
        url = f"{api_base}/repos/{owner}/{repo}/releases/latest"

        try:
            response = self.session.get(url, timeout=15)
        except requests.RequestException as exc:
            raise UpdateError(f"GitHub API request failed: {exc}") from exc

        # Check rate limit
        rate_limit_remaining = response.headers.get("X-RateLimit-Remaining")
        if rate_limit_remaining and int(rate_limit_remaining) < 10:
            logger.warning(f"GitHub API rate limit low: {rate_limit_remaining} remaining")

        if response.status_code == 404:
            return UpdateCheckResult(
                checked=True,
                update_available=False,
                current_version=current_version,
                current_product_version=current_product_version,
                downloaded_update=self.get_downloaded_update(),
                message="No releases found on GitHub",
                endpoint=api_base,
            )

        if response.status_code != 200:
            raise UpdateError(f"GitHub API returned {response.status_code}")

        try:
            payload = response.json()
        except ValueError as exc:
            raise UpdateError(f"Invalid JSON from GitHub API: {exc}") from exc

        # Parse release
        tag_name = payload.get("tag_name", "")
        if not tag_name:
            raise UpdateError("No tag_name in GitHub release")

        # Remove 'v' prefix if present
        version_str = tag_name.lstrip("v")

        # Find the Windows x64 asset
        assets = payload.get("assets", [])
        asset = None
        sha256_asset = None

        for a in assets:
            name = a.get("name", "")
            if name == "zapret-manager-windows-x64.exe":
                asset = a
            elif name == "zapret-manager-windows-x64.exe.sha256":
                sha256_asset = a

        if not asset:
            raise UpdateError("No Windows x64 asset found in GitHub release")

        download_url = asset.get("browser_download_url")
        if not download_url:
            raise UpdateError("No download URL in GitHub asset")

        # Get SHA256
        sha256 = ""
        if sha256_asset:
            sha256_url = sha256_asset.get("browser_download_url")
            try:
                sha256_response = self.session.get(sha256_url, timeout=10)
                if sha256_response.status_code == 200:
                    sha256 = sha256_response.text.strip()
            except Exception:
                pass

        if not sha256:
            logger.warning("No SHA256 checksum found for GitHub release")
            sha256 = ""  # Will skip verification

        # Create UpdateRelease
        release = UpdateRelease(
            version=version_str,
            product_version=normalize_product_version(version_str),
            channel=self.config.UPDATE_CHANNEL,
            platform=self.config.UPDATE_PLATFORM,
            arch=self.config.UPDATE_ARCH,
            mandatory=False,
            published_at=payload.get("published_at"),
            download_url=download_url,
            sha256=sha256,
            size=asset.get("size"),
            release_notes=payload.get("body", ""),
            source_endpoint=api_base,
        )

        # Compare versions
        if compare_versions(current_product_version, release.product_version) >= 0:
            return UpdateCheckResult(
                checked=True,
                update_available=False,
                current_version=current_version,
                current_product_version=current_product_version,
                downloaded_update=self.get_downloaded_update(),
                message="Current version is up to date",
                endpoint=api_base,
            )

        # Check if we already downloaded this version
        downloaded = self.get_downloaded_update()
        if downloaded and downloaded.release.product_version != release.product_version:
            self.clear_downloaded_update()
            downloaded = None

        return UpdateCheckResult(
            checked=True,
            update_available=True,
            current_version=current_version,
            current_product_version=current_product_version,
            release=release,
            downloaded_update=downloaded,
            message=f"Update available: {release.product_version}",
            endpoint=api_base,
        )

    def _check_artifact_server(self, endpoint: str) -> UpdateCheckResult:
        """Check artifact server for updates (original implementation)."""
        current_version = self.config.VERSION
        current_product_version = self.config.PRODUCT_VERSION
        params = {
            "artifact": self.config.UPDATE_ARTIFACT_SLUG,
            "channel": self.config.UPDATE_CHANNEL,
            "platform": self.config.UPDATE_PLATFORM,
            "arch": self.config.UPDATE_ARCH,
            "version": current_product_version,
        }

        url = urljoin(endpoint.rstrip("/") + "/", self.config.UPDATE_CHECK_PATH.lstrip("/"))

        try:
            response = self.session.get(url, params=params, timeout=15)
        except requests.RequestException as exc:
            raise UpdateError(f"Request failed: {exc}") from exc

        if response.status_code == 204:
            return UpdateCheckResult(
                checked=True,
                update_available=False,
                current_version=current_version,
                current_product_version=current_product_version,
                downloaded_update=self.get_downloaded_update(),
                message="No updates available",
                endpoint=endpoint,
            )

        if response.status_code != 200:
            raise UpdateError(f"Unexpected response: {response.status_code}")

        try:
            payload = response.json()
        except ValueError as exc:
            raise UpdateError(f"Invalid JSON payload: {exc}") from exc

        if not payload.get("update_available", True):
            return UpdateCheckResult(
                checked=True,
                update_available=False,
                current_version=current_version,
                current_product_version=current_product_version,
                downloaded_update=self.get_downloaded_update(),
                message="No updates available",
                endpoint=endpoint,
            )

        release = self._parse_release(payload, endpoint)
        if compare_versions(current_product_version, release.product_version) >= 0:
            return UpdateCheckResult(
                checked=True,
                update_available=False,
                current_version=current_version,
                current_product_version=current_product_version,
                downloaded_update=self.get_downloaded_update(),
                message="Current version is up to date",
                endpoint=endpoint,
            )

        downloaded = self.get_downloaded_update()
        if downloaded and downloaded.release.product_version != release.product_version:
            self.clear_downloaded_update()
            downloaded = None

        return UpdateCheckResult(
            checked=True,
            update_available=True,
            current_version=current_version,
            current_product_version=current_product_version,
            release=release,
            downloaded_update=downloaded,
            message=f"Update available: {release.product_version}",
            endpoint=endpoint,
        )

    def _parse_release(self, payload: Dict[str, Any], endpoint: str) -> UpdateRelease:
        required_fields = [
            "latest_version",
            "product_version",
            "channel",
            "platform",
            "arch",
            "download_url",
            "sha256",
        ]
        missing = [field for field in required_fields if not payload.get(field)]
        if missing:
            raise UpdateError(f"Update payload missing fields: {', '.join(missing)}")

        return UpdateRelease(
            version=str(payload["latest_version"]),
            product_version=normalize_product_version(str(payload["product_version"])),
            channel=str(payload["channel"]),
            platform=str(payload["platform"]),
            arch=str(payload["arch"]),
            mandatory=bool(payload.get("mandatory", False)),
            published_at=payload.get("published_at"),
            download_url=str(payload["download_url"]),
            sha256=str(payload["sha256"]),
            size=int(payload["size"]) if payload.get("size") is not None else None,
            release_notes=str(payload.get("release_notes", "")),
            source_endpoint=endpoint,
        )

    def _ordered_endpoints(self, state: Dict[str, Any]) -> List[str]:
        """Order endpoints with preferred endpoint first."""
        endpoints = list(self.config.UPDATE_ENDPOINTS)
        preferred = state.get("last_successful_endpoint")

        if preferred:
            # Find and move preferred endpoint to front
            for i, ep in enumerate(endpoints):
                ep_url = ep.get("url") if isinstance(ep, dict) else ep
                if ep_url == preferred:
                    endpoints.insert(0, endpoints.pop(i))
                    break

        return endpoints

    def _should_check(self, state: Dict[str, Any]) -> bool:
        if not self.config.UPDATE_ENABLED:
            return False

        last_check_at = state.get("last_check_at")
        if not last_check_at:
            return True

        try:
            last_check = _parse_iso(last_check_at)
        except ValueError:
            return True

        return datetime.now(timezone.utc) - last_check >= timedelta(
            hours=self.config.UPDATE_CHECK_INTERVAL_HOURS
        )

    def _ensure_paths(self) -> None:
        self.config.ensure_config_dir()
        self.download_dir.mkdir(parents=True, exist_ok=True)

    def _load_state(self) -> Dict[str, Any]:
        if not self.state_file.exists():
            return {}

        try:
            return json.loads(self.state_file.read_text(encoding="utf-8"))
        except Exception:
            return {}

    def _save_state(self, state: Dict[str, Any]) -> None:
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        self.state_file.write_text(
            json.dumps(state, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def _serialize_downloaded_update(self, downloaded: DownloadedUpdate) -> Dict[str, Any]:
        return {
            "release": {
                "version": downloaded.release.version,
                "product_version": downloaded.release.product_version,
                "channel": downloaded.release.channel,
                "platform": downloaded.release.platform,
                "arch": downloaded.release.arch,
                "mandatory": downloaded.release.mandatory,
                "published_at": downloaded.release.published_at,
                "download_url": downloaded.release.download_url,
                "sha256": downloaded.release.sha256,
                "size": downloaded.release.size,
                "release_notes": downloaded.release.release_notes,
                "source_endpoint": downloaded.release.source_endpoint,
            },
            "file_path": str(downloaded.file_path),
            "downloaded_at": downloaded.downloaded_at,
        }

    def _deserialize_downloaded_update(self, payload: Dict[str, Any]) -> DownloadedUpdate:
        release_payload = payload["release"]
        release = UpdateRelease(
            version=release_payload["version"],
            product_version=release_payload["product_version"],
            channel=release_payload["channel"],
            platform=release_payload["platform"],
            arch=release_payload["arch"],
            mandatory=bool(release_payload["mandatory"]),
            published_at=release_payload.get("published_at"),
            download_url=release_payload["download_url"],
            sha256=release_payload["sha256"],
            size=release_payload.get("size"),
            release_notes=release_payload.get("release_notes", ""),
            source_endpoint=release_payload["source_endpoint"],
        )
        return DownloadedUpdate(
            release=release,
            file_path=Path(payload["file_path"]),
            downloaded_at=payload["downloaded_at"],
        )

    def _write_helper_script(self, downloaded: DownloadedUpdate, target_exe: Path) -> Path:
        temp_dir = Path(tempfile.gettempdir()) / "ZapretManager" / "updates"
        temp_dir.mkdir(parents=True, exist_ok=True)
        backup_exe = target_exe.with_suffix(".old.exe")
        script_path = temp_dir / "apply_update.ps1"

        script = textwrap.dedent(
            f"""
            $ErrorActionPreference = "Stop"
            $targetExe = "{_ps_escape(target_exe)}"
            $newExe = "{_ps_escape(downloaded.file_path)}"
            $backupExe = "{_ps_escape(backup_exe)}"
            $workingDir = "{_ps_escape(target_exe.parent)}"
            $currentPid = {os.getpid()}

            for ($i = 0; $i -lt 120; $i++) {{
                if (-not (Get-Process -Id $currentPid -ErrorAction SilentlyContinue)) {{
                    break
                }}
                Start-Sleep -Milliseconds 500
            }}

            if (Test-Path $backupExe) {{
                Remove-Item $backupExe -Force -ErrorAction SilentlyContinue
            }}

            Move-Item -LiteralPath $targetExe -Destination $backupExe -Force
            Copy-Item -LiteralPath $newExe -Destination $targetExe -Force
            Start-Process -FilePath $targetExe -WorkingDirectory $workingDir
            """
        ).strip()

        script_path.write_text(script, encoding="utf-8")
        return script_path


def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _parse_iso(value: str) -> datetime:
    return datetime.fromisoformat(value)


def _ps_escape(value: Path | str) -> str:
    return str(value).replace('"', '`"')
