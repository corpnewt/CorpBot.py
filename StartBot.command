#!/usr/bin/env bash

clear
echo "   ###                   ###"
echo "  # BotStarter - CorpNewt #"
echo " ###                   ###"
echo

dir="${0%/*}"
start="Start.command"
ld="Lavalink"
lava="Lavalink.jar"
rd="Redis"
redis="redis-server"
wait=5

is_mac="$(uname -s | grep -i Darwin)"
if [ -z "$is_mac" ]; then
    echo This script can only be used on macOS.
    exit 1
fi

if [ -e "$dir/$ld/$lava" ]; then
    echo "Starting Lavalink server..."
    osascript -e "tell app \"Terminal\" to do script \"cd \\\"$dir/$ld\\\"; java -jar \\\"$lava\\\""\" > /dev/null 2>&1
    echo
else
    echo "\"$dir/$ld/$lava\""
    echo "does not exist!"
    echo
    echo "You can get it from:"
    echo "  https://github.com/lavalink-devs/Lavalink/releases/latest"
    echo
    exit 1
fi
read -t "$wait" -p "Waiting "$wait" seconds..."
echo
echo
# Only start the Redis server if we're using the redis
# branch of CorpBot.py
if [ -e "$dir/Cogs/PandorasDB.py" ]; then
    if [ -e "$dir/$rd/$redis" ]; then
        echo "Starting database..."
        osascript -e "tell app \"Terminal\" to do script \"cd \\\"$dir/$rd\\\"; \\\"./$redis\\\""\" > /dev/null 2>&1
        echo
    else
        echo "\"$dir/$rd/$redis\""
        echo "does not exist!"
        echo
        echo "You can follow instructions to build it here:"
        echo "  https://redis.io/docs/install/install-redis/install-redis-from-source/"
        echo
        exit 1
    fi
    read -t "$wait" -p "Waiting "$wait" seconds..."
    echo
    echo
fi
if [ -e "$dir/$start" ]; then
    echo "Starting bot..."
    /usr/bin/env bash "$dir/$start"
else
    echo "$dir/$start"
    echo "does not exist!"
    echo
    exit 1
fi