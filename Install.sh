#!/bin/bash

function main () {
    echo \#\#\# Updating CorpBot \#\#\#
    
    
    # Check for some linux
    if [[ "$(uname)" == "Linux" ]]; then
        # Check what Linux we're on
        distro="$(egrep -i "^id=" /etc/os-release | cut -d"=" -f2)"  
        
        case $distro in
        "arch"|"archarm")
            echo "Arch Linux $(uname -m) detected"
            echo
            echo "Installing required packages: libffi python-pip ffmpeg"
            sudo pacman -S libffi python-pip ffmpeg
            ;;
        "ubuntu"|"debian"|"linuxmint")
            echo "Ubuntu or debian (*.deb based distro) detected"
            echo
            echo "Installing required packages: libffi-dev python-dev ffmpeg"
            if which apt 2>/dev/null; then
                echo "Using apt"
                cmd=apt
            else
                echo "Using apt-get"
                cmd=apt-get
            fi
            sudo $cmd install libffi-dev python-dev ffmpeg
            ;;
        *)
            echo "No compatible distro found!"
            echo
            if [[ "$ignorepkg" != 1 ]]; then
                echo "Please install libbffi, python-pip and ffmpeg for your distro and rerun as"
                echo "ignorepkg=1 $0"
                
                return 1
            fi
            ;;
        esac
    fi

    #echo Updating Chatterbot...
    #echo
    #update "chatterbot"
    #echo
    
    #echo Updating Discord...
    #echo
    #update "discord.py[voice]"
    #echo

    echo Updating Discord [Development Version]...
    echo
    update "https://github.com/Rapptz/discord.py/archive/rewrite.zip#egg=discord.py[voice]"
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

    echo Updating PyQuery...
    echo
    update "pyquery"
    echo

    echo Updating PyAIML
    echo
    update "git+https://github.com/paulovn/python-aiml"
    echo

    echo Updating PySpeedTest
    echo
    update "pyspeedtest"
    echo

    #echo Updating Flask...
    #echo
    #update "Flask"
    #echo
    
    # echo Updating Levenshtein...
    # echo
    # update "python-levenshtein"
    # echo
    
    echo Done.
    sleep 5
}

function update () {
    python3 -m pip install -U "$1"
}

main
