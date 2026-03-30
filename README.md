# Zerobyte Integration for Home Assistant

A [HACS](https://hacs.xyz/) custom integration that connects [Zerobyte](https://github.com/nicotsx/zerobyte) to Home Assistant, giving you visibility into your backup schedules, volumes, and repositories.

## Features

- **Backup schedules** -- status, last/next backup timestamps, enabled state
- **Volumes** -- mount status, type (NFS, SMB, SFTP, etc.), health
- **Repositories** -- health, type, total size, snapshot count

All entities are grouped under a single Zerobyte device per instance.

## Installation

### HACS (recommended)

1. Open HACS in Home Assistant
2. Go to **Integrations** and click the three-dot menu
3. Select **Custom repositories**
4. Add the repository URL and choose **Integration** as the category
5. Search for **Zerobyte** and install it
6. Restart Home Assistant

### Manual

1. Copy the `custom_components/zerobyte` folder into your Home Assistant `config/custom_components/` directory
2. Restart Home Assistant

## Configuration

1. Go to **Settings > Devices & Services > Add Integration**
2. Search for **Zerobyte**
3. Enter:
   - **URL** -- the base URL of your Zerobyte instance (e.g. `http://192.168.1.59:4096`)
   - **Email** -- your Zerobyte account email
   - **Password** -- your Zerobyte account password
   - **Verify SSL** -- uncheck if you use a self-signed certificate
4. Click **Submit**

## Entities

### Sensors

| Entity | Description |
|--------|-------------|
| `sensor.<backup>_status` | Last backup status (success / error / in_progress / warning) |
| `sensor.<backup>_last_backup` | Timestamp of the last backup |
| `sensor.<backup>_next_backup` | Timestamp of the next scheduled backup |
| `sensor.<volume>_status` | Volume mount status (mounted / unmounted / error) |
| `sensor.<volume>_type` | Volume backend type |
| `sensor.<repo>_status` | Repository health status |
| `sensor.<repo>_type` | Repository backend type |
| `sensor.<repo>_size` | Total repository size |
| `sensor.<repo>_snapshots` | Number of snapshots in the repository |

### Binary Sensors

| Entity | Description |
|--------|-------------|
| `binary_sensor.<backup>_enabled` | Whether the backup schedule is active |
| `binary_sensor.<volume>_health` | Whether the volume is mounted |
| `binary_sensor.<repo>_health` | Whether the repository has a problem |

## Polling Interval

Data is refreshed every 5 minutes. This is not configurable in the current version.
