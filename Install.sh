#!/bin/bash

function main () {
    echo \#\#\# Updating CorpBot \#\#\#

    # Check for some linux
    "unamestr = $(uname)"
    if [[ "$unamestr" == "Linux" ]]; then
        # Install linux dependencies
        echo Installing libffi-dev (run as sudo if this fails)...
        echo
        sudo apt-get install libffi-dev
        echo

        echo Installing python-dev (run as sudo if this fails)...
        echo
        sudo apt-get install python-dev
        echo
    fi
    
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

    echo Updating ParseDateTime...
    echo
    update "parsedatetime"
    echo

    echo Updating Psutil...
    echo
    update "psutil"
    echo

    echo Updating PyParsing...
    echo
    update "pyparsing"
    echo
    
    echo Done.
    sleep 5
}

function update () {
    python3 -m pip install -U "$1"
}

main
