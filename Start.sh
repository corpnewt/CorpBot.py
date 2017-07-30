#!/bin/bash

# Turn on case-insensitive matching
shopt -s nocasematch
# turn on extended globbing
shopt -s extglob

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

gitupdate="No"
autorestart="No"

function main () {
    echo \#\#\# Starting CorpBot \#\#\#
    cd "$DIR"
    runBot
}

function runBot () {
    if [[ "$gitupdate" == "Yes" ]]; then
        echo
        update
    fi
    echo
    python3 Main.py -reboot No -path python3
    echo
    if [[ "$autorestart" == "Yes" ]]; then
        echo "$(timestamp): CorpBot died."
        echo "Restarting in 10 seconds..."
        sleep 10
        runBot
    fi
}

function update () {
    echo "Updating..."
    echo
    git pull origin rewrite
}

# Define a timestamp function
function timestamp () {
    date +"%T"
}

main
