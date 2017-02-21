#!/bin/bash

# Turn on case-insensitive matching
shopt -s nocasematch
# turn on extended globbing
shopt -s extglob

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

pythonFile="WebServer.py"

function main () {
    echo \#\#\# Starting CorpBot \#\#\#
    echo WebServer
    cd "$DIR"
    # Set path var
    export FLASK_APP=$pythonFile
    flask run
}

main
