#!/bin/bash

# Turn on case-insensitive matching
shopt -s nocasematch
# turn on extended globbing
shopt -s extglob

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

gitupdate="Yes"

function main () {
    echo \#\#\# Starting CorpBot \#\#\#
    cd "$DIR"
    runBot
}

function runBot () {
    echo
    python3 Main.py
    echo
    echo "$(timestamp): CorpBot died."
    echo "Restarting in 10 seconds..."
    sleep 10
    if [[ "$gitupdate" == "Yes" ]]; then
        update
    fi
    runBot
}

function update () {
    echo "Updating..."
    git pull
}

# Define a timestamp function
function timestamp () {
    date +"%T"
}

main
