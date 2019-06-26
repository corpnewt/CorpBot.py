import asyncio, discord, youtube_dl, subprocess, os, re, time, math, uuid
from   discord.ext import commands
from   Cogs import Message

# This file is modified from Rapptz's basic_voice.py:
# https://github.com/Rapptz/discord.py/blob/master/examples/basic_voice.py

# Suppress noise about console usage from errors
youtube_dl.utils.bug_reports_message = lambda: ''

ytdl_format_options = {
	'format': 'bestaudio/best',
	'extractaudio': True,
	'audioformat': 'mp3',
	'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
	'restrictfilenames': True,
	'noplaylist': True,
	'nocheckcertificate': True,
	'ignoreerrors': True,
	'logtostderr': False,
	'quiet': True,
	'no_warnings': True,
	'default_search': 'auto',
	'source_address': '0.0.0.0' # bind to ipv4 since ipv6 addresses cause issues sometimes
}

ffmpeg_options = {
	'before_options': '-re -reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5'
	#'options': '-ac 2 -f s16le -ar 48000'
}

ytdl = youtube_dl.YoutubeDL(ytdl_format_options)

class YTDLSource(discord.PCMVolumeTransformer):
	def __init__(self, source, *, data, volume=0.5):
		super().__init__(source, volume)
		self.data = data
		self.title = data.get('title')
		# Try to get the best abr
		format_list = sorted(self.data["formats"], key=lambda x: x.get("abr",-1), reverse=True)
		self.url = format_list[0].get("url")

	@classmethod
	async def from_url(cls, ctx, data, *, loop=None, folder=None):
		loop = loop or asyncio.get_event_loop()
		format_list = sorted(data["formats"], key=lambda x: x.get("abr",-1), reverse=True)
		# Re-grab the link in case it died
		new_data = await loop.run_in_executor(None, lambda: ytdl.extract_info(format_list[0]['url'], download=False))
		# Gather the needed info
		format_list = sorted(new_data["formats"], key=lambda x: x.get("abr",-1), reverse=True)
		video_url   = format_list[0]['url']
		local_file = "{}-{}.mp3".format(ctx.guild.id,str(uuid.uuid4()).upper())
		# Save to a target folder if need be
		local_file  = os.path.join(folder,local_file) if folder else local_file

		# Start the download process itself as it will download the file as our player process streams it
		stream_proc = subprocess.Popen([
			'ffmpeg', '-hide_banner', '-loglevel',
			'error', '-y', '-i',
			video_url, local_file
		])

		waited = 0
		while True:
			# Wait for our file to show up, or for the streaming process to error
			if (os.path.exists(local_file) and os.stat(local_file).st_size >= 1026) or waited >= 10:
				break
			await asyncio.sleep(0.1)
			waited += 0.1
		data["filename"] = local_file
		data["stream_proc"] = stream_proc
		data["started_at"] = int(time.time())
		return cls(discord.FFmpegPCMAudio(local_file),data=data)

	def cleanup(self):
		super().cleanup()
		proc = self.data.get("stream_proc",None)
		if not proc is None:
			proc.kill()
			if proc.poll() is None:
				proc.communicate()
		try:
			if os.path.exists(self.data.get("filename")):
				os.remove(self.data.get("filename"))
		except Exception as e:
			print(e)
			pass

class YTDLStreamSource(discord.PCMVolumeTransformer):
	def __init__(self, source, *, data, volume=0.5):
		super().__init__(source, volume)
		self.data = data
		self.title = data.get('title')
		# Try to get the best abr
		format_list = sorted(self.data["formats"], key=lambda x: x.get("abr",-1), reverse=True)
		self.url = format_list[0].get("url")

	@classmethod
	async def from_url(cls, data, *, loop=None, folder=None):
		loop = loop or asyncio.get_event_loop()
		format_list = sorted(data["formats"], key=lambda x: x.get("abr",-1), reverse=True)
		# Re-grab the link in case it died
		new_data = await loop.run_in_executor(None, lambda: ytdl.extract_info(format_list[0]['url'], download=False))
		# Gather the needed info
		format_list = sorted(new_data["formats"], key=lambda x: x.get("abr",-1), reverse=True)
		video_url   = format_list[0]['url']
		data["started_at"] = int(time.time())
		return cls(discord.FFmpegPCMAudio(video_url,**ffmpeg_options),data=data)

def setup(bot):
	settings = bot.get_cog("Settings")
	bot.add_cog(Music(bot,settings))

