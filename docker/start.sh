#!/usr/bin/env bash

# Enable error handling
set -e
set -o pipefail

# Enable debugging
#set -x

# Switch to the application directory
cd /usr/src/app

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

# Modify the lavalink host in Music.py to use the configured lavalink host instead
sed -i "s/127.0.0.1/$LAVALINK_HOST/g" ./Cogs/Music.py

# Modify the lavalink region in Music.py to use the configured lavalink region instead
sed -i "s/us_central/$LAVALINK_REGION/g" ./Cogs/Music.py

# Start the application
#python ./WatchDog.py
python ./Main.py
