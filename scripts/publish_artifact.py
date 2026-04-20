#!/usr/bin/env python3
"""
Publish artifact to Artifact Server.

Usage:
    python scripts/publish_artifact.py \
        --url https://artifacts.example.com \
        --api-key YOUR_API_KEY \
        --version 1.0.0+build.1 \
        --product-version 1.0.0 \
        --channel stable \
        --file dist/ZapretManager.exe \
        --platform windows \
        --arch x64
"""

import argparse
import sys
from pathlib import Path

try:
    import requests
except ImportError:
    print("ERROR: requests library not installed")
    print("Install: pip install requests")
    sys.exit(1)


def publish_artifact(
    url,
    api_key,
    version,
    channel,
    file_path,
    platform,
    arch,
    product_version=None,
):
    """
    Publish artifact to Artifact Server.

    Args:
        url: Base URL artifact server
        api_key: API key for authentication
        version: Artifact build version
        channel: Publication channel (stable, dev, pre-dev)
        file_path: Path to artifact file
        platform: Platform (windows, linux, macos)
        arch: Architecture (x64, x86, arm64)
        product_version: Product SemVer without build metadata
    """
    file_path = Path(file_path)

    if not file_path.exists():
        print(f"ERROR: Artifact file not found: {file_path}")
        sys.exit(1)

    base_url = url.rstrip("/")
    headers = {"X-Api-Key": api_key}
    slug = "zapret-manager"

    print(f"Checking artifact definition: {slug}")
    artifact_resp = requests.get(
        f"{base_url}/api/v1/artifacts/{slug}",
        headers=headers,
        timeout=10,
    )

    if artifact_resp.status_code == 404:
        print(f"Creating artifact definition: {slug}")
        artifact_def = {
            "slug": slug,
            "name": "Zapret Manager",
            "category": "binary",
            "project": "zapret2",
            "is_public": True,
        }
        create_resp = requests.post(
            f"{base_url}/api/v1/artifacts/",
            headers=headers,
            json=artifact_def,
            timeout=10,
        )
        if create_resp.status_code not in (201, 409):
            print(f"ERROR: Failed to create artifact: {create_resp.status_code}")
            print(create_resp.text)
            sys.exit(1)
        print("OK: Artifact definition created")
    elif artifact_resp.status_code != 200:
        print(f"ERROR: Failed to check artifact: {artifact_resp.status_code}")
        print(artifact_resp.text)
        sys.exit(1)
    else:
        print("OK: Artifact definition exists")

    print(f"Uploading artifact: {file_path.name} ({file_path.stat().st_size / 1024 / 1024:.2f} MB)")

    upload_payload = {
        "version": version,
        "platform": platform,
        "arch": arch,
    }
    if product_version:
        upload_payload["product_version"] = product_version

    with file_path.open("rb") as handle:
        upload_resp = requests.post(
            f"{base_url}/api/v1/artifacts/{slug}/upload",
            headers=headers,
            files={"file": (file_path.name, handle)},
            data=upload_payload,
            timeout=300,
        )

    if upload_resp.status_code not in (200, 201):
        print(f"ERROR: Failed to upload artifact: {upload_resp.status_code}")
        print(upload_resp.text)
        sys.exit(1)

    upload_data = upload_resp.json()
    print("OK: Artifact uploaded")
    print(f"  Version ID: {upload_data.get('version', {}).get('id')}")
    print(f"  Checksum: {upload_data.get('checksum')}")
    print(f"  Download URL: {upload_data.get('download_url')}")

    print(f"Promoting to channel: {channel}")

    promote_resp = requests.post(
        f"{base_url}/api/v1/channels/{slug}/promote",
        headers=headers,
        json={
            "version_id": upload_data["version"]["id"],
            "channel_name": channel,
            "platform": platform,
            "arch": arch,
        },
        timeout=10,
    )

    if promote_resp.status_code != 200:
        print(f"ERROR: Failed to promote to channel: {promote_resp.status_code}")
        print(promote_resp.text)
        sys.exit(1)

    print(f"OK: Promoted to {channel} channel")
    print()
    print("Publication successful!")
    print(f"  Artifact: {slug}")
    print(f"  Build version: {version}")
    if product_version:
        print(f"  Product version: {product_version}")
    print(f"  Platform: {platform}/{arch}")
    print(f"  Channel: {channel}")
    print(f"  Download: {upload_data.get('download_url')}")

    return upload_data


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Publish artifact to Artifact Server")
    parser.add_argument("--url", required=True, help="Artifact server base URL")
    parser.add_argument("--api-key", required=True, help="API key for authentication")
    parser.add_argument("--version", required=True, help="Artifact version (e.g., 1.0.0+build.1)")
    parser.add_argument("--product-version", help="Product SemVer without build metadata")
    parser.add_argument(
        "--channel", required=True, help="Publication channel (stable, dev, pre-dev)"
    )
    parser.add_argument("--file", required=True, help="Path to artifact file")
    parser.add_argument("--platform", required=True, help="Platform (windows, linux, macos)")
    parser.add_argument("--arch", required=True, help="Architecture (x64, x86, arm64)")

    args = parser.parse_args()

    try:
        publish_artifact(
            args.url,
            args.api_key,
            args.version,
            args.channel,
            args.file,
            args.platform,
            args.arch,
            args.product_version,
        )
    except requests.exceptions.RequestException as exc:
        print(f"ERROR: Network error: {exc}")
        sys.exit(1)
    except Exception as exc:
        print(f"ERROR: {exc}")
        sys.exit(1)
