import asyncio
import discord
import os
from   datetime import datetime
from   operator import itemgetter
from   discord.ext import commands
from   Cogs import DisplayName

# This is the Debugging module. It keeps track of how long the bot's been up

class Debugging:

	# Init with the bot reference, and a reference to the settings var
	def __init__(self, bot, settings, debug = False):
		self.bot = bot
		self.settings = settings
		self.debug = debug

	async def oncommand(self, command, ctx):
		if self.debug:
			# We're Debugging
			timeStamp = datetime.today().strftime("%Y-%m-%d %H.%M")
			msg = '{}{}:\n"{}"\nRun at {}\nBy {}\nOn {}'.format(ctx.prefix, command, ctx.message.content, timeStamp, ctx.message.author.name, ctx.message.server.name)
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

	async def oncommandcompletion(self, command, ctx):
		if self.debug:
			# We're Debugging
			timeStamp = datetime.today().strftime("%Y-%m-%d %H.%M")
			msg = '{}{}:\n"{}"\nCompleted at {}\nBy {}\nOn {}'.format(ctx.prefix, command, ctx.message.content, timeStamp, ctx.message.author.name, ctx.message.server.name)
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
					
	async def onjoin(self, member, server):
		# A new member joined
		msg = '*{}#{}* joined *{}*.'.format(member.name, member.discriminator, server.name)
		logLevel = 0
		await self._logEvent(server, msg, logLevel)
		
	async def onleave(self, member, server):
		# A member left
		msg = '*{}#{}* left *{}*.'.format(member.name, member.discriminator, server.name)
		logLevel = 0
		await self._logEvent(server, msg, logLevel)
		
	async def member_update(self, before, after):
		# A member changed something about their user-profile
		logLevel = 1
		server = before.server
		if not str(before.status).lower() == str(after.status).lower():
			msg = '*{}#{}* went from *{}* to *{}*.'.format(before.name, before.discriminator, str(before.status).lower(), str(after.status).lower())
			await self._logEvent(server, msg, 2)
		if not before.game == after.game:
			# Something changed
			msg = '*{}#{}* changed playing status: ```\n'.format(before.name, before.discriminator)
			if not before.game.name == after.game.name:
				# Name change
				msg += 'Name:\n   {}\n   --->\n   {}'.format(before.game.name, after.game.name)
			if not before.game.url == after.game.url:
				# URL changed
				msg += 'URL:\n   {}\n   --->\n   {}'.format(before.game.url, after.game.url)
			if not before.game.type == after.game.type:
				# Type changed
				msg += 'Type:\n   {}\n   --->\n   {}'.format(before.game.type, after.game.type)
			msg += '```'
			await self._logEvent(server, msg, logLevel)
		if not before.avatar_url == after.avatar_url:
			# Avatar changed
			msg = '*{}#{}* changed avatars: ```\n{}\n   --->\n{}```'.format(before.name, before.discriminator, before.avatar_url, after.avatar_url)
			await self._logEvent(server, msg, logLevel)
		if not before.nick == after.nick:
			# Nickname changed
			msg = '*{}#{}* changed nickname: ```\n{}\n   --->\n{}```'.format(before.name, before.discriminator, before.nick, after.nick)
			await self._logEvent(server, msg, logLevel)
		if not before.name == after.name:
			# Name changed
			msg = '*{}#{}* changed name: ```\n{}\n   --->\n{}```'.format(before.name, before.discriminator, before.name, after.name)
			await self._logEvent(server, msg, logLevel)
		
	async def message(self, message):
		# A message was sent
		msg = '*{}#{}* sent: ```\n{}```\nIn *#{}*'.format(message.author.name, message.author.discriminator, message.content, message.channel.name)
		logLevel = 2
		await self._logEvent(message.server, msg, logLevel)
		return { 'Ignore' : False, 'Delete' : False}
		
	async def message_edit(self, before, after):
		# A message was edited
		msg = '*{}#{}* edited: ```\n{}```'.format(before.author.name, before.author.discriminator, before.content)
		logLevel = 1
		await self._logEvent(before.server, msg, logLevel)
		msg = 'To: ```\n{}```\nIn *#{}*'.format(after.content, before.channel.name)
		await self._logEvent(before.server, msg, logLevel)
		return { 'Ignore' : False, 'Delete' : False}
		
	async def message_delete(self, message):
		# A message was deleted
		msg = '*{}#{}* deleted: ```\n{}```\nIn *#{}*'.format(message.author.name, message.author.discriminator, message.content, message.channel.name)
		logLevel = 1
		await self._logEvent(message.server, msg, logLevel)
	
	async def _logEvent(self, server, log_message, log_level = 0):
		# Here's where we log our info
		# Get log channel
		logChanID = self.settings.getServerStat(server, "LogChannel")
		if not logChanID:
			return
		logChan = self.bot.get_channel(logChanID)
		if not logChan:
			return
		# At this point - we have a log channel - get/compare the log levels
		logLevel  = self.settings.getServerStat(server, "LogLevel")
		if log_level > logLevel:
			# Too verbose
			return
		# At this point - we log the message
		await self.bot.send_message(logChan, log_message)
	
	
	@commands.command(pass_context=True)
	async def logging(self, ctx):
		"""Outputs whether or not we're logging is enabled (bot-admin only)."""
		author  = ctx.message.author
		server  = ctx.message.server
		channel = ctx.message.channel
		
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
		
		logChannel = self.settings.getServerStat(ctx.message.server, "LogChannel")
		if logChannel:
			channel = self.bot.get_channel(logChannel)
			if channel:
				logLevel = self.settings.getServerStat(ctx.message.server, "LogLevel")
				logText = 'Quiet'
				if logLevel == 1:
					logText = 'Normal'
				elif logLevel == 2:
					logText = 'Verbose'
				msg = '*{}* logging is *enabled* in *{}*.'.format(logText, channel.name)
				await self.bot.send_message(ctx.message.channel, msg)
				return
		await self.bot.send_message(ctx.message.channel, 'Logging is currently *disabled*.')
		
	
	@commands.command(pass_context=True)
	async def loglevel(self, ctx, *, log = None):
		"""Sets the server's logging level (0 = quiet, 1 = normal, 2 = verbose [bot-admin only])."""

		author  = ctx.message.author
		server  = ctx.message.server
		channel = ctx.message.channel
		
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

		logLevel  = self.settings.getServerStat(server, "LogLevel")

		if log == None:
			# Output log level
			if logLevel == 2:
				await self.bot.send_message(ctx.message.channel, 'Log level is *verbose*.')
			elif logLevel == 1:
				await self.bot.send_message(ctx.message.channel, 'Log level is *normal*.')
			else:
				await self.bot.send_message(ctx.message.channel, 'Log level is *quiet*.')
			return
		elif log.lower() == "0" or log.lower() == "quiet":
			self.settings.setServerStat(server, "LogLevel", 0)
			await self.bot.send_message(ctx.message.channel, 'Log level set to *quiet*.')
		elif log.lower() == "1" or log.lower() == "normal":
			self.settings.setServerStat(server, "LogLevel", 1)
			await self.bot.send_message(ctx.message.channel, 'Log level set to *normal*.')
		elif log.lower() == "2" or log.lower() == "verbose":
			self.settings.setServerStat(server, "LogLevel", 2)
			await self.bot.send_message(ctx.message.channel, 'Log level set to *verbose*.')
			
			
	@commands.command(pass_context=True)
	async def setlogchannel(self, ctx, *, channel : discord.Channel = None):
		"""Sets the channel for Logging (bot-admin only)."""
		
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

		if channel == None:
			self.settings.setServerStat(ctx.message.server, "LogChannel", "")
			msg = 'Logging is now *disabled*.'
			await self.bot.send_message(ctx.message.channel, msg)
			return

		# If we made it this far - then we can add it
		self.settings.setServerStat(ctx.message.server, "LogChannel", channel.id)

		msg = 'Logging is now *enabled* in **{}**.'.format(channel.name)
		await self.bot.send_message(ctx.message.channel, msg)
		
	
	@setlogchannel.error
	async def setlogchannel_error(self, ctx, error):
		# do stuff
		msg = 'setlogchannel Error: {}'.format(ctx)
		await self.bot.say(msg)
	

	@commands.command(pass_context=True)
	async def setdebug(self, ctx, *, debug = None):
		"""Turns on/off debugging (owner only - always off by default)."""

		author  = ctx.message.author
		server  = ctx.message.server
		channel = ctx.message.channel

		try:
			owner = self.settings.serverDict['Owner']
		except KeyError:
			owner = None

		if owner == None:
			# No previous owner, let's set them
			msg = 'I cannot adjust debugging until I have an owner.'
			await self.bot.send_message(channel, msg)
			return
		if not author.id == owner:
			# Not the owner
			msg = 'You are not the *true* owner of me.  Only the rightful owner can change this setting.'
			await self.bot.send_message(channel, msg)
			return

		if debug == None:
			# Output debug status
			if self.debug:
				await self.bot.send_message(ctx.message.channel, 'Debugging is enabled.')
			else:
				await self.bot.send_message(ctx.message.channel, 'Debugging is disabled.')
			return
		elif debug.lower() == "yes" or debug.lower() == "on" or debug.lower() == "true":
			debug = True
		elif debug.lower() == "no" or debug.lower() == "off" or debug.lower() == "false":
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
		
		await self.bot.send_message(ctx.message.channel, msg)
		
		
	@commands.command(pass_context=True)
	async def cleardebug(self, ctx):
		"""Deletes the debug.txt file (owner only)."""

		author  = ctx.message.author
		server  = ctx.message.server
		channel = ctx.message.channel

		try:
			owner = self.settings.serverDict['Owner']
		except KeyError:
			owner = None

		if owner == None:
			# No previous owner, let's set them
			msg = 'I cannot adjust debugging until I have an owner.'
			await self.bot.send_message(channel, msg)
			return
		if not author.id == owner:
			# Not the owner
			msg = 'You are not the *true* owner of me.  Only the rightful owner can change this setting.'
			await self.bot.send_message(channel, msg)
			return
		
		if not os.path.exists('debug.txt'):
			msg = 'No *debug.txt* found.'
			await self.bot.send_message(channel, msg)
			return
		# Exists - remove it
		os.remove('debug.txt')
		msg = '*debug.txt* removed!'
		await self.bot.send_message(channel, msg)


	@commands.command(pass_context=True)
	async def heartbeat(self, ctx):
		"""Write to the console and attempt to send a message (owner only)."""

		author  = ctx.message.author
		server  = ctx.message.server
		channel = ctx.message.channel

		try:
			owner = self.settings.serverDict['Owner']
		except KeyError:
			owner = None

		if owner == None:
			# No previous owner, let's set them
			msg = 'I cannot adjust debugging until I have an owner.'
			await self.bot.send_message(channel, msg)
			return
		if not author.id == owner:
			# Not the owner
			msg = 'You are not the *true* owner of me.  Only the rightful owner can change this setting.'
			await self.bot.send_message(channel, msg)
			return

		timeStamp = datetime.today().strftime("%Y-%m-%d %H.%M")
		print('Heartbeat tested at {}.'.format(timeStamp))
		# Message send
		message = await self.bot.send_message(ctx.message.channel, 'Heartbeat tested at {}.'.format(timeStamp))
		if message:
			print('Message:\n{}'.format(message))
		else:
			print('No message returned.')
