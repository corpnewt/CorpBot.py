import asyncio
import discord
from   discord.ext import commands
import json
import os


# This is the settings module - it allows the other modules to work with
# a global settings variable and to make changes

class Settings:
	"""The Doorway To The Server Settings"""
	# Let's initialize with a file location
	def __init__(self, bot, file : str = None):
		if file == None:
			# We weren't given a file, default to ./Settings.json
			file = "Settings.json"
		
		self.file = file
		self.bot = bot
		self.serverDict = {}
		
		# Let's load our settings file
		if os.path.exists(file):
			self.serverDict = json.load(open(file))
		else:
			# File doesn't exist - create a placeholder
			self.serverDict = {}
		
		# Removed for now as it may not be necessary,
		# Servers should auto-add whenever a user/server value
		# is requested or changed
		'''# Now we go through all the servers the bot is in and
		# make sure they're initialized
		for server in bot.servers:
			# Iterate through the servers and add them
			checkServer(server, globals.serverList)
			for user in server.members:
				checkUser(user, server, globals.serverList)'''

	def message(self, message):
		# Check the message and see if we should allow it - always yes.
		# This module doesn't need to cancel messages.
		return { 'Ignore' : False, 'Delete' : False}

	def getServerDict(self):
		# Returns the server dictionary
		return self.serverDict

	# Let's make sure the server is in our list
	def checkServer(self, server):
		# Checks the server agains the globals.serverList variable
		
		# Assumes server = discord.Server and serverList is a dict
		if not "Servers" in self.serverDict:
			# Let's add an empty placeholder
			self.serverDict["Servers"] = []
		found = False
		for x in self.serverDict["Servers"]:
			if x["Name"] == server.name:
				# We found our server
				found = True
		if found == False:
			# We didn't locate our server
			# print("Server not located, adding...")
			newServer = { "Name" : server.name, "ID" : server.id,
				"AutoRole" 				: "No", 	# No/ID/Position
				"DefaultRole" 			: "1", 		# Auto-assigned role position
				"AdminLock" 			: "No", 	# Does the bot *only* answer to admins?
				"MinimumXPRole" 		: "1", 		# Minimum role position for XP
				"RequiredLinkRole" 		: "", 		# ID or blank for Admin-Only
				"RequiredHackRole" 		: "", 		# ID or blank for Admin-Only
				"RequiredKillRole" 		: "", 		# ID or blank for Admin-Only
				"RequiredStopRole"      : "",       # ID or blank for Admin-Only
				"XPApprovalChannel" 	: "", 		# Not Used
				"MadLibsChannel"        : "",       # ID or blank for any channel
				"LastAnswer" 			: "",		# URL to last $question post
				"HourlyXP" 				: "1",		# How much xp reserve per hour
				"IncreasePerRank" 		: "1",		# Extra XP per rank
				"RequireOnline" 		: "Yes",	# Must be online for xp?
				"AdminUnlimited" 		: "Yes",	# Do admins have unlimited xp to give?
				"XPPromote" 			: "Yes",	# Can xp raise your rank?
				"PromoteBy" 			: "Array", 	# Position/Array
				"MaxPosition" 			: "5",		# Furthest position xp can promote you to
				"RequiredXP" 			: "0",		# Required xp per level in positional promotion
				"DifficultyMultiplier" 	: "0",		# How much MORE xp you need per role increase (position only)
				"PadXPRoles" 			: "0",		# How many roles worth of padding to give
				"XPDemote" 				: "No",		# Can xp lower your rank?
				"Killed" 				: "No",		# Is the bot dead?
				"KilledBy" 				: "",		# Who killed the bot?
				"LastPicture" 			: "0",		# UTC Timestamp of last picture uploaded
				"PictureThreshold" 		: "10",		# 
				"Rules" 				: "Be nice to each other.",
				"PromotionArray" 		: [],		# An array of roles for promotions
				"Hunger" 				: "0",		# The bot's hunger % 0-100 (can also go negative)
				"HungerLock" 			: "Yes",	# Will the bot stop answering at 100% hunger?
				"Hacks" 				: [],		# List of hack tips
				"Links" 				: [],		# List of links
				"Members" 				: [],		# List of members
				"AdminArray"	 		: [],		# List of admin roles
				"ChannelMOTD" 			: []}		# List of channel messages of the day
			self.serverDict["Servers"].append(newServer)
			self.flushSettings()
	
	
	# Let's make sure the user is in the specified server
	def checkUser(self, user, server):
		# Make sure our server exists in the list
		self.checkServer(server)
		# Check for our username
		found = False
		for x in self.serverDict["Servers"]:
			if x["ID"] == server.id:
				# We found our server, now to iterate users
				for y in x["Members"]:
					if y["ID"] == user.id:
						found = True
						needsUpdate = False
						if not "XP" in y:
							y["XP"] = 0
							needsUpdate = True
						if not "XPReserve" in y:
							y["XPReserve"] = 10
							needsUpdate = True
						if not "ID" in y:
							y["ID"] = user.id
							needsUpdate = True
						if not "Discriminator" in y:
							y["Discriminator"] = user.discriminator
							needsUpdate = True
						if not "Name" in y:
							y["Name"] = user.name
							needsUpdate = True
						if not "DisplayName" in y:
							y["DisplayName"] = user.display_name
							needsUpdate = True
						if not "Parts" in y:
							y["Parts"] = ""
							needsUpdate = True
						if not "Muted" in y:
							y["Muted"] = "No"
							needsUpdate = True
						if not "LastOnline" in y:
							y["LastOnline"] = "Unknown"
							needsUpdate = True
				if not found:
					needsUpdate = True
					# We didn't locate our user - add them
					newUser = { "Name" 			: user.name,
								"DisplayName" 	: user.display_name,
								"XP" 			: 0,
								"XPReserve" 	: 10,
								"ID" 			: user.id,
								"Discriminator" : user.discriminator,
								"Parts"			: "",
								"Muted"			: "No",
								"LastOnline"	: "Unknown" }
					x["Members"].append(newUser)
				if needsUpdate:
					self.flushSettings()

	# Let's make sure the user is in the specified server
	def removeUser(self, user, server):
		# Make sure our server exists in the list
		self.checkServer(server)
		# Check for our username
		found = False
		for x in self.serverDict["Servers"]:
			if x["ID"] == server.id:
				# We found our server, now to iterate users
				for y in x["Members"]:
					if y["ID"] == user.id:
						found = True
						# Found our user - remove
						x["Members"].remove(y)
		if found:
			self.flushSettings()

	
	# Return the requested stat
	def getUserStat(self, user, server, stat):
		# Make sure our user and server exists in the list
		self.checkUser(user, server)
		# Check for our username
		for x in self.serverDict["Servers"]:
			if x["ID"] == server.id:
				# We found our server, now to iterate users
				for y in x["Members"]:
					if y["ID"] == user.id:
						# Found our user - now check for the stat
						if stat in y:
							# Stat exists - return it
							return y[stat]
						else:
							# Stat does not exist - return None
							return None
		# If we were unable to add/find the user (unlikely), return None
		return None
	
	
	# Set the provided stat
	def setUserStat(self, user, server, stat, value):
		# Make sure our user and server exists in the list
		self.checkUser(user, server)
		# Check for our username
		for x in self.serverDict["Servers"]:
			if x["ID"] == server.id:
				# We found our server, now to iterate users
				for y in x["Members"]:
					if y["ID"] == user.id:
						# Found our user - let's set the stat
						y[stat] = value
						self.flushSettings()
						
					
	# Increment a specified user stat by a provided amount
	# returns the stat post-increment, or None if error
	def incrementStat(self, user, server, stat, incrementAmount):
		# Make sure our user and server exist
		self.checkUser(user, server)
		# Check for our username
		for x in self.serverDict["Servers"]:
			if x["ID"] == server.id:
				# We found our server, now to iterate users
				for y in x["Members"]:
					if y["ID"] == user.id:
						# Found our user - check for stat
						if stat in y:
							# Found
							tempStat = int(y[stat])
							tempStat += int(incrementAmount)
							y[stat] = tempStat
							self.flushSettings()
							return tempStat
						else:
							# No stat - set stat to increment amount
							y[stat] = incrementAmount
							self.flushSettings()
							return incrementAmount
		# If we made it here - we failed somewhere, return None
		return None
	
	
	# Get the requested stat
	def getServerStat(self, server, stat):
		# Make sure our server exists in the list
		self.checkServer(server)
		# Check for our server
		for x in self.serverDict["Servers"]:
			if x["ID"] == server.id:
				# Found the server, check for the stat
				if stat in x:
					return x[stat]
				else:
					return None
		# Server was not located - return None
		return None
	
	
	# Set the provided stat
	def setServerStat(self, server, stat, value):
		# Make sure our server exists in the list
		self.checkServer(server)
		# Check for our server
		for x in self.serverDict["Servers"]:
			if x["ID"] == server.id:
				# We found our server - set the stat
				x[stat] = value
				self.flushSettings()

	
	@commands.command(pass_context=True)
	async def owner(self, ctx, member : discord.Member = None):
		"""Sets the bot owner - once set, can only be changed by the current owner."""
		author  = ctx.message.author
		server  = ctx.message.server
		channel = ctx.message.channel

		if member == None:
			member = author

		if type(member) is str:
			try:
				member = discord.utils.get(server.members, name=member)
			except:
				print("That member does not exist")
				return

		try:
			owner = self.serverDict['Owner']
		except KeyError:
			owner = None

		if owner == None:
			# No previous owner, let's set them
			self.serverDict['Owner'] = member.id
			self.flushSettings()
		else:
			if not author.id == owner:
				msg = 'You are not the *true* owner of me.  Only the rightful owner can change this setting.'
				await self.bot.send_message(channel, msg)
				return
			self.serverDict['Owner'] = member.id
			self.flushSettings()

		msg = 'I have been claimed by *{}!*'.format(member.name)
		await self.bot.send_message(channel, msg)

	@owner.error
	async def owner_error(ctx, error):
		msg = 'owner Error: {}'.format(ctx)
		await self.bot.say(msg)


	@commands.command(pass_context=True)
	async def disown(self, ctx):
		"""Revokes ownership of the bot."""
		author  = ctx.message.author
		server  = ctx.message.server
		channel = ctx.message.channel

		try:
			owner = self.serverDict['Owner']
		except KeyError:
			owner = None

		if owner == None:
			# No previous owner, let's set them
			msg = 'I have already been disowned...'
			await self.bot.send_message(channel, msg)
			return
		else:
			if not author.id == owner:
				msg = 'You are not the *true* owner of me.  Only the rightful owner can disown me.'
				await self.bot.send_message(channel, msg)
				return
			self.serverDict['Owner'] = None
			self.flushSettings()

		msg = 'I have been disowned by *{}!*'.format(author.name)
		await self.bot.send_message(channel, msg)


	@commands.command(pass_context=True)
	async def getstat(self, ctx, stat : str = None, member : discord.Member = None):
		"""Gets the value for a specific stat for the listed member (case-sensitive)."""
		
		author  = ctx.message.author
		server  = ctx.message.server
		channel = ctx.message.channel
		
		if member == None:
			member = author

		if str == None:
			msg = 'Usage: `$getstat [stat] [member]`'
			await self.bot.send_message(channel, msg)
			return

		if type(member) is str:
			try:
				member = discord.utils.get(server.members, name=member)
			except:
				print("That member does not exist")
				return

		if member is None:
			msg = 'Usage: `$getstat [stat] [member]`'
			await self.bot.send_message(channel, msg)
			return

		try:
			newStat = self.getUserStat(member, server, stat)
		except KeyError:
			msg = '"{}" is not a valid stat for {}'.format(stat, member.name)
			await self.bot.send_message(channel, msg)
			return

		msg = '**{}** for *{}* is *{}!*'.format(stat, member.name, newStat)
		await self.bot.send_message(channel, msg)

	# Catch errors for stat
	@getstat.error
	async def getstat_error(ctx, error):
		msg = 'getstat Error: {}'.format(ctx)
		await self.bot.say(msg)
		

	@commands.command(pass_context=True)
	async def setsstat(self, ctx, stat : str = None, value : str = None):
		"""Sets a server stat (admin only)."""
		
		author  = ctx.message.author
		server  = ctx.message.server
		channel = ctx.message.channel
		
		isAdmin = author.permissions_in(ctx.message.channel).administrator
		# Only allow admins to change server stats
		if not isAdmin:
			await self.bot.send_message(channel, 'You do not have sufficient privileges to access this command.')
			return

		if stat == None or value == None:
			msg = 'Usage: $setsstat Stat Value'
			await self.bot.send_message(channel, msg)
			return

		self.setServerStat(server, stat, value)

		msg = '**{}** set to *{}!*'.format(stat, value)
		await self.bot.send_message(channel, msg)


	@commands.command(pass_context=True)
	async def getsstat(self, ctx, stat : str = None):
		"""Gets a server stat (admin only)."""
		
		author  = ctx.message.author
		server  = ctx.message.server
		channel = ctx.message.channel
		
		isAdmin = author.permissions_in(channel).administrator
		# Only allow admins to change server stats
		if not isAdmin:
			await self.bot.send_message(ctx.message.channel, 'You do not have sufficient privileges to access this command.')
			return

		if stat == None:
			msg = 'Usage: `$getsstat [stat]`'
			await self.bot.send_message(ctx.message.channel, msg)
			return

		value = self.getServerStat(server, stat)

		msg = '**{}** is currently *{}!*'.format(stat, value)
		await self.bot.send_message(channel, msg)
		
	@commands.command(pass_context=True)
	async def flush(self, ctx):
		"""Flush the bot settings to disk (admin only)."""
		isAdmin = ctx.message.author.permissions_in(ctx.message.channel).administrator
		# Only allow admins to change server stats
		if not isAdmin:
			await self.bot.send_message(ctx.message.channel, 'You do not have sufficient privileges to access this command.')
			return
		# Flush settings
		self.flushSettings()
		msg = 'Flushed settings to disk.'
		await self.bot.send_message(ctx.message.channel, msg)
				
				
	# Flush settings to disk
	def flushSettings(self):
		json.dump(self.serverDict, open(self.file, 'w'), indent=2)