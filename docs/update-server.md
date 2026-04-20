# Update Server Contract

This client checks these endpoints in failover order:

- `https://artifact.devflux.ru/api/v1/update/check`
- `https://update.devflux.ru/api/v1/update/check`

Query parameters:

- `artifact=zapret-manager`
- `channel=stable`
- `platform=windows`
- `arch=x64`
- `version=<current_product_version>`

Successful responses:

- `204 No Content` means no update is available.
- `200 OK` may also return `{"update_available": false}`.
- `200 OK` with update metadata must include:
  - `latest_version`
  - `product_version`
  - `channel`
  - `platform`
  - `arch`
  - `mandatory`
  - `published_at`
  - `download_url`
  - `sha256`
  - `size`
  - `release_notes`

Example payload:

```json
{
  "update_available": true,
  "latest_version": "1.0.1+build.42.sha.abcdef123456",
  "product_version": "1.0.1",
  "channel": "stable",
  "platform": "windows",
  "arch": "x64",
  "mandatory": false,
  "published_at": "2026-04-17T10:00:00Z",
  "download_url": "https://artifact.devflux.ru/downloads/zapret-manager-1.0.1.exe",
  "sha256": "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef",
  "size": 73400320,
  "release_notes": "Bug fixes and update foundation"
}
```

Notes:

- `latest_version` may include build metadata from Jenkins.
- `product_version` must be plain SemVer and is the field the client compares.
- Both hostnames should serve identical semantics; the client treats them as active-active failover.
- `scripts/publish_artifact.py` now accepts `--product-version` so the server can store both build version and product SemVer.
