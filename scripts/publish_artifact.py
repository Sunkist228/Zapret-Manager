#!/usr/bin/env python3
"""
Публикация артефакта в Artifact Server (из Playerok-devflux).
Используется в Jenkins pipeline для публикации Windows EXE.

Usage:
    python scripts/publish_artifact.py \\
        --url https://artifacts.example.com \\
        --api-key YOUR_API_KEY \\
        --version 1.0.0 \\
        --channel stable \\
        --file dist/ZapretManager.exe \\
        --platform windows \\
        --arch x64
"""
import argparse
import json
import sys
from pathlib import Path

try:
    import requests
except ImportError:
    print('ERROR: requests library not installed')
    print('Install: pip install requests')
    sys.exit(1)


def publish_artifact(url, api_key, version, channel, file_path, platform, arch):
    """
    Публикация артефакта в Artifact Server.

    Args:
        url: Base URL artifact server
        api_key: API ключ для аутентификации
        version: Версия артефакта (e.g., 1.0.0)
        channel: Канал публикации (stable, dev, pre-dev)
        file_path: Путь к файлу артефакта
        platform: Платформа (windows, linux, macos)
        arch: Архитектура (x64, x86, arm64)
    """
    file_path = Path(file_path)

    if not file_path.exists():
        print(f'ERROR: Artifact file not found: {file_path}')
        sys.exit(1)

    base_url = url.rstrip('/')
    headers = {'X-Api-Key': api_key}

    # Slug для zapret2
    slug = 'zapret-manager'

    # 1. Проверяем/создаем артефакт
    print(f'Checking artifact definition: {slug}')
    artifact_resp = requests.get(
        f'{base_url}/api/v1/artifacts/{slug}',
        headers=headers,
        timeout=10
    )

    if artifact_resp.status_code == 404:
        print(f'Creating artifact definition: {slug}')
        artifact_def = {
            'slug': slug,
            'name': 'Zapret Manager',
            'category': 'binary',
            'project': 'zapret2',
            'is_public': True,
        }
        create_resp = requests.post(
            f'{base_url}/api/v1/artifacts/',
            headers=headers,
            json=artifact_def,
            timeout=10
        )
        if create_resp.status_code not in (201, 409):
            print(f'ERROR: Failed to create artifact: {create_resp.status_code}')
            print(create_resp.text)
            sys.exit(1)
        print('✓ Artifact definition created')
    elif artifact_resp.status_code != 200:
        print(f'ERROR: Failed to check artifact: {artifact_resp.status_code}')
        print(artifact_resp.text)
        sys.exit(1)
    else:
        print('✓ Artifact definition exists')

    # 2. Загружаем файл
    print(f'Uploading artifact: {file_path.name} ({file_path.stat().st_size / 1024 / 1024:.2f} MB)')

    with file_path.open('rb') as f:
        upload_resp = requests.post(
            f'{base_url}/api/v1/artifacts/{slug}/upload',
            headers=headers,
            files={'file': (file_path.name, f)},
            data={
                'version': version,
                'platform': platform,
                'arch': arch,
            },
            timeout=300
        )

    if upload_resp.status_code not in (200, 201):
        print(f'ERROR: Failed to upload artifact: {upload_resp.status_code}')
        print(upload_resp.text)
        sys.exit(1)

    upload_data = upload_resp.json()
    print('✓ Artifact uploaded')
    print(f'  Version ID: {upload_data.get("version", {}).get("id")}')
    print(f'  Checksum: {upload_data.get("checksum")}')
    print(f'  Download URL: {upload_data.get("download_url")}')

    # 3. Публикуем в канал
    print(f'Promoting to channel: {channel}')

    promote_resp = requests.post(
        f'{base_url}/api/v1/channels/{slug}/promote',
        headers=headers,
        json={
            'version_id': upload_data['version']['id'],
            'channel_name': channel,
            'platform': platform,
            'arch': arch,
        },
        timeout=10
    )

    if promote_resp.status_code != 200:
        print(f'ERROR: Failed to promote to channel: {promote_resp.status_code}')
        print(promote_resp.text)
        sys.exit(1)

    print(f'✓ Promoted to {channel} channel')
    print()
    print('Publication successful!')
    print(f'  Artifact: {slug}')
    print(f'  Version: {version}')
    print(f'  Platform: {platform}/{arch}')
    print(f'  Channel: {channel}')
    print(f'  Download: {upload_data.get("download_url")}')

    return upload_data


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Publish artifact to Artifact Server'
    )
    parser.add_argument('--url', required=True, help='Artifact server base URL')
    parser.add_argument('--api-key', required=True, help='API key for authentication')
    parser.add_argument('--version', required=True, help='Artifact version (e.g., 1.0.0)')
    parser.add_argument('--channel', required=True, help='Publication channel (stable, dev, pre-dev)')
    parser.add_argument('--file', required=True, help='Path to artifact file')
    parser.add_argument('--platform', required=True, help='Platform (windows, linux, macos)')
    parser.add_argument('--arch', required=True, help='Architecture (x64, x86, arm64)')

    args = parser.parse_args()

    try:
        publish_artifact(
            args.url,
            args.api_key,
            args.version,
            args.channel,
            args.file,
            args.platform,
            args.arch
        )
    except requests.exceptions.RequestException as e:
        print(f'ERROR: Network error: {e}')
        sys.exit(1)
    except Exception as e:
        print(f'ERROR: {e}')
        sys.exit(1)
