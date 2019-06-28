import asyncio, discord, youtube_dl, subprocess, os, re, time, math, uuid
from   discord.ext import commands
from   Cogs import Message
from   Cogs import DisplayName

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

	__slots__ = ("bot","settings","folder","delay","queue","skips","vol","loop","data","regex")

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
		self.loop     = {}
		self.data     = {}
		# Regex for extracting urls from strings
		self.regex    = re.compile(r"(http|ftp|https)://([\w_-]+(?:(?:\.[\w_-]+)+))([\w.,@?^=%&:/~+#-]*[\w@?^=%&/~+#-])?")

	def skip_pop(self, ctx):
		# Pops the current skip list and dispatches the "next_song" event
		self.skips.pop(str(ctx.guild.id),None)
		self.bot.dispatch("skip_song",ctx)

	def dict_pop(self, ctx):
		# Pops the current guild id from all the class dicts
		self.queue.pop(str(ctx.guild.id),None)
		self.vol.pop(str(ctx.guild.id),None)
		self.skips.pop(str(ctx.guild.id),None)
		self.loop.pop(str(ctx.guild.id),None)
		self.data.pop(str(ctx.guild.id),None)

	def is_admin(self, ctx):
		isAdmin = ctx.author.permissions_in(ctx.channel).administrator
		if not isAdmin:
			for role in self.settings.getServerStat(ctx.guild,"AdminArray",[]):
				if ctx.guild.get_role(int(role["ID"])) in ctx.author.roles:
					isAdmin = True
					break
		if isAdmin:
			# Admin and bot-admin override
			return True
		return False

	async def _check_role(self, ctx):
		if self.is_admin(ctx):
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
		if not data:
			return None
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
		if not data:
			return None
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

	def format_elapsed(self, data):
		progress = int(time.time())-data.get("started_at",0)
		total    = data.get("duration",0)
		return "{} -- {}".format(self.format_duration(progress),self.format_duration(total))

	def progress_bar(self,data,bar_width=27,show_percent=True,include_time=False):
		# Returns a [#####-----] XX.x% style progress bar
		progress = int(time.time())-data.get("started_at",0)
		total    = data.get("duration",0)
		bar = ""
		# Account for the brackets
		bar_width = 10 if bar_width-2 < 10 else bar_width-2
		if total == 0:
			# We don't know how long the song is - or it's a stream
			# return a progress bar of [//////////////] instead
			bar = "[{}]".format("/"*bar_width)
		else:
			# Calculate the progress vs total
			p = int(round((progress/total*bar_width)))
			bar = "[{}{}]".format("■"*p,"□"*(bar_width-p))
		if show_percent:
			bar += " --%" if total == 0 else " {}%".format(int(round(progress/total*100)))
		if include_time:
			time_prefix = "{} - {}\n".format(self.format_duration(progress),self.format_duration(total))
			bar = time_prefix + bar
		return bar

	def progress_moon(self,data,moon_count=10,show_percent=True,include_time=False):
		# Make some shitty moon memes or something... thanks Midi <3
		progress = int(time.time())-data.get("started_at",0)
		total    = data.get("duration",0)
		if total == 0:
			# No idea how long this song is - let's make a repeating pattern
			# of moons - keeping this rotating moon code in, because it's kinda cool
			# moon_list = ["🌑","🌘","🌗","🌖","🌕","🌔","🌓","🌒"]*math.ceil(moon_count/8)
			moon_list = ["🌕","🌑"]*math.ceil(moon_count/2)
			moon_list = moon_list[:moon_count]
			bar = "".join(moon_list)
		else:
			# Each moon can be broken into 25% chunks
			moon_max = 100/moon_count
			percent  = progress/total*100
			full_moons = int(percent/moon_max)
			leftover   = percent%moon_max
			remaining  = int(leftover/(moon_max/4))
			bar = "🌕"*full_moons
			bar += ["🌑","🌘","🌗","🌖","🌕"][remaining]
			bar += "🌑"*(moon_count-full_moons-1)
		if show_percent:
			bar += " --%" if total == 0 else " {}%".format(int(round(progress/total*100)))
		if include_time:
			time_prefix = "{} - {}\n".format(self.format_duration(progress),self.format_duration(total))
			bar = time_prefix + bar
		return bar

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
	async def on_skip_song(self,ctx):
		if ctx.voice_client:
			ctx.voice_client.stop()
	
	@commands.Cog.listener()
	async def on_next_song(self,ctx,error=None):
		task = "playing"
		if error:
			print(error)
		# Try to cleanup before starting
		if not ctx.voice_client:
			# Stopped - or late-fired signal
			return
		else:
			ctx.voice_client.stop()
		queue = self.queue.get(str(ctx.guild.id),[])
		if self.loop.get(str(ctx.guild.id),False) and self.data.get(str(ctx.guild.id),None):
			# Re-add the track to the end of the playlist
			queue.append(self.data.get(str(ctx.guild.id),None))
		if not len(queue):
			# Nothing to play, bail
			return await Message.EmbedText(title="♫ End of playlist!",color=ctx.author,delete_after=self.delay).send(ctx)
		# Get the first song in the list and start playing it
		data = queue.pop(0)
		# Save the current data in case of repeats
		self.data[str(ctx.guild.id)] = data
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
			ctx.voice_client.play(player, after=lambda e: self.bot.dispatch("next_song",ctx,e if e else None))
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
	async def join(self, ctx, *, channel = None):
		"""Joins a voice channel."""

		if channel == None:
			if not ctx.author.voice:
				return await Message.EmbedText(title="♫ You need to pass a voice channel for me to join!",color=ctx.author,delete_after=self.delay).send(ctx)
			channel = ctx.author.voice.channel
		else:
			channel = DisplayName.channelForName(channel, ctx.guild, "voice")
		if not channel:
			return await Message.EmbedText(title="♫ I couldn't find that voice channel!",color=ctx.author,delete_after=self.delay).send(ctx)
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
		"""Plays from a url (almost anything youtube_dl supports) or resumes a currently paused song."""

		if ctx.voice_client is None:
			return await Message.EmbedText(title="♫ I am not connected to a voice channel!",color=ctx.author,delete_after=self.delay).send(ctx)
		if ctx.voice_client.is_paused():
			# We're trying to resume
			ctx.voice_client.resume()
			data = self.data.get(str(ctx.guild.id))
			data["started_at"] = int(time.time()) - data.get("elapsed_time",0)
			return await Message.EmbedText(title="♫ Resumed: {}".format(data.get("title","Unknown")),color=ctx.author,delete_after=self.delay).send(ctx)
		if url == None:
			return await Message.EmbedText(title="♫ You need to pass a url or search term!",color=ctx.author,delete_after=self.delay).send(ctx)
		# Add our url to the queue
		message = await Message.EmbedText(
			title="♫ Searching For: {}...".format(url.strip("<>")),
			color=ctx.author
			).send(ctx)
		data = await self.add_to_queue(ctx, url)
		if not data:
			# Nothing found
			return await Message.EmbedText(title="♫ I couldn't find anything for that search!",description="Try using more specific search terms, or pass a url instead.",color=ctx.author,delete_after=self.delay).edit(ctx,message)
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
	async def pause(self, ctx):
		"""Pauses the currently playing song."""

		if ctx.voice_client is None:
			return await Message.EmbedText(title="♫ Not connected to a voice channel!",color=ctx.author,delete_after=self.delay).send(ctx)
		if ctx.voice_client.is_paused():
			return await Message.EmbedText(title="♫ Already paused!",color=ctx.author,delete_after=self.delay).send(ctx)
		if not ctx.voice_client.is_playing():
			return await Message.EmbedText(title="♫ Not playing anything!",color=ctx.author,delete_after=self.delay).send(ctx)
		if not (ctx.author.voice or ctx.voice.author.channel == ctx.voice_client.channel) and not self.is_admin(ctx):
			return await Message.EmbedText(title="♫ You have to be in the same voice channel as me to use that!",color=ctx.author,delete_after=self.delay).send(ctx)
		# Pause the track and save the currently elapsed time
		ctx.voice_client.pause()
		data = self.data.get(str(ctx.guild.id))
		data["elapsed_time"] = int(time.time()-data.get("started_at",0))
		await Message.EmbedText(title="♫ Paused: {}".format(data.get("title","Unknown")),color=ctx.author,delete_after=self.delay).send(ctx)

	@commands.command()
	async def paused(self, ctx, *, moons = None):
		"""Lists whether or not the player is paused.  Synonym of the playing command."""
		await ctx.invoke(self.playing,moons=moons)

	@commands.command()
	async def resume(self, ctx):
		"""Resumes the song if paused."""
		if ctx.voice_client is None:
			return await Message.EmbedText(title="♫ I am not connected to a voice channel!",color=ctx.author,delete_after=self.delay).send(ctx)
		if not ctx.voice_client.is_paused():
			return await Message.EmbedText(title="♫ Not currently paused!",color=ctx.author,delete_after=self.delay).send(ctx)
		if not (ctx.author.voice or ctx.voice.author.channel == ctx.voice_client.channel) and not self.is_admin(ctx):
			return await Message.EmbedText(title="♫ You have to be in the same voice channel as me to use that!",color=ctx.author,delete_after=self.delay).send(ctx)
		# We're trying to resume
		ctx.voice_client.resume()
		data = self.data.get(str(ctx.guild.id))
		data["started_at"] = int(time.time()) - data.get("elapsed_time",0)
		await Message.EmbedText(title="♫ Resumed: {}".format(data.get("title","Unknown")),color=ctx.author,delete_after=self.delay).send(ctx)

	@commands.command()
	async def unplay(self, ctx, *, song_number = None):
		"""Removes the passed song number from the queue.  You must be the requestor, or an admin to remove it.  Does not include the currently playing song."""
		
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
		if song.get("added_by",None) == ctx.author or self.is_admin(ctx):
			queue.pop(song_number)
			return await Message.EmbedText(title="♫ Removed {} at position {}!".format(song["title"],song_number+1),color=ctx.author,delete_after=self.delay).send(ctx)
		await Message.EmbedText(title="♫ You can only remove songs you requested!", description="Only {} or an admin can remove that song!".format(song["added_by"].mention),color=ctx.author,delete_after=self.delay).send(ctx)

	@commands.command()
	async def unqueue(self, ctx):
		"""Removes all songs you've added from the queue (does not include the currently playing song).  Admins remove all songs from the queue."""
		
		if ctx.voice_client is None:
			return await Message.EmbedText(title="♫ I am not connected to a voice channel!",color=ctx.author,delete_after=self.delay).send(ctx)
		queue = self.queue.get(str(ctx.guild.id))
		if not len(queue):
			# No songs in queue
			return await Message.EmbedText(title="♫ No songs in queue!", description="If you want to bypass a currently playing song, use `{}skip` instead.".format(ctx.prefix),color=ctx.author,delete_after=self.delay).send(ctx)
		removed = 0
		new_queue = []
		for song in queue:
			if song.get("added_by",None) == ctx.author or self.is_admin(ctx):
				removed += 1
			else:
				new_queue.append(song)
		self.queue[str(ctx.guild.id)] = new_queue
		if removed > 0:
			return await Message.EmbedText(title="♫ Removed {} song{} from queue!".format(removed,"" if removed == 1 else "s"),color=ctx.author,delete_after=self.delay).send(ctx)
		await Message.EmbedText(title="♫ You can only remove songs you requested!", description="Only an admin can remove all queued songs!",color=ctx.author,delete_after=self.delay).send(ctx)

	@commands.command()
	async def playing(self, ctx, *, moons = None):
		"""Lists the currently playing song if any."""

		if not ctx.voice_client or not (ctx.voice_client.is_playing() or ctx.voice_client.is_paused()):
			# No client - and we're not playing or paused
			return await Message.EmbedText(
				title="♫ Currently Playing",
				color=ctx.author,
				description="Not playing anything.",
				delete_after=self.delay
			).send(ctx)
		data = self.data.get(str(ctx.guild.id))
		if ctx.voice_client.is_playing():
			play_text = "Playing" if data.get("duration",0)>0 else "Streaming"
		else:
			# paused - update the progress
			data["started_at"] = int(time.time()) - data.get("elapsed_time",0)
			play_text = "Paused"
		await Message.Embed(
			title="♫ Currently {}: {}".format(play_text,data.get("title","Unknown")),
			description="Requested by {}".format(data["added_by"].mention),
			color=ctx.author,
			fields=[
				{"name":"Elapsed","value":self.format_elapsed(data),"inline":False},
				{"name":"Progress","value":self.progress_moon(data) if moons and moons.lower() == "moons" else self.progress_bar(data),"inline":False}
			],
			url=data.get("webpage_url",None),
			thumbnail=data.get("thumbnail",None),
			delete_after=self.delay
		).send(ctx)

	@commands.command()
	async def playingin(self, ctx):
		"""Shows the number of servers the bot is currently playing music in."""

		playing_list = [x for x in self.bot.guilds if x.voice_client and (x.voice_client.is_playing() or x.voice_client.is_paused())]
		playing_in = len(playing_list)
		paused_in  = len([x for x in playing_list if x.voice_client.is_paused()])
		msg = "♫ Playing music in {:,} of {:,} server{} ({:,} paused).".format(playing_in, len(self.bot.guilds), "" if len(self.bot.guilds) == 1 else "s", paused_in)
		await Message.EmbedText(title=msg,color=ctx.author,delete_after=self.delay).send(ctx)

	@commands.command()
	async def playlist(self, ctx):
		"""Lists the queued songs in the playlist."""

		if not ctx.voice_client or not (ctx.voice_client.is_playing() or ctx.voice_client.is_paused()):
			return await Message.EmbedText(
				title="♫ Current Playlist",
				color=ctx.author,
				description="Not playing anything.",
				delete_after=self.delay
			).send(ctx)
		data = self.data.get(str(ctx.guild.id))
		if ctx.voice_client.is_playing():
			play_text = "Playing"
		else:
			data["started_at"] = int(time.time()) - data.get("elapsed_time",0)
			play_text = "Paused"
		queue = self.queue.get(str(ctx.guild.id))
		fields = [{"name":"{}".format(data.get("title")),"value":"Currently {} - at {} - Requested by {}".format(
			play_text,
			self.format_duration(int(time.time())-data["started_at"],True),
			data["added_by"].mention),"inline":False}
		]
		if len(queue):
			total_time = 0
			total_streams = 0
			time_string = stream_string = ""
			for x in queue:
				t = x.get("duration",0)
				if t:
					total_time+=t
				else:
					total_streams+=1
			if total_time:
				# Got time at least
				time_string += "{} total -- ".format(self.format_duration(total_time))
			if total_streams:
				# Got at least one stream
				time_string += "{:,} Stream{} -- ".format(total_streams, "" if total_streams == 1 else "s") 
			q_text = "-- {:,} Song{} in Queue -- {}".format(len(queue), "" if len(queue) == 1 else "s", time_string)
			fields.append({"name":"♫ Up Next","value":q_text,"inline":False})
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
			pl_string = " (10/{:,} shown)".format(len(queue)+1)
		else:
			pl_string = ""
		if self.loop.get(str(ctx.guild.id),False):
			pl_string += " - Repeat Enabled"
		await Message.Embed(
			title="♫ Current Playlist{}".format(pl_string),
			color=ctx.author,
			fields=fields,
			delete_after=self.delay,
			pm_after=15
		).send(ctx)

	@commands.command()
	async def skip(self, ctx):
		"""Adds your vote to skip the current song.  50% or more of the non-bot users need to vote to skip a song.  Original requestors and admins can skip without voting."""

		if ctx.voice_client is None:
			return await Message.EmbedText(title="♫ Not connected to a voice channel!",color=ctx.author,delete_after=self.delay).send(ctx)
		if not ctx.voice_client.is_playing():
			return await Message.EmbedText(title="♫ Not playing anything!",color=ctx.author,delete_after=self.delay).send(ctx)
		# Check for added by first, then check admin
		data = self.data.get(str(ctx.guild.id))
		if self.is_admin(ctx):
			self.skip_pop(ctx)
			return await Message.EmbedText(title="♫ Admin override activated - skipping!",color=ctx.author,delete_after=self.delay).send(ctx)	
		if data.get("added_by",None) == ctx.author:
			self.skip_pop(ctx)
			return await Message.EmbedText(title="♫ Requestor chose to skip - skipping!",color=ctx.author,delete_after=self.delay).send(ctx)
		# At this point, we're not admin, and not the requestor, let's make sure we're in the same vc
		if not ctx.author.voice or not ctx.author.voice.channel == ctx.voice_client.channel:
			return await Message.EmbedText(title="♫ You have to be in the same voice channel as me to use that!",color=ctx.author,delete_after=self.delay).send(ctx)
		
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
		"""Changes the player's volume (0-100)."""

		if ctx.voice_client is None:
			return await Message.EmbedText(title="♫ Not connected to a voice channel!",color=ctx.author,delete_after=self.delay).send(ctx)
		if not ctx.voice_client.is_playing():
			return await Message.EmbedText(title="♫ Not playing anything!",color=ctx.author,delete_after=self.delay).send(ctx)
		if not (ctx.author.voice or ctx.voice.author.channel == ctx.voice_client.channel) and not self.is_admin(ctx):
			return await Message.EmbedText(title="♫ You have to be in the same voice channel as me to use that!",color=ctx.author,delete_after=self.delay).send(ctx)
		if volume == None:
			# We're listing the current volume
			cv = int(ctx.voice_client.source.volume*100)
			return await Message.EmbedText(title="♫ Current volume at {}%.".format(cv),color=ctx.author,delete_after=self.delay).send(ctx)
		try:
			volume = int(volume)
		except:
			return await Message.EmbedText(title="♫ Volume must be an integer between 0-100.",color=ctx.author,delete_after=self.delay).send(ctx)
		# Ensure our volume is between 0 and 100
		if not -1 < volume < 101:
			volume = 100 if volume > 100 else 0
		self.vol[str(ctx.guild.id)] = volume / 100
		ctx.voice_client.source.volume = volume / 100
		await Message.EmbedText(title="♫ Changed volume to {}%.".format(volume),color=ctx.author,delete_after=self.delay).send(ctx)

	@commands.command()
	async def repeat(self, ctx, *, yes_no = None):
		"""Checks or sets whether to repeat the current playlist."""

		if ctx.voice_client is None:
			return await Message.EmbedText(title="♫ Not connected to a voice channel!",color=ctx.author,delete_after=self.delay).send(ctx)
		current = self.loop.get(str(ctx.guild.id),False)
		setting_name = "Repeat"
		if yes_no == None:
			if current:
				msg = "{} currently enabled!".format(setting_name)
			else:
				msg = "{} currently disabled!".format(setting_name)
		elif yes_no.lower() in [ "yes", "on", "true", "enabled", "enable" ]:
			yes_no = True
			if current == True:
				msg = '{} remains enabled!'.format(setting_name)
			else:
				msg = '{} is now enabled!'.format(setting_name)
		elif yes_no.lower() in [ "no", "off", "false", "disabled", "disable" ]:
			yes_no = False
			if current == False:
				msg = '{} remains disabled!'.format(setting_name)
			else:
				msg = '{} is now disabled!'.format(setting_name)
		else:
			msg = "That's not a valid setting!"
			yes_no = current
		if not yes_no == None and not yes_no == current:
			self.loop[str(ctx.guild.id)] = yes_no
		await Message.EmbedText(title="♫ "+msg,color=ctx.author,delete_after=self.delay).send(ctx)

	@commands.command()
	async def stop(self, ctx):
		"""Stops and disconnects the bot from voice."""
		
		# Remove the per-server temp settings
		self.dict_pop(ctx)
		if ctx.voice_client:
			await ctx.voice_client.disconnect()
			return await Message.EmbedText(title="♫ I've left the voice channel!",color=ctx.author,delete_after=self.delay).send(ctx)
		await Message.EmbedText(title="♫ Not connected to a voice channel!",color=ctx.author,delete_after=self.delay).send(ctx)

	@join.before_invoke
	@play.before_invoke
	@resume.before_invoke
	@pause.before_invoke
	@skip.before_invoke
	@stop.before_invoke
	@volume.before_invoke
	@repeat.before_invoke
	async def ensure_roles(self, ctx):
		if not await self._check_role(ctx):
			raise commands.CommandError("Missing DJ roles.")

	@play.before_invoke
	async def ensure_voice(self, ctx):
		if not await self._check_role(ctx):
			raise commands.CommandError("Missing DJ roles.")
		if not ctx.author.voice and not self.is_admin(ctx):
			await Message.EmbedText(title="♫ You are not connected to a voice channel!",color=ctx.author,delete_after=self.delay).send(ctx)
			raise commands.CommandError("Author not connected to a voice channel.")
		if ctx.voice_client is None:
			if ctx.author.voice:
				await ctx.author.voice.channel.connect()
