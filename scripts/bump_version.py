#!/usr/bin/env python3
"""
Автоматический bump версии в VERSION файле.
Использование: python scripts/bump_version.py [major|minor|patch]
"""
import sys
from pathlib import Path


def bump_version(bump_type):
    """Bump version in VERSION file."""
    version_file = Path(__file__).parent.parent / 'VERSION'

    if not version_file.exists():
        print(f'ERROR: VERSION file not found at {version_file}')
        sys.exit(1)

    current = version_file.read_text().strip()

    try:
        major, minor, patch = map(int, current.split('.'))
    except ValueError:
        print(f'ERROR: Invalid version format in VERSION file: {current}')
        print('Expected format: MAJOR.MINOR.PATCH (e.g., 1.0.0)')
        sys.exit(1)

    if bump_type == 'major':
        major += 1
        minor = 0
        patch = 0
    elif bump_type == 'minor':
        minor += 1
        patch = 0
    elif bump_type == 'patch':
        patch += 1
    else:
        print(f'ERROR: Invalid bump type: {bump_type}')
        print('Valid types: major, minor, patch')
        sys.exit(1)

    new_version = f'{major}.{minor}.{patch}'
    version_file.write_text(new_version + '\n')

    print(f'✓ Version bumped: {current} → {new_version}')
    print(f'  File: {version_file}')
    print()
    print('Next steps:')
    print('  1. Update CHANGELOG.md with release notes')
    print(f'  2. git commit -am "chore: bump version to {new_version}"')
    print(f'  3. git tag v{new_version}')
    print('  4. git push origin master --tags')

    return new_version


if __name__ == '__main__':
    if len(sys.argv) != 2 or sys.argv[1] not in ['major', 'minor', 'patch']:
        print('Usage: python scripts/bump_version.py [major|minor|patch]')
        print()
        print('Examples:')
        print('  python scripts/bump_version.py patch   # 1.0.0 → 1.0.1')
        print('  python scripts/bump_version.py minor   # 1.0.0 → 1.1.0')
        print('  python scripts/bump_version.py major   # 1.0.0 → 2.0.0')
        sys.exit(1)

    bump_version(sys.argv[1])
