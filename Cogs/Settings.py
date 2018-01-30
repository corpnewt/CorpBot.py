import asyncio
import discord
from   datetime    import datetime
from   discord.ext import commands
from   shutil      import copyfile
import time
import json
import os
import copy
import subprocess
from   Cogs        import DisplayName
from   Cogs        import Nullify


def setup(bot):
	# Add the cog
	bot.add_cog(Settings(bot))

class MemberRole:

	def __init__(self, **kwargs):
		self.member = kwargs.get("member", None)
		self.add_roles = kwargs.get("add_roles", [])
		self.rem_roles = kwargs.get("rem_roles", [])
		if type(self.member) == discord.Member:
			self.guild = self.member.guild
		else:
			self.guild = None

class RoleManager:

	# Init with the bot reference
	def __init__(self, bot):
		self.bot = bot
		self.sleep = 1
		self.delay = 0.2
		self.next_member_delay = 1
		self.running = True
		self.q = asyncio.Queue()
		self.loop_list = [self.bot.loop.create_task(self.check_roles())]

	def clean_up(self):
		self.running = False
		for task in self.loop_list:
			task.cancel()

	async def check_roles(self):
		while self.running:
			# Try with a queue I suppose
			current_role = await self.q.get()
			await self.check_member_role(current_role)
			self.q.task_done()

	async def check_member_role(self, r):
		if r.guild == None or r.member == None:
			# Not applicable
			return
		if not r.guild.me.guild_permissions.manage_roles:
			# Missing permissions to manage roles
			return
		# Let's add roles
		if len(r.add_roles):
			try:
				await r.member.add_roles(*r.add_roles)
			except Exception as e:
				if not type(e) is discord.Forbidden:
					try:
						print(e)
					except:
						pass
					pass
		if len(r.add_roles) and len(r.rem_roles):
			# Pause for a sec before continuing
			await asyncio.sleep(self.delay)
		if len(r.rem_roles):
			try:
				await r.member.remove_roles(*r.rem_roles)
			except Exception as e:
				if not type(e) is discord.Forbidden:
					try:
						print(e)
					except:
						pass
					pass

	def _update(self, member, *, add_roles = [], rem_roles = []):
		# Updates an existing record - or adds a new one
		if not type(member) == discord.Member:
			# Can't change roles without a guild
			return
		# Check first if any of the add_roles are above our own
		top_index = member.guild.me.top_role.position
		new_add = []
		new_rem = []
		for a in add_roles:
			if not a:
				continue
			if a.position < top_index:
				# Can add this one
				new_add.append(a)
		for r in rem_roles:
			if not r:
				continue
			if r.position < top_index:
				# Can remove this one
				new_rem.append(r)
		if len(new_add) == 0 and len(new_rem) == 0:
			# Nothing to do here
			return
		self.q.put_nowait(MemberRole(member=member, add_roles=new_add, rem_roles=new_rem))

	def add_roles(self, member, role_list):
		# Adds the member and roles as a MemberRole object to the heap
		self._update(member, add_roles=role_list)

	def rem_roles(self, member, role_list):
		# Adds the member and roles as a MemberRole object to the heap
		self._update(member, rem_roles=role_list)

	def change_roles(self, member, *, add_roles = [], rem_roles = []):
		# Adds the member and both role types as a MemberRole object to the heap
		self._update(member, add_roles=add_roles, rem_roles=rem_roles)

# This is the settings module - it allows the other modules to work with
# a global settings variable and to make changes

