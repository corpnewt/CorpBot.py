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
            as_root pacman -S --needed libffi python-pip ffmpeg
            ;;
        "ubuntu"|"debian"|"linuxmint")
            echo "Ubuntu or debian (*.deb based distro) detected"
            echo
            echo "Installing required packages: libffi-dev python-dev ffmpeg"
            as_root apt-get install libffi-dev python-dev python3-pip ffmpeg
            ;;
        "fedora")
            echo "Fedora detected"
            echo "Fedora support is UNTESTED! You have been warned."
            echo "Installing required packages from official repos: libffi-devel python3-pip"
            as_root dnf install libffi-devel python3-pip
            
            # Get FFMpeg for Fedora from RPMfusion repos
            getrpmfusion
            
            echo "Checking for and Installing RPMfusion nonfree..."
            as_root dnf install ffmpeg
            ;;
        "rhel"|"centos")
            echo "RHEL/CentOS detected"
            echo "RHEL/CentOS support is UNTESTED! You have been warned."
            echo "Installing required packages from official repos: libffi-devel python3-pip"
            as_root dnf install libffi-devel python3-pip
            ;;
        *)
            echo "No compatible distro found!"
            echo
            if [[ "$ignorepkg" != 1 ]]; then
                echo "Please install libffi, python-pip and ffmpeg for your distro and rerun as"
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

# From Beyond Linux From Scratch: http://www.linuxfromscratch.org/blfs/view/stable/x/x7proto.html

function as_root()
{
  if   [ $EUID = 0 ];        then $*
  elif [ -x /usr/bin/sudo ]; then sudo $*
  else                            su -c \\"$*\\"
  fi
}

function getrpmfusion()
{
    if dnf list installed rpmfusion-nonfree; then
        echo "RPMfusion nonfree found!"
    else
        echo "RPMfusion nonfree not found."
        if dnf list installed rpmfusion-free; then
            echo "RPMfusion free found!"
        else
            echo "RPMfusion free not found."
            echo "Installing RPMfusion free..."
            as_root dnf install https://download1.rpmfusion.org/free/fedora/rpmfusion-free-release-$(rpm -E %fedora).noarch.rpm
        fi
        echo "Installing RPMfusion nonfree..."
        as_root dnf install https://download1.rpmfusion.org/nonfree/fedora/rpmfusion-nonfree-release-$(rpm -E %fedora).noarch.rpm
        as_root dnf update
        echo "Please verify GPG signatures: https://rpmfusion.org/keys"
    fi
}

main
