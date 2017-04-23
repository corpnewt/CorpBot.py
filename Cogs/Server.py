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

		# We're admin
		if not prefix:
			self.settings.setServerStat(ctx.message.guild, "Prefix", None)
			msg = 'Custom server prefix *removed*.'
		else:
			if prefix == '@everyone' or prefix == '@here':
				await ctx.channel.send("Yeah, that'd get annoying *reaaaal* fast.  Try another prefix.")
				return

			self.settings.setServerStat(ctx.message.guild, "Prefix", prefix)
			msg = 'Custom server prefix is now: {}'.format(prefix)

		await ctx.channel.send(msg)


	@commands.command(pass_context=True)
	async def prefix(self, ctx):
		"""Output's the server's prefix - custom or otherwise."""

		try:
			serverPrefix = self.settings.getServerStat(ctx.message.guild, "Prefix")
		except Exception:
			serverPrefix = None

		if not serverPrefix:
			serverPrefix = self.settings.prefix

		msg = 'Prefix is: {}'.format(serverPrefix)
		await ctx.channel.send(msg)


	@commands.command(pass_context=True)
	async def setinfo(self, ctx, *, word : str = None):
		"""Sets the server info (admin only)."""

		# Check for admin status
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

		# We're admin
		if not word:
			self.settings.setServerStat(ctx.message.guild, "Info", None)
			msg = 'Server info *removed*.'
		else:
			self.settings.setServerStat(ctx.message.guild, "Info", word)
			msg = 'Server info *updated*.'

		await ctx.channel.send(msg)

	@commands.command(pass_context=True)
	async def info(self, ctx):
		"""Displays the server info if any."""

		# Check if we're suppressing @here and @everyone mentions
		if self.settings.getServerStat(ctx.message.guild, "SuppressMentions").lower() == "yes":
			suppress = True
		else:
			suppress = False

		serverInfo = self.settings.getServerStat(ctx.message.guild, "Info")
		msg = 'I have no info on *{}* yet.'.format(ctx.message.guild.name)
		if serverInfo:
			msg = '*{}*:\n\n{}'.format(ctx.message.guild.name, serverInfo)

		# Check for suppress
		if suppress:
			msg = Nullify.clean(msg)

		await ctx.channel.send(msg)

	@commands.command(pass_context=True)
	async def dumpservers(self, ctx):
		"""Dumps a timpestamped list of servers into the same directory as the bot (owner only)."""
		
		author  = ctx.message.author
		server  = ctx.message.guild
		channel = ctx.message.channel

		try:
			owner = self.settings.serverDict['Owner']
		except KeyError:
			owner = None

		if owner == None:
			# No previous owner, let's set them
			msg = 'I cannot dump the server list until I have an owner.'
			await channel.send(msg)
			return
		if not str(author.id) == str(owner):
			# Not the owner
			msg = 'You are not the *true* owner of me.  Only the rightful owner can dump the server list.'
			await channel.send(msg)
			return

		timeStamp = datetime.today().strftime("%Y-%m-%d %H.%M")
		serverFile = 'ServerList-{}.txt'.format(timeStamp)
		message = await ctx.message.author.send('Saving server list to *{}*...'.format(serverFile))
		msg = ''
		for server in self.bot.guilds:
			msg += server.name + "\n"
			msg += str(server.id) + "\n"
			msg += server.owner.name + "#" + str(server.owner.discriminator) + "\n\n"
			msg += str(len(server.members)) + "\n\n"

		# Trim the last 2 newlines
		msg = msg[:-2].encode("utf-8")
		
		with open(serverFile, "wb") as myfile:
			myfile.write(msg)

		await message.edit(content='Uploading *{}*...'.format(serverFile))
		await ctx.message.author.send(file=discord.File(serverFile))
		await message.edit(content='Uploaded *{}!*'.format(serverFile))
		os.remove(serverFile)


	@commands.command(pass_context=True)
	async def leaveserver(self, ctx, *, targetServer = None):
		"""Leaves a server - can take a name or id (owner only)."""
		
		author  = ctx.message.author
		server  = ctx.message.guild
		channel = ctx.message.channel

		try:
			owner = self.settings.serverDict['Owner']
		except KeyError:
			owner = None

		if owner == None:
			# No previous owner, let's set them
			msg = 'I cannot leave servers until I have an owner.'
			await channel.send(msg)
			return
		if not str(author.id) == str(owner):
			# Not the owner
			msg = 'You are not the *true* owner of me.  Only the rightful owner can have me leave servers.'
			await channel.send(msg)
			return

		if targetServer == None:
			# No server passed
			msg = 'Usage: `{}leaveserver [id/name]`'.format(ctx.prefix)
			await channel.send(msg)
			return

		# Check id first, then name
		for aServer in self.bot.guilds:
			if str(aServer.id) == str(targetServer):
				# Found it by id
				try:
					await aServer.default_channel.send('Thanks for having me - but it\'s my time to go...')
				except Exception:
					pass
				await aServer.leave()
				return
		# Didn't find it - try by name
		for aServer in self.bot.guilds:
			if aServer.name.lower() == targetServer.lower():
				# Found it by name
				try:
					await aServer.default_channel.send('Thanks for having me - but it\'s my time to go...')
				except Exception:
					pass
				await aServer.leave()
				return

		await ctx.channel.send('I couldn\'t find that server.')