class Settings:
	"""The Doorway To The Server Settings"""
	# Let's initialize with a file location
	def __init__(self, bot, prefix = "$", file : str = None):
		if file == None:
			# We weren't given a file, default to ./Settings.json
			file = "Settings.json"
		
		self.file = file
		self.backupDir = "Settings-Backup"
		self.backupMax = 100
		self.backupTime = 7200 # runs every 2 hours
		self.backupWait = 10 # initial wait time before first backup
		self.settingsDump = 300 # runs every 5 minutes
		self.bot = bot
		self.serverDict = {}
		self.prefix = prefix
		self.loop_list = []
		self.role = RoleManager(bot)

		self.defaultServer = { 						# Negates Name and ID - those are added dynamically to each new server
				"DefaultRole" 			: "", 		# Auto-assigned role position
				"TempRole"				: None,		# Assign a default temporary role
				"TempRoleTime"			: 2,		# Number of minutes before temp role expires
				"TempRoleList"			: [],		# List of temporary roles
				"TempRolePM"			: False,	# Do we pm when a user is given a temp role?
				"DefaultXP"				: 0,		# Default xp given to each new member on join
				"DefaultXPReserve"		: 10,		# Default xp reserve given to new members on join
				"AdminLock" 			: False, 	# Does the bot *only* answer to admins?
				"TableFlipMute"			: False,	# Do we mute people who flip tables?
				"IgnoreDeath"			: True,		# Does the bot keep talking post-mortem?
				"DJArray"				: [],		# List of roles that can use music
				"FilteredWords"			: [],		# List of words to filter out of user messages
				"UserRoles"				: [],		# List of roles users can self-select
				"OnlyOneUserRole"		: True,		# Limits user role selection to one at a time
				"YTMultiple"			: False,	# Shows a list of 5 videos per yt search with play
				"RequiredXPRole"		: "",		# ID or blank for Everyone
				"RequiredLinkRole" 		: "", 		# ID or blank for Admin-Only
				"RequiredTagRole" 		: "", 		# ID or blank for Admin-Only
				"RequiredHackRole" 		: "", 		# ID or blank for Admin-Only
				"RequiredKillRole" 		: "", 		# ID or blank for Admin-Only
				"RequiredStopRole"      : "",       # ID or blank for Admin-Only
				"TeleChannel"			: "",		# ID or blank for disabled
				"TeleConnected"			: False,	# Disconnect any lingering calls
				"LastCallHidden"		: False,	# Was the last call with *67?
				"TeleNumber"			: None,		# The 7-digit number of the server
				"TeleBlock"				: [],		# List of blocked numbers
				"MadLibsChannel"        : "",       # ID or blank for any channel
				"ChatChannel"			: "", 		# ID or blank for no channel
				"HardwareChannel"       : "",		# ID or blank for no channel
				"DefaultChannel"		: "",		# ID or blank for no channel
				"WelcomeChannel"		: None,		# ID or None for no channel
				"LastChat"				: 0,		# UTC Timestamp of last chat message
				"PlayingMadLibs"		: False,	# Yes if currently playing MadLibs
				"LastAnswer" 			: "",		# URL to last {prefix}question post
				"StrikeOut"				: 3,		# Number of strikes needed for consequence
				"KickList"				: [],		# List of id's that have been kicked
				"BanList"				: [],		# List of id's that have been banned
				"Prefix"				: None,		# Custom Prefix
				"AutoPCPP"				: None,		# Auto-format pcpartpicker links?
				"XP Count"				: 10,		# Default number of xp transactions to log
				"XP Array"				: [],		# Holds the xp transaction list
				"XPLimit"				: None,		# The maximum xp a member can get
				"XPReserveLimit"		: None,		# The maximum xp reserve a member can get
				"XpBlockArray"			: [],		# List of roles/users blocked from xp
				"HourlyXP" 				: 3,		# How much xp reserve per hour
				"HourlyXPReal"			: 0,		# How much xp per hour (typically 0)
				"XPPerMessage"			: 0,		# How much xp per message (typically 0)
				"XPRPerMessage"			: 0,		# How much xp reserve per message (typically 0)
				"RequireOnline" 		: True,		# Must be online for xp?
				"AdminUnlimited" 		: True,		# Do admins have unlimited xp to give?
				"BotAdminAsAdmin" 		: False,	# Do bot-admins count as admins with xp?
				"RemindOffline"			: False,	# Let users know when they ping offline members
				"JoinPM"				: True,		# Do we pm new users with rules?
				"XPPromote" 			: True,		# Can xp raise your rank?
				"XPDemote" 				: False,	# Can xp lower your rank?
				"SuppressPromotions"	: False,	# Do we suppress the promotion message?
				"SuppressDemotions"		: False,	# Do we suppress the demotion message?
				"TotalMessages"			: 0,		# The total number of messages the bot has witnessed
				"Killed" 				: False,	# Is the bot dead?
				"KilledBy" 				: "",		# Who killed the bot?
				"LastShrug"				: "",		# Who shrugged last?
				"LastLenny"				: "", 		# Who Lenny'ed last?
				"VerificationTime"		: 0,		# Time to wait (in minutes) before assigning default role
				"LastPicture" 			: 0,		# UTC Timestamp of last picture uploaded
				"PictureThreshold" 		: 10,		# Number of seconds to wait before allowing pictures
				"Rules" 				: "Be nice to each other.",
				"Welcome"				: "Welcome *[[user]]* to *[[server]]!*",
				"Goodbye"				: "Goodbye *[[user]]*, *[[server]]* will miss you!",
				"Info"					: "",		# This is where you can say a bit about your server
				"PromotionArray" 		: [],		# An array of roles for promotions
				"OnlyOneRole"			: False,	# Only allow one role from the promo array at a time
				"Hunger" 				: 0,		# The bot's hunger % 0-100 (can also go negative)
				"HungerLock" 			: False,	# Will the bot stop answering at 100% hunger?
				"SuppressMentions"		: True,		# Will the bot suppress @here and @everyone in its own output?
				"Volume"				: "",		# Float volume for music player
				"DefaultVolume"			: 0.6,		# Default volume for music player
				"Playlisting"			: None,		# Not adding a playlist
				"PlaylistRequestor"		: None,		# No one requested a playlist
				"IgnoredUsers"			: [],		# List of users that are ignored by the bot
				"LastComic"				: [],		# List of julian dates for last comic
				"Hacks" 				: [],		# List of hack tips
				"Links" 				: [],		# List of links
				"Tags"					: [],		# List of tags
				"Members" 				: {},		# List of members
				"AdminArray"	 		: [],		# List of admin roles
				"GifArray"				: [],		# List of roles that can use giphy
				"LogChannel"			: "",		# ID or blank for no logging
				"LogVars"				: [],		# List of options to log
				"DisabledCommands"		: [],		# List of disabled command names
				"AdminDisabledAccess"	: True,		# Can admins access disabled commands?
				"BAdminDisabledAccess"	: True,		# Can bot-admins access disabled commands?
				"DisabledReactions"		: True,		# Does the bot react to disabled commands?
				"VoteKickChannel"		: None,		# ID or none if not setup
				"VoteKickMention"		: None,		# ID of role to mention - or none for no mention
				"VotesToMute"			: 0,		# Positive number - or 0 for disabled
				"VotesToMention"		: 0,		# Positive number - or 0 for disabled
				"VotesMuteTime"			: 0,		# Number of seconds to mute - or 0 for disabled
				"VotesResetTime"		: 0,		# Number of seconds to roll off - or 0 for disabled
				"VoteKickArray"			: [],		# Contains a list of users who were voted to kick - and who voted against them
				"VoteKickAnon"			: False,	# Are vk messages deleted after sending?
				"QuoteReaction"			: None,		# Trigger reaction for quoting messages
				"QuoteChannel"			: None,		# Channel id for quotes
				"QuoteAdminOnly"		: True,		# Only admins/bot-admins can quote?
				"MuteList"				: []}		# List of muted members
				# Removed for spam
				# "ChannelMOTD" 			: {}}		# List of channel messages of the day

		# Let's load our settings file
		if os.path.exists(file):
			self.serverDict = json.load(open(file))
			if "Servers" in self.serverDict and type(self.serverDict["Servers"]) is list and os.path.exists("MigrateSettings.py"):
				# Wrong type!  Update
				print("Updating settings...\n")
				sub_args = ['python', 'MigrateSettings.py', file ]
				proc = subprocess.Popen(sub_args)
				proc.wait()
				# Reload json
				self.serverDict = json.load(open(file))
			# Verify that we're bool-oriented now, instead of string "yes"/"no"
			changed_global = [
				"OwnerLock"
			]
			changed_settings = [
				"AdminLock",
				"LastCallHidden",
				"RequireOnline",
				"AdminUnlimited",
				"BotAdminAsAdmin",
				"JoinPM",
				"XPPromote",
				"XPDemote",
				"SuppressPromotions",
				"SuppressDemotions",
				"Killed",
				"HungerLock",
				"SuppressMentions"
			]
			changed_user_settings = [
				"Muted"
			]
			checked = False
			for x in self.serverDict:
				if not x in changed_global:
					continue
				if type(self.serverDict[x]) is bool:
					# Already done
					checked = True
					break
				self.serverDict[x] = True if self.serverDict[x].lower() == "yes" else False
			if not checked:
				# We need to verify all our settings
				for s_id in self.serverDict["Servers"]:
					for s in changed_settings:
						if not s in self.serverDict["Servers"][s_id]:
							continue
						if type(self.serverDict["Servers"][s_id][s]) is bool:
							continue
						# Set the bool vals
						self.serverDict["Servers"][s_id][s] = True if self.serverDict["Servers"][s_id][s].lower() == "yes" else False
					for m in self.serverDict["Servers"][s_id]["Members"]:
						for ms in changed_user_settings:
							if not ms in self.serverDict["Servers"][s_id]["Members"][m]:
								continue
							if type(self.serverDict["Servers"][s_id]["Members"][m][ms]) is bool:
								continue
							# Set the bool vals
							self.serverDict["Servers"][s_id]["Members"][m][ms] = True if self.serverDict["Servers"][s_id]["Members"][m][ms].lower() == "yes" else False
				# Flush our changes
				self.flushSettings()
		else:
			# File doesn't exist - create a placeholder
			self.serverDict = {}

	def suppressed(self, guild, msg):
		# Check if we're suppressing @here and @everyone mentions
		if self.settings.getServerStat(guild, "SuppressMentions"):
			return Nullify.clean(msg)
		else:
			return msg

	async def onjoin(self, member, server):
		# Welcome - and initialize timers
		self.bot.loop.create_task(self.giveRole(member, server))

	# Proof of concept stuff for reloading cog/extension
	def _is_submodule(self, parent, child):
		return parent == child or child.startswith(parent + ".")

	@asyncio.coroutine
	async def on_unloaded_extension(self, ext):
		# Called to shut things down
		if not self._is_submodule(ext.__name__, self.__module__):
			return
		# Flush settings
		self.flushSettings()
		# Shutdown role manager loop
		self.role.clean_up()
		for task in self.loop_list:
			task.cancel()

	@asyncio.coroutine
	async def on_loaded_extension(self, ext):
		# See if we were loaded
		if not self._is_submodule(ext.__name__, self.__module__):
			return
		# Check all verifications - and start timers if needed
		self.loop_list.append(self.bot.loop.create_task(self.checkAll()))
		# Start the backup loop
		self.loop_list.append(self.bot.loop.create_task(self.backup()))
		# Start the settings loop
		self.loop_list.append(self.bot.loop.create_task(self.flushLoop()))

	async def checkAll(self):
		# Check all verifications - and start timers if needed
		for server in self.bot.guilds:
			# Check if we can even manage roles here
			if not server.me.guild_permissions.manage_roles:
				continue
			# Get default role
			defRole = self.getServerStat(server, "DefaultRole")
			defRole = DisplayName.roleForID(defRole, server)
			if defRole:
				# We have a default - check for it
				for member in server.members:
					foundRole = False
					for role in member.roles:
						if role == defRole:
							# We have our role
							foundRole = True
					if not foundRole:
						# We don't have the role - set a timer
						self.loop_list.append(self.bot.loop.create_task(self.giveRole(member, server)))

	async def giveRole(self, member, server):
		# Let the api settle
		# Add 2 second delay to hopefully prevent the api from hating us :(
		# await asyncio.sleep(2)
		# Pls no hate
		
		# Start the countdown
		task = asyncio.Task.current_task()
		verifiedAt  = self.getUserStat(member, server, "VerificationTime")
		try:
			verifiedAt = int(verifiedAt)
		except ValueError:
			verifiedAt = 0
		currentTime = int(time.time())
		timeRemain  = verifiedAt - currentTime
		if timeRemain > 0:
			# We have to wait for verification still
			await asyncio.sleep(timeRemain)
		
		# We're already verified - make sure we have the role
		defRole = self.getServerStat(server, "DefaultRole")
		defRole = DisplayName.roleForID(defRole, server)
		if defRole:
			# We have a default - check for it
			foundRole = False
			for role in member.roles:
				if role == defRole:
					# We have our role
					foundRole = True
			if not foundRole:
				try:
					self.role.add_roles(member, [defRole])
					fmt = '*{}*, you\'ve been assigned the role **{}** in *{}!*'.format(DisplayName.name(member), defRole.name, self.suppressed(server, server.name))
					await member.send(fmt)
				except Exception:
					pass
		if task in self.loop_list:
			self.loop_list.remove(task)

	async def backup(self):
		# Wait initial time - then start loop
		await asyncio.sleep(self.backupWait)
		while not self.bot.is_closed():
			# Initial backup - then wait
			if not os.path.exists(self.backupDir):
				# Create it
				os.makedirs(self.backupDir)
			# Flush backup
			timeStamp = datetime.today().strftime("%Y-%m-%d %H.%M")
			self.flushSettings("./{}/Backup-{}.json".format(self.backupDir, timeStamp))

			# Get curr dir and change curr dir
			retval = os.getcwd()
			os.chdir(self.backupDir)

			# Get reverse sorted backups
			backups = sorted(os.listdir(os.getcwd()), key=os.path.getmtime)
			numberToRemove = None
			if len(backups) > self.backupMax:
				# We have more than 100 backups right now, let's prune
				numberToRemove = len(backups)-self.backupMax
				for i in range(0, numberToRemove):
					os.remove(backups[i])
			
			# Restore curr dir
			os.chdir(retval)
			if numberToRemove:
				print("Settings Backed Up ({} removed): {}".format(numberToRemove, timeStamp))
			else:
				print("Settings Backed Up: {}".format(timeStamp))
			await asyncio.sleep(self.backupTime)


	def isOwner(self, member):
		# This method converts prior, string-only ownership to a list,
		# then searches the list for the passed member
		try:
			ownerList = self.serverDict['Owner']
		except KeyError:
			self.serverDict['Owner'] = []
			ownerList = self.serverDict['Owner']
		if not len(ownerList):
			return None
		if not type(ownerList) is list:
			# We have a string, convert
			ownerList = [ int(ownerList) ]
			self.serverDict['Owner'] = ownerList
		# At this point - we should have a list
		for owner in ownerList:
			if not self.bot.get_user(owner):
				# Invalid user - remove
				self.serverDict['Owner'].remove(owner)
				continue
			if int(owner) == member.id:
				# We're in the list
				return True
		# Not in the list.. :(
		return False


	def getServerDict(self):
		# Returns the server dictionary
		return self.serverDict

	# Let's make sure the server is in our list
	def checkServer(self, server):
		# Assumes server = discord.Server and serverList is a dict
		if not "Servers" in self.serverDict:
			# Let's add an empty placeholder
			self.serverDict["Servers"] = {}

		if str(server.id) in self.serverDict["Servers"]:
			# Found it
			# Verify all the default keys have values
			for key in self.defaultServer:
				if not key in self.serverDict["Servers"][str(server.id)]:
					#print("Adding: {} -> {}".format(key, server.name))
					if type(self.defaultServer[key]) == dict:
						self.serverDict["Servers"][str(server.id)][key] = {}
					elif type(self.defaultServer[key]) == list:
						# We have lists/dicts - copy them
						self.serverDict["Servers"][str(server.id)][key] = copy.deepcopy(self.defaultServer[key])
					else:
						self.serverDict["Servers"][str(server.id)][key] = self.defaultServer[key]

		else:
			# We didn't locate our server
			# print("Server not located, adding...")
			# Set name and id - then compare to default server
			self.serverDict["Servers"][str(server.id)] = {}
			for key in self.defaultServer:
				if type(self.defaultServer[key]) == dict:
					self.serverDict["Servers"][str(server.id)][key] = {}
				elif type(self.defaultServer[key]) == list:
					# We have lists/dicts - copy them
					self.serverDict["Servers"][str(server.id)][key] = copy.deepcopy(self.defaultServer[key])
				else:
					self.serverDict["Servers"][str(server.id)][key] = self.defaultServer[key]

	# Let's make sure the user is in the specified server
	def removeServer(self, server):
		# Check for our server name
		self.serverDict["Servers"].pop(str(server.id), None)
		self.checkGlobalUsers()


	def removeServerID(self, id):
		# Check for our server ID
		self.serverDict["Servers"].pop(str(id), None)
		self.checkGlobalUsers()

	#"""""""""""""""""""""""""#
	#""" NEEDS TO BE FIXED """#
	#"""""""""""""""""""""""""#

	def removeChannel(self, channel):
		motdArray = self.settings.getServerStat(channel.guild, "ChannelMOTD")
		for a in motdArray:
			# Get the channel that corresponds to the id
			if str(a['ID']) == str(channel.id):
				# We found it - throw an error message and return
				motdArray.remove(a)
				self.setServerStat(server, "ChannelMOTD", motdArray)


	def removeChannelID(self, id, server):
		found = False
		for x in self.serverDict["Servers"]:
			if str(x["ID"]) == str(server.id):
				for y in x["ChannelMOTD"]:
					if y["ID"] == id:
						found = True
						x["ChannelMOTD"].remove(y)
	
	
	# Let's make sure the user is in the specified server
	def checkUser(self, user, server):
		# Make sure our server exists in the list
		self.checkServer(server)
		if str(user.id) in self.serverDict["Servers"][str(server.id)]["Members"]:
			y = self.serverDict["Servers"][str(server.id)]["Members"][str(user.id)]
			needsUpdate = False
			if not "XP" in y:
				y["XP"] = int(self.getServerStat(server, "DefaultXP"))
				needsUpdate = True
			# XP needs to be an int - and uh... got messed up once so we check it here
			if type(y["XP"]) is float:
				y["XP"] = int(y["XP"])
			if not "XPLeftover" in y:
				y["XPLeftover"] = 0
				needsUpdate = True
			if not "XPRealLeftover" in y:
				y["XPRealLeftover"] = 0
				needsUpdate = True
			if not "XPReserve" in y:
				y["XPReserve"] = int(self.getServerStat(server, "DefaultXPReserve"))
				needsUpdate = True
			if not "Parts" in y:
				y["Parts"] = ""
				needsUpdate = True
			if not "Muted" in y:
				y["Muted"] = False
				needsUpdate = True
			if not "LastOnline" in y:
				y["LastOnline"] = None
				needsUpdate = True
			if not "Cooldown" in y:
				y["Cooldown"] = None
				needsUpdate = True
			if not "Reminders" in y:
				y["Reminders"] = []
				needsUpdate = True
			if not "Strikes" in y:
				y["Strikes"] = []
				needsUpdate = True
			if not "StrikeLevel" in y:
				y["StrikeLevel"] = 0
				needsUpdate = True
			if not "Profiles" in y:
				y["Profiles"] = []
				needsUpdate = True
			if not "TempRoles" in y:
				y["TempRoles"] = []
				needsUpdate = True
			if not "UTCOffset" in y:
				y["UTCOffset"] = None
				needsUpdate = True
			if not "LastCommand" in y:
				y["LastCommand"] = 0
			if not "Hardware" in y:
				y["Hardware"] = []
			if not "VerificationTime" in y:
				currentTime = int(time.time())
				waitTime = int(self.getServerStat(server, "VerificationTime"))
				y["VerificationTime"] = currentTime + (waitTime * 60)
		else:
			needsUpdate = True
			# We didn't locate our user - add them
			newUser = { "XP" 			: int(self.getServerStat(server, "DefaultXP")),
						"XPReserve" 	: (self.getServerStat(server, "DefaultXPReserve")),
						"Parts"			: "",
						"Muted"			: False,
						"LastOnline"	: "Unknown",
						"Reminders"		: [],
						"Profiles"		: [] }
			if not newUser["XP"]:
				newUser["XP"] = 0
			if not newUser["XPReserve"]:
				newUser["XPReserve"] = 0
			self.serverDict["Servers"][str(server.id)]["Members"][str(user.id)] = newUser


	# Let's make sure the user is in the specified server
	def removeUser(self, user, server):
		# Make sure our server exists in the list
		self.checkServer(server)
		self.serverDict["Servers"][str(server.id)]["Members"].pop(str(user.id), None)
		self.checkGlobalUsers()


	def checkGlobalUsers(self):
		try:
			userList = self.serverDict['GlobalMembers']
		except:
			userList = {}
		remove_users = []
		for u in userList:
			if not self.bot.get_user(int(u)):
				# Can't find... delete!
				remove_users.append(u)
		for u in remove_users:
			userList.pop(u, None)
		self.serverDict['GlobalMembers'] = userList
		return len(remove_users)

	# Let's make sure the user is in the specified server
	def removeUserID(self, id, server):
		# Make sure our server exists in the list
		self.checkServer(server)
		self.serverDict["Servers"][str(server.id)]["Members"].pop(str(id), None)
		self.checkGlobalUsers()

	
	# Return the requested stat
	def getUserStat(self, user, server, stat):
		# Make sure our user and server exists in the list
		self.checkUser(user, server)
		if stat in self.serverDict["Servers"][str(server.id)]["Members"][str(user.id)]:
			return self.serverDict["Servers"][str(server.id)]["Members"][str(user.id)][stat]
		return None
	
	
	def getGlobalUserStat(self, user, stat):
		# Loop through options, and get the most common
		try:
			userList = self.serverDict['GlobalMembers']
		except:
			return None
		if str(user.id) in userList:
			if stat in userList[str(user.id)]:
				return userList[str(user.id)][stat]
		return None
	
	
	# Set the provided stat
	def setUserStat(self, user, server, stat, value):
		# Make sure our user and server exists in the list
		self.checkUser(user, server)
		self.serverDict["Servers"][str(server.id)]["Members"][str(user.id)][stat] = value
						
						
	# Set a provided global stat
	def setGlobalUserStat(self, user, stat, value):
		try:
			userList = self.serverDict['GlobalMembers']
		except:
			userList = {}
		
		if str(user.id) in userList:
			userList[str(user.id)][stat] = value
			return

		userList[str(user.id)] = { stat : value }
		self.serverDict['GlobalMembers'] = userList
						
					
	# Increment a specified user stat by a provided amount
	# returns the stat post-increment, or None if error
	def incrementStat(self, user, server, stat, incrementAmount):
		# Make sure our user and server exist
		self.checkUser(user, server)
		# Check for our username
		if stat in self.serverDict["Servers"][str(server.id)]["Members"][str(user.id)]:
			self.serverDict["Servers"][str(server.id)]["Members"][str(user.id)][stat] += incrementAmount
		else:
			self.serverDict["Servers"][str(server.id)]["Members"][str(user.id)][stat] = incrementAmount
		return self.getUserStat(user, server, stat)
	
	
	# Get the requested stat
	def getServerStat(self, server, stat):
		# Make sure our server exists in the list
		self.checkServer(server)
		if stat in self.serverDict["Servers"][str(server.id)]:
			return self.serverDict["Servers"][str(server.id)][stat]
		return None
	
	
	# Set the provided stat
	def setServerStat(self, server, stat, value):
		# Make sure our server exists in the list
		self.checkServer(server)
		self.serverDict["Servers"][str(server.id)][stat] = value


	@commands.command(pass_context=True)
	async def dumpsettings(self, ctx):
		"""Sends the Settings.json file to the owner."""
		author  = ctx.message.author
		server  = ctx.message.guild
		channel = ctx.message.channel

		# Only allow owner
		isOwner = self.isOwner(ctx.author)
		if isOwner == None:
			msg = 'I have not been claimed, *yet*.'
			await ctx.channel.send(msg)
			return
		elif isOwner == False:
			msg = 'You are not the *true* owner of me.  Only the rightful owner can use this command.'
			await ctx.channel.send(msg)
			return
		
		message = await ctx.message.author.send('Uploading *Settings.json*...')
		await ctx.message.author.send(file=discord.File('Settings.json'))
		await message.edit(content='Uploaded *Settings.json!*')

	@commands.command(pass_context=True)
	async def ownerlock(self, ctx):
		"""Locks/unlocks the bot to only respond to the owner."""
		author  = ctx.message.author
		server  = ctx.message.guild
		channel = ctx.message.channel

		# Only allow owner
		isOwner = self.isOwner(ctx.author)
		if isOwner == None:
			msg = 'I have not been claimed, *yet*.'
			await ctx.channel.send(msg)
			return
		elif isOwner == False:
			msg = 'You are not the *true* owner of me.  Only the rightful owner can use this command.'
			await ctx.channel.send(msg)
			return

		# We have an owner - and the owner is talking to us
		# Let's try and get the OwnerLock setting and toggle it
		try:
			ownerLock = self.serverDict['OwnerLock']
		except KeyError:
			ownerLock = False
		# OwnerLock defaults to "No"
		if not ownerLock:
			self.serverDict['OwnerLock'] = True
			msg = 'Owner lock **Enabled**.'
			await self.bot.change_presence(game=discord.Game(name="OwnerLocked"))
		else:
			self.serverDict['OwnerLock'] = False
			msg = 'Owner lock **Disabled**.'
			if self.serverDict["Game"]:
				# Reset the game if there was one
				await self.bot.change_presence(game=discord.Game(name=self.serverDict["Game"]))
			else:
				# Set to nothing - no game prior
				await self.bot.change_presence(game=None)
		await channel.send(msg)
		#self.flushSettings()


	@commands.command(pass_context=True)
	async def owners(self, ctx):
		"""Lists the bot's current owners."""
		author  = ctx.message.author
		server  = ctx.message.guild
		channel = ctx.message.channel

		# Check to force the owner list update
		self.isOwner(ctx.author)

		ownerList = self.serverDict['Owner']

		if not len(ownerList):
			# No owners.
			msg = 'I have not been claimed, *yet*.'
		else:
			msg = 'I am owned by '
			userList = []
			for owner in ownerList:
				# Get the owner's name
				user = self.bot.get_user(int(owner))
				if not user:
					userString = "*Unknown User ({})*".format(owner)
				else:
					userString = "*{}#{}*".format(user.name, user.discriminator)
				userList.append(userString)
			msg += ', '.join(userList)

		await channel.send(msg)

	
	@commands.command(pass_context=True)
	async def claim(self, ctx):
		"""Claims the bot if disowned - once set, can only be changed by the current owner."""
		author  = ctx.message.author
		server  = ctx.message.guild
		channel = ctx.message.channel
		member = author

		owned = self.isOwner(ctx.author)
		if owned:
			# We're an owner
			msg = "You're already one of my owners."
		elif owned == False:
			# We're not an owner
			msg = "I've already been claimed."
		else:
			# Claim it up
			self.serverDict['Owner'].append(ctx.author.id)
			msg = 'I have been claimed by *{}!*'.format(DisplayName.name(member))
		await channel.send(msg)
	
	@commands.command(pass_context=True)
	async def addowner(self, ctx, *, member : str = None):
		"""Adds an owner to the owner list.  Can only be done by a current owner."""
		
		owned = self.isOwner(ctx.author)
		if owned == False:
			msg = "Only an existing owner can add more owners."
			await ctx.channel.send(msg)
			return
		
		if member == None:
			member = ctx.author

		if type(member) is str:
			memberCheck = DisplayName.memberForName(member, ctx.guild)
			if memberCheck:
				member = memberCheck
			else:
				msg = 'I couldn\'t find that user...'
				await ctx.channel.send(msg)
				return
		
		if member.bot:
			msg = "I can't be owned by other bots.  I don't roll that way."
			await ctx.channel.send(msg)
			return

		if member.id in self.serverDict['Owner']:
			# Already an owner
			msg = "Don't get greedy now - *{}* is already an owner.".format(DisplayName.name(member))
		else:
			self.serverDict['Owner'].append(member.id)
			msg = '*{}* has been added to my owner list!'.format(DisplayName.name(member))
		await ctx.channel.send(msg)


	@commands.command(pass_context=True)
	async def remowner(self, ctx, *, member : str = None):
		"""Removes an owner from the owner list.  Can only be done by a current owner."""
		
		owned = self.isOwner(ctx.author)
		if owned == False:
			msg = "Only an existing owner can remove owners."
			await ctx.channel.send(msg)
			return
		
		if member == None:
			member = ctx.author

		if type(member) is str:
			memberCheck = DisplayName.memberForName(member, ctx.guild)
			if memberCheck:
				member = memberCheck
			else:
				msg = 'I couldn\'t find that user...'
				await ctx.channel.send(msg)
				return
		
		if member.id in self.serverDict['Owner']:
			# Already an owner
			msg = "*{}* is no longer an owner.".format(DisplayName.name(member))
			self.serverDict['Owner'].remove(member.id)
		else:
			msg = "*{}* can't be removed because they're not one of my owners.".format(DisplayName.name(member))
		if not len(self.serverDict['Owner']):
			# No more owners
			msg += " I have been disowned!"
		
		await ctx.channel.send(msg)


	@commands.command(pass_context=True)
	async def disown(self, ctx):
		"""Revokes all ownership of the bot."""
		owned = self.isOwner(ctx.author)
		if owned == False:
			msg = "Only an existing owner can revoke ownership."
			await ctx.channel.send(msg)
			return
		elif owned == None:
			# No owners
			msg = 'I have already been disowned...'
			await ctx.channel.send(msg)
			return

		self.serverDict['Owner'] = []
		msg = 'I have been disowned!'
		await ctx.channel.send(msg)


	@commands.command(pass_context=True)
	async def getstat(self, ctx, stat : str = None, member : discord.Member = None):
		"""Gets the value for a specific stat for the listed member (case-sensitive)."""
		
		author  = ctx.message.author
		server  = ctx.message.guild
		channel = ctx.message.channel
		
		if member == None:
			member = author

		if str == None:
			msg = 'Usage: `{}getstat [stat] [member]`'.format(ctx.prefix)
			await channel.send(msg)
			return

		if type(member) is str:
			try:
				member = discord.utils.get(server.members, name=member)
			except:
				print("That member does not exist")
				return

		if member is None:
			msg = 'Usage: `{}getstat [stat] [member]`'.format(ctx.prefix)
			await channel.send(msg)
			return

		try:
			newStat = self.getUserStat(member, server, stat)
		except KeyError:
			msg = '"{}" is not a valid stat for *{}*'.format(stat, DisplayName.name(member))
			await channel.send(msg)
			return

		msg = '**{}** for *{}* is *{}!*'.format(stat, DisplayName.name(member), newStat)
		await channel.send(msg)

	'''# Catch errors for stat
	@getstat.error
	async def getstat_error(self, error, ctx):
		msg = 'getstat Error: {}'.format(error)
		await ctx.channel.send(msg)'''
		

	@commands.command(pass_context=True)
	async def setsstat(self, ctx, stat : str = None, value : str = None):
		"""Sets a server stat (admin only)."""
		
		author  = ctx.message.author
		server  = ctx.message.guild
		channel = ctx.message.channel
		
		isAdmin = author.permissions_in(ctx.message.channel).administrator
		# Only allow admins to change server stats
		if not isAdmin:
			await channel.send('You do not have sufficient privileges to access this command.')
			return

		if stat == None or value == None:
			msg = 'Usage: `{}setsstat Stat Value`'.format(ctx.prefix)
			await channel.send(msg)
			return

		self.setServerStat(server, stat, value)

		msg = '**{}** set to *{}!*'.format(stat, value)
		await channel.send(msg)


	@commands.command(pass_context=True)
	async def getsstat(self, ctx, stat : str = None):
		"""Gets a server stat (admin only)."""
		
		author  = ctx.message.author
		server  = ctx.message.guild
		channel = ctx.message.channel
		
		isAdmin = author.permissions_in(channel).administrator
		# Only allow admins to change server stats
		if not isAdmin:
			await ctx.channel.send('You do not have sufficient privileges to access this command.')
			return

		if stat == None:
			msg = 'Usage: `{}getsstat [stat]`'.format(ctx.prefix)
			await ctx.channel.send(msg)
			return

		value = self.getServerStat(server, stat)

		msg = '**{}** is currently *{}!*'.format(stat, value)
		await channel.send(msg)
		
	@commands.command(pass_context=True)
	async def flush(self, ctx):
		"""Flush the bot settings to disk (admin only)."""
		# Only allow owner
		isOwner = self.isOwner(ctx.author)
		if isOwner == None:
			msg = 'I have not been claimed, *yet*.'
			await ctx.channel.send(msg)
			return
		elif isOwner == False:
			msg = 'You are not the *true* owner of me.  Only the rightful owner can use this command.'
			await ctx.channel.send(msg)
			return
		# Flush settings
		self.flushSettings()
		msg = 'Flushed settings to disk.'
		await ctx.channel.send(msg)
				

	# Flush loop - run every 10 minutes
	async def flushLoop(self, file = None):
		print('Starting flush loop - runs every {} seconds.'.format(self.settingsDump))
		if not file:
			file = self.file
		while not self.bot.is_closed():
			await asyncio.sleep(self.settingsDump)
			self.flushSettings()
				
	# Flush settings to disk
	def flushSettings(self, file = None):
		if not file:
			file = self.file
		if os.path.exists(file):
			# Delete file - then flush new settings
			os.remove(file)
		json.dump(self.serverDict, open(file, 'w'), indent=2)

	@commands.command(pass_context=True)
	async def prunelocalsettings(self, ctx):
		"""Compares the current server's settings to the default list and removes any non-standard settings (owner only)."""

		author  = ctx.message.author
		server  = ctx.message.guild
		channel = ctx.message.channel

		# Only allow owner
		isOwner = self.isOwner(ctx.author)
		if isOwner == None:
			msg = 'I have not been claimed, *yet*.'
			await ctx.channel.send(msg)
			return
		elif isOwner == False:
			msg = 'You are not the *true* owner of me.  Only the rightful owner can use this command.'
			await ctx.channel.send(msg)
			return

		removedSettings = 0
		settingsWord = "settings"

		if str(server.id) in self.serverDict["Servers"]:
			removeKeys = []
			for key in self.serverDict["Servers"][str(server.id)]:
				if not key in self.defaultServer:
					# Key isn't in default list - clear it
					removeKeys.append(key)
					removedSettings += 1
			for key in removeKeys:
				self.serverDict["Servers"][str(server.id)].pop(key, None)

		if removedSettings is 1:
			settingsWord = "setting"
		
		msg = 'Pruned *{} {}*.'.format(removedSettings, settingsWord)
		await ctx.channel.send(msg)
		# Flush settings
		self.flushSettings()


	def _prune_servers(self):
		# Remove any orphaned servers
		removed = 0
		servers = []
		for server in self.serverDict["Servers"]:
			# Check if the bot is still connected to the server
			g_check = self.bot.get_guild(int(server))
			if not g_check:
				servers.append(server)
		for server in servers:
			self.serverDict["Servers"].pop(server, None)
			removed += 1
		return removed

	def _prune_users(self):
		# Remove any orphaned servers
		removed = 0
		for server in self.serverDict["Servers"]:
			# Check if the bot is still connected to the server
			g_check = self.bot.get_guild(int(server))
			if not g_check:
				# Skip
				continue
			mems = []
			for mem in self.serverDict["Servers"][server]["Members"]:
				m_check = g_check.get_member(int(mem))
				if not m_check:
					mems.append(mem)
			for mem in mems:
				self.serverDict["Servers"][server]["Members"].pop(mem, None)
				removed += 1
		return removed

	'''def _prune_channels(self):
		# Remove orphaned MOTD settings
		removed = 0
		for server in self.serverDict["Servers"]:
			# Check if the bot is still connected to the server
			g_check = self.bot.get_guild(int(server))
			if not g_check:
				# Skip
				continue
			chans = []
			for chan in self.serverDict["Servers"][server]["ChannelMOTD"]:
				c_check = g_check.get_channel(int(chan))
				if not c_check:
					chans.append(chan)
			for chan in chans:
				self.serverDict["Servers"][server]["ChannelMOTD"].pop(chan, None)
				removed += 1
		return removed'''

	def _prune_settings(self):
		# Remove orphaned settings
		removed = 0
		for server in self.serverDict["Servers"]:
			# Check if the bot is still connected to the server
			g_check = self.bot.get_guild(int(server))
			if not g_check:
				# Skip
				continue
			keys = []
			for key in self.serverDict["Servers"][server]:
				if not key in self.defaultServer:
					keys.append(key)
			for key in keys:
				self.serverDict["Servers"][server].pop(key, None)
				removed += 1
		return removed


	@commands.command(pass_context=True)
	async def prunesettings(self, ctx):
		"""Compares all connected servers' settings to the default list and removes any non-standard settings (owner only)."""

		author  = ctx.message.author
		server  = ctx.message.guild
		channel = ctx.message.channel

		# Only allow owner
		isOwner = self.isOwner(ctx.author)
		if isOwner == None:
			msg = 'I have not been claimed, *yet*.'
			await ctx.channel.send(msg)
			return
		elif isOwner == False:
			msg = 'You are not the *true* owner of me.  Only the rightful owner can use this command.'
			await ctx.channel.send(msg)
			return

		removedSettings = 0
		settingsWord = "settings"

		for serv in self.serverDict["Servers"]:
			# Found it - let's check settings
			removeKeys = []
			for key in self.serverDict["Servers"][serv]:
				if not key in self.defaultServer:
					if key == "Name" or key == "ID":
						continue
					# Key isn't in default list - clear it
					removeKeys.append(key)
					removedSettings += 1
			for key in removeKeys:
				self.serverDict["Servers"][serv].pop(key, None)

		if removedSettings is 1:
			settingsWord = "setting"
		
		msg = 'Pruned *{} {}*.'.format(removedSettings, settingsWord)
		await ctx.channel.send(msg)
		# Flush settings
		self.flushSettings()


	@commands.command(pass_context=True)
	async def prune(self, ctx):
		"""Iterate through all members on all connected servers and remove orphaned settings (owner only)."""
		
		author  = ctx.message.author
		server  = ctx.message.guild
		channel = ctx.message.channel

		# Only allow owner
		isOwner = self.isOwner(ctx.author)
		if isOwner == None:
			msg = 'I have not been claimed, *yet*.'
			await ctx.channel.send(msg)
			return
		elif isOwner == False:
			msg = 'You are not the *true* owner of me.  Only the rightful owner can use this command.'
			await ctx.channel.send(msg)
			return

		ser = self._prune_servers()
		sst = self._prune_settings()
		mem = self._prune_users()
		#cha = self._prune_channels()
		glo = self.checkGlobalUsers()

		ser_str = "servers"
		sst_str = "settings"
		mem_str = "members"
		#cha_str = "channels"
		glo_str = "global users"

		if ser == 1:
			ser_str = "server"
		if sst == 1:
			sst_str = "setting"
		if mem == 1:
			mem_str = "member"
		#if cha == 1:
		#	cha_str = "channel"
		if glo == 1:
			glo_str = "global user"
		
		msg = 'Pruned *{} {}*, *{} {}*, *{} {}*, and *{} {}*.'.format(ser, ser_str, sst, sst_str, mem, mem_str, glo, glo_str)
		await ctx.channel.send(msg)

		# Flush settings
		self.flushSettings()
