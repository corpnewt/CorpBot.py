import asyncio
import discord
import os
from   PIL         import Image
from   discord.ext import commands
from   Cogs import Settings
from   Cogs import DisplayName

# This is the Bot module - it contains things like nickname, status, etc

class Bot:

	# Init with the bot reference, and a reference to the settings var
	def __init__(self, bot, settings):
		self.bot = bot
		self.settings = settings
		
	def message(self, message):
		# Check the message and see if we should allow it - always yes.
		# This module doesn't need to cancel messages.
		return { 'Ignore' : False, 'Delete' : False}
		
	@commands.command(pass_context=True)
	async def nickname(self, ctx, name : str = None):
		"""Set the bot's nickname (admin-only)."""
		
		isAdmin = ctx.message.author.permissions_in(ctx.message.channel).administrator
		# Only allow admins to change server stats
		if not isAdmin:
			await self.bot.send_message(ctx.message.channel, 'You do not have sufficient privileges to access this command.')
			return
		
		# Let's get the bot's member in the current server
		botName = "{}#{}".format(self.bot.user.name, self.bot.user.discriminator)
		botMember = ctx.message.server.get_member_named(botName)
		await self.bot.change_nickname(botMember, name)

	@commands.command(pass_context=True)
	async def avatar(self, ctx, filename : str = None, sizeLimit : int = 8000000):
		"""Sets the bot's avatar (owner-only)."""

		channel = ctx.message.channel
		author  = ctx.message.author
		server  = ctx.message.server

		# Only allow owner to change server stats
		serverDict = self.settings.serverDict

		try:
			owner = serverDict['Owner']
		except KeyError:
			owner = None

		if owner == None:
			# No owner set
			msg = 'I have not been claimed, *yet*.'
			await self.bot.send_message(channel, msg)
			return
		else:
			if not author.id == owner:
				msg = 'You are not the *true* owner of me.  Only the rightful owner can change my avatar.'
				await self.bot.send_message(channel, msg)
				return
		if filename is None:
			await self.bot.edit_profile(avatar=None)
			return
		
		if not os.path.isfile('./{}'.format(filename)):
			# File doesn't exist
			msg = '*{}* doesn\'t exist in my working directory.'.format(filename)
			await self.bot.send_message(channel, msg)
			return
		
		# File exists - check if image
		img = Image.open(filename)
		ext = img.format

		if not ext:
			# File isn't a valid image
			msg = '*{}* isn\'t a valid image format.'.format(filename)
			await self.bot.send_message(channel, msg)
			return

		# Is an image PIL understands
		if not ext.lower == "png":
			# Not a PNG - let's convert
			filename = '{}.png'.format(filename)
			img.save(filename)
		# Should be a png here - let's check size
		# Let's make sure it's less than the passed limit

		imageSize = os.stat(filename)
		while int(imageSize.st_size) > sizeLimit:
			# Image is too big - resize
			myimage = Image.open(filename)
			xsize, ysize = myimage.size
			ratio = sizeLimit/int(imageSize.st_size)
			xsize *= ratio
			ysize *= ratio
			myimage = myimage.resize((int(xsize), int(ysize)), Image.ANTIALIAS)
			myimage.save(filename)
			imageSize = os.stat(filename)
		# Image is resized - let's save it
		img = Image.open(filename)
		ext = img.format
		img.close()

		with open(filename, 'rb') as f:
			newAvatar = f.read()
			await self.bot.edit_profile(avatar=newAvatar)

			

	@commands.command(pass_context=True)
	async def servers(self, ctx):
		"""Lists the number of servers I'm connected to!"""

		channel = ctx.message.channel
		author  = ctx.message.author
		server  = ctx.message.server
		
		total = 0
		for server in self.bot.servers:
			total += 1
		msg = 'I am a part of *{}* servers!'.format(total)
		await self.bot.send_message(channel, msg)
		
		
	@commands.command(pass_context=True)
	async def playgame(self, ctx, game : str = None):
		"""Sets the playing status of the bot (owner-only)."""

		channel = ctx.message.channel
		author  = ctx.message.author
		server  = ctx.message.server

		# Only allow owner to change server stats
		serverDict = self.settings.serverDict

		try:
			owner = serverDict['Owner']
		except KeyError:
			owner = None

		if owner == None:
			# No owner set
			msg = 'I have not been claimed, *yet*.'
			await self.bot.send_message(channel, msg)
			return
		else:
			if not author.id == owner:
				msg = 'You are not the *true* owner of me.  Only the rightful owner can set my playing status.'
				await self.bot.send_message(channel, msg)
				return

		if game == None:
			await self.bot.change_presence(game=None)
			return

		await self.bot.change_presence(game=discord.Game(name=game))

	@commands.command(pass_context=True)
	async def setbotparts(self, ctx, parts : str = None):
		"""Set the bot's parts - can be a url, formatted text, or nothing to clear."""
		
		isAdmin = ctx.message.author.permissions_in(ctx.message.channel).administrator
		# Only allow admins to change server stats
		if not isAdmin:
			await self.bot.send_message(ctx.message.channel, 'You do not have sufficient privileges to access this command.')
			return

		channel = ctx.message.channel
		author  = ctx.message.author
		server  = ctx.message.server

		if not parts:
			parts = ""
			
		self.settings.setUserStat(self.bot.user, server, "Parts", parts)
		msg = '*{}\'s* parts have been set to:\n{}'.format(DisplayName.name(self.bot.user), parts)
		await self.bot.send_message(channel, msg)