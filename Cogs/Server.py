import asyncio
import discord
import string
import os
import re
from   datetime import datetime
from   discord.ext import commands
from   Cogs import Settings
from   Cogs import Message
from   Cogs import Nullify
from   Cogs import PCPP

def setup(bot):
	# Add the bot and deps
	settings = bot.get_cog("Settings")
	bot.add_cog(Server(bot, settings))

# This module sets/gets some server info

class Server:

	# Init with the bot reference, and a reference to the settings var and xp var
	def __init__(self, bot, settings):
		self.bot = bot
		self.settings = settings
		# Regex for extracting urls from strings
		self.regex = re.compile(r"(http|ftp|https)://([\w_-]+(?:(?:\.[\w_-]+)+))([\w.,@?^=%&:/~+#-]*[\w@?^=%&/~+#-])?")


	async def message(self, message):
		if not type(message.channel) is discord.TextChannel:
			return { "Ignore" : False, "Delete" : False }
		# Make sure we're not already in a parts transaction
		if self.settings.getGlobalUserStat(message.author, 'HWActive'):
			return { "Ignore" : False, "Delete" : False }
		
		# Check if we're attempting to run the pcpp command
		the_prefix = await self.bot.command_prefix(self.bot, message)
		if message.content.startswith(the_prefix):
			# Running a command - return
			return { "Ignore" : False, "Delete" : False }

		# Check if we have a pcpartpicker link
		matches = re.finditer(self.regex, message.content)

		pcpplink = None
		for match in matches:
			if 'pcpartpicker.com' in match.group(0).lower():
				pcpplink = match.group(0)
		
		if not pcpplink:
			# Didn't find any
			return { "Ignore" : False, "Delete" : False }
		
		autopcpp = self.settings.getServerStat(message.guild, "AutoPCPP")
		if autopcpp == None:
			return { "Ignore" : False, "Delete" : False }

		ret = await PCPP.getMarkdown(pcpplink, autopcpp)
		return { "Ignore" : False, "Delete" : False, "Respond" : ret }

		

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
	async def getprefix(self, ctx):
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
	async def autopcpp(self, ctx, *, setting : str = None):
		"""Sets the bot's auto-pcpartpicker markdown if found in messages (admin-only). Setting can be normal, md, mdblock, bold, bolditalic, or nothing."""
		# Check for admin status
		isAdmin = ctx.message.author.permissions_in(ctx.message.channel).administrator
		# Only allow admins to change server stats
		if not isAdmin:
			await ctx.channel.send('You do not have sufficient privileges to access this command.')
			return

		if setting == None:
			# Disabled
			self.settings.setServerStat(ctx.guild, "AutoPCPP", None)
			msg = 'Auto pcpartpicker *disabled*.'
		elif setting.lower() == "normal":
			self.settings.setServerStat(ctx.guild, "AutoPCPP", "normal")
			msg = 'Auto pcpartpicker set to *Normal*.'
		elif setting.lower() == "md":
			self.settings.setServerStat(ctx.guild, "AutoPCPP", "md")
			msg = 'Auto pcpartpicker set to *Markdown*.'
		elif setting.lower() == "mdblock":
			self.settings.setServerStat(ctx.guild, "AutoPCPP", "mdblock")
			msg = 'Auto pcpartpicker set to *Markdown Block*.'
		elif setting.lower() == "bold":
			self.settings.setServerStat(ctx.guild, "AutoPCPP", "bold")
			msg = 'Auto pcpartpicker set to *Bold*.'
		elif setting.lower() == "bolditalic":
			self.settings.setServerStat(ctx.guild, "AutoPCPP", "bolditalic")
			msg = 'Auto pcpartpicker set to *Bold Italics*.'
		else:
			msg = "That's not one of the options."
		
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
		if self.settings.getServerStat(ctx.message.guild, "SuppressMentions"):
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
					tc = aServer.get_channel(aServer.id)
					if tc:
						await tc.send('Thanks for having me - but it\'s my time to go...')
				except Exception:
					pass
				await aServer.leave()
				try:
					await ctx.channel.send('Alright - I left that server.')
				except Exception:
					pass
				return
		# Didn't find it - try by name
		for aServer in self.bot.guilds:
			if aServer.name.lower() == targetServer.lower():
				# Found it by name
				try:
					tc = aServer.get_channel(aServer.id)
					if tc:
						await tc.send('Thanks for having me - but it\'s my time to go...')
				except Exception:
					pass
				await aServer.leave()
				try:
					await ctx.channel.send('Alright - I left that server.')
				except Exception:
					pass
				return

		await ctx.channel.send('I couldn\'t find that server.')