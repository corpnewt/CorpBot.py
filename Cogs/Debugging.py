import asyncio
import discord
import os
import textwrap
from   datetime import datetime
from   operator import itemgetter
from   discord.ext import commands
from   Cogs import DisplayName
from   Cogs import Nullify
from   Cogs import Message

def setup(bot):
	# Add the bot and deps
	settings = bot.get_cog("Settings")
	bot.add_cog(Debugging(bot, settings))

# This is the Debugging module. It keeps track of how long the bot's been up

class Debugging:

	# Init with the bot reference, and a reference to the settings var
	def __init__(self, bot, settings, debug = False):
		self.bot = bot
		self.wrap = False
		self.settings = settings
		self.debug = debug
		self.logvars = [ 'user.ban', 'user.unban', 'user.join', 'user.leave', 'user.status',
				'user.game.name', 'user.game.url', 'user.game.type', 'user.avatar',
				'user.nick', 'user.name', 'message.send', 'message.delete',
				'message.edit', "xp" ]
		self.quiet = [ 'user.ban', 'user.unban', 'user.join', 'user.leave' ]
		self.normal = [ 'user.ban', 'user.unban', 'user.join', 'user.leave', 'user.avatar', 'user.nick', 'user.name',
			       'message.edit', 'message.delete', "xp" ]
		self.verbose = [ 'user.ban', 'user.unban', 'user.join', 'user.leave', 'user.status',
				'user.game.name', 'user.game.url', 'user.game.type', 'user.avatar',
				'user.nick', 'user.name', 'message.send', 'message.delete',
				'message.edit', "xp" ]
		self.cleanChannels = []

	def suppressed(self, guild, msg):
		# Check if we're suppressing @here and @everyone mentions
		if self.settings.getServerStat(guild, "SuppressMentions"):
			return Nullify.clean(msg)
		else:
			return msg

	async def oncommand(self, ctx):
		if self.debug:
			# We're Debugging
			timeStamp = datetime.today().strftime("%Y-%m-%d %H.%M")
			msg = '{}{}:\n"{}"\nRun at {}\nBy {}\nOn {}'.format(ctx.prefix, ctx.command, ctx.message.content, timeStamp, ctx.message.author.name, ctx.message.guild.name)
			if os.path.exists('debug.txt'):
				# Exists - let's append
				msg = "\n\n" + msg
				msg = msg.encode("utf-8")
				with open("debug.txt", "ab") as myfile:
					myfile.write(msg)
			else:
				msg = msg.encode("utf-8")
				with open("debug.txt", "wb") as myfile:
					myfile.write(msg)

	async def oncommandcompletion(self, ctx):
		if self.debug:
			# We're Debugging
			timeStamp = datetime.today().strftime("%Y-%m-%d %H.%M")
			msg = '{}{}:\n"{}"\nCompleted at {}\nBy {}\nOn {}'.format(ctx.prefix, ctx.command, ctx.message.content, timeStamp, ctx.message.author.name, ctx.message.guild.name)
			if os.path.exists('debug.txt'):
				# Exists - let's append
				msg = "\n\n" + msg
				msg = msg.encode("utf-8")
				with open("debug.txt", "ab") as myfile:
					myfile.write(msg)
			else:
				msg = msg.encode("utf-8")
				with open("debug.txt", "wb") as myfile:
					myfile.write(msg)


	def shouldLog(self, logVar, server):
		serverLogVars = self.settings.getServerStat(server, "LogVars")
		checks = logVar.split('.')
		check = ''
		for item in checks:
			if len(check):
				check += '.' + item
			else:
				check = item
			if check.lower() in serverLogVars:
				return True
		return False

	# Catch custom xp event
	@asyncio.coroutine
	async def on_xp(self, to_user, from_user, amount):
		server = from_user.guild
		if not self.shouldLog('xp', server):
			return
		if type(to_user) is discord.Role:
			msg = "🌟 {}#{} ({}) gave {} xp to the {} role.".format(from_user.name, from_user.discriminator, from_user.id, amount, to_user.name)
		else:
			msg = "🌟 {}#{} ({}) gave {} xp to {}#{} ({}).".format(from_user.name, from_user.discriminator, from_user.id, amount, to_user.name, to_user.discriminator, to_user.id)
		await self._logEvent(server, "", title=msg, color=discord.Color.blue())

	@asyncio.coroutine
	async def on_member_ban(self, guild, member):
		server = guild
		if not self.shouldLog('user.ban', server):
			return
		# A member was banned
		msg = '🚫 {}#{} ({}) was banned from {}.'.format(member.name, member.discriminator, member.id, self.suppressed(server, server.name))
		await self._logEvent(server, "", title=msg, color=discord.Color.red())

	@asyncio.coroutine
	async def on_member_unban(self, server, member):
		if not self.shouldLog('user.unban', server):
			return
		# A member was banned
		msg = '🔵 {}#{} ({}) was unbanned from {}.'.format(member.name, member.discriminator, member.id, self.suppressed(server, server.name))
		await self._logEvent(server, "", title=msg, color=discord.Color.green())

	@asyncio.coroutine	
	async def on_member_join(self, member):
		server = member.guild
		if not self.shouldLog('user.join', server):
			return
		# A new member joined
		msg = '👐 {}#{} ({}) joined {}.'.format(member.name, member.discriminator, member.id, self.suppressed(server, server.name))
		await self._logEvent(server, "", title=msg, color=discord.Color.teal())
		
	@asyncio.coroutine
	async def on_member_remove(self, member):
		server = member.guild
		if not self.shouldLog('user.leave', server):
			return
		# A member left
		msg = '👋 {}#{} ({}) left {}.'.format(member.name, member.discriminator, member.id, self.suppressed(server, server.name))
		await self._logEvent(server, "", title=msg, color=discord.Color.light_grey())
		
	@asyncio.coroutine
	async def on_member_update(self, before, after):
		if before.bot:
			return
		# A member changed something about their user-profile
		server = before.guild
		if not before.status == after.status and self.shouldLog('user.status', server):
			msg = 'Changed Status:\n\n{}\n   --->\n{}'.format(str(before.status).lower(), str(after.status).lower())
			await self._logEvent(server, msg, title="👤 {}#{} ({}) Updated".format(before.name, before.discriminator, before.id), color=discord.Color.gold())
		if not before.game == after.game:
			# Something changed
			msg = ''

			if before.game == None:
				before.game = discord.Game(name=None, url=None, type=0)

			if after.game == None:
				after.game = discord.Game(name=None, url=None, type=0)

			if not before.game.name == after.game.name and self.shouldLog('user.game.name', server):
				# Name change
				msg += 'Name:\n   {}\n   --->\n   {}\n'.format(before.game.name, after.game.name)
			if not before.game.url == after.game.url and self.shouldLog('user.game.url', server):
				# URL changed
				msg += 'URL:\n   {}\n   --->\n   {}\n'.format(before.game.url, after.game.url)
			if not before.game.type == after.game.type and self.shouldLog('user.game.type', server):
				# Type changed
				play_list = [ "Playing", "Streaming", "Listening", "Watching" ]
				try:
					b_string = play_list[before.game.type]
					a_string = play_list[after.game.type]
				except:
					b_string = a_string = "Playing"
				msg += 'Type:\n   {}\n   --->\n   {}\n'.format(b_string, a_string)
			if len(msg):
				# We saw something tangible change
				msg = 'Changed Playing Status: \n\n{}'.format(msg)
				if self.shouldLog('user.game.name', server) or self.shouldLog('user.game.url', server) or self.shouldLog('user.game.type', server):
					await self._logEvent(server, msg, title="👤 {}#{} ({}) Updated".format(before.name, before.discriminator, before.id), color=discord.Color.gold())
		if not before.avatar_url == after.avatar_url and self.shouldLog('user.avatar', server):
			# Avatar changed
			msg = 'Changed Avatars: \n\n{}\n   --->\n{}'.format(before.avatar_url, after.avatar_url)
			await self._logEvent(server, msg, title="👤 {}#{} ({}) Updated".format(before.name, before.discriminator, before.id), color=discord.Color.gold())
		if not before.nick == after.nick and self.shouldLog('user.nick', server):
			# Nickname changed
			msg = 'Changed Nickname: \n\n{}\n   --->\n{}'.format(before.nick, after.nick)
			await self._logEvent(server, msg, title="👤 {}#{} ({}) Updated".format(before.name, before.discriminator, before.id), color=discord.Color.gold())
		if not before.name == after.name and self.shouldLog('user.name', server):
			# Name changed
			msg = 'Changed Name: \n\n{}\n   --->\n{}'.format(before.name, after.name)
			await self._logEvent(server, msg, title="👤 {}#{} ({}) Updated".format(before.name, before.discriminator, before.id), color=discord.Color.gold())
		
	@asyncio.coroutine
	async def on_message(self, message):
		# context = await self.bot.get_context(message)
		# print(context)
		# print(context.command)

		if not message.guild:
			return
		
		if message.author.bot:
			return
		if not self.shouldLog('message.send', message.guild):
			return
		# A message was sent
		title = '📧 {}#{} ({}), in #{}, sent:'.format(message.author.name, message.author.discriminator, message.author.id, message.channel.name)
		msg = message.content
		if len(message.attachments):
			msg += "\n\n--- Attachments ---\n\n"
			for a in message.attachments:
				msg += a.url + "\n"
		
		await self._logEvent(message.guild, msg, title=title, color=discord.Color.dark_grey())
		return
		
	@asyncio.coroutine
	async def on_message_edit(self, before, after):

		if not before.guild:
			return

		if before.author.bot:
			return
		if not self.shouldLog('message.edit', before.guild):
			return
		if before.content == after.content:
			# Edit was likely a preview happening
			return
		# A message was edited
		title = '✏️ {}#{} ({}), in #{}, edited:'.format(before.author.name, before.author.discriminator, before.author.id, before.channel.name)
		msg = before.content
		if len(before.attachments):
			msg += "\n\n--- Attachments ---\n\n"
			for a in before.attachments:
				msg += a.url + "\n"
		msg += '\n\n--- To ---\n\n{}\n'.format(after.content)
		if len(after.attachments):
			msg += "\n--- Attachments ---\n\n"
			for a in after.attachments:
				msg += a.url + "\n"
		
		await self._logEvent(before.guild, msg, title=title, color=discord.Color.purple())
		return
		
	@asyncio.coroutine
	async def on_message_delete(self, message):

		if not message.guild:
			return

		if message.author.bot:
			return
		if not self.shouldLog('message.delete', message.guild):
			return
		# Check if we're cleaning from said channel
		if message.channel in self.cleanChannels:
			# Don't log these - as they'll spit out a text file later
			return
		# A message was deleted
		title = '❌ {}#{} ({}), in #{}, deleted:'.format(message.author.name, message.author.discriminator, message.author.id, message.channel.name)
		msg = message.content
		if len(message.attachments):
			msg += "\n\n--- Attachments ---\n\n"
			for a in message.attachments:
				msg += a.url + "\n"
		await self._logEvent(message.guild, msg, title=title, color=discord.Color.orange())
	
	async def _logEvent(self, server, log_message, *, filename = None, color = None, title = None):
		# Here's where we log our info
		# Check if we're suppressing @here and @everyone mentions
		if color == None:
			color = discord.Color.default()
		if self.settings.getServerStat(server, "SuppressMentions"):
			suppress = True
		else:
			suppress = False
		# Get log channel
		logChanID = self.settings.getServerStat(server, "LogChannel")
		if not logChanID:
			return
		logChan = self.bot.get_channel(int(logChanID))
		if not logChan:
			return
		# At this point - we log the message
		if filename:
			await logChan.send(log_message, file=discord.File(filename))
		else:
			# Check for suppress
			if suppress:
				log_message = Nullify.clean(log_message)
			# Remove triple backticks and replace any single backticks with single quotes
			log_back  = log_message.replace("`", "'")
			if log_back == log_message:
				# Nothing changed
				footer = datetime.utcnow().strftime("%I:%M %p") + " UTC"
			else:
				# We nullified some backticks - make a note of it
				log_message = log_back
				footer = datetime.utcnow().strftime("%I:%M %p") + " UTC - Note: Backticks --> Single Quotes"
			if self.wrap:
				# Wraps the message to lines no longer than 70 chars
				log_message = textwrap.fill(log_message, replace_whitespace=False)
			await Message.EmbedText(
				title=title,
				description=log_message,
				color=color,
				desc_head="```\n",
				desc_foot="```",
				footer=footer
			).send(logChan)
			# await logChan.send(log_message)


	@commands.command(pass_context=True)
	async def clean(self, ctx, messages : int = 100, *, chan : discord.TextChannel = None):
		"""Cleans the passed number of messages from the given channel - 100 by default (admin only)."""

		author  = ctx.message.author
		server  = ctx.message.guild
		channel = ctx.message.channel

		# Check for admin status
		isAdmin = author.permissions_in(channel).administrator
		if not isAdmin:
			checkAdmin = self.settings.getServerStat(server, "AdminArray")
			for role in author.roles:
				for aRole in checkAdmin:
					# Get the role that corresponds to the id
					if str(aRole['ID']) == str(role.id):
						isAdmin = True

		if not isAdmin:
			await channel.send('You do not have sufficient privileges to access this command.')
			return

		if not chan:
			chan = channel

		if chan in self.cleanChannels:
			# Don't clean messages from a channel that's being cleaned
			return

		# Add channel to list
		self.cleanChannels.append(ctx.channel)

		# Remove original message
		await ctx.message.delete()
		
		if messages > 1000:
			messages = 1000

		# Use history instead of purge
		counter = 0

		# I tried bulk deleting - but it doesn't work on messages over 14 days
		# old - so we're doing them individually I guess.

		# Setup deleted message logging
		# Log the user who called for the clean
		msg = ''
		totalMess = messages
		while totalMess > 0:
			gotMessage = False
			if totalMess > 100:
				tempNum = 100
			else:
				tempNum = totalMess
			try:
				async for message in channel.history(limit=tempNum):
					# Save to a text file
					new_msg = '{}#{}:\n    {}\n'.format(message.author.name, message.author.discriminator, message.content)
					if len(message.attachments):
						new_msg += "\n    --- Attachments ---\n\n"
						for a in message.attachments:
							new_msg += "    " + a.url + "\n"
					new_msg += "\n"
					msg = new_msg + msg
					await message.delete()
					gotMessage = True
					counter += 1
					totalMess -= 1
			except Exception:
				pass
			if not gotMessage:
				# No more messages - exit
				break

		# Remove channel from list
		self.cleanChannels.remove(ctx.channel)

		msg = 'Messages cleaned by {}#{} in {} - #{}\n\n'.format(ctx.message.author.name, ctx.message.author.discriminator, self.suppressed(ctx.guild, ctx.guild.name), ctx.channel.name) + msg

		# Timestamp and save to file
		timeStamp = datetime.today().strftime("%Y-%m-%d %H.%M")
		filename = "cleaned-{}.txt".format(timeStamp)
		msg = msg.encode('utf-8')
		with open(filename, "wb") as myfile:
			myfile.write(msg)

		# Send the cleaner a pm letting them know we're done
		if counter == 1:
			await ctx.message.author.send('*1* message removed from *#{}* in *{}!*'.format(channel.name, self.suppressed(server, server.name)))
		else:
			await ctx.message.author.send('*{}* messages removed from *#{}* in *{}!*'.format(counter, channel.name, self.suppressed(server, server.name)))
		# PM the file
		await ctx.message.author.send(file=discord.File(filename))
		if self.shouldLog('message.delete', message.guild):
			# We're logging
			logmess = '{}#{} cleaned in #{}'.format(ctx.message.author.name, ctx.message.author.discriminator, ctx.channel.name)
			await self._logEvent(ctx.guild, logmess, filename=filename)
		# Delete the remaining file
		os.remove(filename)
	
	
	@commands.command(pass_context=True)
	async def logpreset(self, ctx, *, preset = None):
		"""Can select one of 4 available presets - off, quiet, normal, verbose (bot-admin only)."""
		author  = ctx.message.author
		server  = ctx.message.guild
		channel = ctx.message.channel
		
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
		
		if preset == None:
			await ctx.channel.send('Usage: `{}logpreset [off/quiet/normal/verbose]`'.format(ctx.prefix))
			return
		currentVars = self.settings.getServerStat(server, "LogVars")
		if preset.lower() in ["0", "off"]:
			currentVars = []
			self.settings.setServerStat(server, "LogVars", currentVars)
			await ctx.channel.send('Removed *all* logging options.')
		elif preset.lower() in ['quiet', '1']:
			currentVars = []
			currentVars.extend(self.quiet)
			self.settings.setServerStat(server, "LogVars", currentVars)
			await ctx.channel.send('Logging with *quiet* preset.')
		elif preset.lower() in ['normal', '2']:
			currentVars = []
			currentVars.extend(self.normal)
			self.settings.setServerStat(server, "LogVars", currentVars)
			await ctx.channel.send('Logging with *normal* preset.')
		elif preset.lower() in ['verbose', '3']:
			currentVars = []
			currentVars.extend(self.verbose)
			self.settings.setServerStat(server, "LogVars", currentVars)
			await ctx.channel.send('Logging with *verbose* preset.')
		else:
			await ctx.channel.send('Usage: `{}logpreset [off/quiet/normal/verbose]`'.format(ctx.prefix))
		
	
	@commands.command(pass_context=True)
	async def logging(self, ctx):
		"""Outputs whether or not we're logging is enabled (bot-admin only)."""
		author  = ctx.message.author
		server  = ctx.message.guild
		channel = ctx.message.channel
		
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
		
		logChannel = self.settings.getServerStat(ctx.message.guild, "LogChannel")
		if logChannel:
			channel = self.bot.get_channel(int(logChannel))
			if channel:
				logVars = self.settings.getServerStat(ctx.message.guild, "LogVars")
				if len(logVars):
					logText = ', '.join(logVars)
				else:
					logText = '*Nothing*'
				msg = 'Logging is *enabled* in *{}*.\nCurrently logging: {}'.format(channel.name, logText)
				await ctx.channel.send(msg)
				return
		await ctx.channel.send('Logging is currently *disabled*.')
		
		
	@commands.command(pass_context=True)
	async def logenable(self, ctx, *, options = None):
		"""Enables the passed, comma-delimited log vars."""
		author  = ctx.message.author
		server  = ctx.message.guild
		channel = ctx.message.channel
		
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
		
		if options == None:
			msg = 'Usage: `{}logenable option1, option2, option3...`\nAvailable options:\n{}'.format(ctx.prefix, ', '.join(self.logvars))
			await ctx.channel.send(msg)
			return
		
		serverOptions = self.settings.getServerStat(server, "LogVars")
		options = "".join(options.split())
		optionList = options.split(',')
		addedOptions = []
		for option in optionList:
			for varoption in self.logvars:
				if varoption.startswith(option.lower()) and not varoption in serverOptions:
					# Only add if valid and not already added
					addedOptions.append(varoption)
		if not len(addedOptions):
			await ctx.channel.send('No valid or disabled options were passed.')
			return
		
		for option in addedOptions:
			serverOptions.append(option)
		
		if len(addedOptions) == 1:
			await ctx.channel.send('*1* logging option enabled.')
		else:
			await ctx.channel.send('*{}* logging options enabled.'.format(len(addedOptions)))
		
				
	@commands.command(pass_context=True)
	async def logdisable(self, ctx, *, options = None):
		"""Disables the passed, comma-delimited log vars."""
		author  = ctx.message.author
		server  = ctx.message.guild
		channel = ctx.message.channel
		
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
		
		if options == None:
			msg = 'Cleared all logging options.'
			self.settings.setServerStat(server, "LogVars", [])
			await ctx.channel.send(msg)
			return
		
		serverOptions = self.settings.getServerStat(server, "LogVars")
		options = "".join(options.split())
		optionList = options.split(',')
		addedOptions = []
		for option in optionList:
			for varoption in self.logvars:
				if varoption.startswith(option.lower()) and varoption in serverOptions:
					# Only remove if valid and in list
					addedOptions.append(varoption)
					serverOptions.remove(varoption)
		if not len(addedOptions):
			await ctx.channel.send('No valid or enabled options were passed.  Nothing to disable.')
			return
		
		if len(addedOptions) == 1:
			await ctx.channel.send('*1* logging option disabled.')
		else:
			await ctx.channel.send('*{}* logging options disabled.'.format(len(addedOptions)))			
			
			
	@commands.command(pass_context=True)
	async def setlogchannel(self, ctx, *, channel : discord.TextChannel = None):
		"""Sets the channel for Logging (bot-admin only)."""
		
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

		if channel == None:
			self.settings.setServerStat(ctx.message.guild, "LogChannel", "")
			msg = 'Logging is now *disabled*.'
			await ctx.channel.send(msg)
			return

		# If we made it this far - then we can add it
		self.settings.setServerStat(ctx.message.guild, "LogChannel", channel.id)

		msg = 'Logging is now *enabled* in **{}**.'.format(channel.name)
		await ctx.channel.send(msg)
		
	
	@setlogchannel.error
	async def setlogchannel_error(self, ctx, error):
		# do stuff
		msg = 'setlogchannel Error: {}'.format(ctx)
		await error.channel.send(msg)


	@commands.command(pass_context=True)
	async def setdebug(self, ctx, *, debug = None):
		"""Turns on/off debugging (owner only - always off by default)."""

		author  = ctx.message.author
		server  = ctx.message.guild
		channel = ctx.message.channel

		# Only allow owner
		isOwner = self.settings.isOwner(ctx.author)
		if isOwner == None:
			msg = 'I have not been claimed, *yet*.'
			await ctx.channel.send(msg)
			return
		elif isOwner == False:
			msg = 'You are not the *true* owner of me.  Only the rightful owner can use this command.'
			await ctx.channel.send(msg)
			return

		if debug == None:
			# Output debug status
			if self.debug:
				await channel.send('Debugging is enabled.')
			else:
				await channel.send('Debugging is disabled.')
			return
		elif debug.lower() in [ "yes", "on", "true", "enabled", "enable" ]:
			debug = True
		elif debug.lower() in [ "no", "off", "false", "disabled", "disable" ]:
			debug = False
		else:
			debug = None

		if debug == True:
			if self.debug == True:
				msg = 'Debugging remains enabled.'
			else:
				msg = 'Debugging now enabled.'
		else:
			if self.debug == False:
				msg = 'Debugging remains disabled.'
			else:
				msg = 'Debugging now disabled.'
		self.debug = debug
		
		await channel.send(msg)
		
		
	@commands.command(pass_context=True)
	async def cleardebug(self, ctx):
		"""Deletes the debug.txt file (owner only)."""

		author  = ctx.message.author
		server  = ctx.message.guild
		channel = ctx.message.channel

		# Only allow owner
		isOwner = self.settings.isOwner(ctx.author)
		if isOwner == None:
			msg = 'I have not been claimed, *yet*.'
			await ctx.channel.send(msg)
			return
		elif isOwner == False:
			msg = 'You are not the *true* owner of me.  Only the rightful owner can use this command.'
			await ctx.channel.send(msg)
			return
		
		if not os.path.exists('debug.txt'):
			msg = 'No *debug.txt* found.'
			await channel.send(msg)
			return
		# Exists - remove it
		os.remove('debug.txt')
		msg = '*debug.txt* removed!'
		await channel.send(msg)


	@commands.command(pass_context=True)
	async def heartbeat(self, ctx):
		"""Write to the console and attempt to send a message (owner only)."""

		author  = ctx.message.author
		server  = ctx.message.guild
		channel = ctx.message.channel

		# Only allow owner
		isOwner = self.settings.isOwner(ctx.author)
		if isOwner == None:
			msg = 'I have not been claimed, *yet*.'
			await ctx.channel.send(msg)
			return
		elif isOwner == False:
			msg = 'You are not the *true* owner of me.  Only the rightful owner can use this command.'
			await ctx.channel.send(msg)
			return

		timeStamp = datetime.today().strftime("%Y-%m-%d %H.%M")
		print('Heartbeat tested at {}.'.format(timeStamp))
		# Message send
		message = await channel.send('Heartbeat tested at {}.'.format(timeStamp))
		if message:
			print('Message:\n{}'.format(message))
		else:
			print('No message returned.')
