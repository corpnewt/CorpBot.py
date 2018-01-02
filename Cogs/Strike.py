import asyncio
import discord
import time
import parsedatetime
from   datetime import datetime
from   operator import itemgetter
from   discord.ext import commands
from   Cogs import ReadableTime
from   Cogs import DisplayName
from   Cogs import Nullify

def setup(bot):
	# Add the bot and deps
	settings = bot.get_cog("Settings")
	mute     = bot.get_cog("Mute")
	bot.add_cog(Strike(bot, settings, mute))

# This is the Strike module. It keeps track of warnings and kicks/bans accordingly

# Strikes = [ time until drops off ]
# StrikeOut = 3 (3 strikes and you're out)
# StrikeLevel (a list similar to xproles)
# Standard strike roles:
# 0 = Not been punished already
# 1 = Muted for x amount of time
# 2 = Already been kicked (id in kick list)
# 3 = Already been banned (auto-mute)

class Strike:

	# Init with the bot reference, and a reference to the settings var
	def __init__(self, bot, settings, mute):
		self.bot = bot
		self.settings = settings
		self.mute = mute
		self.loop_list = []

	def suppressed(self, guild, msg):
		# Check if we're suppressing @here and @everyone mentions
		if self.settings.getServerStat(guild, "SuppressMentions"):
			return Nullify.clean(msg)
		else:
			return msg

	async def onjoin(self, member, server):
		# Check id against the kick and ban list and react accordingly
		kickList = self.settings.getServerStat(server, "KickList")
		if str(member.id) in kickList:
			# The user has been kicked before - set their strikeLevel to 2
			self.settings.setUserStat(member, server, "StrikeLevel", 2)

		banList = self.settings.getServerStat(server, "BanList")
		if str(member.id) in banList:
			# The user has been kicked before - set their strikeLevel to 3
			# Also mute them
			self.settings.setUserStat(member, server, "StrikeLevel", 3)
			self.settings.setUserStat(member, server, "Muted", True)
			self.settings.setUserStat(member, server, "Cooldown", None)
			await self.mute.mute(member, server)

	# Proof of concept stuff for reloading cog/extension
	def _is_submodule(self, parent, child):
		return parent == child or child.startswith(parent + ".")

	@asyncio.coroutine
	async def on_unloaded_extension(self, ext):
		# Called to shut things down
		if not self._is_submodule(ext.__name__, self.__module__):
			return
		for task in self.loop_list:
			task.cancel()

	@asyncio.coroutine
	async def on_loaded_extension(self, ext):
		# See if we were loaded
		if not self._is_submodule(ext.__name__, self.__module__):
			return
		# Check all strikes - and start timers
		for server in self.bot.guilds:
			for member in server.members:
				strikes = self.settings.getUserStat(member, server, "Strikes")
				if strikes == None:
					continue
				if len(strikes):
					# We have a list
					for strike in strikes:
						# Make sure it's a strike that *can* roll off
						if not strike['Time'] == -1:
							self.loop_list.append(self.bot.loop.create_task(self.checkStrike(member, strike)))

	async def checkStrike(self, member, strike):
		# Start our countdown
		countDown = int(strike['Time'])-int(time.time())
		if countDown > 0:
			# We have a positive countdown - let's wait
			await asyncio.sleep(countDown)
		
		strikes = self.settings.getUserStat(member, member.guild, "Strikes")
		# Verify strike is still valid
		if not strike in strikes:
			return
		strikes.remove(strike)
		self.settings.setUserStat(member, member.guild, "Strikes", strikes)

	
	@commands.command(pass_context=True)
	async def strike(self, ctx, member : discord.Member = None, days = None, *, message : str = None):
		"""Give a user a strike (bot-admin only)."""
		isAdmin = ctx.message.author.permissions_in(ctx.message.channel).administrator
		if not isAdmin:
			checkAdmin = self.settings.getServerStat(ctx.message.guild, "AdminArray")
			for role in ctx.message.author.roles:
				for aRole in checkAdmin:
					# Get the role that corresponds to the id
					if str(aRole['ID']) == str(role.id):
						isAdmin = True
		# Only allow admins to change server stats
		if not isAdmin:
			await ctx.channel.send('You do not have sufficient privileges to access this command.')
			return
			
		if member == None:
			msg = 'Usage: `{}strike [member] [strike timeout (in days) - 0 = forever] [message (optional)]`'.format(ctx.prefix)
			await ctx.channel.send(msg)
			return
		
		# Check if we're striking ourselves
		if member.id == ctx.message.author.id:
			# We're giving ourselves a strike?
			await ctx.channel.send('You can\'t give yourself a strike, silly.')
			return
		
		# Check if the bot is getting the strike
		if member.id == self.bot.user.id:
			await ctx.channel.send('I can\'t do that, *{}*.'.format(DisplayName.name(ctx.message.author)))
			return
		
		# Check if we're striking another admin/bot-admin
		isAdmin = member.permissions_in(ctx.message.channel).administrator
		if not isAdmin:
			checkAdmin = self.settings.getServerStat(ctx.message.guild, "AdminArray")
			for role in member.roles:
				for aRole in checkAdmin:
					# Get the role that corresponds to the id
					if str(aRole['ID']) == str(role.id):
						isAdmin = True
		if isAdmin:
			await ctx.channel.send('You can\'t give other admins/bot-admins strikes, bub.')
			return

		# Check if days is an int - otherwise assume it's part of the message
		try:
			days = int(days)
		except Exception:
			if not days == None:
				if message == None:
					message = days
				else:
					message = days + ' ' + message
			days = 0

		# If it's not at least a day, it's forever
		if days < 1:
			days = -1

		currentTime = int(time.time())

		# Build our Strike
		strike = {}
		if days == -1:
			strike['Time'] = -1
		else:
			strike['Time'] = currentTime+(86400*days)
			self.loop_list.append(self.bot.loop.create_task(self.checkStrike(member, strike)))
		strike['Message'] = message
		strike['GivenBy'] = ctx.message.author.id
		strikes = self.settings.getUserStat(member, ctx.message.guild, "Strikes")
		strikeout = int(self.settings.getServerStat(ctx.message.guild, "StrikeOut"))
		strikeLevel = int(self.settings.getUserStat(member, ctx.message.guild, "StrikeLevel"))
		strikes.append(strike)
		self.settings.setUserStat(member, ctx.message.guild, "Strikes", strikes)
		strikeNum = len(strikes)
		# Set up consequences
		if strikeLevel == 0:
			consequence = '**muted for a day**.'
		elif strikeLevel == 1:
			consequence = '**kicked**.'
		else:
			consequence = '**banned**.'

		# Check if we've struck out
		if strikeNum < strikeout:
			# We haven't struck out yet
			msg = '*{}* has just received *strike {}*.  *{}* more and they will be {}'.format(DisplayName.name(member), strikeNum, strikeout-strikeNum, consequence)
		else:
			# We struck out - let's evaluate
			if strikeLevel == 0:
				cooldownFinal = currentTime+86400
				checkRead = ReadableTime.getReadableTimeBetween(currentTime, cooldownFinal)
				if message:
					mutemessage = 'You have been muted in *{}*.\nThe Reason:\n{}'.format(self.suppressed(ctx.guild, ctx.guild.name), message)
				else:
					mutemessage = 'You have been muted in *{}*.'.format(self.suppressed(ctx.guild, ctx.guild.name))
				# Check if already muted
				alreadyMuted = self.settings.getUserStat(member, ctx.message.guild, "Muted")
				if alreadyMuted:
					# Find out for how long
					muteTime = self.settings.getUserStat(member, ctx.message.guild, "Cooldown")
					if not muteTime == None:
						if muteTime < cooldownFinal:
							self.settings.setUserStat(member, ctx.message.guild, "Cooldown", cooldownFinal)
							timeRemains = ReadableTime.getReadableTimeBetween(currentTime, cooldownFinal)
							if message:
								mutemessage = 'Your muted time in *{}* has been extended to *{}*.\nThe Reason:\n{}'.format(self.suppressed(ctx.guild, ctx.guild.name), timeRemains, message)
							else:
								mutemessage = 'You muted time in *{}* has been extended to *{}*.'.format(self.suppressed(ctx.guild, ctx.guild.name), timeRemains)
				else:
					self.settings.setUserStat(member, ctx.message.guild, "Muted", True)
					self.settings.setUserStat(member, ctx.message.guild, "Cooldown", cooldownFinal)
					await self.mute.mute(member, ctx.message.guild, cooldownFinal)

				await member.send(mutemessage)
			elif strikeLevel == 1:
				kickList = self.settings.getServerStat(ctx.message.guild, "KickList")
				if not str(member.id) in kickList:
					kickList.append(str(member.id))
					self.settings.setServerStat(ctx.message.guild, "KickList", kickList)
				if message:
					kickmessage = 'You have been kicked from *{}*.\nThe Reason:\n{}'.format(self.suppressed(ctx.guild, ctx.guild.name), message)
				else:
					kickmessage = 'You have been kicked from *{}*.'.format(self.suppressed(ctx.guild, ctx.guild.name))
				await member.send(kickmessage)
				await ctx.guild.kick(member)
			else:
				banList = self.settings.getServerStat(ctx.message.guild, "BanList")
				if not str(member.id) in banList:
					banList.append(str(member.id))
					self.settings.setServerStat(ctx.message.guild, "BanList", banList)
				if message:
					banmessage = 'You have been banned from *{}*.\nThe Reason:\n{}'.format(self.suppressed(ctx.guild, ctx.guild.name), message)
				else:
					banmessage = 'You have been banned from *{}*.'.format(self.suppressed(ctx.guild, ctx.guild.name))
				await member.send(banmessage)
				await ctx.guild.ban(member)
			self.settings.incrementStat(member, ctx.message.guild, "StrikeLevel", 1)
			self.settings.setUserStat(member, ctx.message.guild, "Strikes", [])
			
			msg = '*{}* has just received *strike {}*.  They have been {}'.format(DisplayName.name(member), strikeNum, consequence) 
		await ctx.channel.send(msg)
	@strike.error
	async def strike_error(self, ctx, error):
		# do stuff
		msg = 'strike Error: {}'.format(error)
		await ctx.channel.send(msg)


	@commands.command(pass_context=True)
	async def strikes(self, ctx, *, member = None):
		"""Check a your own, or another user's total strikes (bot-admin needed to check other users)."""
		isAdmin = ctx.message.author.permissions_in(ctx.message.channel).administrator
		if not isAdmin:
			checkAdmin = self.settings.getServerStat(ctx.message.guild, "AdminArray")
			for role in ctx.message.author.roles:
				for aRole in checkAdmin:
					# Get the role that corresponds to the id
					if str(aRole['ID']) == str(role.id):
						isAdmin = True

		if member == None:
			member = ctx.message.author

		# Check if we're suppressing @here and @everyone mentions
		if self.settings.getServerStat(ctx.message.guild, "SuppressMentions"):
			suppress = True
		else:
			suppress = False

		if type(member) is str:
			memberName = member
			member = DisplayName.memberForName(memberName, ctx.message.guild)
			if not member:
				msg = 'I couldn\'t find *{}*...'.format(memberName)
				# Check for suppress
				if suppress:
					msg = Nullify.clean(msg)
				await ctx.channel.send(msg)
				return
			
		# Only allow admins to check others' strikes
		if not isAdmin:
			if member:
				if not member.id == ctx.message.author.id:
					await ctx.channel.send('You are not a bot-admin.  You can only see your own strikes.')
					member = ctx.message.author

		# Create blank embed
		stat_embed = discord.Embed(color=member.color)

		strikes = self.settings.getUserStat(member, ctx.message.guild, "Strikes")
		strikeout = int(self.settings.getServerStat(ctx.message.guild, "StrikeOut"))
		strikeLevel = int(self.settings.getUserStat(member, ctx.message.guild, "StrikeLevel"))

		# Add strikes, and strike level
		stat_embed.add_field(name="Strikes", value=len(strikes), inline=True)
		stat_embed.add_field(name="Strike Level", value=strikeLevel, inline=True)

		# Get member's avatar url
		avURL = member.avatar_url
		if not len(avURL):
			avURL = member.default_avatar_url

		if member.nick:
			# We have a nickname
			msg = "__***{},*** **who currently goes by** ***{}:***__\n\n".format(member.name, member.nick)
			
			# Add to embed
			stat_embed.set_author(name='{}, who currently goes by {}'.format(member.name, member.nick), icon_url=avURL)
		else:
			msg = "__***{}:***__\n\n".format(member.name)
			# Add to embed
			stat_embed.set_author(name='{}'.format(member.name), icon_url=avURL)
		
		# Get messages - and cooldowns
		currentTime = int(time.time())

		if not len(strikes):
			# no strikes
			messages = "None."
			cooldowns = "None."
			givenBy = "None."
		else:
			messages    = ''
			cooldowns   = ''
			givenBy = ''

		for i in range(0, len(strikes)):
			if strikes[i]['Message']:
				messages += '{}. {}\n'.format(i+1, strikes[i]['Message'])
			else:
				messages += '{}. No message\n'.format(i+1)
			timeLeft = strikes[i]['Time']
			if timeLeft == -1:
				cooldowns += '{}. Never rolls off\n'.format(i+1)
			else:
				timeRemains = ReadableTime.getReadableTimeBetween(currentTime, timeLeft)
				cooldowns += '{}. {}\n'.format(i+1, timeRemains)
			given = strikes[i]['GivenBy']
			givenBy += '{}. {}\n'.format(i+1, DisplayName.name(DisplayName.memberForID(given, ctx.message.guild)))
		
		# Add messages and cooldowns
		stat_embed.add_field(name="Messages", value=messages, inline=True)
		stat_embed.add_field(name="Time Left", value=cooldowns, inline=True)
		stat_embed.add_field(name="Given By", value=givenBy, inline=True)

		# Strikes remaining
		stat_embed.add_field(name="Strikes Remaining", value=strikeout-len(strikes), inline=True)

		await ctx.channel.send(embed=stat_embed)


	@commands.command(pass_context=True)
	async def removestrike(self, ctx, *, member = None):
		"""Removes a strike given to a member (bot-admin only)."""
		isAdmin = ctx.message.author.permissions_in(ctx.message.channel).administrator
		if not isAdmin:
			checkAdmin = self.settings.getServerStat(ctx.message.guild, "AdminArray")
			for role in ctx.message.author.roles:
				for aRole in checkAdmin:
					# Get the role that corresponds to the id
					if str(aRole['ID']) == str(role.id):
						isAdmin = True
		# Only allow admins to change server stats
		if not isAdmin:
			await ctx.channel.send('You do not have sufficient privileges to access this command.')
			return
			
		if member == None:
			msg = 'Usage: `{}removestrike [member]`'.format(ctx.prefix)
			await ctx.channel.send(msg)
			return

		# Check if we're suppressing @here and @everyone mentions
		if self.settings.getServerStat(ctx.message.guild, "SuppressMentions"):
			suppress = True
		else:
			suppress = False

		if type(member) is str:
			memberName = member
			member = DisplayName.memberForName(memberName, ctx.message.guild)
			if not member:
				msg = 'I couldn\'t find *{}*...'.format(memberName)
				# Check for suppress
				if suppress:
					msg = Nullify.clean(msg)
				await ctx.channel.send(msg)
				return
		
		# We have what we need - get the list
		strikes = self.settings.getUserStat(member, ctx.message.guild, "Strikes")
		# Return if no strikes to take
		if not len(strikes):
			await ctx.channel.send('*{}* has no strikes to remove.'.format(DisplayName.name(member)))
			return
		# We have some - naughty naughty!
		strikes = sorted(strikes, key=lambda x:int(x['Time']))
		for strike in strikes:
			# Check if we've got one that's not -1
			if not strike['Time'] == -1:
				# First item that isn't forever - kill it
				strikes.remove(strike)
				self.settings.setUserStat(member, ctx.message.guild, "Strikes", strikes)
				await ctx.channel.send('*{}* has one less strike.  They are down to *{}*.'.format(DisplayName.name(member), len(strikes)))
				return
		# If we're here - we just remove one
		del strikes[0]
		self.settings.setUserStat(member, ctx.message.guild, "Strikes", strikes)
		await ctx.channel.send('*{}* has one less strike.  They are down to *{}*.'.format(DisplayName.name(member), len(strikes)))
		return

	@commands.command(pass_context=True)
	async def setstrikelevel(self, ctx, *, member = None, strikelevel : int = None):
		"""Sets the strike level of the passed user (bot-admin only)."""

		isAdmin = ctx.message.author.permissions_in(ctx.message.channel).administrator
		if not isAdmin:
			checkAdmin = self.settings.getServerStat(ctx.message.guild, "AdminArray")
			for role in ctx.message.author.roles:
				for aRole in checkAdmin:
					# Get the role that corresponds to the id
					if str(aRole['ID']) == str(role.id):
						isAdmin = True
		# Only allow admins to change server stats
		if not isAdmin:
			await ctx.channel.send('You do not have sufficient privileges to access this command.')
			return

		author  = ctx.message.author
		server  = ctx.message.guild
		channel = ctx.message.channel

		# Check if we're suppressing @here and @everyone mentions
		if self.settings.getServerStat(server, "SuppressMentions"):
			suppress = True
		else:
			suppress = False

		usage = 'Usage: `{}setstrikelevel [member] [strikelevel]`'.format(ctx.prefix)

		if member == None:
			await ctx.channel.send(usage)
			return

		# Check for formatting issues
		if strikelevel == None:
			# Either strike level wasn't set - or it's the last section
			if type(member) is str:
				# It' a string - the hope continues
				nameCheck = DisplayName.checkNameForInt(member, server)
				if not nameCheck:
					await ctx.channel.send(usage)
					return
				if not nameCheck["Member"]:
					msg = 'I couldn\'t find *{}* on the server.'.format(member)
					# Check for suppress
					if suppress:
						msg = Nullify.clean(msg)
					await ctx.channel.send(msg)
					return
				member      = nameCheck["Member"]
				strikelevel = nameCheck["Int"]

		if strikelevel == None:
			# Still no strike level
			await ctx.channel.send(usage)
			return

		self.settings.setUserStat(member, ctx.message.guild, "StrikeLevel", strikelevel)
		msg = '*{}\'s* strike level has been set to *{}!*'.format(DisplayName.name(member), strikelevel)
		await ctx.channel.send(msg)



	@commands.command(pass_context=True)
	async def addkick(self, ctx, *, member = None):
		"""Adds the passed user to the kick list (bot-admin only)."""
		isAdmin = ctx.message.author.permissions_in(ctx.message.channel).administrator
		if not isAdmin:
			checkAdmin = self.settings.getServerStat(ctx.message.guild, "AdminArray")
			for role in ctx.message.author.roles:
				for aRole in checkAdmin:
					# Get the role that corresponds to the id
					if str(aRole['ID']) == str(role.id):
						isAdmin = True
		# Only allow admins to change server stats
		if not isAdmin:
			await ctx.channel.send('You do not have sufficient privileges to access this command.')
			return
			
		if member == None:
			msg = 'Usage: `{}addkick [member]`'.format(ctx.prefix)
			await ctx.channel.send(msg)
			return

		# Check if we're suppressing @here and @everyone mentions
		if self.settings.getServerStat(ctx.message.guild, "SuppressMentions"):
			suppress = True
		else:
			suppress = False

		if type(member) is str:
			memberName = member
			member = DisplayName.memberForName(memberName, ctx.message.guild)
			if not member:
				msg = 'I couldn\'t find *{}*...'.format(memberName)
				# Check for suppress
				if suppress:
					msg = Nullify.clean(msg)
				await ctx.channel.send(msg)
				return
		msg = ''
		
		kickList = self.settings.getServerStat(ctx.message.guild, "KickList")
		if not str(member.id) in kickList:
			kickList.append(str(member.id))
			self.settings.setServerStat(ctx.message.guild, "KickList", kickList)
			msg = '*{}* was added to the kick list.'.format(DisplayName.name(member))
		else:
			msg = '*{}* is already in the kick list.'.format(DisplayName.name(member))
		
		await ctx.channel.send(msg)


	@commands.command(pass_context=True)
	async def removekick(self, ctx, *, member = None):
		"""Removes the passed user from the kick list (bot-admin only)."""
		isAdmin = ctx.message.author.permissions_in(ctx.message.channel).administrator
		if not isAdmin:
			checkAdmin = self.settings.getServerStat(ctx.message.guild, "AdminArray")
			for role in ctx.message.author.roles:
				for aRole in checkAdmin:
					# Get the role that corresponds to the id
					if str(aRole['ID']) == str(role.id):
						isAdmin = True
		# Only allow admins to change server stats
		if not isAdmin:
			await ctx.channel.send('You do not have sufficient privileges to access this command.')
			return
			
		if member == None:
			msg = 'Usage: `{}removekick [member]`'.format(ctx.prefix)
			await ctx.channel.send(msg)
			return

		# Check if we're suppressing @here and @everyone mentions
		if self.settings.getServerStat(ctx.message.guild, "SuppressMentions"):
			suppress = True
		else:
			suppress = False

		if type(member) is str:
			memberName = member
			member = DisplayName.memberForName(memberName, ctx.message.guild)
			if not member:
				msg = 'I couldn\'t find *{}*...'.format(memberName)
				# Check for suppress
				if suppress:
					msg = Nullify.clean(msg)
				await ctx.channel.send(msg)
				return
		msg = ''
		
		kickList = self.settings.getServerStat(ctx.message.guild, "KickList")
		if str(member.id) in kickList:
			kickList.remove(str(member.id))
			self.settings.setServerStat(ctx.message.guild, "KickList", kickList)
			msg = '*{}* was removed from the kick list.'.format(DisplayName.name(member))
		else:
			msg = '*{}* was not found in the kick list.'.format(DisplayName.name(member))
		
		await ctx.channel.send(msg)

	

	@commands.command(pass_context=True)
	async def addban(self, ctx, *, member = None):
		"""Adds the passed user to the ban list (bot-admin only)."""
		isAdmin = ctx.message.author.permissions_in(ctx.message.channel).administrator
		if not isAdmin:
			checkAdmin = self.settings.getServerStat(ctx.message.guild, "AdminArray")
			for role in ctx.message.author.roles:
				for aRole in checkAdmin:
					# Get the role that corresponds to the id
					if str(aRole['ID']) == str(role.id):
						isAdmin = True
		# Only allow admins to change server stats
		if not isAdmin:
			await ctx.channel.send('You do not have sufficient privileges to access this command.')
			return
			
		if member == None:
			msg = 'Usage: `{}addban [member]`'.format(ctx.prefix)
			await ctx.channel.send(msg)
			return

		# Check if we're suppressing @here and @everyone mentions
		if self.settings.getServerStat(ctx.message.guild, "SuppressMentions"):
			suppress = True
		else:
			suppress = False

		if type(member) is str:
			memberName = member
			member = DisplayName.memberForName(memberName, ctx.message.guild)
			if not member:
				msg = 'I couldn\'t find *{}*...'.format(memberName)
				# Check for suppress
				if suppress:
					msg = Nullify.clean(msg)
				await ctx.channel.send(msg)
				return
		msg = ''
		
		banList = self.settings.getServerStat(ctx.message.guild, "BanList")
		if not str(member.id) in banList:
			banList.append(str(member.id))
			self.settings.setServerStat(ctx.message.guild, "BanList", banList)
			msg = '*{}* was added to the ban list.'.format(DisplayName.name(member))
		else:
			msg = '*{}* is already in the ban list.'.format(DisplayName.name(member))
		
		await ctx.channel.send(msg)


	@commands.command(pass_context=True)
	async def removeban(self, ctx, *, member = None):
		"""Removes the passed user from the ban list (bot-admin only)."""
		isAdmin = ctx.message.author.permissions_in(ctx.message.channel).administrator
		if not isAdmin:
			checkAdmin = self.settings.getServerStat(ctx.message.guild, "AdminArray")
			for role in ctx.message.author.roles:
				for aRole in checkAdmin:
					# Get the role that corresponds to the id
					if str(aRole['ID']) == str(role.id):
						isAdmin = True
		# Only allow admins to change server stats
		if not isAdmin:
			await ctx.channel.send('You do not have sufficient privileges to access this command.')
			return
			
		if member == None:
			msg = 'Usage: `{}removeban [member]`'.format(ctx.prefix)
			await ctx.channel.send(msg)
			return

		# Check if we're suppressing @here and @everyone mentions
		if self.settings.getServerStat(ctx.message.guild, "SuppressMentions"):
			suppress = True
		else:
			suppress = False

		if type(member) is str:
			memberName = member
			member = DisplayName.memberForName(memberName, ctx.message.guild)
			if not member:
				msg = 'I couldn\'t find *{}*...'.format(memberName)
				# Check for suppress
				if suppress:
					msg = Nullify.clean(msg)
				await ctx.channel.send(msg)
				return
		msg = ''
		
		banList = self.settings.getServerStat(ctx.message.guild, "BanList")
		if str(member.id) in banList:
			banList.remove(str(member.id))
			self.settings.setServerStat(ctx.message.guild, "BanList", banList)
			msg = '*{}* was removed from the ban list.'.format(DisplayName.name(member))
		else:
			msg = '*{}* was not found in the ban list.'.format(DisplayName.name(member))
		
		await ctx.channel.send(msg)

	@commands.command(pass_context=True)
	async def iskicked(self, ctx, *, member = None):
		"""Lists whether the user is in the kick list."""
		if member == None:
			member = ctx.message.author

		# Check if we're suppressing @here and @everyone mentions
		if self.settings.getServerStat(ctx.message.guild, "SuppressMentions"):
			suppress = True
		else:
			suppress = False

		if type(member) is str:
			memberName = member
			member = DisplayName.memberForName(memberName, ctx.message.guild)
			if not member:
				msg = 'I couldn\'t find *{}*...'.format(memberName)
				# Check for suppress
				if suppress:
					msg = Nullify.clean(msg)
				await ctx.channel.send(msg)
				return

		kickList = self.settings.getServerStat(ctx.message.guild, "KickList")
		if str(member.id) in kickList:
			msg = '*{}* is in the kick list.'.format(DisplayName.name(member))
		else:
			msg = '*{}* is **not** in the kick list.'.format(DisplayName.name(member))
		await ctx.channel.send(msg)

	@commands.command(pass_context=True)
	async def isbanned(self, ctx, *, member = None):
		"""Lists whether the user is in the ban list."""
		if member == None:
			member = ctx.message.author

		# Check if we're suppressing @here and @everyone mentions
		if self.settings.getServerStat(ctx.message.guild, "SuppressMentions"):
			suppress = True
		else:
			suppress = False

		if type(member) is str:
			memberName = member
			member = DisplayName.memberForName(memberName, ctx.message.guild)
			if not member:
				msg = 'I couldn\'t find *{}*...'.format(memberName)
				# Check for suppress
				if suppress:
					msg = Nullify.clean(msg)
				await ctx.channel.send(msg)
				return

		banList = self.settings.getServerStat(ctx.message.guild, "BanList")
		if str(member.id) in banList:
			msg = '*{}* is in the ban list.'.format(DisplayName.name(member))
		else:
			msg = '*{}* is **not** in the ban list.'.format(DisplayName.name(member))
		await ctx.channel.send(msg)

	@commands.command(pass_context=True)
	async def strikelimit(self, ctx):
		"""Lists the number of strikes before advancing to the next consequence."""
		strikeout = int(self.settings.getServerStat(ctx.message.guild, "StrikeOut"))
		msg = '*{}* strikes are required to strike out.'.format(strikeout)
		await ctx.channel.send(msg)

	@commands.command(pass_context=True)
	async def setstrikelimit(self, ctx, limit = None):
		"""Sets the number of strikes before advancing to the next consequence (bot-admin only)."""
		isAdmin = ctx.message.author.permissions_in(ctx.message.channel).administrator
		if not isAdmin:
			checkAdmin = self.settings.getServerStat(ctx.message.guild, "AdminArray")
			for role in ctx.message.author.roles:
				for aRole in checkAdmin:
					# Get the role that corresponds to the id
					if str(aRole['ID']) == str(role.id):
						isAdmin = True
		# Only allow admins to change server stats
		if not isAdmin:
			await ctx.channel.send('You do not have sufficient privileges to access this command.')
			return

		if not limit:
			await ctx.channel.send('Strike limit must be *at least* one.')
			return

		try:
			limit = int(limit)
		except Exception:
			await ctx.channel.send('Strike limit must be an integer.')
			return
		
		self.settings.setServerStat(ctx.message.guild, "StrikeOut", limit)
		msg = '*{}* strikes are now required to strike out.'.format(limit)
		await ctx.channel.send(msg)

		
	@setstrikelimit.error
	async def setstrikelimit_error(self, ctx, error):
		# do stuff
		msg = 'setstrikelimit Error: {}'.format(ctx)
		await error.channel.send(msg)
