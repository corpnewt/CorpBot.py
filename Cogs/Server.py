import asyncio
import discord
import requests
import string
import os
from   datetime import datetime
from   discord.ext import commands
from   Cogs import Settings
from   Cogs import Message
from   Cogs import Nullify

# This module sets/gets some server info

class Server:

	# Init with the bot reference, and a reference to the settings var and xp var
	def __init__(self, bot, settings):
		self.bot = bot
		self.settings = settings

	@commands.command(pass_context=True)
	async def setprefix(self, ctx, *, prefix : str = None):
		"""Sets the bot's prefix (admin only)."""
		# Check for admin status
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

		# We're admin
		if not prefix:
			self.settings.setServerStat(ctx.message.server, "Prefix", None)
			msg = 'Custom server prefix *removed*.'
		else:
			if prefix == '@everyone' or prefix == '@here':
				await self.bot.send_message(ctx.message.channel, "Yeah, that'd get annoying *reaaaal* fast.  Try another prefix.")
				return

			self.settings.setServerStat(ctx.message.server, "Prefix", prefix)
			msg = 'Custom server prefix is now: {}'.format(prefix)

		await self.bot.send_message(ctx.message.channel, msg)


	@commands.command(pass_context=True)
	async def prefix(self, ctx):
		"""Output's the server's prefix - custom or otherwise."""

		try:
			serverPrefix = self.settings.getServerStat(ctx.message.server, "Prefix")
		except Exception:
			serverPrefix = None

		if not serverPrefix:
			serverPrefix = self.settings.prefix

		msg = 'Prefix is: {}'.format(serverPrefix)
		await self.bot.send_message(ctx.message.channel, msg)


	@commands.command(pass_context=True)
	async def setinfo(self, ctx, *, word : str = None):
		"""Sets the server info (admin only)."""

		# Check for admin status
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

		# We're admin
		if not word:
			self.settings.setServerStat(ctx.message.server, "Info", None)
			msg = 'Server info *removed*.'
		else:
			self.settings.setServerStat(ctx.message.server, "Info", word)
			msg = 'Server info *updated*.'

		await self.bot.send_message(ctx.message.channel, msg)

	@commands.command(pass_context=True)
	async def info(self, ctx):
		"""Displays the server info if any."""

		# Check if we're suppressing @here and @everyone mentions
		if self.settings.getServerStat(ctx.message.server, "SuppressMentions").lower() == "yes":
			suppress = True
		else:
			suppress = False

		serverInfo = self.settings.getServerStat(ctx.message.server, "Info")
		msg = 'I have no info on *{}* yet.'.format(ctx.message.server.name)
		if serverInfo:
			msg = '*{}*:\n\n{}'.format(ctx.message.server.name, serverInfo)

		# Check for suppress
		if suppress:
			msg = Nullify.clean(msg)

		await self.bot.send_message(ctx.message.channel, msg)

	@commands.command(pass_context=True)
	async def dumpservers(self, ctx):
		"""Dumps a timpestamped list of servers into the same directory as the bot (owner only)."""
		
		author  = ctx.message.author
		server  = ctx.message.server
		channel = ctx.message.channel

		try:
			owner = self.settings.serverDict['Owner']
		except KeyError:
			owner = None

		if owner == None:
			# No previous owner, let's set them
			msg = 'I cannot dump the server list until I have an owner.'
			await self.bot.send_message(channel, msg)
			return
		if not author.id == owner:
			# Not the owner
			msg = 'You are not the *true* owner of me.  Only the rightful owner can dump the server list.'
			await self.bot.send_message(channel, msg)
			return

		timeStamp = datetime.today().strftime("%Y-%m-%d %H.%M")
		serverFile = 'ServerList-{}.txt'.format(timeStamp)
		message = await self.bot.send_message(ctx.message.channel, 'Saving server list to *{}*...'.format(serverFile))
		msg = ''
		for server in self.bot.servers:
			msg += server.name + "\n"
			msg += server.id + "\n"
			msg += str(len(server.members)) + "\n\n"

		# Trim the last 2 newlines
		msg = msg[:-2].encode("utf-8")
		
		with open(serverFile, "wb") as myfile:
			myfile.write(msg)

		message = await self.bot.edit_message(message, 'Uploading *{}*...'.format(serverFile))
		await self.bot.send_file(ctx.message.channel, serverFile)
		message = await self.bot.edit_message(message, 'Uploaded *{}!*'.format(serverFile))
		os.remove(serverFile)


	@commands.command(pass_context=True)
	async def leaveserver(self, ctx, *, targetServer = None):
		"""Leaves a server - can take a name or id (owner only)."""
		
		author  = ctx.message.author
		server  = ctx.message.server
		channel = ctx.message.channel

		try:
			owner = self.settings.serverDict['Owner']
		except KeyError:
			owner = None

		if owner == None:
			# No previous owner, let's set them
			msg = 'I cannot leave servers until I have an owner.'
			await self.bot.send_message(channel, msg)
			return
		if not author.id == owner:
			# Not the owner
			msg = 'You are not the *true* owner of me.  Only the rightful owner can have me leave servers.'
			await self.bot.send_message(channel, msg)
			return

		if targetServer == None:
			# No server passed
			msg = 'Usage: `{}leaveserver [id/name]`'.format(ctx.prefix)
			await self.bot.send_message(channel, msg)
			return

		# Check id first, then name
		for aServer in self.bot.servers:
			if str(aServer.id) == str(targetServer):
				# Found it by id
				await self.bot.send_message(aServer, 'Thanks for having me - but it\'s my time to go...')
				await self.bot.leave_server(aServer)
				return
		# Didn't find it - try by name
		for aServer in self.bot.servers:
			if aServer.name.lower() == targetServer.lower():
				# Found it by name
				await self.bot.send_message(aServer, 'Thanks for having me - but it\'s my time to go...')
				await self.bot.leave_server(aServer)
				return

		await self.bot.send_message(ctx.message.channel, 'I couldn\'t find that server.')