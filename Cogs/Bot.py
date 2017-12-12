import asyncio
import discord
import os
import re
import psutil
import platform
import time
import sys
import fnmatch
import subprocess
import pyspeedtest
import json
import struct
from   PIL         import Image
from   discord.ext import commands
from   Cogs import Settings
from   Cogs import DisplayName
from   Cogs import ReadableTime
from   Cogs import GetImage
from   Cogs import Nullify
from   Cogs import ProgressBar
from   Cogs import UserTime
from   Cogs import Message
from   Cogs import DL
try:
    from urllib.parse import urlparse
except ImportError:
    from urlparse import urlparse

def setup(bot):
	# Add the bot and deps
	settings = bot.get_cog("Settings")
	bot.add_cog(Bot(bot, settings, sys.argv[0], 'python'))

# This is the Bot module - it contains things like nickname, status, etc

class Bot:

	# Init with the bot reference, and a reference to the settings var
	def __init__(self, bot, settings, path = None, pypath = None):
		self.bot = bot
		self.settings = settings
		self.startTime = int(time.time())
		self.path = path
		self.pypath = pypath
		self.regex = re.compile(r"(http|ftp|https)://([\w_-]+(?:(?:\.[\w_-]+)+))([\w.,@?^=%&:/~+#-]*[\w@?^=%&/~+#-])?")
		
	def _is_submodule(self, parent, child):
		return parent == child or child.startswith(parent + ".")

	@asyncio.coroutine
	async def on_loaded_extension(self, ext):
		# See if we were loaded
		if not self._is_submodule(ext.__name__, self.__module__):
			return
		await self._update_status()


	async def onserverjoin(self, server):
		try:
			serverList = self.settings.serverDict['BlockedServers']
		except KeyError:
			self.settings.serverDict['BlockedServers'] = []
			serverList = self.settings.serverDict['BlockedServers']
		for serv in serverList:
			serverName = str(serv).lower()
			try:
				serverID = int(serv)
			except Exception:
				serverID = None
			if serverName == server.name.lower() or serverID == server.id:
				# Found it
				await server.leave()
				return True
			# Check for owner name and id quick
			# Name *MUST* be case-sensitive and have the discriminator for safety
			namecheck = server.owner.name + "#" + str(server.owner.discriminator)
			if serv == namecheck or serverID == server.owner.id:
				# Got the owner
				await server.leave()
				return True
		return False
	
	@commands.command(pass_context=True)
	async def botinfo(self, ctx):
		"""Lists some general stats about the bot."""
		bot_member = ctx.guild.get_member(self.bot.user.id)
		server_embed = discord.Embed(color=bot_member.color)
		server_embed.title = DisplayName.name(bot_member) + " Info"
		
		# Get guild count
		guild_count = "{:,}".format(len(self.bot.guilds))
			
		# Get member count *and* unique member count
		userCount = 0
		counted_users = []
		for server in self.bot.guilds:
			userCount += len(server.members)
			for member in server.members:
				if not member.id in counted_users:
					counted_users.append(member.id)
		if userCount == len(counted_users):
			member_count = "{:,}".format(userCount)
		else:
			member_count = "{:,} ({:,} unique)".format(userCount, len(counted_users))
			
		# Get commands/cogs count
		cog_amnt  = 0
		empty_cog = 0
		for cog in self.bot.cogs:
			visible = []
			for c in self.bot.get_cog_commands(cog):
				if c.hidden:
					continue
				visible.append(c)
			if not len(visible):
				empty_cog +=1
				# Skip empty cogs
				continue
			cog_amnt += 1
		
		cog_count = "{:,} cog".format(cog_amnt)
		# Easy way to append "s" if needed:
		if not len(self.bot.cogs) == 1:
			cog_count += "s"
		if empty_cog:
			cog_count += " [{:,} without commands]".format(empty_cog)

		visible = []
		for command in self.bot.commands:
			if command.hidden:
				continue
			visible.append(command)
			
		command_count = "{:,}".format(len(visible))
		
		# Get localized created time
		local_time = UserTime.getUserTime(ctx.author, self.settings, bot_member.created_at)
		created_at = "{} {}".format(local_time['time'], local_time['zone'])
		
		# Get localized joined time
		local_time = UserTime.getUserTime(ctx.author, self.settings, bot_member.joined_at)
		joined_at = "{} {}".format(local_time['time'], local_time['zone'])
		
		# Get the current prefix
		prefix = await self.bot.command_prefix(self.bot, ctx.message)
		prefix = ", ".join(prefix)

		# Get the owners
		ownerList = self.settings.serverDict['Owner']
		owners = "Unclaimed..."
		if len(ownerList):
			userList = []
			for owner in ownerList:
				# Get the owner's name
				user = self.bot.get_user(int(owner))
				if not user:
					userString = "Unknown User ({})".format(owner)
				else:
					userString = "{}#{}".format(user.name, user.discriminator)
				userList.append(userString)
			owners = ', '.join(userList)
			
		# Get bot's avatar url
		avatar = bot_member.avatar_url
		if not len(avatar):
			avatar = bot_member.default_avatar_url
			
		# Get status
		status_text = ":green_heart:"
		if bot_member.status == discord.Status.offline:
			status_text = ":black_heart:"
		elif bot_member.status == discord.Status.dnd:
			status_text = ":heart:"
		elif bot_member.status == discord.Status.idle:
			status_text = ":yellow_heart:"
			
		# Build the embed
		server_embed.add_field(name="Members", value=member_count, inline=True)
		server_embed.add_field(name="Servers", value=guild_count, inline=True)
		server_embed.add_field(name="Commands", value=command_count + " (in {})".format(cog_count), inline=True)
		server_embed.add_field(name="Created", value=created_at, inline=True)
		server_embed.add_field(name="Joined", value=joined_at, inline=True)
		server_embed.add_field(name="Owners", value=owners, inline=True)
		server_embed.add_field(name="Prefixes", value=prefix, inline=True)
		server_embed.add_field(name="Status", value=status_text, inline=True)
		if bot_member.game and bot_member.game.name:
			play_list = [ "Playing", "Streaming", "Listening to", "Watching" ]
			try:
				play_string = play_list[bot_member.game.type]
			except:
				play_string = "Playing"
			server_embed.add_field(name=play_string, value=str(bot_member.game.name), inline=True)
			if bot_member.game.type == 1:
				# Add the URL too
				server_embed.add_field(name="Stream URL", value="[Watch Now]({})".format(bot_member.game.url), inline=True)
		server_embed.set_thumbnail(url=avatar)
		# Send the embed
		await ctx.channel.send(embed=server_embed)
		

	@commands.command(pass_context=True)
	async def ping(self, ctx):
		"""Feeling lonely?"""
		before_typing = time.monotonic()
		await ctx.trigger_typing()
		after_typing = time.monotonic()
		ms = int((after_typing - before_typing) * 1000)
		msg = '*{}*, ***PONG!*** (~{}ms)'.format(ctx.message.author.mention, ms)
		await ctx.channel.send(msg)

		
	@commands.command(pass_context=True)
	async def nickname(self, ctx, *, name : str = None):
		"""Set the bot's nickname (admin-only)."""
		
		isAdmin = ctx.message.author.permissions_in(ctx.message.channel).administrator
		# Only allow admins to change server stats
		if not isAdmin:
			await ctx.channel.send('You do not have sufficient privileges to access this command.')
			return
		
		# Let's get the bot's member in the current server
		botName = "{}#{}".format(self.bot.user.name, self.bot.user.discriminator)
		botMember = ctx.message.guild.get_member_named(botName)
		await botMember.edit(nick=name)

	@commands.command(pass_context=True)
	async def hostinfo(self, ctx):
		"""List info about the bot's host environment."""

		message = await ctx.channel.send('Gathering info...')

		# cpuCores    = psutil.cpu_count(logical=False)
		# cpuThred    = psutil.cpu_count()
		cpuThred      = os.cpu_count()
		cpuUsage      = psutil.cpu_percent(interval=1)
		memStats      = psutil.virtual_memory()
		memPerc       = memStats.percent
		memUsed       = memStats.used
		memTotal      = memStats.total
		memUsedGB     = "{0:.1f}".format(((memUsed / 1024) / 1024) / 1024)
		memTotalGB    = "{0:.1f}".format(((memTotal/1024)/1024)/1024)
		currentOS     = platform.platform()
		system        = platform.system()
		release       = platform.release()
		version       = platform.version()
		processor     = platform.processor()
		botMember     = DisplayName.memberForID(self.bot.user.id, ctx.message.guild)
		botName       = DisplayName.name(botMember)
		currentTime   = int(time.time())
		timeString    = ReadableTime.getReadableTimeBetween(self.startTime, currentTime)
		pythonMajor   = sys.version_info.major
		pythonMinor   = sys.version_info.minor
		pythonMicro   = sys.version_info.micro
		pythonRelease = sys.version_info.releaselevel
		pyBit         = struct.calcsize("P") * 8
		process       = subprocess.Popen(['git', 'rev-parse', '--short', 'HEAD'], shell=False, stdout=subprocess.PIPE)
		git_head_hash = process.communicate()[0].strip()

		threadString = 'thread'
		if not cpuThred == 1:
			threadString += 's'

		msg = '***{}\'s*** **Home:**\n'.format(botName)
		msg += '```\n'
		msg += 'OS       : {}\n'.format(currentOS)
		msg += 'Hostname : {}\n'.format(platform.node())
		msg += 'Language : Python {}.{}.{} {} ({} bit)\n'.format(pythonMajor, pythonMinor, pythonMicro, pythonRelease, pyBit)
		msg += 'Commit   : {}\n\n'.format(git_head_hash.decode("utf-8"))
		msg += ProgressBar.center('{}% of {} {}'.format(cpuUsage, cpuThred, threadString), 'CPU') + '\n'
		msg += ProgressBar.makeBar(int(round(cpuUsage))) + "\n\n"
		#msg += '{}% of {} {}\n\n'.format(cpuUsage, cpuThred, threadString)
		#msg += '{}% of {} ({} {})\n\n'.format(cpuUsage, processor, cpuThred, threadString)
		msg += ProgressBar.center('{} ({}%) of {}GB used'.format(memUsedGB, memPerc, memTotalGB), 'RAM') + '\n'
		msg += ProgressBar.makeBar(int(round(memPerc))) + "\n\n"
		#msg += '{} ({}%) of {}GB used\n\n'.format(memUsedGB, memPerc, memTotalGB)
		msg += '{} uptime```'.format(timeString)

		await message.edit(content=msg)
		
	@commands.command(pass_context=True)
	async def getimage(self, ctx, *, image):
		"""Tests downloading - owner only"""
		# Only allow owner to modify the limits
		isOwner = self.settings.isOwner(ctx.author)
		if not isOwner:
			return
		
		mess = await Message.Embed(title="Test", description="Downloading file...").send(ctx)
		file_path = await GetImage.download(image)
		mess = await Message.Embed(title="Test", description="Uploading file...").edit(ctx, mess)
		await Message.EmbedText(title="Image", file=file_path).edit(ctx, mess)
		GetImage.remove(file_path)
		

	@commands.command(pass_context=True)
	async def embed(self, ctx, embed_type = "field", *, embed):
		"""Builds an embed using json formatting.

		Types:
		
		field
		text

		----------------------------------

		Limits      (All - owner only):

		title_max   (256)
		desc_max    (2048)
		field_max   (25)
		fname_max   (256)
		fval_max    (1024)
		foot_max    (2048)
		auth_max    (256)
		total_max   (6000)

		----------------------------------
		
		Options     (All):

		pm_after    (int - fields, or pages)
		pm_react    (str)
		title       (str)
		page_count  (bool)
		url         (str)
		description (str)
		image       (str)
		footer      (str or dict { text, icon_url })
		thumbnail   (str)
		author      (str, dict, or User/Member)
		color       (user/member)

		----------------------------------

		Options      (field only):

		fields       (list of dicts { name (str), value (str), inline (bool) })

		----------------------------------

		Options      (text only):

		desc_head    (str)
		desc_foot    (str)
		max_pages    (int)
		"""

		channel = ctx.message.channel
		author  = ctx.message.author
		server  = ctx.message.guild

		# Only allow owner to modify the limits
		isOwner = self.settings.isOwner(ctx.author)

		try:
			embed_dict = json.loads(embed)
		except Exception as e:
			await Message.EmbedText(title="Something went wrong...", description=str(e)).send(ctx)
			return
		
		# Only allow owner to modify the limits
		isOwner = self.settings.isOwner(ctx.author)
		if not isOwner:
			embed_dict["title_max"] = 256
			embed_dict["desc_max"] = 2048
			embed_dict["field_max"] = 25
			embed_dict["fname_max"] = 256
			embed_dict["fval_max"] = 1024
			embed_dict["foot_max"] = 2048
			embed_dict["auth_max"] = 256
			embed_dict["total_max"] = 6000

		try:
			if embed_type.lower() == "field":
				await Message.Embed(**embed_dict).send(ctx)
			elif embed_type.lower() == "text":
				await Message.EmbedText(**embed_dict).send(ctx)
			else:
				await Message.EmbedText(title="Something went wrong...", description="\"{}\" is not one of the available embed types...".format(embed_type)).send(ctx)
		except Exception as e:
			try:
				e = str(e)
			except:
				e = "An error occurred :("
			await Message.EmbedText(title="Something went wrong...", description=e).send(ctx)


	@commands.command(pass_context=True)
	async def speedtest(self, ctx):
		"""Run a network speed test (owner only)."""

		channel = ctx.message.channel
		author  = ctx.message.author
		server  = ctx.message.guild

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

		message = await channel.send('Running speed test...')
		st = pyspeedtest.SpeedTest()
		msg = '**Speed Test Results:**\n'
		msg += '```\n'
		msg += '    Ping: {}\n'.format(round(st.ping(), 2))
		msg += 'Download: {}MB/s\n'.format(round(st.download()/1024/1024, 2))
		msg += '  Upload: {}MB/s```'.format(round(st.upload()/1024/1024, 2))
		await message.edit(content=msg)
		
		
	@commands.command(pass_context=True)
	async def adminunlim(self, ctx, *, yes_no : str = None):
		"""Sets whether or not to allow unlimited xp to admins (owner only)."""

		# Check for admin status
		isAdmin = ctx.author.permissions_in(ctx.channel).administrator
		if not isAdmin:
			checkAdmin = self.settings.getServerStat(ctx.guild, "AdminArray")
			for role in ctx.author.roles:
				for aRole in checkAdmin:
					# Get the role that corresponds to the id
					if str(aRole['ID']) == str(role.id):
						isAdmin = True
		if not isAdmin:
			await ctx.send("You do not have permission to use this command.")
			return

		setting_name = "Admin unlimited xp"
		setting_val  = "AdminUnlimited"

		current = self.settings.getServerStat(ctx.guild, setting_val)
		if yes_no == None:
			# Output what we have
			if current:
				msg = "{} currently *enabled.*".format(setting_name)
			else:
				msg = "{} currently *disabled.*".format(setting_name)
		elif yes_no.lower() in [ "yes", "on", "true", "enabled", "enable" ]:
			yes_no = True
			if current == True:
				msg = '{} remains *enabled*.'.format(setting_name)
			else:
				msg = '{} is now *enabled*.'.format(setting_name)
		elif yes_no.lower() in [ "no", "off", "false", "disabled", "disable" ]:
			yes_no = False
			if current == False:
				msg = '{} remains *disabled*.'.format(setting_name)
			else:
				msg = '{} is now *disabled*.'.format(setting_name)
		else:
			msg = "That's not a valid setting."
			yes_no = current
		if not yes_no == None and not yes_no == current:
			self.settings.setServerStat(ctx.guild, setting_val, yes_no)
		await ctx.send(msg)
		
	
	@commands.command(pass_context=True)
	async def basadmin(self, ctx, *, yes_no : str = None):
		"""Sets whether or not to treat bot-admins as admins with regards to xp (admin only)."""

		# Check for admin status
		isAdmin = ctx.author.permissions_in(ctx.channel).administrator
		if not isAdmin:
			checkAdmin = self.settings.getServerStat(ctx.guild, "AdminArray")
			for role in ctx.author.roles:
				for aRole in checkAdmin:
					# Get the role that corresponds to the id
					if str(aRole['ID']) == str(role.id):
						isAdmin = True
		if not isAdmin:
			await ctx.send("You do not have permission to use this command.")
			return

		setting_name = "Bot-admin as admin"
		setting_val  = "BotAdminAsAdmin"

		current = self.settings.getServerStat(ctx.guild, setting_val)
		if yes_no == None:
			# Output what we have
			if current:
				msg = "{} currently *enabled.*".format(setting_name)
			else:
				msg = "{} currently *disabled.*".format(setting_name)
		elif yes_no.lower() in [ "yes", "on", "true", "enabled", "enable" ]:
			yes_no = True
			if current == True:
				msg = '{} remains *enabled*.'.format(setting_name)
			else:
				msg = '{} is now *enabled*.'.format(setting_name)
		elif yes_no.lower() in [ "no", "off", "false", "disabled", "disable" ]:
			yes_no = False
			if current == False:
				msg = '{} remains *disabled*.'.format(setting_name)
			else:
				msg = '{} is now *disabled*.'.format(setting_name)
		else:
			msg = "That's not a valid setting."
			yes_no = current
		if not yes_no == None and not yes_no == current:
			self.settings.setServerStat(ctx.guild, setting_val, yes_no)
		await ctx.send(msg)
		
		
	@commands.command(pass_context=True)
	async def joinpm(self, ctx, *, yes_no : str = None):
		"""Sets whether or not to pm the rules to new users when they join (bot-admin only)."""

		# Check for admin status
		isAdmin = ctx.author.permissions_in(ctx.channel).administrator
		if not isAdmin:
			checkAdmin = self.settings.getServerStat(ctx.guild, "AdminArray")
			for role in ctx.author.roles:
				for aRole in checkAdmin:
					# Get the role that corresponds to the id
					if str(aRole['ID']) == str(role.id):
						isAdmin = True
		if not isAdmin:
			await ctx.send("You do not have permission to use this command.")
			return

		setting_name = "New user pm"
		setting_val  = "JoinPM"

		current = self.settings.getServerStat(ctx.guild, setting_val)
		if yes_no == None:
			if current:
				msg = "{} currently *enabled.*".format(setting_name)
			else:
				msg = "{} currently *disabled.*".format(setting_name)
		elif yes_no.lower() in [ "yes", "on", "true", "enabled", "enable" ]:
			yes_no = True
			if current == True:
				msg = '{} remains *enabled*.'.format(setting_name)
			else:
				msg = '{} is now *enabled*.'.format(setting_name)
		elif yes_no.lower() in [ "no", "off", "false", "disabled", "disable" ]:
			yes_no = False
			if current == False:
				msg = '{} remains *disabled*.'.format(setting_name)
			else:
				msg = '{} is now *disabled*.'.format(setting_name)
		else:
			msg = "That's not a valid setting."
			yes_no = current
		if not yes_no == None and not yes_no == current:
			self.settings.setServerStat(ctx.guild, setting_val, yes_no)
		await ctx.send(msg)


	@commands.command(pass_context=True)
	async def avatar(self, ctx, filename = None):
		"""Sets the bot's avatar (owner only)."""

		channel = ctx.message.channel
		author  = ctx.message.author
		server  = ctx.message.guild

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

		if filename is None and not len(ctx.message.attachments):
			m = await ctx.send("Removing avatar...")
			try:
				await self.bot.user.edit(avatar=None)
			except discord.errors.HTTPException as e:
				await m.edit(content="Looks like I can't do that right now.  Try again later!")
				return
			await m.edit(content='Avatar removed!')
			# await self.bot.edit_profile(avatar=None)
			return
		
		# Check if attachment
		if filename == None:
			filename = ctx.message.attachments[0].url

		# Let's check if the "url" is actually a user
		test_user = DisplayName.memberForName(filename, ctx.guild)
		if test_user:
			# Got a user!
			filename = test_user.avatar_url if len(test_user.avatar_url) else test_user.default_avatar_url
			filename = filename.split("?size=")[0]

		# Check if we created a temp folder for this image
		isTemp = False

		status = await channel.send('Checking if url (and downloading if valid)...')

		# File name is *something* - let's first check it as a url, then a file
		extList = ["jpg", "jpeg", "png", "gif", "tiff", "tif"]
		if GetImage.get_ext(filename).lower() in extList:
			# URL has an image extension
			file = await GetImage.download(filename)
			if file:
				# we got a download - let's reset and continue
				filename = file
				isTemp = True

		if not os.path.isfile(filename):
			if not os.path.isfile('./{}'.format(filename)):
				await status.edit(content='*{}* doesn\'t exist absolutely, or in my working directory.'.format(filename))
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
			await status.edit(content='*{}* isn\'t a valid image format.'.format(filename))
			return

		wasConverted = False
		# Is an image PIL understands
		if not ext.lower == "png":
			# Not a PNG - let's convert
			await status.edit(content='Converting to png...')
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
		img.crop((dw, dh, w-dw, h-dh)).save(filename)

		await status.edit(content='Uploading and applying avatar...')
		with open(filename, 'rb') as f:
			newAvatar = f.read()
			try:
				await self.bot.user.edit(avatar=newAvatar)
			except discord.errors.HTTPException as e:
				await status.edit(content="Looks like I can't do that right now.  Try again later!")
				return
			# await self.bot.edit_profile(avatar=newAvatar)
		# Cleanup - try removing with shutil.rmtree, then with os.remove()
		await status.edit(content='Cleaning up...')
		if isTemp:
			GetImage.remove(filename)
		else:
			if wasConverted:
				os.remove(filename)
		await status.edit(content='Avatar set!')


	# Needs rewrite!
	@commands.command(pass_context=True)
	async def reboot(self, ctx, force = None):
		"""Reboots the bot (owner only)."""

		channel = ctx.message.channel
		author  = ctx.message.author
		server  = ctx.message.guild

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
		
		# Save the return channel and flush settings
		self.settings.serverDict["ReturnChannel"] = ctx.channel.id
		self.settings.flushSettings()

		quiet = False
		if force and force.lower() == 'force':
			quiet = True
		if not quiet:
			msg = 'Flushed settings to disk.\nRebooting...'
			await ctx.channel.send(msg)
		# Logout, stop the event loop, close the loop, quit
		for task in asyncio.Task.all_tasks():
			try:
				task.cancel()
			except:
				continue
		try:
			await self.bot.logout()
			self.bot.loop.stop()
			self.bot.loop.close()
		except:
			pass
		# Kill this process
		os._exit(2)


	@commands.command(pass_context=True)
	async def shutdown(self, ctx, force = None):
		"""Shuts down the bot (owner only)."""

		channel = ctx.message.channel
		author  = ctx.message.author
		server  = ctx.message.guild

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
		
		self.settings.flushSettings()

		quiet = False
		if force and force.lower() == 'force':
			quiet = True
		if not quiet:
			msg = 'Flushed settings to disk.\nShutting down...'
			await ctx.channel.send(msg)
		# Logout, stop the event loop, close the loop, quit
		for task in asyncio.Task.all_tasks():
			try:
				task.cancel()
			except Exception:
				continue
		try:
			await self.bot.logout()
			self.bot.loop.stop()
			self.bot.loop.close()
		except Exception:
			pass
		# Kill this process
		os._exit(3)
			

	@commands.command(pass_context=True)
	async def servers(self, ctx):
		"""Lists the number of servers I'm connected to!"""

		channel = ctx.message.channel
		author  = ctx.message.author
		server  = ctx.message.guild
		
		total = 0
		for server in self.bot.guilds:
			total += 1
		if total == 1:
			msg = 'I am a part of *1* server!'
		else:
			msg = 'I am a part of *{}* servers!'.format(total)
		await channel.send(msg)


	async def _update_status(self):
		# Helper method to update the status based on the server dict
		# Get ready - play game!
		game   = self.settings.serverDict.get("Game", None)
		url    = self.settings.serverDict.get("Stream", None)
		t      = self.settings.serverDict.get("Type", 0)
		status = self.settings.serverDict.get("Status", None)
		# Set status
		if status == "2":
			s = discord.Status.idle
		elif status == "3":
			s = discord.Status.dnd
		elif status == "4":
			s = discord.Status.invisible
		else:
			# Online when in doubt
			s = discord.Status.online
		dgame = discord.Game(name=game, url=url, type=t) if game else None
		await self.bot.change_presence(status=s, game=dgame)
		
		
	@commands.command(pass_context=True)
	async def pres(self, ctx, playing_type="0", status_type="online", game=None, url=None):
		"""Changes the bot's presence (owner-only).
	
		Playing type options are:
		
		0. Playing (or None without game)
		1. Streaming (requires valid twitch url)
		2. Listening
		3. Watching
		
		Status type options are:
		
		1. Online
		2. Idle
		3. DnD
		4. Invisible
		
		If any of the passed entries have spaces, they must be in quotes."""
		
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
		
		# Check playing type
		play = None
		play_string = ""
		if playing_type.lower() in [ "0", "play", "playing" ]:
			play = 0
			play_string = "Playing"
		elif playing_type.lower() in [ "1", "stream", "streaming" ]:
			play = 1
			play_string = "Streaming"
			if url == None or not "twitch.tv" in url.lower():
				# Guess what - you failed!! :D
				await ctx.send("You need a valid twitch.tv url to set a streaming status!")
				return
		elif playing_type.lower() in [ "2", "listen", "listening" ]:
			play = 2
			play_string = "Listening"
		elif playing_type.lower() in [ "3", "watch", "watching" ]:
			play = 3
			play_string = "Watching"
		# Verify we got something
		if play == None:
			# NOooooooooaooOOooOOooope.
			await ctx.send("Playing type is invalid!")
			return
		
		# Clear the URL if we're not streaming
		if not play == 1:
			url = None
		
		# Check status type
		stat = None
		stat_string = ""
		if status_type.lower() in [ "1", "online", "here", "green" ]:
			stat = "1"
			stat_string = "Online"
		elif status_type.lower() in [ "2", "idle", "away", "gone", "yellow" ]:
			stat = "2"
			stat_string = "Idle"
		elif status_type.lower() in [ "3", "dnd", "do not disturb", "don't disturb", "busy", "red" ]:
			stat = "3"
			stat_string = "Do Not Disturb"
		elif status_type.lower() in [ "4", "offline", "invisible", "ghost", "gray", "black" ]:
			stat = "4"
			stat_string = "Invisible"
		# Verify we got something
		if stat == None:
			# OHMYGODHOWHARDISITTOFOLLOWDIRECTIONS?!?!?
			await ctx.send("Status type is invalid!")
			return
		
		# Here, we assume that everything is A OK.  Peachy keen.
		# Set the shiz and move along
		self.settings.serverDict["Game"]   = game
		self.settings.serverDict["Stream"] = url
		self.settings.serverDict["Status"] = stat
		self.settings.serverDict["Type"]   = play
		
		# Actually update our shit
		await self._update_status()
		
		# Let's formulate a sexy little response concoction
		inline = True
		await Message.Embed(
			title="Presence Update",
			color=ctx.author,
			fields=[
				{ "name" : "Game",   "value" : str(game),   "inline" : inline },
				{ "name" : "Status", "value" : stat_string, "inline" : inline },
				{ "name" : "Type",   "value" : play_string, "inline" : inline },
				{ "name" : "URL",    "value" : str(url),    "inline" : inline }
			]
		).send(ctx)


	@commands.command(pass_context=True)
	async def status(self, ctx, status = None):
		"""Gets or sets the bot's online status (owner-only).
		Options are:
		1. Online
		2. Idle
		3. DnD
		4. Invisible"""

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

		if status == None:
			botmem = ctx.guild.get_member(self.bot.user.id)
			await ctx.send("I'm currently set to *{}!*".format(botmem.status))
			return

		stat_string = "1"
		if status == "1" or status.lower() == "online":
			s = discord.Status.online
			stat_name = "online"
		elif status == "2" or status.lower() == "idle" or status.lower() == "away" or status.lower() == "afk":
			stat_string = "2"
			s = discord.Status.idle
			stat_name = "idle"
		elif status == "3" or status.lower() == "dnd" or status.lower() == "do not disturb" or status.lower() == "don't disturb":
			stat_string = "3"
			s = discord.Status.dnd
			stat_name = "dnd"
		elif status == "4" or status.lower() == "offline" or status.lower() == "invisible":
			stat_string = "4"
			s = discord.Status.invisible
			stat_name = "invisible"
		else:
			await ctx.send("That is not a valid status.")
			return

		self.settings.serverDict["Status"] = stat_string
		await self._update_status()
		await ctx.send("Status changed to *{}!*".format(stat_name))
			
		
	@commands.command(pass_context=True)
	async def playgame(self, ctx, *, game : str = None):
		"""Sets the playing status of the bot (owner-only)."""

		channel = ctx.message.channel
		author  = ctx.message.author
		server  = ctx.message.guild

		# Check if we're suppressing @here and @everyone mentions
		if self.settings.getServerStat(ctx.message.guild, "SuppressMentions"):
			suppress = True
		else:
			suppress = False

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

		if game == None:
			self.settings.serverDict['Game'] = None
			self.settings.serverDict['Stream'] = None
			self.settings.serverDict['Type'] = 0
			msg = 'Removing my playing status...'
			status = await channel.send(msg)

			await self._update_status()
			
			await status.edit(content='Playing status removed!')
			return

		self.settings.serverDict['Game'] = game
		self.settings.serverDict['Stream'] = None
		self.settings.serverDict['Type'] = 0
		msg = 'Setting my playing status to *{}*...'.format(game)
		# Check for suppress
		if suppress:
			msg = Nullify.clean(msg)
		status = await channel.send(msg)

		await self._update_status()
		# Check for suppress
		if suppress:
			game = Nullify.clean(game)
		await status.edit(content='Playing status set to *{}!*'.format(game))
		
	@commands.command(pass_context=True)
	async def watchgame(self, ctx, *, game : str = None):
		"""Sets the watching status of the bot (owner-only)."""

		channel = ctx.message.channel
		author  = ctx.message.author
		server  = ctx.message.guild

		# Check if we're suppressing @here and @everyone mentions
		if self.settings.getServerStat(ctx.message.guild, "SuppressMentions"):
			suppress = True
		else:
			suppress = False

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

		if game == None:
			self.settings.serverDict['Game'] = None
			self.settings.serverDict['Stream'] = None
			self.settings.serverDict['Type'] = 0
			msg = 'Removing my watching status...'
			status = await channel.send(msg)

			await self._update_status()
			
			await status.edit(content='Watching status removed!')
			return

		self.settings.serverDict['Game'] = game
		self.settings.serverDict['Stream'] = None
		self.settings.serverDict['Type'] = 3
		msg = 'Setting my watching status to *{}*...'.format(game)
		# Check for suppress
		if suppress:
			msg = Nullify.clean(msg)
		status = await channel.send(msg)

		await self._update_status()
		# Check for suppress
		if suppress:
			game = Nullify.clean(game)
		await status.edit(content='Watching status set to *{}!*'.format(game))
		
	@commands.command(pass_context=True)
	async def listengame(self, ctx, *, game : str = None):
		"""Sets the listening status of the bot (owner-only)."""

		channel = ctx.message.channel
		author  = ctx.message.author
		server  = ctx.message.guild

		# Check if we're suppressing @here and @everyone mentions
		if self.settings.getServerStat(ctx.message.guild, "SuppressMentions"):
			suppress = True
		else:
			suppress = False

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

		if game == None:
			self.settings.serverDict['Game'] = None
			self.settings.serverDict['Stream'] = None
			self.settings.serverDict['Type'] = 0
			msg = 'Removing my listening status...'
			status = await channel.send(msg)

			await self._update_status()
			
			await status.edit(content='Listening status removed!')
			return

		self.settings.serverDict['Game'] = game
		self.settings.serverDict['Stream'] = None
		self.settings.serverDict['Type'] = 2
		msg = 'Setting my listening status to *{}*...'.format(game)
		# Check for suppress
		if suppress:
			msg = Nullify.clean(msg)
		status = await channel.send(msg)

		await self._update_status()
		# Check for suppress
		if suppress:
			game = Nullify.clean(game)
		await status.edit(content='Listening status set to *{}!*'.format(game))


	@commands.command(pass_context=True)
	async def streamgame(self, ctx, url = None, *, game : str = None):
		"""Sets the streaming status of the bot, requires the url and the game (owner-only)."""

		channel = ctx.message.channel
		author  = ctx.message.author
		server  = ctx.message.guild

		# Check if we're suppressing @here and @everyone mentions
		if self.settings.getServerStat(ctx.message.guild, "SuppressMentions"):
			suppress = True
		else:
			suppress = False

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

		if url == None:
			self.settings.serverDict['Game'] = None
			self.settings.serverDict['Stream'] = None
			self.settings.serverDict['Type'] = 0
			msg = 'Removing my streaming status...'
			status = await channel.send(msg)

			await self._update_status()
			
			await status.edit(content='Streaming status removed!')
			return

		if game == None:
			# We're missing parts
			msg = "Usage: `{}streamgame [url] [game]`".format(ctx.prefix)
			await ctx.send(msg)
			return

		# Verify url
		matches = re.finditer(self.regex, url)
		match_url = None
		for match in matches:
			match_url = match.group(0)
		
		if not match_url:
			# No valid url found
			await ctx.send("Url is invalid!")
			return

		self.settings.serverDict['Game'] = game
		self.settings.serverDict['Stream'] = url
		self.settings.serverDict['Type'] = 1
		msg = 'Setting my streaming status to *{}*...'.format(game)
		# Check for suppress
		if suppress:
			msg = Nullify.clean(msg)
		status = await channel.send(msg)

		await self._update_status()
		# Check for suppress
		if suppress:
			game = Nullify.clean(game)
		await status.edit(content='Streaming status set to *{}* at `{}`!'.format(game, url))
	

	@commands.command(pass_context=True)
	async def setbotparts(self, ctx, *, parts : str = None):
		"""Set the bot's parts - can be a url, formatted text, or nothing to clear."""
		
		# Check if we're suppressing @here and @everyone mentions
		if self.settings.getServerStat(ctx.message.guild, "SuppressMentions"):
			suppress = True
		else:
			suppress = False

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

		channel = ctx.message.channel
		author  = ctx.message.author
		server  = ctx.message.guild

		if not parts:
			parts = ""
			
		self.settings.setGlobalUserStat(self.bot.user, "Parts", parts)
		msg = '*{}\'s* parts have been set to:\n{}'.format(DisplayName.serverNick(self.bot.user, server), parts)
		# Check for suppress
		if suppress:
			msg = Nullify.clean(msg)
		await channel.send(msg)

	@commands.command(pass_context=True)
	async def source(self, ctx):
		"""Link the github source."""
		source = "https://github.com/corpnewt/CorpBot.py"
		msg = '**My insides are located at:**\n\n{}'.format(source)
		await ctx.channel.send(msg)

	@commands.command(pass_context=True)
	async def block(self, ctx, *, server : str = None):
		"""Blocks the bot from joining a server - takes either a name or an id (owner-only).
		Can also take the id or case-sensitive name + descriminator of the owner (eg. Bob#1234)."""
		# Check if we're suppressing @here and @everyone mentions
		if self.settings.getServerStat(ctx.message.guild, "SuppressMentions"):
			suppress = True
		else:
			suppress = False

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
		
		if server == None:
			# No server provided
			await ctx.send("Usage: `{}block [server name/id or owner name#desc/id]`".format(ctx.prefix))
			return
		
		try:
			serverList = self.settings.serverDict['BlockedServers']
		except KeyError:
			self.settings.serverDict['BlockedServers'] = []
			serverList = self.settings.serverDict['BlockedServers']

		for serv in serverList:
			if str(serv).lower() == server.lower():
				# Found a match - already blocked.
				msg = "*{}* is already blocked!".format(serv)
				if suppress:
					msg = Nullify.clean(msg)
				await ctx.channel.send(msg)
				return
		
		# Not blocked
		self.settings.serverDict['BlockedServers'].append(server)
		msg = "*{}* now blocked!".format(server)
		# Check for suppress
		if suppress:
			msg = Nullify.clean(msg)
		await ctx.channel.send(msg)


	@commands.command(pass_context=True)
	async def unblock(self, ctx, *, server : str = None):
		"""Unblocks a server or owner (owner-only)."""
		# Check if we're suppressing @here and @everyone mentions
		if self.settings.getServerStat(ctx.message.guild, "SuppressMentions"):
			suppress = True
		else:
			suppress = False

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
		
		if server == None:
			# No server provided
			await ctx.send("Usage: `{}unblock [server name/id or owner name#desc/id]`".format(ctx.prefix))
			return
		
		try:
			serverList = self.settings.serverDict['BlockedServers']
		except KeyError:
			self.settings.serverDict['BlockedServers'] = []
			serverList = self.settings.serverDict['BlockedServers']

		for serv in serverList:
			if str(serv).lower() == server.lower():
				# Found a match - already blocked.
				self.settings.serverDict['BlockedServers'].remove(serv)
				msg = "*{}* unblocked!".format(serv)
				if suppress:
					msg = Nullify.clean(msg)
				await ctx.channel.send(msg)
				return
		
		# Not found
		msg = "I couldn't find *{}* in my blocked list.".format(server)
		# Check for suppress
		if suppress:
			msg = Nullify.clean(msg)
		await ctx.channel.send(msg)


	@commands.command(pass_context=True)
	async def unblockall(self, ctx):
		"""Unblocks all blocked servers and owners (owner-only)."""
		# Check if we're suppressing @here and @everyone mentions
		if self.settings.getServerStat(ctx.message.guild, "SuppressMentions"):
			suppress = True
		else:
			suppress = False

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
		
		self.settings.serverDict['BlockedServers'] = []

		await ctx.channel.send("*All* servers and owners unblocked!")


	@commands.command(pass_context=True)
	async def blocked(self, ctx):
		"""Lists all blocked servers and owners (owner-only)."""
		# Check if we're suppressing @here and @everyone mentions
		if self.settings.getServerStat(ctx.message.guild, "SuppressMentions"):
			suppress = True
		else:
			suppress = False

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

		try:
			serverList = self.settings.serverDict['BlockedServers']
		except KeyError:
			self.settings.serverDict['BlockedServers'] = []
			serverList = self.settings.serverDict['BlockedServers']

		if not len(serverList):
			msg = "There are no blocked servers or owners!"
		else:
			msg = "__Currently Blocked:__\n\n{}".format(', '.join(serverList))

		# Check for suppress
		if suppress:
			msg = Nullify.clean(msg)
		await ctx.channel.send(msg)
			


	@commands.command(pass_context=True)
	async def cloc(self, ctx):
		"""Outputs the total count of lines of code in the currently installed repo."""
		# Script pulled and edited from https://github.com/kyco/python-count-lines-of-code/blob/python3/cloc.py
		
		# Get our current working directory - should be the bot's home
		path = os.getcwd()
		
		# Set up some lists
		extensions = []
		code_count = []
		include = ['py','bat','sh']
		
		# Get the extensions - include our include list
		extensions = self.get_extensions(path, include)
		
		for run in extensions:
			extension = "*."+run
			temp = 0
			for root, dir, files in os.walk(path):
				for items in fnmatch.filter(files, extension):
					value = root + "/" + items
					temp += sum(+1 for line in open(value, 'rb'))
			code_count.append(temp)
			pass
		
		# Set up our output
		msg = 'Some poor soul took the time to sloppily write the following to bring me life:\n```\n'
		padTo = 0
		for idx, val in enumerate(code_count):
			# Find out which has the longest
			tempLen = len(str('{:,}'.format(code_count[idx])))
			if tempLen > padTo:
				padTo = tempLen
		for idx, val in enumerate(code_count):
			lineWord = 'lines'
			if code_count[idx] == 1:
				lineWord = 'line'
			# Setup a right-justified string padded with spaces
			numString = str('{:,}'.format(code_count[idx])).rjust(padTo, ' ')
			msg += numString + " " + lineWord + " of " + extensions[idx] + "\n"
			# msg += extensions[idx] + ": " + str(code_count[idx]) + ' ' + lineWord + '\n'
			# print(extensions[idx] + ": " + str(code_count[idx]))
			pass
		msg += '```'
		await ctx.channel.send(msg)
		
	@cloc.error
	async def cloc_error(self, ctx, error):
		# do stuff
		msg = 'cloc Error: {}'.format(ctx)
		await error.channel.send(msg)

	# Helper function to get extensions
	def get_extensions(self, path, excl):
		extensions = []
		for root, dir, files in os.walk(path):
			for items in fnmatch.filter(files, "*"):
				temp_extensions = items.rfind(".")
				ext = items[temp_extensions+1:]
				if ext not in extensions:
					if ext in excl:
						extensions.append(ext)
						pass
		return extensions
