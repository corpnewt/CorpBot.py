import asyncio, discord, os, re, psutil, platform, time, sys, fnmatch, subprocess, speedtest, json, struct, shutil, tempfile
from   PIL         import Image
from   discord.ext import commands
from   Cogs import Utils, Settings, DisplayName, ReadableTime, GetImage, ProgressBar, UserTime, Message, DL
try:
	from urllib.parse import urlparse
except ImportError:
	from urlparse import urlparse

def setup(bot):
	# Add the bot and deps
	settings = bot.get_cog("Settings")
	bot.add_cog(Bot(bot, settings, sys.argv[0], 'python'))

# This is the Bot module - it contains things like nickname, status, etc

class Bot(commands.Cog):

	# Init with the bot reference, and a reference to the settings var
	def __init__(self, bot, settings, path = None, pypath = None):
		self.bot = bot
		self.settings = settings
		self.startTime = int(time.time())
		self.path = path
		self.pypath = pypath
		self.regex = re.compile(r"(http|ftp|https)://([\w_-]+(?:(?:\.[\w_-]+)+))([\w.,@?^=%&:/~+#-]*[\w@?^=%&/~+#-])?")
		self.is_current = False
		global Utils, DisplayName
		Utils = self.bot.get_cog("Utils")
		DisplayName = self.bot.get_cog("DisplayName")
		
	def _is_submodule(self, parent, child):
		return parent == child or child.startswith(parent + ".")

	@commands.Cog.listener()
	async def on_unloaded_extension(self, ext):
		# Called to shut things down
		if not self._is_submodule(ext.__name__, self.__module__):
			return
		self.is_current = False

	@commands.Cog.listener()
	async def on_loaded_extension(self, ext):
		# See if we were loaded
		if not self._is_submodule(ext.__name__, self.__module__):
			return
		await self.bot.wait_until_ready()
		self.is_current = True
		self.bot.loop.create_task(self.status_loop())

	async def status_loop(self):
		# Helper method to loop through and ensure the status remains
		while not self.bot.is_closed():
			try:
				if not self.is_current:
					# Bail if we're not the current instance
					return
				await self._update_status()
			except Exception as e:
				print(str(e))
			await asyncio.sleep(3600) # runs only every 60 minutes (3600 seconds)

	async def onserverjoin(self, server):
		# Iterate the blocked list and see if we are blocked
		serverList = self.settings.getGlobalStat('BlockedServers',[])
		for serv in serverList:
			serverName = str(serv).lower()
			try:
				serverID = int(serv)
			except Exception:
				serverID = None
			if serverName == server.name.lower() or serverID == server.id:
				# Found it
				try:
					await server.leave()
				except:
					pass
				return True
			# Check for owner name and id quick
			# Name *MUST* be case-sensitive and have the discriminator for safety
			namecheck = server.owner.name + "#" + str(server.owner.discriminator)
			if serv == namecheck or serverID == server.owner.id:
				# Got the owner
				try:
					await server.leave()
				except:
					pass
				return True
		return False
	
	@commands.command(pass_context=True)
	async def botinfo(self, ctx):
		"""Lists some general stats about the bot."""
		bot_member = self.bot.user if not ctx.guild else ctx.guild.get_member(self.bot.user.id)
		color = bot_member if isinstance(bot_member,discord.Member) else None
		message = await Message.EmbedText(title="Gathering info...", color=color).send(ctx)
		
		# Get guild count
		guild_count = "{:,}".format(len(self.bot.guilds))
		
		# Try to do this more efficiently, and faster
		total_members = [x.id for x in self.bot.get_all_members()]
		unique_members = set(total_members)
		if len(total_members) == len(unique_members):
			member_count = "{:,}".format(len(total_members))
		else:
			member_count = "{:,} ({:,} unique)".format(len(total_members), len(unique_members))
			
		# Get commands/cogs count
		cog_amnt  = 0
		empty_cog = 0
		for cog in self.bot.cogs:
			visible = []
			for c in self.bot.get_cog(cog).get_commands():
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
		created_at = joined_at = "Unknown"
		if bot_member.created_at:
			ts = int(bot_member.created_at.timestamp())
			created_at = "<t:{}> (<t:{}:R>)".format(ts,ts)
		
		# Get localized joined time if in a server
		if isinstance(bot_member,discord.Member) and bot_member.joined_at:
			ts = int(bot_member.joined_at.timestamp())
			joined_at = "<t:{}> (<t:{}:R>)".format(ts,ts)
		
		# Get the current prefix
		prefix = await self.bot.command_prefix(self.bot, ctx.message)
		prefix = ", ".join([x for x in prefix if not x == "<@!{}> ".format(self.bot.user.id)])

		# Get the owners
		ownerList = self.settings.getGlobalStat('Owner',[])
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
		avatar = Utils.get_avatar(bot_member)
		
		# Build the embed
		fields = [
			{"name":"Members","value":member_count,"inline":True},
			{"name":"Servers","value":guild_count,"inline":True},
			{"name":"Commands","value":command_count + " (in {})".format(cog_count),"inline":True},
			{"name":"Created","value":created_at,"inline":True},
			{"name":"Owners","value":owners,"inline":True},
			{"name":"Prefixes","value":prefix,"inline":True},
			{"name":"Shard Count","value":self.bot.shard_count,"inline":True}
		]
		if isinstance(bot_member,discord.Member):
			fields.append({"name":"Joined","value":joined_at,"inline":True})
			# Get status
			status_text = ":green_heart:"
			if bot_member.status == discord.Status.offline:
				status_text = ":black_heart:"
			elif bot_member.status == discord.Status.dnd:
				status_text = ":heart:"
			elif bot_member.status == discord.Status.idle:
				status_text = ":yellow_heart:"
			fields.append({"name":"Status","value":status_text,"inline":True})

			if bot_member.activity and bot_member.activity.name:
				play_list = [ "Playing", "Streaming", "Listening to", "Watching" ]
				try:
					play_string = play_list[bot_member.activity.type]
				except:
					play_string = "Playing"
				fields.append({"name":play_string,"value":str(bot_member.activity.name),"inline":True})
				if bot_member.activity.type == 1:
					# Add the URL too
					fields.append({"name":"Stream URL","value":"[Watch Now]({})".format(bot_member.activity.url),"inline":True})
		# Update the embed
		await Message.Embed(
			title=DisplayName.name(bot_member) + " Info",
			color=color,
			description="Current Bot Information",
			fields=fields,
			thumbnail=avatar
		).edit(ctx, message)

	@commands.command(pass_context=True)
	async def ping(self, ctx):
		"""Feeling lonely?"""
		before_typing = time.monotonic()
		await ctx.trigger_typing()
		after_typing = time.monotonic()
		ms = int((after_typing - before_typing) * 1000)
		msg = '*{}*, ***PONG!*** (~{}ms)'.format(ctx.message.author.mention, ms)
		await ctx.send(msg,allowed_mentions=discord.AllowedMentions.all())
		
	@commands.command(pass_context=True)
	async def nickname(self, ctx, *, name : str = None):
		"""Set the bot's nickname (admin-only)."""
		
		if not await Utils.is_admin_reply(ctx): return
		
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
		if not self.settings.getGlobalStat("HideHostname",False):
			msg += 'Hostname : {}\n'.format(platform.node())
		msg += 'Language : Python {}.{}.{} {} ({} bit)\n'.format(pythonMajor, pythonMinor, pythonMicro, pythonRelease, pyBit)
		msg += 'Commit   : {}\n\n'.format(git_head_hash.decode("utf-8"))
		msg += ProgressBar.center('{}% of {} {}'.format(cpuUsage, cpuThred, threadString), 'CPU') + '\n'
		msg += ProgressBar.makeBar(int(round(cpuUsage))) + "\n\n"
		msg += ProgressBar.center('{} ({}%) of {}GB used'.format(memUsedGB, memPerc, memTotalGB), 'RAM') + '\n'
		msg += ProgressBar.makeBar(int(round(memPerc))) + "\n\n"
		msg += '{} uptime```'.format(timeString)

		await message.edit(content=msg)

	@commands.command()
	async def hidehostname(self, ctx, *, yes_no = None):
		"""Queries or turns on/off hostname hiding in the hostinfo command (owner-only)."""
		if not await Utils.is_owner_reply(ctx): return
		await ctx.send(Utils.yes_no_setting(
			ctx,
			"Hostname hiding in `hostinfo`".format(ctx.prefix),
			"HideHostname",
			yes_no,
			default=False,
			is_global=True
		))
		
	@commands.command(pass_context=True)
	async def getimage(self, ctx, *, image):
		"""Tests downloading - owner only"""
		# Only allow owner to modify the limits
		if not await Utils.is_owner_reply(ctx): return
		
		mess = await Message.Embed(title="Test", description="Downloading file...").send(ctx)
		file_path = await GetImage.download(image)
		mess = await Message.Embed(title="Test", description="Uploading file...").edit(ctx, mess)
		await Message.EmbedText(title="Image", file=file_path).edit(ctx, mess)
		GetImage.remove(file_path)

	@commands.command(pass_context=True)
	async def speedtest(self, ctx):
		"""Run a network speed test (owner only)."""
		if not await Utils.is_owner_reply(ctx): return

		message = await ctx.send('Running speed test...')
		try:
			st = speedtest.Speedtest()
			st.get_best_server()
			l = asyncio.get_event_loop()
			msg = '**Speed Test Results:**\n'
			msg += '```\n'
			await message.edit(content="Running speed test...\n- Downloading...")
			d = await self.bot.loop.run_in_executor(None, st.download)
			msg += '    Ping: {} ms\nDownload: {} Mb/s\n'.format(round(st.results.ping, 2), round(d/1024/1024, 2))
			await message.edit(content="Running speed test...\n- Downloading...\n- Uploading...")
			u = await self.bot.loop.run_in_executor(None, st.upload)
			msg += '  Upload: {} Mb/s```'.format(round(u/1024/1024, 2))
			await message.edit(content=msg)
		except Exception as e:
			await message.edit(content="Speedtest Error: {}".format(str(e)))
		
	@commands.command(pass_context=True)
	async def adminunlim(self, ctx, *, yes_no : str = None):
		"""Sets whether or not to allow unlimited xp to admins (bot-admin only)."""
		if not await Utils.is_bot_admin_reply(ctx): return
		await ctx.send(Utils.yes_no_setting(ctx,"Admin unlimited xp","AdminUnlimited",yes_no))
	
	@commands.command(pass_context=True)
	async def basadmin(self, ctx, *, yes_no : str = None):
		"""Sets whether or not to treat bot-admins as admins with regards to xp (admin only)."""
		if not await Utils.is_bot_admin_reply(ctx): return
		await ctx.send(Utils.yes_no_setting(ctx,"Bot-admin as admin","BotAdminAsAdmin",yes_no))
		
	@commands.command(pass_context=True)
	async def joinpm(self, ctx, *, yes_no : str = None):
		"""Sets whether or not to pm the rules to new users when they join (bot-admin only)."""
		if not await Utils.is_bot_admin_reply(ctx): return
		await ctx.send(Utils.yes_no_setting(ctx,"New user pm","JoinPM",yes_no))

	@commands.command(pass_context=True)
	async def avatar(self, ctx, filename = None):
		"""Sets the bot's avatar (owner only)."""
		if not await Utils.is_owner_reply(ctx): return

		if filename is None and not len(ctx.message.attachments):
			m = await ctx.send("Removing avatar...")
			try:
				await self.bot.user.edit(avatar=None)
			except discord.errors.HTTPException as e:
				return await m.edit(content="Looks like I can't do that right now.  Try again later!")
			return await m.edit(content='Avatar removed!')
		
		# Check if attachment
		if filename == None:
			filename = ctx.message.attachments[0].url

		# Let's check if the "url" is actually a user
		test_user = DisplayName.memberForName(filename, ctx.guild)
		if test_user:
			# Got a user!
			filename = Utils.get_avatar(test_user)
		# Ensure string
		filename = str(filename)

		# Check if we created a temp folder for this image
		isTemp = False
		status = await ctx.send('Checking if url (and downloading if valid)...')

		# File name is *something* - let's first check it as a url, then a file
		extList = ["jpg", "jpeg", "png", "gif", "tiff", "tif", "webp"]
		if GetImage.get_ext(filename).lower() in extList:
			# URL has an image extension
			f = await GetImage.download(filename)
			if f:
				# we got a download - let's reset and continue
				filename = f
				isTemp = True

		if not os.path.isfile(filename):
			if not os.path.isfile('./{}'.format(filename)):
				return await status.edit(content='*{}* doesn\'t exist absolutely, or in my working directory.'.format(filename))
			else:
				# Local file name
				filename = './{}'.format(filename)
		
		# File exists - check if image
		img = Image.open(filename)
		ext = img.format

		if not ext:
			# File isn't a valid image
			return await status.edit(content='*{}* isn\'t a valid image format.'.format(filename))

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
				return await status.edit(content="Looks like I can't do that right now.  Try again later!")
		# Cleanup - try removing with shutil.rmtree, then with os.remove()
		await status.edit(content='Cleaning up...')
		if isTemp:
			GetImage.remove(filename)
		else:
			if wasConverted:
				os.remove(filename)
		await status.edit(content='Avatar set!')

	@commands.command()
	async def setname(self, ctx, *, name = None):
		"""Sets the bot's name - may take awhile to reflect (owner only)."""

		if not await Utils.is_owner_reply(ctx): return

		if not name: return await ctx.send("Usage: `{}setname [new name]`".format(ctx.prefix))
		if name == self.bot.user.name: return await ctx.send("That's already my name!")

		try:
			await self.bot.user.edit(username=name)
		except discord.errors.HTTPException as e:
			return await ctx.send(content="Looks like I can't do that right now.  Try again later!")
		
		# Must have gone through - we'll state that it was updated, but may take awhile for the changes
		# to show up.
		return await ctx.send("Username updated - may take some time to show!")

	# Needs rewrite!
	@commands.command(pass_context=True)
	async def reboot(self, ctx):
		"""Reboots the bot (owner only)."""
		if not await Utils.is_owner_reply(ctx): return

		# Save the return channel and flush settings
		self.settings.setGlobalStat("ReturnChannel",ctx.channel.id)
		# Flush settings asynchronously here
		await ctx.invoke(self.settings.flush)
		await ctx.send("Rebooting...")
		# Logout, stop the event loop, close the loop, quit
		try:
			task_list = asyncio.Task.all_tasks()
		except AttributeError:
			task_list = asyncio.all_tasks()

		for task in task_list:
			try:
				task.cancel()
			except:
				continue
		try:
			await self.bot.close()
			self.bot.loop.stop()
			self.bot.loop.close()
		except:
			pass
		# Kill this process
		os._exit(2)

	@commands.command(pass_context=True)
	async def shutdown(self, ctx):
		"""Shuts down the bot (owner only)."""
		if not await Utils.is_owner_reply(ctx): return
		# Flush settings asynchronously here
		await ctx.invoke(self.settings.flush)
		await ctx.send("Shutting down...")
		# Logout, stop the event loop, close the loop, quit
		try:
			task_list = asyncio.Task.all_tasks()
		except AttributeError:
			task_list = asyncio.all_tasks()

		for task in task_list:
			try:
				task.cancel()
			except:
				continue
		try:
			await self.bot.close()
			self.bot.loop.stop()
			self.bot.loop.close()
		except:
			pass
		# Kill this process
		os._exit(3)		

	@commands.command(pass_context=True)
	async def servers(self, ctx):
		"""Lists the number of servers I'm connected to!"""
		await ctx.send("I am a part of *{}* server{}!".format(len(self.bot.guilds),"" if len(self.bot.guilds) == 1 else "s"))

	async def _update_status(self):
		# Helper method to update the status based on the server dict
		# Get ready - play game!
		game   = self.settings.getGlobalStat("Game", None)
		url    = self.settings.getGlobalStat("Stream", None)
		t      = self.settings.getGlobalStat("Type", 0)
		status = self.settings.getGlobalStat("Status", None)
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
		dgame = discord.Activity(name=game, url=url, type=t) if game else None
		await self.bot.change_presence(status=s, activity=dgame)
		
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
		if not await Utils.is_owner_reply(ctx): return
		
		# Check playing type
		play = None
		play_string = ""
		if playing_type.lower() in [ "0", "play", "playing" ]:
			play = 0
			play_string = "Playing"
		elif playing_type.lower() in [ "1", "stream", "streaming" ]:
			play = 1
			play_string = "Streaming"
			if url == None or not any("twitch.tv" in x.lower() for x in Utils.get_urls(url)):
				# Guess what - you failed!! :D
				return await ctx.send("You need a valid twitch.tv url to set a streaming status!")
		elif playing_type.lower() in [ "2", "listen", "listening" ]:
			play = 2
			play_string = "Listening"
		elif playing_type.lower() in [ "3", "watch", "watching" ]:
			play = 3
			play_string = "Watching"
		# Verify we got something
		if play == None:
			# NOooooooooaooOOooOOooope.
			return await ctx.send("Playing type is invalid!")
		
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
			return await ctx.send("Status type is invalid!")
		
		# Here, we assume that everything is A OK.  Peachy keen.
		# Set the shiz and move along
		self.settings.setGlobalStat("Game",game)
		self.settings.setGlobalStat("Stream",url)
		self.settings.setGlobalStat("Status",stat)
		self.settings.setGlobalStat("Type",play)
		
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
		if not await Utils.is_owner_reply(ctx): return

		if status == None:
			botmem = ctx.guild.get_member(self.bot.user.id)
			return await ctx.send("I'm currently set to *{}!*".format(botmem.status))

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
			return await ctx.send("That is not a valid status.")

		self.settings.setGlobalStat("Status",stat_string)
		await self._update_status()
		await ctx.send("Status changed to *{}!*".format(stat_name))
			
	async def set_status(self, ctx, status, status_name="Playing", status_type=0, status_url=None):
		# Only allow owner
		if not await Utils.is_owner_reply(ctx): return

		if status == status_url == None:
			self.settings.setGlobalStat('Game',None)
			self.settings.setGlobalStat('Stream',None)
			self.settings.setGlobalStat('Type',0)
			msg = 'Removing my {} status...'.format(status_name.lower())
			message = await ctx.send(msg)
			await self._update_status()
			return await message.edit(content='{} status removed!'.format(status_name))

		if status_type == 1:
			if not status:
				return await ctx.send("You need to provide a url if streaming!")
			if not any("twitch.tv" in x.lower() for x in Utils.get_urls(ctx)):
				return await ctx.send("You need to provide a valid twitch.tv url for streaming!")

		self.settings.setGlobalStat('Game',status)
		self.settings.setGlobalStat('Stream',status_url)
		self.settings.setGlobalStat('Type',status_type)
		msg = 'Setting my {} status to *{}*...'.format(status_name.lower(), status)
		message = await ctx.send(Utils.suppressed(ctx,msg))

		await self._update_status()
		await message.edit(content='{} status set to **{}**{}!'.format(status_name,Utils.suppressed(ctx,status)," at `{}`".format(status_url) if status_url else ""))
		
	@commands.command(pass_context=True)
	async def playgame(self, ctx, *, game : str = None):
		"""Sets the playing status of the bot (owner-only)."""
		await self.set_status(ctx,game,"Playing",0)
		
	@commands.command(pass_context=True)
	async def watchgame(self, ctx, *, game : str = None):
		"""Sets the watching status of the bot (owner-only)."""
		await self.set_status(ctx,game,"Watching",3)
		
	@commands.command(pass_context=True)
	async def listengame(self, ctx, *, game : str = None):
		"""Sets the listening status of the bot (owner-only)."""
		await self.set_status(ctx,game,"Listening",2)

	@commands.command(pass_context=True)
	async def streamgame(self, ctx, url = None, *, game : str = None):
		"""Sets the streaming status of the bot, requires the url and the game (owner-only)."""
		await self.set_status(ctx,game,"Streaming",1,url)

	@commands.command(pass_context=True)
	async def setbotparts(self, ctx, *, parts : str = None):
		"""Set the bot's parts - can be a url, formatted text, or nothing to clear."""
		if not await Utils.is_owner_reply(ctx): return

		if not parts:
			parts = ""
			
		self.settings.setGlobalUserStat(self.bot.user, "Parts", parts)
		msg = '*{}\'s* parts have been set to:\n{}'.format(DisplayName.serverNick(self.bot.user, ctx.guild), parts)
		await ctx.send(Utils.suppressed(ctx,msg))

	@commands.command(pass_context=True)
	async def source(self, ctx):
		"""Link the github source."""
		source = "https://github.com/corpnewt/CorpBot.py"
		msg = '**My insides are located at:**\n\n{}'.format(source)
		await ctx.send(msg)

	@commands.command(pass_context=True)
	async def cloc(self, ctx):
		"""Outputs the total count of lines of code in the currently installed repo."""
		# Script pulled and edited from https://github.com/kyco/python-count-lines-of-code/blob/python3/cloc.py
		
		message = await Message.EmbedText(title="Shuffling papers...", color=ctx.author).send(ctx)
		bot_member = self.bot.user if not ctx.guild else ctx.guild.get_member(self.bot.user.id)

		# Get our current working directory - should be the bot's home
		path = os.getcwd()
		
		# Set up some lists
		extensions = []
		code_count = []
		ext_dict = {
			"py":"Python (.py)",
			"bat":"Windows Batch (.bat)",
			"sh":"Shell Script (.sh)",
			"command":"Command Script (.command)"}
		
		# Get the extensions - include our include list
		extensions = self.get_extensions(path, list(ext_dict))
		
		for run in extensions:
			extension = "*."+run
			temp = 0
			for root, dir, files in os.walk(path):
				for items in fnmatch.filter(files, extension):
					value = root + "/" + items
					temp += sum(+1 for line in open(value, 'rb'))
			code_count.append(temp)
		
		# Set up our output
		fields = [{"name":ext_dict.get(extensions[x],extensions[x]),"value":"{:,} line{}".format(code_count[x],"" if code_count[x]==1 else "s")} for x in range(len(code_count))]
		return await Message.Embed(
			title="Counted Lines of Code",
			description="Some poor soul took the time to sloppily write the following to bring me life...",
			fields=fields,
			thumbnail=Utils.get_avatar(bot_member)
		).edit(ctx,message)

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
		return extensions
