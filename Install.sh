#!/bin/bash

function main () {
    echo \#\#\# Updating CorpBot \#\#\#
    # Check for some linux
    if [[ "$(uname)" == "Linux"  && "$ignorepkg" != 1 ]]; then
        # Check what Linux we're on
        distro="$(egrep -i "^id=" /etc/os-release | cut -d"=" -f2)"  
        
        case $distro in
        "arch"|"archarm")
            echo "Arch Linux $(uname -m) detected"
            echo
            echo "Installing required packages: libffi python-pip ffmpeg"
            as_root pacman -S --needed libffi python-pip ffmpeg
            ;;
        "ubuntu"|"debian"|"linuxmint")
            echo "Ubuntu or debian (*.deb based distro) detected"
            echo
            echo "Installing required packages: libffi-dev python-dev ffmpeg"
            as_root apt-get install libffi-dev python-dev python3-pip ffmpeg
            ;;
        *)
            echo "No compatible distro found!"
            echo
            echo "Please install libffi, python-pip and ffmpeg and rerun as"
            echo "ignorepkg=1 $0"                
            return 1
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

    echo Updating Pytz
    echo
    update "pytz"
    echo

    echo Updating Wikipedia
    echo
    update "wikipedia"
    echo

    echo Updating MTranslate
    echo
    update "mtranslate"
    echo

    echo Updating GiphyPop
    echo
    update "git+https://github.com/shaunduncan/giphypop.git#egg=giphypop"
    echo

    echo Updating NumPy
    echo
    update "numpy"
    echo

    echo Updating Weather
    echo
    update "weather-api"
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

# From Beyond Linux From Scratch: http://www.linuxfromscratch.org/blfs/view/stable/x/x7proto.html

function as_root()
{
  if   [ $EUID = 0 ];        then $*
  elif [ -x /usr/bin/sudo ]; then sudo $*
  else                            su -c \\"$*\\"
  fi
}

main
