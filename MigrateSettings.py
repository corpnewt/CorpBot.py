import json
import os
import sys
from datetime import datetime

def check_path(path):
	# Add os checks for path escaping/quote stripping
	if os.name == 'nt':
		# Windows - remove quotes
		path = path.replace('"', "")
	else:
		# Unix - remove quotes and space-escapes
		path = path.replace("\\", "").replace('"', "")
	# Remove trailing space if drag and dropped
	if path[len(path)-1:] == " ":
		path = path[:-1]
	# Expand tilde
	path = os.path.expanduser(path)
	if not os.path.exists(path):
		cprint("That file doesn't exist!")
		return None
	return path

# OS Independent clear method
def cls():
	os.system('cls' if os.name=='nt' else 'clear')

def leave(error=0):
	input("Press [enter] to exit...")
	exit(error)

def parse(json_data):
	new_data = {}
	for key in json_data:
		if key.lower() == "globalmembers":
			new_data[key] = {}
			for gmem in json_data[key]:
				# Add blank member
				new_data[key][str(gmem["ID"])] = {}
				# Iterate all global members' keys and restructure
				for gmemkey in gmem:
					if gmemkey.lower() == "id":
						continue
					new_data[key][str(gmem["ID"])][gmemkey] = gmem[gmemkey]
		elif key.lower() == "servers":
			# json_data["Servers"]
			# Got a server
			new_data[key] = {}
			for skey in json_data[key]:
				# Gets each server json_data["Servers"][1, 2, 3, 4, etc]
				# Create a blank server entry
				new_data[key][str(skey["ID"])] = {}
				# Goes through each key in the server's dict
				for sdkey in skey:
					if sdkey.lower() == "name" or sdkey.lower() == "id":
						continue
					if sdkey.lower() == "channelmotd":
						# Got the channel motd list

						# Var  Servers   ServerID      MOTDs
						new_data[key][str(skey["ID"])][sdkey] = {}
						for chan in skey[sdkey]:
							# Var  Servers   ServerID      MOTDs     ChannelID
							new_data[key][str(skey["ID"])][sdkey][str(chan["ID"])] = {}
							for ckey in chan:
								if ckey.lower() == "id":
									continue
								# Var  Servers   ServerID      MOTDs     ChannelID     Key
								new_data[key][str(skey["ID"])][sdkey][str(chan["ID"])][ckey] = chan[ckey]
					elif sdkey.lower() == "members":
						# Got the member list

						# Var  Servers   ServerID     Members
						new_data[key][str(skey["ID"])][sdkey] = {}
						for member in skey[sdkey]:
							# Go through each member
							# Var  Servers   ServerID     Members     MemberID
							new_data[key][str(skey["ID"])][sdkey][str(member["ID"])] = {}
							for mkey in member:
								# Got through all the member list keys
								if mkey.lower() in [ "id", "name", "discriminator", "displayname" ]:
									continue
								new_data[key][str(skey["ID"])][sdkey][str(member["ID"])][mkey] = member[mkey]
					else:
						new_data[key][str(skey["ID"])][sdkey] = skey[sdkey]
		else:
			new_data[key] = json_data[key]
	return new_data


def main():
	cls()
	settings_file = input("Please select the settings file:  ")
	settings_file = check_path(settings_file)
	if not settings_file:
		leave(1)
	try:
		settings_json = json.load(open(settings_file))
	except Exception:
		print("I couldn't load that file!")
		leave(1)
	
	new_file = input("Type the name for the new file:  ")
	if not new_file.lower().endswith(".json"):
		new_file = new_file + ".json"

	new_contents = parse(settings_json)

	json.dump(new_contents, open(new_file, 'w'), indent=2)

	print("Done.\n")

	leave(0)

if len(sys.argv) > 1:
	# We have command line args
	settings = sys.argv[1]
	if not os.path.exists(settings):
		print("Doesn't exist!")
		exit(1)
	try:
		settings_json = json.load(open(settings))
	except Exception:
		print("Error loading settings!")
		exit(1)
	# Save to backup
	timeStamp = datetime.today().strftime("%Y-%m-%d %H.%M")
	try:
		json.dump(settings_json, open("Old-Settings-{}.json".format(timeStamp), "w"), indent=2)
	except Exception:
		print("Error backing up!")
		exit(1)
	# Parse for new style
	try:
		new_contents = parse(settings_json)
	except Exception:
		print("Settings conversion error!")
		exit(1)
	# Save to original file
	try:
		json.dump(new_contents, open(settings, 'w'), indent=2)
	except Exception:
		print("Error saving new settings!")
		exit(1)
else:
	main()