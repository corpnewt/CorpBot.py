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
import redis
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
		self.settingsDump = 3600 # runs every hour
		self.bot = bot
		self.prefix = prefix
		self.loop_list = []
		self.role = RoleManager(bot)
		
		# Database time!!!!!
		self.r = redis.Redis(host="localhost",port=6379,db=0,decode_responses=True)

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
				"UserRoleBlock"			: [],		# List of users blocked from UserRoles
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
				"StreamChannel"			: None, 	# None or channel id
				"StreamList"			: [],		# List of user id's to watch for
				"StreamMessage"			: "Hey everyone! *[[user]]* started streaming *[[game]]!* Check it out here: [[url]]",
				"MuteList"				: []}		# List of muted members
		
		self.default_member = { 					# Default member vars - any dynamic vars will return None if not initialized
				"XP" : 0, 							# Will be overridden to the server's default XP
				"XPReserve" : 0, 					# Same as above
				"XPLeftover" : 0,
				"XPRealLeftOver" : 0,
				"Parts" : "",
				"Muted" : False,
				"LastOnline" : None,
				"Cooldown" : None,
				"Reminders" : [],					# Will be set to an empty list - not copied
				"Strikes" : [],
				"StrikeLevel" : 0,
				"Profiles" : [],
				"TempRoles" : [],
				"UTCOffset" : None,
				"LastCommand" : 0,
				"Hardware" : [],
				"VerificationTime" : 0
		}

		# Here we determine if we have a Settings.json file - if so
		# we load it, and migrate it to the Redis db, then rename
		# the file to Settings-migrated.json to avoid confusion
		# or double-migration.
		if os.path.exists(self.file):
			self.migrate_json(self.file)


	def migrate_json(self, f):
		# Function to migrate from a flat json file to a redis db
		# this will clear the redis db, load the json data, then
		# migrate all settings over.  There will be a logical order
		# to the naming of the keys:
		#
		# Global, top level values:
		#
		# PlistMax
		# PlistLevel
		# OwnerLock
		# Status
		# Type
		# Game
		# Stream
		# BlockedServers
		# ReturnChannel
		# CommandCooldown
		# Owner
		#
		# Global member stats formatting:
		#
		# globalmember:0123456789:statname
		#
		# HWActive
		# TimeZone
		# UTCOffset
		# Parts
		# Hardware
		#
		# Server-level stats formatting (see defaultServer):
		#
		# server:0123456789:statname
		#
		# Member stats per-server (see default_member):
		#
		# server:0123456789:member:0123456789:statname
		#
		start = time.time()
		print("")
		print("Located {} - preparing for migration...".format(f))
		print(" - Loading {}...".format(f))
		try:
			oldset = json.load(open(f))
		except Exception as e:
			print(" --> Failed to open, attempting to rename...")
			print(" ----> {}".format(e))
			try:
				parts = f.split(".")
				if len(parts) == 1:
					parts.append("json")
				name = ".".join(parts[0:-1]) + "-Error-{:%Y-%m-%d %H.%M.%S}".format(datetime.now()) + "." + parts[-1]
				os.rename(f, name)
				print(" ----> Renamed to {}".format(name))
			except Exception as e:
				print(" ----> Rename failed... wut... Bail.")
				print(" ------> {}".format(e))
				return
		# We should have the loaded json doc now
		# We first need to flush our db so we can import the settings
		print(" - Flushing current db...")
		self.r.flushall()
		# Let's go over all the parts and add them to our db
		glob_count = 0
		serv_count = 0
		memb_count = 0
		stat_count = 0
		print(" - Parsing GlobalMembers...")
		glob = oldset.get("GlobalMembers",{})
		glob_count = len(glob)
		# Walk the globs and move them over using the above format
		for g in glob:
			stat_count += len(glob[g])
			for stat in glob[g]:
				if stat == "HWActive":
					# This doesn't need to persist
					continue
				self.jset("globalmember:{}:{}".format(g, stat),glob[g][stat])
		
		# Walk the servers - and members when found in the same fashion
		print(" - Parsing Servers/Members...")
		servs = oldset.get("Servers",{})
		serv_count = len(servs)
		for s in servs:
			# Get the stats
			for t in servs[s]:
				if not t.lower() == "members":
					stat_count += 1
					# Not members, we just need to add the stat
					self.jset("server:{}:{}".format(s,t),servs[s][t])
				else:
					# Membertime!
					memb_count += len(servs[s][t])
					for m in servs[s][t]:
						# Iterate each member, and their subsequent stats
						stat_count += len(servs[s][t][m])
						for stat in servs[s][t][m]:
							# LOOPS FOR DAYS
							self.jset("server:{}:member:{}:{}".format(s,m,stat),servs[s][t][m][stat])
		# Iterate through any settings that aren't Servers or GlobalMembers
		print(" - Parsing remaining Global settings")
		for s in oldset:
			if s in ["GlobalMembers","Servers"]:
				continue
			stat_count += 1
			# Save the global setting!
			self.jset("{}".format(s), oldset[s])
		# Now we need to rename the file
		print(" - Renaming {}...".format(f))
		try:
			parts = f.split(".")
			if len(parts) == 1:
				parts.append("json")
			name = ".".join(parts[0:-1]) + "-Migrated-{:%Y-%m-%d %H.%M.%S}".format(datetime.now()) + "." + parts[-1]
			os.rename(f, name)
			print(" --> Renamed to {}".format(name))
		except Exception as e:
			print(" --> Rename failed... wut...")
			print(" ----> {}".format(e))
		print("Migrated {:,} GlobalMembers, {:,} Servers, {:,} Members, and {:,} total stats.".format(
			glob_count,
			serv_count,
			memb_count,
			stat_count
		))
		print("Migration took {:,} seconds.".format(time.time() - start))
		print("")

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
					if member.bot:
						# skip bots
						continue
					if not defRole in member.roles:
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
		# Works only for JSON files, not for database yet... :(
		# Works only for JSON files, not for database yet... :(
		# Works only for JSON files, not for database yet... :(

		# Temporarily avoid this until I have a better strategy
		return

		# Wait initial time - then start loop
		await asyncio.sleep(self.backupWait)
		while not self.bot.is_closed():
			# Initial backup - then wait
			if not os.path.exists(self.backupDir):
				# Create it
				os.makedirs(self.backupDir)
			# Flush backup
			timeStamp = datetime.today().strftime("%Y-%m-%d %H.%M")
			self.flushSettings("./{}/Backup-{}.json".format(self.backupDir, timeStamp), True)

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

	def jget(self, key, default = None):
		# Retrieves and loads the json data passed
		if not self.r.exists(key):
			return default
		return json.loads(self.r.get(key))

	def jset(self, key, value):
		# Sets the key to the json-serialized value
		return self.r.set(key, json.dumps(value))

	def isOwner(self, member):
		# This method converts prior, string-only ownership to a list,
		# then searches the list for the passed member
		ownerList = self.getGlobalStat("Owner",[])
		if not len(ownerList):
			return None
		if not type(ownerList) is list:
			# We have a string, convert
			ownerList = [ int(ownerList) ]
		# At this point - we should have a list
		# Let's make sure all parties exist still
		all_members = set([x.id for x in self.bot.get_all_members()])
		owners = [x for x in ownerList if x in all_members]
		# Update the setting if there were changes
		if len(owners) != len(ownerList):
			self.jset("Owner", owners)
		# Let us know if we're an owner
		return member.id in owners

	# Let's make sure the user is in the specified server
	def removeServer(self, server):
		if isinstance(server, discord.Guild):
			server = server.id
		# use the keys("prefix:*") loop to remove keys with our server:id: prefix
		for key in self.r.keys("server:{}:*".format(server)):
			self.r.delete(key)
		# Verify that we've removed the global members as well
		self.checkGlobalUsers()

	# Let's make sure the user is in the specified server
	def removeUser(self, user, server):
		if isinstance(user, (discord.User, discord.Member)):
			user = user.id
		if isinstance(server, discord.Guild):
			server = server.id
		# use the keys("prefix:*") loop to remove keys with our server:id:member:id prefix
		for key in self.r.keys("server:{}:member:{}*".format(server, user)):
			self.r.delete(key)
		check_members = set([x.id for x in self.bot.get_all_members()])
		if not int(user) in check_members:
			# Remove globally
			for key in self.r.keys("globalmember:{}*".format(user)):
				self.r.delete(key)

	def checkGlobalUsers(self):
		# Let's iterate over all globalmember:id values
		# and add them to a set
		total_members = []
		for key in self.r.keys("globalmember:*"):
			total_members.append(key.split(":")[1])
		# Strip out dupes
		total_members = set(total_members)
		check_members = set([str(x.id) for x in self.bot.get_all_members()])
		# Iterate through total_members, find out if exists - and if not,
		# remove all associated keys
		rem_count = 0
		for m in total_members:
			if m in check_members:
				continue
			rem_count += 1
			for key in self.r.keys("globalmember:{}*".format(m)):
				self.r.delete(key)
		return rem_count
	
	# Return the requested stat
	def getUserStat(self, user, server, stat, default = None):
		# Get user stat - but set up a default in case of some settings
		if isinstance(user, (discord.User, discord.Member)):
			user = user.id
		if isinstance(server, discord.Guild):
			server = server.id
		out = self.jget("server:{}:member:{}:{}".format(server, user, stat), default)
		if out != None:
			return out
		# Check if we need defaults
		if stat == "XP":
			return self.jget("server:{}:DefaultXP", self.defaultServer["DefaultXP"])
		if stat == "XPReserve":
			return self.jget("server:{}:DefaultXPReserve", self.defaultServer["DefaultXPReserve"])
		test = self.default_member.get(stat,out)
		if isinstance(test, list):
			return []
		elif isinstance(test, dict):
			return {}
		# Return whatever we've got
		return test
	
	def getGlobalUserStat(self, user, stat, default = None):
		# Get our global user stat if exists
		if isinstance(user, (discord.User, discord.Member)):
			user = user.id
		return self.jget("globalmember:{}:{}".format(user, stat), default)

	def getGlobalStat(self, stat, default = None):
		return self.jget(stat, default)

	def setGlobalStat(self, stat, value):
		self.jset(stat, value)

	def delGlobalStat(self, stat):
		if self.r.exists(stat):
			self.r.delete(stat)
	
	def setUserStat(self, user, server, stat, value):
		if isinstance(user, (discord.User, discord.Member)):
			user = user.id
		if isinstance(server, discord.Guild):
			server = server.id
		self.jset("server:{}:member:{}:{}".format(server, user, stat), value)
						
	# Set a provided global stat
	def setGlobalUserStat(self, user, stat, value):
		if isinstance(user, (discord.User, discord.Member)):
			user = user.id
		self.jset("globalmember:{}:{}".format(user, stat), value)

	def delGlobalUserStat(self, user, stat):
		if isinstance(user, (discord.User, discord.Member)):
			user = user.id
		if self.r.exists("globalmember:{}:{}".format(user, stat)):
			self.r.delete("globalmember:{}:{}".format(user, stat))
					
	# Increment a specified user stat by a provided amount
	# returns the stat post-increment, or None if error
	def incrementStat(self, user, server, stat, incrementAmount):
		# Get initial value - set to 0 if doesn't exist
		if isinstance(user, (discord.User, discord.Member)):
			user = user.id
		if isinstance(server, discord.Guild):
			server = server.id
		out = self.jget("server:{}:member:{}:{}".format(server, user, stat))
		out = 0 if not out else out
		self.jset("server:{}:member:{}:{}".format(server, user, stat), out+incrementAmount)
		return out+incrementAmount
	
	# Get the requested stat
	def getServerStat(self, server, stat, default = None):
		# Get server stat - but set up a default in case of some settings
		if isinstance(server, discord.Guild):
			server = server.id
		out = self.jget("server:{}:{}".format(server, stat), default)
		if out != None:
			return out
		test = self.defaultServer.get(stat,out)
		if isinstance(test, list):
			return []
		elif isinstance(test, dict):
			return {}
		# Return whatever we've got
		return test
	
	# Set the provided stat
	def setServerStat(self, server, stat, value):
		if isinstance(server, discord.Guild):
			server = server.id
		self.jset("server:{}:{}".format(server, stat), value)

	@commands.command(pass_context=True)
	async def ownerlock(self, ctx):
		"""Locks/unlocks the bot to only respond to the owner (owner-only... ofc)."""
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
		ol = self.getGlobalStat("OwnerLock",[])
		# OwnerLock defaults to "No"
		if not ol:
			self.setGlobalStat("OwnerLock",True)
			msg = 'Owner lock **Enabled**.'
			await self.bot.change_presence(activity=discord.Activity(name="OwnerLocked", type=0))
			# await self.bot.change_presence(game=discord.Game(name="OwnerLocked"))
		else:
			self.setGlobalStat("OwnerLock",False)
			msg = 'Owner lock **Disabled**.'
			await self.bot.change_presence(activity=discord.Activity(status=self.jget("Status"), name=self.jget("Game"), url=self.jget("Stream"), type=self.jget("Type", 0)))
		await ctx.send(msg)

	@commands.command(pass_context=True)
	async def owners(self, ctx):
		"""Lists the bot's current owners."""
		# Check to force the owner list update
		self.isOwner(ctx.author)
		ownerList = self.getGlobalStat('Owner',[])
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
		await ctx.send(msg)

	
	@commands.command(pass_context=True)
	async def claim(self, ctx):
		"""Claims the bot if disowned - once set, can only be changed by the current owner."""
		owned = self.isOwner(ctx.author)
		if owned:
			# We're an owner
			msg = "You're already one of my owners."
		elif owned == False:
			# We're not an owner
			msg = "I've already been claimed."
		else:
			# Claim it up
			self.setGlobalStat("Owner",self.getGlobalStat("Owner",[]).append(ctx.author.id))
			msg = 'I have been claimed by *{}!*'.format(DisplayName.name(ctx.author))
		await ctx.send(msg)
	
	@commands.command(pass_context=True)
	async def addowner(self, ctx, *, member : str = None):
		"""Adds an owner to the owner list.  Can only be done by a current owner."""
		owned = self.isOwner(ctx.author)
		if owned == False:
			msg = "Only an existing owner can add more owners."
			await ctx.send(msg)
			return
		if member == None:
			member = ctx.author
		if type(member) is str:
			memberCheck = DisplayName.memberForName(member, ctx.guild)
			if memberCheck:
				member = memberCheck
			else:
				msg = 'I couldn\'t find that user...'
				await ctx.send(msg)
				return
		if member.bot:
			msg = "I can't be owned by other bots.  I don't roll that way."
			await ctx.send(msg)
			return
		owners = self.getGlobalStat("Owner",[])
		if member.id in owners:
			# Already an owner
			msg = "Don't get greedy now - *{}* is already an owner.".format(DisplayName.name(member))
		else:
			owners.append(member.id)
			self.setGlobalStat("Owner",owners)
			msg = '*{}* has been added to my owner list!'.format(DisplayName.name(member))
		await ctx.send(msg)

	@commands.command(pass_context=True)
	async def remowner(self, ctx, *, member : str = None):
		"""Removes an owner from the owner list.  Can only be done by a current owner."""
		owned = self.isOwner(ctx.author)
		if owned == False:
			msg = "Only an existing owner can remove owners."
			await ctx.send(msg)
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
		owners = self.getGlobalStat("Owner",[])
		if member.id in owners:
			# Found an owner!
			msg = "*{}* is no longer an owner.".format(DisplayName.name(member))
			owners.remove(member.id)
			self.setGlobalStat("Owner",owners)
		else:
			msg = "*{}* can't be removed because they're not one of my owners.".format(DisplayName.name(member))
		if not len(owners):
			# No more owners
			msg += " I have been disowned!"
		await ctx.send(msg)

	@commands.command(pass_context=True)
	async def disown(self, ctx):
		"""Revokes all ownership of the bot."""
		owned = self.isOwner(ctx.author)
		if owned == False:
			msg = "Only an existing owner can revoke ownership."
			await ctx.send(msg)
			return
		elif owned == None:
			# No owners
			msg = 'I have already been disowned...'
			await ctx.send(msg)
			return
		self.setGlobalStat("Owner",[])
		msg = 'I have been disowned!'
		await ctx.send(msg)

	@commands.command(pass_context=True)
	async def getstat(self, ctx, stat : str = None, member : discord.Member = None):
		"""Gets the value for a specific stat for the listed member (case-sensitive)."""
		if member == None:
			member = ctx.author
		if str == None:
			msg = 'Usage: `{}getstat [stat] [member]`'.format(ctx.prefix)
			await ctx.send(msg)
			return
		if type(member) is str:
			try:
				member = discord.utils.get(ctx.guild.members, name=member)
			except:
				print("That member does not exist")
				return
		if member is None:
			msg = 'Usage: `{}getstat [stat] [member]`'.format(ctx.prefix)
			await ctx.send(msg)
			return
		try:
			newStat = self.getUserStat(member, ctx.guild, stat)
		except KeyError:
			msg = '"{}" is not a valid stat for *{}*'.format(stat, DisplayName.name(member))
			await ctx.send(msg)
			return
		msg = '**{}** for *{}* is *{}!*'.format(stat, DisplayName.name(member), newStat)
		await ctx.send(msg)

	@commands.command(pass_context=True)
	async def setsstat(self, ctx, stat : str = None, value : str = None):
		"""Sets a server stat (admin only)."""
		isAdmin = ctx.author.permissions_in(ctx.channel).administrator
		# Only allow admins to change server stats
		if not isAdmin:
			await ctx.send('You do not have sufficient privileges to access this command.')
			return
		if stat == None or value == None:
			msg = 'Usage: `{}setsstat Stat Value`'.format(ctx.prefix)
			await ctx.send(msg)
			return
		self.setServerStat(ctx.guild, stat, value)
		msg = '**{}** set to *{}!*'.format(stat, value)
		await ctx.send(msg)

	@commands.command(pass_context=True)
	async def getsstat(self, ctx, stat : str = None):
		"""Gets a server stat (admin only)."""
		isAdmin = ctx.author.permissions_in(ctx.channel).administrator
		# Only allow admins to change server stats
		if not isAdmin:
			await ctx.send('You do not have sufficient privileges to access this command.')
			return
		if stat == None:
			msg = 'Usage: `{}getsstat [stat]`'.format(ctx.prefix)
			await ctx.send(msg)
			return
		value = self.getServerStat(ctx.guild, stat)
		msg = '**{}** is currently *{}!*'.format(stat, value)
		await ctx.send(msg)
		
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
		message = await ctx.send("Flushing settings to disk...")
		# Actually flush settings
		self.flushSettings()
		msg = 'Flushed settings to disk.'
		await message.edit(content=msg)
				
	# Flush loop json - run every 10 minutes
	async def flushLoop(self):
		print('Starting flush loop - runs every {} seconds.'.format(self.settingsDump))
		while not self.bot.is_closed():
			await asyncio.sleep(self.settingsDump)
			# Actually flush settings
			self.flushSettings()
				
	# Flush settings to disk
	def flushSettings(self):
		self.r.bgsave()

	@commands.command(pass_context=True)
	async def prunelocalsettings(self, ctx):
		"""Compares the current server's settings to the default list and removes any non-standard settings (owner only)."""
		# Only allow owner
		isOwner = self.isOwner(ctx.author)
		if isOwner == None:
			msg = 'I have not been claimed, *yet*.'
			await ctx.send(msg)
			return
		elif isOwner == False:
			msg = 'You are not the *true* owner of me.  Only the rightful owner can use this command.'
			await ctx.send(msg)
			return
		message = await ctx.send("Pruning local settings...")
		removedSettings = 0
		settingsWord = "settings"
		for entry in self.r.keys("server:{}:[^member]*".format(ctx.guild.id)):
			name = entry.split(":")[-1]
			if not name in self.defaultServer:
				self.r.delete(entry)
				removedSettings += 1
		if removedSettings is 1:
			settingsWord = "setting"
		await message.edit(content="Flushing settings to disk...", embed=None)
		# Actually flush settings
		# self.flushSettings()
		msg = 'Pruned *{} {}*.'.format(removedSettings, settingsWord)
		await message.edit(content=msg, embed=None)

	def _prune_servers(self):
		# Remove any orphaned servers
		removed = 0
		server_list = [str(x.id) for x in self.bot.guilds]
		server_db   = self.r.keys("server:*")
		current     = set([x.split(":")[1] for x in server_db])
		# We now have a list of all the servers in our settings,
		# as well as a list of all servers the bot is connected to
		for s in current:
			if not s in server_list:
				# Remove
				removed += 1
				for x in self.r.keys("server:{}*".format(s)):
					self.r.delete(x)
		return removed

	def _prune_users(self):
		# Remove any orphaned members
		removed = 0
		server_list = ["{}:{}".format(x.guild.id, x.id) for x in self.bot.get_all_members()]
		server_db   = self.r.keys("server:*:member:*")
		current     = set([":".join(x.split(":")[1:4:2]) for x in server_db])
		for s in current:
			if not s in server_list:
				# Remove
				removed += 1
				sp = s.split(":")
				for x in self.r.keys("server:{}:member:{}*".format(sp[0],sp[1])):
					self.r.delete(x)
		return removed

	def _prune_settings(self):
		# Remove orphaned settings
		removed = 0
		for g in self.bot.guilds:
			for entry in self.r.keys("server:{}:[^member]*".format(g.id)):
				name = entry.split(":")[-1]
				if not name in self.defaultServer:
					self.r.delete(entry)
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

		message = await ctx.send("Pruning settings...")

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

		await message.edit(content="Flushing settings to disk...")
		# Actually flush settings
		self.flushSettings()
		
		msg = 'Pruned *{} {}*.'.format(removedSettings, settingsWord)
		await message.edit(content=msg)


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

		message = await ctx.send("Pruning all orphaned members and settings...")

		l = asyncio.get_event_loop()
		ser = await self.bot.loop.run_in_executor(None, self._prune_servers)
		sst = await self.bot.loop.run_in_executor(None, self._prune_settings)
		mem = await self.bot.loop.run_in_executor(None, self._prune_users)
		glo = await self.bot.loop.run_in_executor(None, self.checkGlobalUsers)

		ser_str = "servers"
		sst_str = "settings"
		mem_str = "members"
		glo_str = "global users"

		if ser == 1:
			ser_str = "server"
		if sst == 1:
			sst_str = "setting"
		if mem == 1:
			mem_str = "member"
		if glo == 1:
			glo_str = "global user"

		await message.edit(content="Flushing settings to disk...")
		# Actually flush settings
		self.flushSettings()
		
		msg = 'Pruned *{} {}*, *{} {}*, *{} {}*, and *{} {}*.'.format(ser, ser_str, sst, sst_str, mem, mem_str, glo, glo_str)
		await message.edit(content=msg)
