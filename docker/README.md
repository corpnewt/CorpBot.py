# Docker support for CorpBot.py

**NOTE:** This is still a work in progress and may not be fully stable or bug free!

## Features

- [x] Bot and its basic features running inside a container
- [x] Working music playback through Lavalink
- [x] Linux support (Alpine)
- [x] Patch `Music.py` to read Lavalink settings from the config file instead
- [x] Expose persistable data (`Settings.json` and `Settings-Backup/`)
- [ ] Fix `Settings.json` mounting (it should ideally be in a folder that we can mount)
- [ ] Redis support (redis branch)
- [ ] MongoDB support (?)
- [ ] Minimal image size (Alpine, multi-staged builds)
- [ ] Windows support (coming soon, maybe)

## Running

Create a `.env` file at the root of this project with the following environment variables):
```
SETTINGS_DICT_PREFIX="<bot_prefix>"
SETTINGS_DICT_TOKEN="<discord_bot_token>"
SETTINGS_DICT_WEATHER="<weather_api_token>"
SETTINGS_DICT_CURRENCY="<currency_api_token>"
SETTINGS_DICT_LAVALINK_HOST="<lavalink_hostname_or_ip>"   (optional)
SETTINGS_DICT_LAVALINK_REGION="<lavalink_discord_region>" (optional)
SETTINGS_DICT_LAVALINK_PASSWORD="<lavalink_password>"     (optional)
```

Create an empty `Settings.json` file at the root of this project, which will be mounted by Docker Compose.

Build and run with Docker Compose while inside the `./docker/` directory:
> docker-compose up --build

To bring it down with Docker Compose:
> docker-compose down
