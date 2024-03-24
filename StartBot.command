#!/usr/bin/env bash

clear
echo "   ###                   ###"
echo "  # BotStarter - CorpNewt #"
echo " ###                   ###"
echo

dir="$(cd -- "$(dirname "$0")" >/dev/null 2>&1; pwd -P)"
start="Start.command"
ld="Lavalink"
lava="Lavalink.jar"
rd="Redis"
redis="redis-server"
wait=5

get_window_id () {
    local window_id="$(
        osascript -e "
            tell app \"Terminal\"
                if not (exists window 1) then reopen
                activate
                return the id of the front window
            end tell"
    )"
    echo "$window_id"
}

do_script () {
    local comm="$1" window_id="$2"
    # Clean up quotes and escapes
    comm="${comm//\\/\\\\}"
    comm="${comm//\"/\\\"}"
    window_id="${window_id//\\/\\\\}"
    window_id="${window_id//\"/\\\"}"
    # Attempt to run our applescript - this tries to open processes
    # in new terminal tabs - and has some safe guards to ensure we're
    # opening tabs in the passed window_id.  Scripting the terminal
    # is weird as tabs count as windows - and the topmost has an index
    # of 1.  Setting a window's index doesn't make it active - so we
    # also have to use System Events to perform an AXRaise.
    osascript -e "
        tell app \"Terminal\"
            if not (exists window 1) then reopen
            activate
            try
                set originalWindow to $window_id
            on error
                set originalWindow to the id of the front window
            end try
            repeat until index of window id originalWindow is equal to 1
                delay 0.1
                tell window id originalWindow
                    activate
                    set index to 1
                end tell
            end repeat
            tell app \"System Events\" to tell process \"Terminal\"
                perform action \"AXRaise\" of window 1
            end tell
            set targetCount to (count of windows) + 1
            tell app \"System Events\" to keystroke \"t\" using command down
            repeat until (count of windows) is greater than or equal to targetCount
                delay 0.1
            end repeat
            set targetWindow to originalWindow
            repeat with w in every window
                if id of w is greater than targetWindow then set targetWindow to id of w
            end repeat
            do script \"$comm\" in window id targetWindow
            set index of window id originalWindow to 1
        end tell" >/dev/null 2>&1
    if [ "$?" != "0" ]; then
        # Try to just run it without all the tab stuffs
        osascript -e "tell app \"Terminal\" to do script \"$comm\"" >/dev/null 2>&1
    fi
}

is_mac="$(uname -s | grep -i Darwin)"
if [ -z "$is_mac" ]; then
    echo This script can only be used on macOS.
    exit 1
fi

# Retain the window id for future use
window_id="$(get_window_id)"

if [ -e "$dir/$ld/$lava" ]; then
    echo "Starting Lavalink server..."
    do_script "cd \"$dir/$ld\" && java -jar \"$lava\"" "$window_id"
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
        do_script "cd \"$dir/$rd\" && \"./$redis\"" "$window_id"
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
