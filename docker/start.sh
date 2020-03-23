#!/usr/bin/env bash

# Enable error handling
set -e
set -o pipefail

# Enable debugging
#set -x

# Switch to the application directory
cd /usr/src/app

# Replace git SSH urls with HTTPS to get around WatchDog issues
sed -i "s/git@github.com:/https:\/\/github.com\//g" ./.git/config

# Switch to the data directory
cd /data

# Parse all environment variables that start with "SETTINGS_DICT_",
# then create a matching JSON object string and store it in "settings_dict.json"
JSON="{" # Starts a new JSON object
for setting in "${!SETTINGS_DICT_@}"; do
    KEY=${setting#"SETTINGS_DICT_"} # Gets the key name without the prefix
    KEY="$(echo "$KEY" | tr -d '"')" # Removes double quotes from the key
    VALUE="${!setting}" # Gets the value
    VALUE="$(echo "$VALUE" | tr -d '"')" # Removes double quotes from the value
    JSON="$JSON\n  \"${KEY,,}\": \"$VALUE\"," # Appends the key-value entry to the JSON object
done
JSON="${JSON::-1}\n}" # Removes the last character (comma) and finishes the JSON object
JSON="$(echo -e $JSON)" # Applies the new lines
echo ${JSON} > settings_dict.json # Writes the JSON string to the file

# Start the application
#python ./WatchDog.py
#python /usr/src/app/WatchDog.py
python /usr/src/app/Main.py
