import asyncio
import discord
import os
import psutil
import platform
import time
import sys
from   PIL         import Image
from   discord.ext import commands
from   Cogs import Settings
from   Cogs import DisplayName
from   Cogs import ReadableTime
from   Cogs import GetImage
from   Cogs import Nullify
from   Cogs import ProgressBar

# This is the Bot module - it contains things like nickname, status, etc

class Bot:

	# Init with the bot reference, and a reference to the settings var
	def __init__(self, bot, settings):
		self.bot = bot
		self.settings = settings
		self.startTime = int(time.time())
		
	async def onready(self):
		# Get ready - play game!
		game = None
		try:
			game = self.settings.serverDict['Game']
		except KeyError:
			pass
		if game:
			await self.bot.change_presence(game=discord.Game(name=game))
		else:
			await self.bot.change_presence(game=None)

	@commands.command(pass_context=True)
	async def ping(self, ctx):
		"""Feeling lonely?"""
		msg = '*{}*, PONG!'.format(ctx.message.author.mention)
		await self.bot.send_message(ctx.message.channel, msg)

		
	@commands.command(pass_context=True)
	async def nickname(self, ctx, *, name : str = None):
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
	async def hostinfo(self, ctx):
		"""List info about the bot's host environment."""
		# cpuCores    = psutil.cpu_count(logical=False)
		# cpuThred    = psutil.cpu_count()
		cpuThred    = os.cpu_count()
		cpuUsage    = psutil.cpu_percent(interval=1)
		memStats    = psutil.virtual_memory()
		memPerc     = memStats.percent
		memUsed     = memStats.used
		memTotal    = memStats.total
		memUsedGB   = "{0:.1f}".format(((memUsed / 1024) / 1024) / 1024)
		memTotalGB  = "{0:.1f}".format(((memTotal/1024)/1024)/1024)
		currentOS   = platform.platform()
		system      = platform.system()
		release     = platform.release()
		version     = platform.version()
		processor   = platform.processor()
		botMember   = DisplayName.memberForID(self.bot.user.id, ctx.message.server)
		botName     = DisplayName.name(botMember)
		currentTime = int(time.time())
		timeString  = ReadableTime.getReadableTimeBetween(self.startTime, currentTime)
		pythonMajor = sys.version_info.major
		pythonMinor = sys.version_info.minor
		pythonMicro = sys.version_info.micro
		pythonRelease = sys.version_info.releaselevel

		msg = '***{}\'s*** **Home:**\n'.format(botName)
		msg += '```{}\n'.format(currentOS)
		msg += 'Python {}.{}.{} {}\n'.format(pythonMajor, pythonMinor, pythonMicro, pythonRelease)
		msg += '{}% of {} ({} thread[s])\n'.format(cpuUsage, processor, cpuThred)
		msg += ProgressBar.makeBar(int(round(cpuUsage))) + "\n"
		msg += '{} ({}%) of {}GB RAM used\n'.format(memUsedGB, memPerc, memTotalGB)
		msg += ProgressBar.makeBar(int(round(memPerc))) + "\n"
		msg += '{} uptime```'.format(timeString)

		await self.bot.send_message(ctx.message.channel, msg)


	@commands.command(pass_context=True)
	async def avatar(self, ctx, filename : str = None, sizeLimit : int = 8000000):
		"""Sets the bot's avatar (owner only)."""

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

		# Check if we created a temp folder for this image
		isTemp = False

		status = await self.bot.send_message(channel, 'Checking if url (and downloading if valid)...')

		# File name is *something* - let's first check it as a url, then a file
		extList = ["jpg", "jpeg", "png", "gif", "tiff", "tif"]
		if GetImage.get_ext(filename) in extList:
			# URL has an image extension
			file = GetImage.download(filename)
			if file:
				# we got a download - let's reset and continue
				filename = file
				isTemp = True

		if not os.path.isfile(filename):
			if not os.path.isfile('./{}'.format(filename)):
				await self.bot.edit_message(status, '*{}* doesn\'t exist absolutely, or in my working directory.'.format(filename))
				# File doesn't exist
				return
			else:
				# Local file name
				filename = './{}'.format(filename)
		
		# File exists - check if image
		img = Image.open(filename)
		ext = img.format

		if not ext:
			# File isn't a valid image
			await self.bot.edit_message(status, '*{}* isn\'t a valid image format.'.format(filename))
			return

		wasConverted = False
		# Is an image PIL understands
		if not ext.lower == "png":
			# Not a PNG - let's convert
			await self.bot.edit_message(status, 'Converting to png...')
			filename = '{}.png'.format(filename)
			img.save(filename)
			wasConverted = True

		# We got it - crop and go from there
		w, h = img.size
		dw = dh = 0
		if w > h:
			# Wide
			dw = int((w-h)/2)
		elif h > w:
			# Tall
			dh = int((h-w)/2)
		# Run the crop
		await self.bot.edit_message(status, 'Cropping (if needed)...')
		img.crop((dw, dh, w-dw, h-dh)).save(filename)

		# Should be a square png here - let's check size
		# Let's make sure it's less than the passed limit

		imageSize = os.stat(filename)
		await self.bot.edit_message(status, 'Resizing (if needed)...')
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

		await self.bot.edit_message(status, 'Uploading and applying avatar...')
		with open(filename, 'rb') as f:
			newAvatar = f.read()
			await self.bot.edit_profile(avatar=newAvatar)
		# Cleanup - try removing with shutil.rmtree, then with os.remove()
		await self.bot.edit_message(status, 'Cleaning up...')
		if isTemp:
			GetImage.remove(filename)
		else:
			if wasConverted:
				os.remove(filename)
		await self.bot.edit_message(status, 'Avatar set!')


	@commands.command(pass_context=True)
	async def reboot(self, ctx):
		"""Shuts down the bot - allows for reboot if using the start script (owner only)."""

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
				msg = 'You are not the *true* owner of me.  Only the rightful owner can reboot me.'
				await self.bot.send_message(channel, msg)
				return
		
		self.settings.flushSettings()
		msg = 'Flushed settings to disk.\nRebooting...'
		await self.bot.send_message(ctx.message.channel, msg)
		# Logout, stop the event loop, close the loop, quit
		for task in asyncio.Task.all_tasks():
			task.cancel()
		
		await self.bot.logout()
		self.bot.loop.stop()
		self.bot.loop.close()
		await exit(0)
			

	@commands.command(pass_context=True)
	async def servers(self, ctx):
		"""Lists the number of servers I'm connected to!"""

		channel = ctx.message.channel
		author  = ctx.message.author
		server  = ctx.message.server
		
		total = 0
		for server in self.bot.servers:
			total += 1
		if total == 1:
			msg = 'I am a part of *1* server!'
		else:
			msg = 'I am a part of *{}* servers!'.format(total)
		await self.bot.send_message(channel, msg)
		
		
	@commands.command(pass_context=True)
	async def playgame(self, ctx, *, game : str = None):
		"""Sets the playing status of the bot (owner-only)."""

		channel = ctx.message.channel
		author  = ctx.message.author
		server  = ctx.message.server

		# Check if we're suppressing @here and @everyone mentions
		if self.settings.getServerStat(ctx.message.server, "SuppressMentions").lower() == "yes":
			suppress = True
		else:
			suppress = False

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
			self.settings.serverDict['Game'] = None
			msg = 'Removing my playing status...'
			status = await self.bot.send_message(channel, msg)

			await self.bot.change_presence(game=None)
			
			await self.bot.edit_message(status, 'Playing status removed!')
			self.settings.flushSettings()
			return

		self.settings.serverDict['Game'] = game
		msg = 'Setting my playing status to *{}*...'.format(game)
		# Check for suppress
		if suppress:
			msg = Nullify.clean(msg)
		status = await self.bot.send_message(channel, msg)

		await self.bot.change_presence(game=discord.Game(name=game))
		# Check for suppress
		if suppress:
			game = Nullify.clean(game)
		await self.bot.edit_message(status, 'Playing status set to *{}!*'.format(game))
		self.settings.flushSettings()

	@commands.command(pass_context=True)
	async def setbotparts(self, ctx, *, parts : str = None):
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
		msg = '*{}\'s* parts have been set to:\n{}'.format(DisplayName.serverNick(self.bot.user, server), parts)
		await self.bot.send_message(channel, msg)

	@commands.command(pass_context=True)
	async def source(self, ctx):
		"""Link the github source."""
		source = "https://github.com/corpnewt/CorpBot.py"
		msg = '**My insides are located at:**\n\n{}'.format(source)
		await self.bot.send_message(ctx.message.channel, msg)
