#!/bin/bash

function main () {
    echo \#\#\# Updating CorpBot \#\#\#
    echo Updating Discord...
    echo
    update "discord.py[voice]"
    echo

    echo Updating Pillow...
    echo
    update "Pillow"
    echo

    echo Updating Youtube-dl...
    echo
    update "youtube-dl"
    echo
    
    echo Updating Requests...
    echo
    update "Requests"
    echo
    
    echo Done.
    sleep 5
}

function update () {
    python3 -m pip install -U "$1"
}

main