class Music(commands.Cog):

	__slots__ = ("bot","settings","folder","delay","queue","skips","vol","skipping","regex")

	def __init__(self, bot, settings):
		self.bot      = bot
		self.settings = settings
		self.folder   = os.path.join(".","Music")
		self.delay    = 20 # Set to None to keep all messages
		if not os.path.exists(self.folder):
			# Create our music folder
			os.mkdir(self.folder)
		self.queue    = {}
		self.skips    = {}
		self.vol      = {}
		self.skipping = False
		# Regex for extracting urls from strings
		self.regex    = re.compile(r"(http|ftp|https)://([\w_-]+(?:(?:\.[\w_-]+)+))([\w.,@?^=%&:/~+#-]*[\w@?^=%&/~+#-])?")

	def skip_pop(self, ctx):
		# Pops the current skip list and dispatches the "next_song" event
		self.skips.pop(str(ctx.guild.id),None)
		self.bot.dispatch("next_song",ctx)

	def dict_pop(self, ctx):
		# Pops the current guild id from all the class dicts
		self.queue.pop(str(ctx.guild.id),None)
		self.vol.pop(str(ctx.guild.id),None)
		self.skips.pop(str(ctx.guild.id),None)

	async def _check_role(self, ctx):
		isAdmin = ctx.author.permissions_in(ctx.channel).administrator
		if not isAdmin:
			for role in self.settings.getServerStat(ctx.guild,"AdminArray",[]):
				if ctx.guild.get_role(int(role["ID"])) in ctx.author.roles:
					isAdmin = True
					break
		if isAdmin:
			# Admin and bot-admin override
			return True
		promoArray = self.settings.getServerStat(ctx.guild, "DJArray", [])
		if not len(promoArray):
			await Message.EmbedText(title="♫ There are no DJ roles set yet.  Use `{}adddj [role]` to add some.".format(ctx.prefix),color=ctx.author,delete_after=self.delay).send(ctx)
			return None
		for role in promoArray:
			if ctx.guild.get_role(int(role["ID"])) in ctx.author.roles:
				return True
		await Message.EmbedText(title="♫ You need a DJ role to do that!",color=ctx.author,delete_after=self.delay).send(ctx)
		return False

	async def get_song_info(self, url, search=False):
		# Grabs some info on the passed song/url
		data = await self.bot.loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=False))
		if 'entries' in data:
			# take first item from a playlist
			data = data['entries'][0]
		return data

	async def add_to_queue(self, ctx, url):
		queue = self.queue.get(str(ctx.guild.id),[])
		url = url.strip('<>')
		# Check if url - if not, remove /
		matches = list(re.finditer(self.regex, url))
		if not len(matches):
			url = url.replace('/', '')
		data = await self.get_song_info(url)
		data["added_by"] = ctx.author
		queue.append(data)
		self.queue[str(ctx.guild.id)] = queue
		if not ctx.voice_client.is_playing() and not ctx.voice_client.is_paused():
			self.bot.dispatch("next_song",ctx)
		return data

	def format_duration(self, dur, allow_zero = False):
		if dur == 0 and not allow_zero:
			return "[Live Stream]"
		hours = dur // 3600
		minutes = (dur % 3600) // 60
		seconds = dur % 60
		return "{:02d}h:{:02d}m:{:02d}s".format(hours, minutes, seconds)

	@commands.Cog.listener()
	async def on_loaded_extension(self, ext):
		# See if we were loaded
		if not self._is_submodule(ext.__name__, self.__module__):
			return
		self.bot.loop.create_task(self.setup_music_folder())
		
	async def setup_music_folder(self):
		await self.bot.wait_until_ready()
		# Clean out the music folder
		for x in os.listdir(self.folder):
			if x.lower().endswith(".mp3"):
				os.remove(os.path.join(self.folder,x))

	def _is_submodule(self, parent, child):
		return parent == child or child.startswith(parent + ".")

	@commands.Cog.listener()
	async def on_unloaded_extension(self, ext):
		# Called to shut things down
		if not self._is_submodule(ext.__name__, self.__module__):
			return
		# Stop all players
		for x in self.bot.guilds:
			if x.voice_client:
				x.voice_client.stop()
	
	@commands.Cog.listener()
	async def on_next_song(self,ctx,error=None):
		if self.skipping:
			# Already trying to skip
			return
		self.skipping = True
		task = "playing"
		if error:
			print(error)
		# Try to cleanup before starting
		if ctx.voice_client:
			ctx.voice_client.stop()
		queue = self.queue.get(str(ctx.guild.id),[])
		if not len(queue):
			# Nothing to play, bail
			return
		# Get the first song in the list and start playing it
		data = queue.pop(0)
		async with ctx.typing():
			if data.get("duration",0) == 0:
				# No idea how long this one is, stream it
				task = "streaming"
				player = await YTDLStreamSource.from_url(data, loop=self.bot.loop, folder=self.folder)
			else:
				# Got a duration - let's play this one normally
				player = await YTDLSource.from_url(ctx, data, loop=self.bot.loop, folder=self.folder)
				# Set the last volume level
				player.volume = self.vol.get(str(ctx.guild.id),0.5)
			try:
				ctx.voice_client.play(player, after=lambda e: self.bot.dispatch("next_song",ctx,e if e else None))
			except Exception as e:
				print(e)
				self.skipping = False
				return
		await Message.Embed(
			title="♫ Now {}: {}".format(task.capitalize(), data.get("title","Unknown")),
			fields=[
				{"name":"Duration","value":self.format_duration(data.get("duration",0)),"inline":False}
			],
			description="Requested by {}".format(data["added_by"].mention),
			color=ctx.author,
			url=data.get("webpage_url",None),
			thumbnail=data.get("thumbnail",None),
			delete_after=self.delay
		).send(ctx)
		self.skipping = False

	@commands.Cog.listener()
	async def on_voice_state_update(self, user, before, after):
		if not user.guild:
			return
		# Get our member on the same server as the user
		bot_voice = user.guild.voice_client
		if not bot_voice or not before.channel is bot_voice.channel:
			# We're not in a voice channel or this isn't our voice channel - don't care
			return
		if len([x for x in before.channel.members if not x.bot]) > 0:
			# At least one non-bot user
			return
		# if we made it here - then we're alone - disconnect
		self.dict_pop(user)
		if user.guild.voice_client:
			await user.guild.voice_client.disconnect()

	@commands.command()
	async def join(self, ctx, *, channel: discord.VoiceChannel):
		"""Joins a voice channel"""

		if ctx.voice_client:
			if not (ctx.voice_client.is_paused() or ctx.voice_client.is_playing()):
				await ctx.voice_client.move_to(channel)
				return await Message.EmbedText(title="♫ Ready to play music in {}!".format(channel),color=ctx.author,delete_after=self.delay).send(ctx)
			else:
				return await Message.EmbedText(title="♫ I'm already playing music in {}!".format(ctx.voice_client.channel),color=ctx.author,delete_after=self.delay).send(ctx)
		await channel.connect()
		await Message.EmbedText(title="♫ Ready to play music in {}!".format(channel),color=ctx.author,delete_after=self.delay).send(ctx)

	@commands.command()
	async def play(self, ctx, *, url = None):
		"""Plays from a url (almost anything youtube_dl supports)"""

		if ctx.voice_client is None:
			return await Message.EmbedText(title="♫ I am not connected to a voice channel!",color=ctx.author,delete_after=self.delay).send(ctx)
		if url == None:
			return await Message.EmbedText(title="♫ You need to pass a url or search term!",color=ctx.author,delete_after=self.delay).send(ctx)
		# Add our url to the queue
		message = await Message.EmbedText(
			title="♫ Searching For: {}...".format(url.strip("<>")),
			color=ctx.author
			).send(ctx)
		data = await self.add_to_queue(ctx, url)
		await Message.Embed(
			title="♫ Enqueued: {}".format(data.get("title","Unknown")),
			description="Requested by {}".format(ctx.author.mention),
			fields=[
				{"name":"Duration","value":self.format_duration(data.get("duration",0)),"inline":False}
			],
			color=ctx.author,
			thumbnail=data.get("thumbnail",None),
			url=data.get("webpage_url",None),
			delete_after=self.delay
		).edit(ctx,message)

	@commands.command()
	async def unplay(self, ctx, *, song_number = None):
		"""Removes the passed song number from the queue.  You must be the requestor, or an admin to remove it."""
		if ctx.voice_client is None:
			return await Message.EmbedText(title="♫ I am not connected to a voice channel!",color=ctx.author,delete_after=self.delay).send(ctx)
		queue = self.queue.get(str(ctx.guild.id))
		if not len(queue):
			# No songs in queue
			return await Message.EmbedText(title="♫ No songs in queue!", description="If you want to bypass a currently playing song, use `{}skip` instead.".format(ctx.prefix),color=ctx.author,delete_after=self.delay).send(ctx)
		try:
			song_number = int(song_number)-1
		except:
			return await Message.EmbedText(title="♫ Not a valid song number!",color=ctx.author,delete_after=self.delay).send(ctx)
		if song_number < 0 or song_number > len(queue):
			return await Message.EmbedText(title="♫ Out of bounds!  Song number must be between 2 and {}.".format(len(queue)),color=ctx.author,delete_after=self.delay).send(ctx)
		# Get the song at the index
		song = queue[song_number]
		if song.get("added_by",None) == ctx.author or ctx.author.permissions_in(ctx.channel).administrator:
			queue.pop(song_number)
			return await Message.EmbedText(title="♫ Removed {} at position {}!".format(song["title"],song_number+1),color=ctx.author,delete_after=self.delay).send(ctx)
		await Message.EmbedText(title="♫ You can only remove songs you requested!", description="Only {} or an admin can remove that song!".format(song["added_by"].mention),color=ctx.author,delete_after=self.delay).send(ctx)

	@commands.command()
	async def playing(self, ctx):
		"""Lists the currently playing song if any."""

		if not ctx.voice_client or not ctx.voice_client.is_playing():
			return await Message.EmbedText(
				title="♫ Currently Playing",
				color=ctx.author,
				description="Not playing anything.",
				delete_after=self.delay
			).send(ctx)
		data = ctx.voice_client.source.data
		await Message.Embed(
			title="♫ Currently {}: {}".format("Playing" if data.get("duration",0)>0 else "Streaming",data.get("title","Unknown")),
			description="Requested by {}".format(data["added_by"].mention),
			color=ctx.author,
			fields=[
				{"name":"Elapsed","value":"{}".format(self.format_duration(int(time.time())-data["started_at"],True)),"inline":False},
				{"name":"Duration","value":self.format_duration(data.get("duration",0)),"inline":False}
			],
			url=data.get("webpage_url",None),
			thumbnail=data.get("thumbnail",None),
			delete_after=self.delay
		).send(ctx)

	@commands.command()
	async def playingin(self, ctx):
		"""Shows the number of servers the bot is currently playing music in."""

		playing_in = len([x for x in self.bot.guilds if x.voice_client and x.voice_client.is_playing()])
		msg = "♫ Playing music in {} of {} server{}.".format(playing_in, len(self.bot.guilds), "" if len(self.bot.guilds) == 1 else "s")
		await Message.EmbedText(title=msg,color=ctx.author,delete_after=self.delay).send(ctx)

	@commands.command()
	async def playlist(self, ctx):
		"""Lists the queued songs in the playlist."""

		if not ctx.voice_client or not ctx.voice_client.is_playing():
			return await Message.EmbedText(
				title="♫ Current Playlist",
				color=ctx.author,
				description="Not playing anything.",
				delete_after=self.delay,
				pm_after=-1
			).send(ctx)
		data = ctx.voice_client.source.data
		queue = self.queue.get(str(ctx.guild.id))
		fields = [{"name":"{}".format(data.get("title")),"value":"Currently Playing - at {} - Requested by {}".format(
			self.format_duration(int(time.time())-data["started_at"],True),
			data["added_by"].mention),"inline":False}
		]
		if len(queue):
			fields.append({"name":"♫ Up Next","value":"-- {} Song{} In Queue --".format(len(queue), "" if len(queue) == 1 else "s"),"inline":False})
		for x,y in enumerate(queue):
			if x >= 10:
				# We have 10 values already - bail
				break
			x += 1 # brings this up to the proper numbering
			fields.append({
				"name":"{}. {}".format(x,y.get("title")),
				"value":"{} - Requested by {}".format(self.format_duration(y.get("duration",0)),y["added_by"].mention),
				"inline":False})
		if len(queue) > 9:
			pl_string = " (10/{} shown)".format(len(queue)+1)
		else:
			pl_string = ""
		await Message.Embed(
			title="♫ Current Playlist{}".format(pl_string),
			color=ctx.author,
			fields=fields,
			delete_after=self.delay
		).send(ctx)

	@commands.command()
	async def skip(self, ctx):
		"""Adds your vote to skip the current song. 50% or more of the non-bot users need to vote to skip a song."""

		if self.skipping:
			# Ignore any skips that don't apply
			return
		if ctx.voice_client is None:
			return await Message.EmbedText(title="♫ Not connected to a voice channel!",color=ctx.author,delete_after=self.delay).send(ctx)
		if not ctx.voice_client.is_playing():
			return await Message.EmbedText(title="♫ Not playing anything!",color=ctx.author,delete_after=self.delay).send(ctx)
		# Check for added by first, then check admin
		data = ctx.voice_client.source.data
		if data.get("added_by",None) == ctx.author:
			self.skip_pop(ctx)
			return await Message.EmbedText(title="♫ Requestor chose to skip - skipping!",color=ctx.author,delete_after=self.delay).send(ctx)
		if ctx.author.permissions_in(ctx.channel).administrator:
			self.skip_pop(ctx)
			return await Message.EmbedText(title="♫ Admin override activated - skipping!",color=ctx.author,delete_after=self.delay).send(ctx)	
		# Do the checking here to validate we can use this and etc.
		skips = self.skips.get(str(ctx.guild.id),[])
		# Relsolve the skips
		new_skips = []
		for x in skips:
			member = ctx.guild.get_member(x)
			if not member or member.bot:
				continue
			if not member in ctx.voice_client.channel.members:
				continue
			# Got a valid user who's in the skip list and the voice channel
			new_skips.append(x)
		# Check if we're not already in the skip list
		if not ctx.author.id in new_skips:
			new_skips.append(ctx.author.id)
		# Let's get the number of valid skippers
		skippers = [x for x in ctx.voice_client.channel.members if not x.bot]
		needed_skips = math.ceil(len(skippers)/2)
		if len(new_skips) >= needed_skips:
			# Got it!
			self.skip_pop(ctx)
			return await Message.EmbedText(title="♫ Skip threshold met ({}/{}) - skipping!".format(len(new_skips),needed_skips),color=ctx.author,delete_after=self.delay).send(ctx)
		# Update the skips
		self.skips[str(ctx.guild.id)] = new_skips
		await Message.EmbedText(title="♫ Skip threshold not met - {}/{} skip votes entered - need {} more!".format(len(new_skips),needed_skips,needed_skips-len(new_skips)),color=ctx.author,delete_after=self.delay).send(ctx)

	@commands.command()
	async def volume(self, ctx, volume = None):
		"""Changes the player's volume"""

		if ctx.voice_client is None:
			return await Message.EmbedText(title="♫ Not connected to a voice channel!",color=ctx.author,delete_after=self.delay).send(ctx)
		if volume == None:
			# We're listing the current volume
			cv = int(ctx.voice_client.source.volume*100)
			return await Message.EmbedText(title="♫ Current volume at {}%.".format(cv),color=ctx.author,delete_after=self.delay).send(ctx)
		try:
			volume = int(volume)
		except:
			return await Message.EmbedText(title="♫ Volume must be an integer between 0-100.",color=ctx.author,delete_after=self.delay).send(ctx)
		# Ensure our volume is between 0 and 100
		volume = 100 if volume > 100 else volume
		volume = 0 if volume < 0 else volume
		self.vol[str(ctx.guild.id)] = volume / 100
		ctx.voice_client.source.volume = volume / 100
		await Message.EmbedText(title="♫ Changed volume to {}%.".format(volume),color=ctx.author,delete_after=self.delay).send(ctx)

	@commands.command()
	async def stop(self, ctx):
		"""Stops and disconnects the bot from voice"""
		
		# Remove the per-server temp settings
		self.dict_pop(ctx)
		if ctx.voice_client:
			await ctx.voice_client.disconnect()
			return await Message.EmbedText(title="♫ I've left the voice channel!",color=ctx.author,delete_after=self.delay).send(ctx)
		await Message.EmbedText(title="♫ Not connected to a voice channel!",color=ctx.author,delete_after=self.delay).send(ctx)

	@join.before_invoke
	@play.before_invoke
	@skip.before_invoke
	@stop.before_invoke
	@volume.before_invoke
	async def ensure_roles(self, ctx):
		if not await self._check_role(ctx):
			raise commands.CommandError("Missing DJ roles.")

	@play.before_invoke
	async def ensure_voice(self, ctx):
		if not await self._check_role(ctx):
			raise commands.CommandError("Missing DJ roles.")
		if ctx.voice_client is None:
			if ctx.author.voice:
				await ctx.author.voice.channel.connect()
			elif ctx.author.permissions_in(ctx.channel).administrator:
				pass
			else:
				await Message.EmbedText(title="♫ You are not connected to a voice channel!",color=ctx.author,delete_after=self.delay).send(ctx)
				raise commands.CommandError("Author not connected to a voice channel.")
