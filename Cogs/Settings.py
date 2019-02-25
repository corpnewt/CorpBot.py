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
from   Cogs        import PandorasDB


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

class Settings(commands.Cog):
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
		self.is_current = False # Used for stopping loops
		self.role = RoleManager(bot)
		self.pd = PandorasDB.PandorasDB()
		
		# Database time!!!!!
		# self.r = redis.Redis(host="localhost",port=6379,db=0,decode_responses=True)

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
				"MuteList"				: [],		# List of muted members
				"ID"					: ""}		# Placeholder to store the server's id
		
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

	def migrate_json(self, f):
		self.pd.migrate(f)

	def suppressed(self, guild, msg):
		# Check if we're suppressing @here and @everyone mentions
		if self.settings.getServerStat(guild, "SuppressMentions"):
			return Nullify.clean(msg)
		else:
			return msg

	async def onjoin(self, member, server):
		# Welcome - and initialize timers
		try:
			vt = time.time() + int(self.getServerStat(server,"VerificationTime",0)) * 60
		except:
			vt = 0
		self.setUserStat(member,server,"VerificationTime",vt)
		self.bot.loop.create_task(self.giveRole(member, server))

	# Proof of concept stuff for reloading cog/extension
	def _is_submodule(self, parent, child):
		return parent == child or child.startswith(parent + ".")

	@commands.Cog.listener()
	async def on_unloaded_extension(self, ext):
		# Called to shut things down
		if not self._is_submodule(ext.__name__, self.__module__):
			return
		# Flush settings
		self.flushSettings()
		# Shutdown role manager loop
		self.role.clean_up()
		self.is_current = False
		#for task in self.loop_list:
		#	task.cancel()

	@commands.Cog.listener()
	async def on_loaded_extension(self, ext):
		# See if we were loaded
		if not self._is_submodule(ext.__name__, self.__module__):
			return
		# Check all verifications - and start timers if needed
		# self.bot.loop.create_task(self.checkAll())
		# Start the backup loop
		# self.bot.loop.create_task(self.backup())
		# Start the settings loop
		self.is_current = True
		# Here we determine if we have a Settings.json file - if so
		# we load it, and migrate it to the Redis db, then rename
		# the file to Settings-migrated.json to avoid confusion
		# or double-migration.
		if os.path.exists(self.file):
			await self.bot.loop.run_in_executor(None, self.migrate_json, self.file)
		# After that's done, we can do other shit
		self.bot.loop.create_task(self.flushLoop())
		print("Verifying default roles...")
		t = time.time()
		await self.bot.loop.run_in_executor(None, self.check_all)
		print("Verified default roles in {} seconds.".format(time.time() - t))

	def check_all(self):
		# Check all verifications - and start timers if needed
		guilds = {}
		for x in self.bot.get_all_members():
			mems = guilds.get(str(x.guild.id),[])
			mems.append(x)
			guilds[str(x.guild.id)] = mems
		for server_id in guilds:
			# Check if we can even manage roles here
			server = self.bot.get_guild(int(server_id))
			if not server.me.guild_permissions.manage_roles:
				continue
			# Get default role
			defRole = self.getServerStat(server, "DefaultRole")
			defRole = DisplayName.roleForID(defRole, server)
			if defRole:
				# We have a default - check for it
				for member in guilds[server_id]:
					if member.bot:
						# skip bots
						continue
					if not defRole in member.roles:
						# We don't have the role - set a timer
						self.bot.loop.create_task(self.giveRole(member, server))

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

		if not self.is_current:
			# Not current anymore, bail
			return
		
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
		'''if task in self.loop_list:
			self.loop_list.remove(task)'''

	async def backup(self):
		# Works only for JSON files, not for database yet... :(
		# Works only for JSON files, not for database yet... :(
		# Works only for JSON files, not for database yet... :(

		# Temporarily avoid this until I have a better strategy
		# will probably only enable this for sqlite - which means
		# the PandorasDB module should handle this.  Any other db
		# should be managed by the db server.
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

	def isOwner(self, member):
		# This method converts prior, string-only ownership to a list,
		# then searches the list for the passed member
		ownerList = self.getGlobalStat("Owner",[])
		ownerList = [] if ownerList == None else ownerList
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
			self.setGlobalStat("Owner", owners)
		# Let us know if we're an owner
		return member.id in owners

	# Let's make sure the user is in the specified server
	def removeServer(self, server):
		self.pd.del_servers(server.id)
		# Verify that we've removed the global members as well
		self.checkGlobalUsers()

	# Let's make sure the user is in the specified server
	def removeUser(self, user, server):
		self.pd.del_users(user.id, server)
		# Verify that we've removed the global members as well
		self.checkGlobalUsers()

	# Global Stat

	def getGlobalStat(self, stat, default = None):
		return self.pd.get_global(stat, default)

	def setGlobalStat(self, stat, value):
		return self.pd.set_global(stat, value)

	def delGlobalStat(self, stat):
		return self.pd.del_global(stat)

	# Global Users Stat

	def getGlobalUserStat(self, user, stat, default = None):
		# Get our global user stat if exists
		return self.pd.get_guser(user, stat, default)
						
	def setGlobalUserStat(self, user, stat, value):
		return self.pd.set_guser(user,stat,value)

	def delGlobalUserStat(self, user, stat):
		return self.pd.del_guser(user,stat)

	def checkGlobalUsers(self):
		total_members = self.pd.all_guser()
		check_members = set([str(x.id) for x in self.bot.get_all_members()])
		return self.pd.del_gusers([x for x in total_members if not x in check_members])

	# Server Stats

	def getServerStat(self, server, stat, default = None):
		# Get server stat - but set up a default in case of some settings
		out = self.pd.get_server(server, stat, default)
		if out != None:
			return out
		test = self.defaultServer.get(stat,out)
		if isinstance(test, list):
			return []
		elif isinstance(test, dict):
			return {}
		# Return whatever we've got
		return test
	
	def setServerStat(self, server, stat, value):
		return self.pd.set_server(server, stat, value)
	
	# User Stats

	def getUserStat(self, user, server, stat, default = None):
		# Get user stat - but set up a default in case of some settings
		out = self.pd.get_user(user, server, stat, default)
		if out != None:
			return out
		# Check if we need defaults
		if stat == "XP":
			return self.getServerStat(server,"DefaultXP",self.defaultServer["DefaultXP"])
		if stat == "XPReserve":
			return self.getServerStat(server,"DefaultXPReserve",self.defaultServer["DefaultXPReserve"])
		test = self.default_member.get(stat,out)
		if isinstance(test, list):
			return []
		elif isinstance(test, dict):
			return {}
		# Return whatever we've got
		return test

	def setUserStat(self, user, server, stat, value):
		return self.pd.set_user(user, server, stat, value)

	def delUserStat(self, user, server, stat):
		return self.pd.del_user(user, server, stat)
					
	# Increment a specified user stat by a provided amount
	# returns the stat post-increment, or None if error
	def incrementStat(self, user, server, stat, incrementAmount):
		# Get initial value - set to 0 if doesn't exist
		out = self.getUserStat(user, server, stat)
		out = 0 if not out else out
		self.setUserStat(user, server, stat, out+incrementAmount)
		return out+incrementAmount

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
			await self.bot.change_presence(activity=discord.Activity(
				status=self.getGlobalStat("Status"), 
				name=self.getGlobalStat("Game"), 
				url=self.getGlobalStat("Stream"), 
				type=self.getGlobalStat("Type", 0)
			))
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
			self.setGlobalStat("Owner",[ctx.author.id])
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
			if not self.is_current:
				# We're not longer the active instance - bail
				return
			# Actually flush settings
			try:
				await self.bot.loop.run_in_executor(None, self.flushSettings)
			except:
				pass
				
	# Flush settings to disk
	def flushSettings(self):
		try:
			self.pd.save_db()
		except:
			print("Failed to save - likely already saving.")

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
		settingsWord = "settings"
		removedSettings = self._prune_settings(ctx.guild)
		if removedSettings is 1:
			settingsWord = "setting"
		msg = 'Pruned *{} {}*.'.format(removedSettings, settingsWord)
		await message.edit(content=msg, embed=None)

	def _prune_servers(self):
		# Remove any orphaned servers
		server_list = set([str(x.guild.id) for x in self.bot.get_all_members()])
		server_db   = set([x.split(":")[1] for x in self.pd.all_server()])
		remove      = [x for x in server_db if not x in server_list]
		return self.pd.del_servers(remove)

	def _prune_users(self):
		# Remove any orphaned members
		removed = 0
		server_list = set([str(x.guild.id) for x in self.bot.get_all_members()])
		for s in server_list:
			ukeys = self.pd.all_user(s)
			u_set = set([x.split(":")[0] for x in ukeys])
			member_list = set([str(x.id) for x in self.bot.get_all_members() if str(x.guild.id)==s])
			for u in u_set:
				if not u in member_list:
					removed += self.pd.del_users(u,s)		
		return removed

	def _prune_settings(self, guild = None):
		# Remove orphaned settings
		removed = 0
		if not guild:
			guilds = set([x.guild.id for x in self.bot.get_all_members()])
		else:
			guilds = [guild]
		for g in guilds:
			for entry in self.pd.get_smatch(g,"[^member]"):
				name = entry.split(":")[-1]
				if not name in self.defaultServer:
					self.pd.del_server(g, entry)
					removed += 1
		return removed

	@commands.command(pass_context=True)
	async def prunesettings(self, ctx):
		"""Compares all connected servers' settings to the default list and removes any non-standard settings (owner only)."""
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

		settingsWord = "settings"

		message = await ctx.send("Pruning settings...")

		removedSettings = await self.bot.loop.run_in_executor(None, self._prune_settings)

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

		message = await ctx.send("Pruning orphaned servers...")
		l = asyncio.get_event_loop()
		ser = await self.bot.loop.run_in_executor(None, self._prune_servers)
		await message.edit(content="Pruning orphaned settings...")
		sst = await self.bot.loop.run_in_executor(None, self._prune_settings)
		await message.edit(content="Pruning orphaned users...")
		mem = await self.bot.loop.run_in_executor(None, self._prune_users)
		await message.edit(content="Pruning orphaned global users...")
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
