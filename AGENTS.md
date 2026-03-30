# Agents Guide — Zerobyte HACS Integration

## Project Overview

This is a Home Assistant custom integration (HACS-compatible) for
[Zerobyte](https://github.com/nicotsx/zerobyte), a backup automation tool
built on top of Restic. The integration polls the Zerobyte REST API and
exposes backup schedules, volumes, and repositories as HA entities.

## Repository Layout

```
hacs.json                              # HACS metadata (name, min HA version)
AGENTS.md                              # This file
README.md                              # User-facing documentation
custom_components/zerobyte/
  manifest.json                        # HA integration manifest (domain, version, iot_class)
  __init__.py                          # Entry setup / teardown
  api.py                               # ZerobyteApiClient — HTTP client with cookie auth
  config_flow.py                       # UI configuration flow (host, email, password, verify_ssl)
  const.py                             # Constants (DOMAIN, config keys, defaults)
  coordinator.py                       # DataUpdateCoordinator — polls every 5 min
  data.py                              # Type aliases (ZerobyteConfigEntry, ZerobyteData)
  entity.py                            # Base entity class with shared DeviceInfo
  sensor.py                            # Sensor entities (status, timestamps, sizes, counts)
  binary_sensor.py                     # Binary sensor entities (enabled, health)
  strings.json                         # Config flow UI strings and error messages
  icons/
    icon.png                           # Zerobyte logo (512×512 PNG from upstream)
```

## Architecture

- **Authentication**: Zerobyte uses `better-auth` with cookie-based sessions.
  The client authenticates via `POST /api/auth/sign-in/email` and stores the
  `better-auth.session_token` cookie. It re-authenticates automatically on 401.
- **Coordinator pattern**: A single `ZerobyteDataUpdateCoordinator` fetches all
  three resource types (volumes, repositories + stats, backups) in one cycle.
  All entities read from this shared coordinator data.
- **Entity naming**: Names follow the pattern `<ResourceType> - <ItemName> <Sensor>`,
  e.g. "Backup - Daily NAS Status".
- **Unique IDs**: Entity unique IDs are `{entry_id}_{collection}_{shortId}_{key}`.
  These must remain stable — do not change the key format.

## Zerobyte API Reference

Base URL is user-configured (e.g. `http://192.168.1.59:4096`).

| Method | Endpoint                                | Purpose                      |
|--------|-----------------------------------------|------------------------------|
| POST   | /api/auth/sign-in/email                 | Authenticate (email+password)|
| GET    | /api/v1/volumes                         | List all volumes             |
| GET    | /api/v1/repositories                    | List all repositories        |
| GET    | /api/v1/repositories/{shortId}/stats    | Repository size & snapshots  |
| GET    | /api/v1/backups                         | List all backup schedules    |

The full OpenAPI spec is available at `/api/v1/openapi.json` on any running
Zerobyte instance.

## Key Data Shapes

**Backup schedule** fields used by entities:
`shortId`, `name`, `enabled`, `lastBackupStatus` (success/error/in_progress/warning),
`lastBackupAt` (epoch ms), `nextBackupAt` (epoch ms).

**Volume** fields used:
`shortId`, `name`, `status` (mounted/unmounted/error), `type` (nfs/smb/directory/webdav/rclone/sftp).

**Repository** fields used:
`shortId`, `name`, `status` (healthy/error/unknown/doctor/cancelled),
`type` (local/s3/r2/gcs/azure/rclone/rest/sftp).
Stats sub-object: `total_size` (bytes), `snapshots_count`.

## Development Notes

- This is a pure Python project. No build step required.
- The integration has no PyPI dependencies beyond what HA provides (`aiohttp`, `async_timeout`, `voluptuous`).
- To test locally, copy `custom_components/zerobyte/` into a HA dev instance's
  `config/custom_components/` directory and restart.
- Timestamps from the Zerobyte API are in **milliseconds** since epoch. The
  `_epoch_to_datetime` helper in `sensor.py` divides by 1000.

## HACS Publishing Checklist

- `hacs.json` at repo root with `name` and `homeassistant` minimum version.
- `manifest.json` must have: `domain`, `name`, `version`, `documentation`,
  `issue_tracker`, `codeowners`, `config_flow`, `iot_class`.
- One integration per repo under `custom_components/<domain>/`.
- Tag releases with semver (e.g. `v0.1.0`). HACS shows the 5 latest releases.

## Common Maintenance Tasks

- **Adding a new sensor**: Add a `ZerobyteSensorEntityDescription` tuple entry
  in `sensor.py` (or `binary_sensor.py`). Set `collection`, `resource_prefix`,
  `key`, `value_fn`/`is_on_fn`. The setup loop auto-discovers items.
- **Adding a new API endpoint**: Add a method to `ZerobyteApiClient` in `api.py`.
  If it should be fetched every cycle, call it from `coordinator.py`'s
  `_async_update_data` and add the result to the returned dict.
- **Changing poll interval**: Edit `DEFAULT_SCAN_INTERVAL` in `const.py`.
- **Updating the icon**: Replace `custom_components/zerobyte/icons/icon.png`.
