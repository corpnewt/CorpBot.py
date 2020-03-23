# Docker support for CorpBot.py

*NOTE:* This is still in progress and may not be fully stable or bug free!

## Features

- [x] Bot and its basic features running inside a container
- [x] Working music playback through Lavalink
- [x] Linux support (Alpine)
- [ ] Minimal image size (Alpine, multi-staged builds)
- [ ] Windows support (coming soon, maybe)

## Running

Create a `.env` file at the root of this project with the following environment variables:
```
SETTINGS_DICT_PREFIX="<bot_prefix>"
SETTINGS_DICT_TOKEN="<discord_bot_token>"
SETTINGS_DICT_WEATHER="<weather_api_token>"
SETTINGS_DICT_CURRENCY="<currency_api_token>"
```

Build and run with Docker Compose while inside the `./docker/` directory:
> docker-compose up --build

To bring it down with Docker Compose:
> docker-compose down
