import asyncio
import discord
import time
import parsedatetime
from   datetime import datetime
from   operator import itemgetter
from   discord.ext import commands
from   Cogs import Settings
from   Cogs import ReadableTime
from   Cogs import DisplayName
from   Cogs import Nullify


class BotAdmin:

	# Init with the bot reference, and a reference to the settings var
	def __init__(self, bot, settings):
		self.bot = bot
		self.settings = settings

	@commands.command(pass_context=True)
	async def setuserparts(self, ctx, member : discord.Member = None, *, parts : str = None):
		"""Set another user's parts list (bot-admin only)."""

		# Check if we're suppressing @here and @everyone mentions
		if self.settings.getServerStat(ctx.message.server, "SuppressMentions").lower() == "yes":
			suppress = True
		else:
			suppress = False

		isAdmin = ctx.message.author.permissions_in(ctx.message.channel).administrator
		if not isAdmin:
			checkAdmin = self.settings.getServerStat(ctx.message.server, "AdminArray")
			for role in ctx.message.author.roles:
				for aRole in checkAdmin:
					# Get the role that corresponds to the id
					if aRole['ID'] == role.id:
						isAdmin = True
		# Only allow admins to change server stats
		if not isAdmin:
			await self.bot.send_message(ctx.message.channel, 'You do not have sufficient privileges to access this command.')
			return
			
		if member == None:
			msg = 'Usage: `{}setuserparts [member] "[parts text]"`'.format(ctx.prefix)
			await self.bot.send_message(ctx.message.channel, msg)
			return

		if type(member) is str:
			try:
				member = discord.utils.get(message.server.members, name=member)
			except:
				print("That member does not exist")
				return

		channel = ctx.message.channel
		server  = ctx.message.server

		if not parts:
			parts = ""
			
		self.settings.setUserStat(member, server, "Parts", parts)
		msg = '*{}\'s* parts have been set to:\n{}'.format(DisplayName.name(member), parts)
		# Check for suppress
		if suppress:
			msg = Nullify.clean(msg)
		await self.bot.send_message(channel, msg)
		
	@setuserparts.error
	async def setuserparts_error(self, ctx, error):
		# do stuff
		msg = 'setuserparts Error: {}'.format(ctx)
		await self.bot.say(msg)


	@commands.command(pass_context=True)
	async def mute(self, ctx, *, member = None, cooldown = None):
		"""Prevents a member from sending messages in chat (bot-admin only)."""

		# Check if we're suppressing @here and @everyone mentions
		if self.settings.getServerStat(ctx.message.server, "SuppressMentions").lower() == "yes":
			suppress = True
		else:
			suppress = False

		isAdmin = ctx.message.author.permissions_in(ctx.message.channel).administrator
		if not isAdmin:
			checkAdmin = self.settings.getServerStat(ctx.message.server, "AdminArray")
			for role in ctx.message.author.roles:
				for aRole in checkAdmin:
					# Get the role that corresponds to the id
					if aRole['ID'] == role.id:
						isAdmin = True
		# Only allow admins to change server stats
		if not isAdmin:
			await self.bot.send_message(ctx.message.channel, 'You do not have sufficient privileges to access this command.')
			return

		if cooldown == None:
			# Either a cooldown wasn't set - or it's the last section
			if type(member) is str:
				# It' a string - the hope continues
				# Let's search for a name at the beginning - and a time at the end
				parts = member.split()
				for j in range(len(parts)):
					# Reverse search direction
					i = len(parts)-1-j
					memFromName = None
					endTime     = None
					# Name = 0 up to i joined by space
					nameStr = ' '.join(parts[0:i+1])
					# Time = end of name -> end of parts joined by space
					timeStr = ' '.join(parts[i+1:])
					memFromName = DisplayName.memberForName(nameStr, ctx.message.server)
					if memFromName:
						# We got a member - let's check for time
						# Get current time - and end time
						try:
							# Get current time - and end time
							currentTime = int(time.time())
							cal         = parsedatetime.Calendar()
							time_struct, parse_status = cal.parse(timeStr)
							start       = datetime(*time_struct[:6])
							end         = time.mktime(start.timetuple())

							# Get the time from now to end time
							endTime = end-currentTime
						except:
							pass
							
						if not endTime == None:
							# We got a member and a time - break
							break
				
				if memFromName == None:
					# We couldn't find one or the other
					msg = 'Usage: `{}mute [member] [cooldown]`'.format(ctx.prefix)
					await self.bot.send_message(ctx.message.channel, msg)
					return
				
				if endTime == 0:
					coolDown = None
				else:
					cooldown = endTime
				member   = memFromName

			
		if member == None:
			msg = 'Usage: `{}mute [member] [cooldown]`'.format(ctx.prefix)
			await self.bot.send_message(ctx.message.channel, msg)
			return

		if type(member) is str:
			try:
				member = discord.utils.get(message.server.members, name=member)
			except:
				msg = 'Couldn\'t find user *{}*.'.format(member)
				# Check for suppress
				if suppress:
					msg = Nullify.clean(msg)
				await self.bot.send_message(ctx.message.channel, msg)
				return

		# Set cooldown - or clear it
		if type(cooldown) is int or type(cooldown) is float:
			if cooldown < 0:
				msg = 'Cooldown cannot be a negative number!'
				await self.bot.send_message(ctx.message.channel, msg)
				return
			currentTime = int(time.time())
			cooldownFinal = currentTime+cooldown
		else:
			cooldownFinal = None

		pm = 'You have been **Muted** by *{}*.'.format(DisplayName.name(ctx.message.author))

		if cooldown:
			mins = "minutes"
			checkRead = ReadableTime.getReadableTimeBetween(currentTime, cooldownFinal)
			msg = '*{}* has been **Muted** for *{}*.'.format(DisplayName.name(member), checkRead)
			pm  = 'You have been **Muted** by *{}* for *{}*.\n\nYou will not be able to send messages on *{}* until either that time has passed, or you have been **Unmuted**.'.format(DisplayName.name(ctx.message.author), checkRead, ctx.message.server.name)
		else:
			msg = '*{}* has been **Muted** *until further notice*.'.format(DisplayName.name(member))
			pm  = 'You have been **Muted** by *{}* *until further notice*.\n\nYou will not be able to send messages on *{}* until you have been **Unmuted**.'.format(DisplayName.name(ctx.message.author), ctx.message.server.name)
		self.settings.setUserStat(member, ctx.message.server, "Muted", "Yes")
		self.settings.setUserStat(member, ctx.message.server, "Cooldown", cooldownFinal)

		await self.bot.send_message(ctx.message.channel, msg)
		await self.bot.send_message(member, pm)
		
	@mute.error
	async def mute_error(self, ctx, error):
		# do stuff
		msg = 'mute Error: {}'.format(ctx)
		await self.bot.say(msg)
		
		
	@commands.command(pass_context=True)
	async def unmute(self, ctx, *, member = None):
		"""Allows a muted member to send messages in chat (bot-admin only)."""

		# Check if we're suppressing @here and @everyone mentions
		if self.settings.getServerStat(ctx.message.server, "SuppressMentions").lower() == "yes":
			suppress = True
		else:
			suppress = False

		isAdmin = ctx.message.author.permissions_in(ctx.message.channel).administrator
		if not isAdmin:
			checkAdmin = self.settings.getServerStat(ctx.message.server, "AdminArray")
			for role in ctx.message.author.roles:
				for aRole in checkAdmin:
					# Get the role that corresponds to the id
					if aRole['ID'] == role.id:
						isAdmin = True
		# Only allow admins to change server stats
		if not isAdmin:
			await self.bot.send_message(ctx.message.channel, 'You do not have sufficient privileges to access this command.')
			return
			
		if member == None:
			msg = 'Usage: `{}mute [member]`'.format(ctx.prefix)
			await self.bot.send_message(ctx.message.channel, msg)
			return

		if type(member) is str:
			memberName = member
			member = DisplayName.memberForName(memberName, ctx.message.server)
			if not member:
				msg = 'I couldn\'t find *{}*...'.format(memberName)
				# Check for suppress
				if suppress:
					msg = Nullify.clean(msg)
				await self.bot.send_message(ctx.message.channel, msg)
				return

		pm = 'You have been **Unmuted** by *{}*.\n\nYou can send messages on *{}* again.'.format(DisplayName.name(ctx.message.author), ctx.message.server.name)
		msg = '*{}* has been **Unmuted**.'.format(DisplayName.name(member))
		self.settings.setUserStat(member, ctx.message.server, "Muted", "No")
		self.settings.setUserStat(member, ctx.message.server, "Cooldown", None)

		await self.bot.send_message(ctx.message.channel, msg)
		await self.bot.send_message(member, pm)
		
	@unmute.error
	async def unmute_error(self, ctx, error):
		# do stuff
		msg = 'unmute Error: {}'.format(ctx)
		await self.bot.say(msg)


	@commands.command(pass_context=True)
	async def ignore(self, ctx, *, member = None):
		"""Adds a member to the bot's "ignore" list (bot-admin only)."""

		# Check if we're suppressing @here and @everyone mentions
		if self.settings.getServerStat(ctx.message.server, "SuppressMentions").lower() == "yes":
			suppress = True
		else:
			suppress = False

		isAdmin = ctx.message.author.permissions_in(ctx.message.channel).administrator
		if not isAdmin:
			checkAdmin = self.settings.getServerStat(ctx.message.server, "AdminArray")
			for role in ctx.message.author.roles:
				for aRole in checkAdmin:
					# Get the role that corresponds to the id
					if aRole['ID'] == role.id:
						isAdmin = True
		# Only allow admins to change server stats
		if not isAdmin:
			await self.bot.send_message(ctx.message.channel, 'You do not have sufficient privileges to access this command.')
			return
			
		if member == None:
			msg = 'Usage: `{}ignore [member]`'.format(ctx.prefix)
			await self.bot.send_message(ctx.message.channel, msg)
			return

		if type(member) is str:
			memberName = member
			member = DisplayName.memberForName(memberName, ctx.message.server)
			if not member:
				msg = 'I couldn\'t find *{}*...'.format(memberName)
				# Check for suppress
				if suppress:
					msg = Nullify.clean(msg)
				await self.bot.send_message(ctx.message.channel, msg)
				return

		ignoreList = self.settings.getServerStat(ctx.message.server, "IgnoredUsers")

		found = False
		for user in ignoreList:
			if member.id == user["ID"]:
				# Found our user - already ignored
				found = True
				msg = '*{}* is already being ignored.'.format(DisplayName.name(member))
		if not found:
			# Let's ignore someone
			ignoreList.append({ "Name" : member.name, "ID" : member.id })
			msg = '*{}* is now being ignored.'.format(DisplayName.name(member))

		await self.bot.send_message(ctx.message.channel, msg)
		
	@ignore.error
	async def ignore_error(self, ctx, error):
		# do stuff
		msg = 'ignore Error: {}'.format(ctx)
		await self.bot.say(msg)


	@commands.command(pass_context=True)
	async def listen(self, ctx, *, member : discord.Member = None):
		"""Removes a member from the bot's "ignore" list (bot-admin only)."""

		# Check if we're suppressing @here and @everyone mentions
		if self.settings.getServerStat(ctx.message.server, "SuppressMentions").lower() == "yes":
			suppress = True
		else:
			suppress = False

		isAdmin = ctx.message.author.permissions_in(ctx.message.channel).administrator
		if not isAdmin:
			checkAdmin = self.settings.getServerStat(ctx.message.server, "AdminArray")
			for role in ctx.message.author.roles:
				for aRole in checkAdmin:
					# Get the role that corresponds to the id
					if aRole['ID'] == role.id:
						isAdmin = True
		# Only allow admins to change server stats
		if not isAdmin:
			await self.bot.send_message(ctx.message.channel, 'You do not have sufficient privileges to access this command.')
			return
			
		if member == None:
			msg = 'Usage: `{}listen [member]`'.format(ctx.prefix)
			await self.bot.send_message(ctx.message.channel, msg)
			return

		if type(member) is str:
			memberName = member
			member = DisplayName.memberForName(memberName, ctx.message.server)
			if not member:
				msg = 'I couldn\'t find *{}*...'.format(memberName)
				# Check for suppress
				if suppress:
					msg = Nullify.clean(msg)
				await self.bot.send_message(ctx.message.channel, msg)
				return

		ignoreList = self.settings.getServerStat(ctx.message.server, "IgnoredUsers")

		found = False
		for user in ignoreList:
			if member.id == user["ID"]:
				# Found our user - already ignored
				found = True
				msg = '*{}* no longer being ignored.'.format(DisplayName.name(member))
				ignoreList.remove(user)

		if not found:
			# Whatchu talkin bout Willis?
			msg = '*{}* wasn\'t being ignored...'.format(DisplayName.name(member))

		await self.bot.send_message(ctx.message.channel, msg)
		
	@listen.error
	async def listen_error(self, ctx, error):
		# do stuff
		msg = 'listen Error: {}'.format(ctx)
		await self.bot.say(msg)


	@commands.command(pass_context=True)
	async def ignored(self, ctx):
		"""Lists the users currently being ignored."""
		ignoreArray = self.settings.getServerStat(ctx.message.server, "IgnoredUsers")
		
		# rows_by_lfname = sorted(rows, key=itemgetter('lname','fname'))
		
		promoSorted = sorted(ignoreArray, key=itemgetter('Name'))
		
		if not len(promoSorted):
			msg = 'I\'m not currently ignoring anyone.'
			await self.bot.send_message(ctx.message.channel, msg)
			return

		roleText = "Currently Ignored Users:\n"

		for arole in promoSorted:
			for role in ctx.message.server.members:
				if role.id == arole["ID"]:
					# Found the role ID
					roleText = '{}*{}*\n'.format(roleText, DisplayName.name(role))

		await self.bot.send_message(ctx.message.channel, roleText)

	@commands.command(pass_context=True)
	async def kick(self, ctx, *, member : str = None):
		"""Kicks the selected member (bot-admin only)."""

		# Check if we're suppressing @here and @everyone mentions
		if self.settings.getServerStat(ctx.message.server, "SuppressMentions").lower() == "yes":
			suppress = True
		else:
			suppress = False

		isAdmin = ctx.message.author.permissions_in(ctx.message.channel).administrator
		if not isAdmin:
			checkAdmin = self.settings.getServerStat(ctx.message.server, "AdminArray")
			for role in ctx.message.author.roles:
				for aRole in checkAdmin:
					# Get the role that corresponds to the id
					if aRole['ID'] == role.id:
						isAdmin = True
		# Only allow admins to kick
		if not isAdmin:
			await self.bot.send_message(ctx.message.channel, 'You do not have sufficient privileges to access this command.')
			return
		
		if not member:
			await self.bot.send_message(ctx.message.channel, 'Usage: `{}kick [member]`'.format(ctx.prefix))
			return
		
		# Resolve member name -> member
		newMem = DisplayName.memberForName(member, ctx.message.server)
		if not newMem:
			msg = 'I couldn\'t find *{}*.'.format(member)
			# Check for suppress
			if suppress:
				msg = Nullify.clean(msg)
			await self.bot.send_message(ctx.message.channel, msg)
			return
		
		# newMem = valid member
		member = newMem
		
		if member.id == ctx.message.author.id:
			await self.bot.send_message(ctx.message.channel, 'Stop kicking yourself.  Stop kicking yourself.')
			return
		
		# Check if the targeted user is admin
		isTAdmin = member.permissions_in(ctx.message.channel).administrator
		if not isTAdmin:
			checkAdmin = self.settings.getServerStat(ctx.message.server, "AdminArray")
			for role in member.roles:
				for aRole in checkAdmin:
					# Get the role that corresponds to the id
					if aRole['ID'] == role.id:
						isTAdmin = True
		
		# Can't kick other admins
		if isTAdmin:
			await self.bot.send_message(ctx.message.channel, 'You can\'t kick other admins with this command.')
			return
		
		# We can kick
		await self.bot.send_message(ctx.message.channel, 'If this were live - you would have **kicked** *{}*'.format(DisplayName.name(member)))
		
		
	@commands.command(pass_context=True)
	async def ban(self, ctx, *, member : str = None):
		"""Bans the selected member (bot-admin only)."""

		# Check if we're suppressing @here and @everyone mentions
		if self.settings.getServerStat(ctx.message.server, "SuppressMentions").lower() == "yes":
			suppress = True
		else:
			suppress = False

		isAdmin = ctx.message.author.permissions_in(ctx.message.channel).administrator
		if not isAdmin:
			checkAdmin = self.settings.getServerStat(ctx.message.server, "AdminArray")
			for role in ctx.message.author.roles:
				for aRole in checkAdmin:
					# Get the role that corresponds to the id
					if aRole['ID'] == role.id:
						isAdmin = True
		# Only allow admins to ban
		if not isAdmin:
			await self.bot.send_message(ctx.message.channel, 'You do not have sufficient privileges to access this command.')
			return
		
		if not member:
			await self.bot.send_message(ctx.message.channel, 'Usage: `{}ban [member]`'.format(ctx.prefix))
			return
		
		# Resolve member name -> member
		newMem = DisplayName.memberForName(member, ctx.message.server)
		if not newMem:
			msg = 'I couldn\'t find *{}*.'.format(member)
			# Check for suppress
			if suppress:
				msg = Nullify.clean(msg)
			await self.bot.send_message(ctx.message.channel, msg)
			return
		
		# newMem = valid member
		member = newMem
		
		if member.id == ctx.message.author.id:
			await self.bot.send_message(ctx.message.channel, 'Ahh - the ol\' self-ban.  Good try.')
			return
		
		# Check if the targeted user is admin
		isTAdmin = member.permissions_in(ctx.message.channel).administrator
		if not isTAdmin:
			checkAdmin = self.settings.getServerStat(ctx.message.server, "AdminArray")
			for role in member.roles:
				for aRole in checkAdmin:
					# Get the role that corresponds to the id
					if aRole['ID'] == role.id:
						isTAdmin = True
		
		# Can't ban other admins
		if isTAdmin:
			await self.bot.send_message(ctx.message.channel, 'You can\'t ban other admins with this command.')
			return
		
		# We can ban
		await self.bot.send_message(ctx.message.channel, 'If this were live - you would have **banned** *{}*'.format(DisplayName.name(member)))
		