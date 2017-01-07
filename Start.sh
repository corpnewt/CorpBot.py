 a#!/bin/bash

# Turn on case-insensitive matching
shopt -s nocasematch
# turn on extended globbing
shopt -s extglob

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

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
    runBot
}

# Define a timestamp function
function timestamp () {
    date +"%T"
}

main
