# Docker support for CorpBot.py

This is a short document detailing the current status of the Docker images, including how to set them up.

## Features

#### Implemented

- [x] Bot running smoothly inside Docker (tested and works well)
- [x] Full data persistence (data is stored under `/data`, see `docker-compose.yml`)
- [x] Lavalink support both as a Docker container and an external service (playback tested and works well)
- [x] Docker image for Linux (tested and working)
- [x] Docker image for Windows (largely untested)

#### Planned

- [ ] Redis support (redis branch)
- [ ] MongoDB support (same deal)
- [ ] Optimized, minimal image sizes (Alpine, multi-staged builds, Windows image needs special attention)

## Running

Create a `.env` file at the root of this project with the following environment variables):
```
SETTINGS_DICT_PREFIX="<bot_prefix>"
SETTINGS_DICT_TOKEN="<discord_bot_token>"
SETTINGS_DICT_WEATHER="<weather_api_token>"
SETTINGS_DICT_CURRENCY="<currency_api_token>"
SETTINGS_DICT_SETTINGS_PATH="<path_to_settings.json>            (optional)
SETTINGS_DICT_SETTINGS_BACKUP_PATH="<path_to_settings_backups>" (optional)
SETTINGS_DICT_LAVALINK_HOST="<lavalink_hostname_or_ip>"         (optional)
SETTINGS_DICT_LAVALINK_REGION="<lavalink_discord_region>"       (optional)
SETTINGS_DICT_LAVALINK_PASSWORD="<lavalink_password>"           (optional)
```

Build and run with Docker Compose while inside the `./docker/` directory:
> docker-compose up --build

To bring it down with Docker Compose:
> docker-compose down
