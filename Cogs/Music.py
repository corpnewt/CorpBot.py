import discord, os, re, math, random, wavelink, json, tempfile, shutil
from   discord.ext import commands
from   Cogs import Utils, Message, DisplayName, PickList, DL

# This file is modified from Rapptz's basic_voice.py:
# https://github.com/Rapptz/discord.py/blob/master/examples/basic_voice.py

def setup(bot):
	settings = bot.get_cog("Settings")
	bot.add_cog(Music(bot,settings))

class Music(commands.Cog):

	__slots__ = ("bot","settings","queue","skips","vol","loop","data")

	def __init__(self, bot, settings):
		self.bot      = bot
		self.settings = settings
		self.queue    = {}
		self.skips    = {}
		self.vol      = {}
		self.loop     = {}
		self.data     = {}
		# Get the Lavalink info as needed
		self.ll_host = bot.settings_dict.get("lavalink_host","127.0.0.1")
		self.ll_port = bot.settings_dict.get("lavalink_port",2333)
		self.ll_uri  = bot.settings_dict.get("lavalink_rest_uri","http://127.0.0.1:2333")
		self.ll_pass = bot.settings_dict.get("lavalink_password","youshallnotpass")
		self.ll_id   = bot.settings_dict.get("lavalink_identifier","TEST")
		self.ll_reg  = bot.settings_dict.get("lavalink_region","us_central")
		global Utils, DisplayName
		Utils = self.bot.get_cog("Utils")
		DisplayName = self.bot.get_cog("DisplayName")
		# Setup Wavelink
		if not hasattr(self.bot,'wavelink'): self.bot.wavelink = wavelink.Client(bot=self.bot)
		self.bot.loop.create_task(self.start_nodes())

	async def download(self, url):
		url = url.strip("<>")
		# Set up a temp directory
		temp = tempfile.mkdtemp()
		temp_path = os.path.join(temp,url.rsplit('/', 1)[-1].split("?")[0])
		try:
			dl = await DL.async_dl(url)
			assert dl != None
			with open(temp_path,"wb") as f:
				f.write(dl)
			assert os.path.isfile(temp_path)
		except:
			shutil.rmtree(temp,ignore_errors=True)
			temp_path = None
		return temp_path

	async def start_nodes(self):
		node = self.bot.wavelink.get_best_node()
		if not node:
			node = await self.bot.wavelink.initiate_node(host=self.ll_host,
				port=self.ll_port,
				rest_uri=self.ll_uri,
				password=self.ll_pass,
				identifier=self.ll_id,
				region=self.ll_reg)
		node.set_hook(self.on_event_hook)

	def skip_pop(self, ctx):
		# Pops the current skip list and dispatches the "skip_song" event
		self.skips.pop(str(ctx.guild.id),None)
		self.bot.dispatch("skip_song",ctx)

	def dict_pop(self, ctx):
		# Pops the current guild id from all the class dicts
		guild = ctx if isinstance(ctx,discord.Guild) else ctx.guild if isinstance(ctx,discord.ext.commands.Context) else ctx.channel.guild if isinstance(ctx,discord.VoiceState) else None
		self.queue.pop(str(guild.id),None)
		self.vol.pop(str(guild.id),None)
		self.skips.pop(str(guild.id),None)
		self.loop.pop(str(guild.id),None)
		self.data.pop(str(guild.id),None)

	async def _check_role(self, ctx):
		if Utils.is_bot_admin(ctx):
			return True
		promoArray = self.settings.getServerStat(ctx.guild, "DJArray", [])
		delay = self.settings.getServerStat(ctx.guild, "MusicDeleteDelay", 20)
		if not len(promoArray):
			await Message.EmbedText(title="♫ There are no DJ roles set yet.  Use `{}adddj [role]` to add some.".format(ctx.prefix),color=ctx.author,delete_after=delay).send(ctx)
			return None
		for role in promoArray:
			if ctx.guild.get_role(int(role["ID"])) in ctx.author.roles:
				return True
		await Message.EmbedText(title="♫ You need a DJ role to do that!",color=ctx.author,delete_after=delay).send(ctx)
		return False

	async def resolve_search(self, ctx, url, shuffle = False):
		# Helper method to search for songs/resolve urls and add the contents to the queue
		delay = self.settings.getServerStat(ctx.guild, "MusicDeleteDelay", 20)
		message = await Message.EmbedText(
			title="♫ Searching For: {}...".format(url.strip("<>")),
			color=ctx.author
			).send(ctx)
		data = await self.add_to_queue(ctx, url, message, shuffle)
		if data == False: return # Something else happened, ignore it.
		if data == None:
			# Nothing found
			return await Message.EmbedText(title="♫ I couldn't find anything for that search!",description="Try using more specific search terms, or pass a url instead.",color=ctx.author,delete_after=delay).edit(ctx,message)
		if isinstance(data,wavelink.Track):
			# Just got one - let's display it
			await Message.Embed(
				title="♫ Enqueued: {}".format(data.title),
				description="Requested by {}".format(ctx.author.mention),
				fields=[
					{"name":"Duration","value":self.format_duration(data.duration,data),"inline":False}
				],
				color=ctx.author,
				thumbnail=data.thumb,
				url=data.uri,
				delete_after=delay
			).edit(ctx,message)
		else:
			await Message.EmbedText(
				title="♫ Added {}playlist: {} ({} song{})".format("shuffled " if shuffle else "",data.data["playlistInfo"]["name"],len(data.tracks),"" if len(data.tracks)==1 else "s"),
				description="Requested by {}".format(ctx.author.mention),
				url=data.search,
				delete_after=delay,
				color=ctx.author
			).edit(ctx,message)

	async def add_to_queue(self, ctx, url, message, shuffle = False):
		delay = self.settings.getServerStat(ctx.guild, "MusicDeleteDelay", 20)
		queue = self.queue.get(str(ctx.guild.id),[])
		url = url.strip('<>')
		# Check if url - if not, remove /
		urls = Utils.get_urls(url)
		url = urls[0] if len(urls) else "ytsearch:"+url.replace('/', '')
		tracks = await self.bot.wavelink.get_tracks(url)
		if tracks == None: return None
		if (url.startswith("ytsearch:") or isinstance(tracks,list)) and len(tracks):
			if self.settings.getServerStat(ctx.guild, "YTMultiple", False):
				# We want to let the user pick
				list_show = "Please select the number of the track you'd like to add:"
				index, message = await PickList.Picker(
					title=list_show,
					list=[x.info['title'] for x in tracks[:5]],
					ctx=ctx,
					message=message
				).pick()
				if index < 0:
					if index == -3:
						await message.edit(content="Something went wrong :(",delete_after=delay)
					elif index == -2:
						await message.edit(content="Times up!  We can search for music another time.",delete_after=delay)
					else:
						await message.edit(content="Aborting!  We can search for music another time.",delete_after=delay)
					return False
				# Got the index of the track to add
				tracks = tracks[index]
			else:
				# We only want the first entry
				tracks = tracks[0]
		player = self.bot.wavelink.get_player(ctx.guild.id)
		if isinstance(tracks,wavelink.Track):
			# Only got one item - add it to the queue
			tracks.info["added_by"] = ctx.author
			tracks.info["ctx"] = ctx
			tracks.info["search"] = url
			# Let's also get the seek position if needed
			try:
				seek_str = next((x[2:] for x in url.split("?")[1].split("&") if x.lower().startswith("t=")),"0").lower()
				values = [x for x in re.split("(\\d+)",seek_str) if x]
				# We should have a list of numbers and non-numbers.  Let's total the values
				total_time = 0
				last_type = "s" # Assume seconds in case no value is given
				for x in values[::-1]:
					if not x.isdigit():
						# Save the type
						last_type = x
						continue
					# We have a digit, let's calculate and add our time
					# Only factor hours, minutes, seconds - anything else is ignored
					if last_type == "h":
						total_time += int(x) * 3600
					elif last_type == "m":
						total_time += int(x) * 60
					elif last_type == "s":
						total_time += int(x)
				seek_pos = total_time
			except Exception as e:
				seek_pos = 0
			tracks.info["seek"] = seek_pos
			queue.append(tracks)
			self.queue[str(ctx.guild.id)] = queue
			if not player.is_playing and not player.is_paused:
				self.bot.dispatch("next_song",ctx)
			return tracks
		# Have more than one item - iterate them
		tracks.search = url
		try: starting_index = next((int(x[6:])-1 for x in url.split("?")[1].split("&") if x.lower().startswith("index=")),0)
		except: starting_index = 0
		starting_index = 0 if starting_index >= len(tracks.tracks) or starting_index < 0 else starting_index # Ensure we're not out of bounds
		tracks.tracks = tracks.tracks[starting_index:]
		if shuffle: random.shuffle(tracks.tracks) # Shuffle before adding
		for index,track in enumerate(tracks.tracks):
			track.info["added_by"] = ctx.author
			track.info["ctx"] = ctx
			queue.append(track)
			self.queue[str(ctx.guild.id)] = queue
			if index == 0 and not player.is_playing and not player.is_paused:
				self.bot.dispatch("next_song",ctx)
		return tracks

	def format_duration(self, dur, data = False):
		if data and data.is_stream:
			return "[Live Stream]"
		dur = dur // 1000 # ms to seconds
		hours = dur // 3600
		minutes = (dur % 3600) // 60
		seconds = dur % 60
		return "{:02d}h:{:02d}m:{:02d}s".format(hours, minutes, seconds)

	def format_elapsed(self, player, track):
		progress = player.last_position
		total    = track.duration
		return "{} -- {}".format(self.format_duration(progress),self.format_duration(total,track))

	def progress_bar(self,player,track,bar_width=27,show_percent=True,include_time=False):
		# Returns a [#####-----] XX.x% style progress bar
		progress = player.last_position
		total    = track.duration if not track.is_stream else 0
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
			time_prefix = "{} - {}\n".format(self.format_duration(progress),self.format_duration(total,track))
			bar = time_prefix + bar
		return bar

	def progress_moon(self,player,track,moon_count=10,show_percent=True,include_time=False):
		# Make some shitty moon memes or something... thanks Midi <3
		progress = player.last_position
		total    = track.duration if not track.is_stream else 0
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
			time_prefix = "{} - {}\n".format(self.format_duration(progress),self.format_duration(total,track))
			bar = time_prefix + bar
		return bar

	def print_eq(self, eq, max_len = 5):
		# EQ values are from -0.25 (muted) to 0.25 (doubled)
		bar      = "│" # "║"
		topleft  = "┌" # "╔"
		topright = "┐" # "╗"
		botleft  = "└" # "╚"
		botright = "┘" # "╝"
		cap      = "─" # "═"
		emp      = " "
		inner    = " "
		sep      = "─" # "═"
		sup      = "┴" # "╩"
		sdn      = "┬" # "╦"
		lpad     = ""
		eq_list  = []
		nums     = ""
		vals     = ""
		for band,value in eq:
			value *= 4 # Quadruple it for -1 to 1 range
			ourbar = math.ceil(abs(value)*max_len)
			vals += str(ourbar if value > 0 else -1*ourbar).rjust(2)+" "
			nums += str(band+1).rjust(2)+" "
			# Check if positive or negative
			if value == 0:
				# They're all 0, nothing to display
				our_cent = our_left = our_right = emp*max_len + sep + emp*max_len
			elif value > 0:
				# Let's draw a bar going up
				our_left  = emp*max_len + sup + bar*(ourbar-1)   + topleft  + emp*(max_len-ourbar)
				our_cent  = emp*max_len + sep + inner*(ourbar-1) + cap      + emp*(max_len-ourbar)
				our_right = emp*max_len + sup + bar*(ourbar-1)   + topright + emp*(max_len-ourbar)
			else:
				# Let's draw a bar going down
				our_left  = emp*(max_len-ourbar) + botleft  + bar*(ourbar-1) + sdn + emp*max_len
				our_cent  = emp*(max_len-ourbar) + cap    + inner*(ourbar-1) + sep + emp*max_len
				our_right = emp*(max_len-ourbar) + botright + bar*(ourbar-1) + sdn + emp*max_len
			our_left  = [x for x in our_left][::-1]
			our_cent  = [x for x in our_cent][::-1]
			our_right = [x for x in our_right][::-1]
			eq_list.extend([our_left,our_cent,our_right])
		# Rotate the eq 90 degrees
		graph = "```\n{}\n{}\n{}\n{}\n{}\n{}\n{}\n```".format(
			"Bands".center(len(nums),sep),
			nums,
			sep*(len(nums)),
			"\n".join(["{}{}{}".format(lpad,x,lpad) for x in map("".join, zip(*eq_list))]),
			"Values".center(len(vals),sep),
			vals,
			sep*(len(vals))
		)
		return graph

	@commands.Cog.listener()
	async def on_loaded_extension(self, ext):
		# See if we were loaded
		if not self._is_submodule(ext.__name__, self.__module__):
			return

	def _is_submodule(self, parent, child):
		return parent == child or child.startswith(parent + ".")

	@commands.Cog.listener()
	async def on_unloaded_extension(self, ext):
		# Called to shut things down
		if not self._is_submodule(ext.__name__, self.__module__):
			return
		# Stop all players
		for x in self.bot.guilds:
			player = self.bot.wavelink.players.get(x.id,None)
			if player: await player.destroy()

	async def on_event_hook(self, event):
		# Node callback
		# print(event)
		if isinstance(event,(wavelink.TrackEnd, wavelink.TrackException, wavelink.TrackStuck)):
			# get ctx from data object
			try: ctx = self.data[str(event.player.guild_id)].info["ctx"]
			except: return # No ctx, no next_song :(
			# Check if we had an issue
			delay = self.settings.getServerStat(ctx.guild, "MusicDeleteDelay", 20)
			if isinstance(event,(wavelink.TrackException,wavelink.TrackStuck)):
				await Message.EmbedText(title="♫ Something went wrong playing that song!",color=ctx.author,delete_after=delay).send(ctx)
				return await event.player.stop() # Sends the TrackStop event to move to the next song as needed
			self.bot.dispatch("next_song",ctx)

	@commands.Cog.listener()
	async def on_skip_song(self,ctx):
		player = self.bot.wavelink.players.get(ctx.guild.id,None)
		if player != None and player.is_connected:
			await player.stop()

	@commands.Cog.listener()
	async def on_play_next(self,player,track):
		# Just a helper to play the next song without hanging things up
		await player.play(track)
		# Seek if we need to
		seek = track.info.get("seek",0)*1000
		if seek and not seek > track.duration: await player.seek(track.info["seek"]*1000)
	
	@commands.Cog.listener()
	async def on_next_song(self,ctx,error=None):
		delay = self.settings.getServerStat(ctx.guild, "MusicDeleteDelay", 20)
		task = "playing"
		if error:
			print(error)
		# Gather our player
		player = self.bot.wavelink.players.get(ctx.guild.id,None)
		if player == None: return # Nothing to do here
		# Try to cleanup before starting
		if not player.is_connected:
			# Stopped - or late-fired signal - destroy the player
			return await player.destroy()
		# Check if we need to stop the player (shouldn't be required, but *just in case*)
		if player.is_playing or player.is_paused: return await player.stop() # This will fire another "next_song" event so we bail here
		# Gather up the queue
		queue = self.queue.get(str(ctx.guild.id),[])
		if self.loop.get(str(ctx.guild.id),False) and self.data.get(str(ctx.guild.id),None):
			# Re-add the track to the end of the playlist
			queue.append(self.data.get(str(ctx.guild.id),None))
		if not len(queue):
			# Nothing to play - strip the last played song and bail
			return await Message.EmbedText(title="♫ End of playlist!",color=ctx.author,delete_after=delay).send(ctx)
		# Get the first song in the list and start playing it
		data = queue.pop(0)
		# Save the current data in case of repeats
		self.data[str(ctx.guild.id)] = data
		# Set the volume - default to 50
		volume = self.vol[str(ctx.guild.id)] if str(ctx.guild.id) in self.vol else self.settings.getServerStat(ctx.guild, "MusicVolume", 100)
		eq = wavelink.eqs.Equalizer.build(levels=self.settings.getServerStat(ctx.guild, "MusicEqualizer", wavelink.eqs.Equalizer.flat().raw))
		if not player.volume == volume/2: await player.set_volume(volume/2)
		if not player.eq.raw == eq.raw:   await player.set_eq(eq)
		player._equalizer = eq # Dirty hack to work around a bug in wavelink
		async with ctx.typing():
			self.bot.dispatch("play_next",player,data)
		await Message.Embed(
			title="♫ Now {}: {}".format(task.capitalize(), data.title),
			fields=[
				{"name":"Duration","value":self.format_duration(data.duration,data),"inline":False}
			],
			description="Requested by {}".format(data.info["added_by"].mention),
			color=ctx.author,
			url=data.uri,
			thumbnail=data.thumb,
			delete_after=delay
		).send(ctx)

	@commands.Cog.listener()
	async def on_voice_state_update(self, user, before, after):
		if not user.guild or not before.channel or (user.bot and user.id != self.bot.user.id):
			return # No guild, someone joined, or the user is a bot that's not us
		player = self.bot.wavelink.players.get(before.channel.guild.id,None)
		if player == None or not player.is_connected:
			return # Player is borked or not connected - just bail
		if int(player.channel_id) != before.channel.id:
			return # No player to worry about, or someone left a different channel - ignore
		if user.id == self.bot.user.id and not after.channel:
			# We were disconnected somehow - try to reconnect and keep playing
			return await player.connect(before.channel.id)
		if len([x for x in before.channel.members if not x.bot]) > 0:
			return # At least one non-bot user
		# if we made it here - then we're alone - disconnect and destroy
		self.dict_pop(user.guild)
		if player: await player.destroy()

	@commands.command(pass_context=True)
	async def searchlist(self, ctx, yes_no = None):
		"""Gets or sets whether or not the server will show a list of options when searching with the play command - or if it'll just pick the first (admin only)."""
		if not await Utils.is_admin_reply(ctx): return
		await ctx.send(Utils.yes_no_setting(ctx,"Music player search list","YTMultiple",yes_no))

	@commands.command()
	async def savepl(self, ctx, *, options = ""):
		"""Saves the current playlist to a json file that can be loaded later.
		
		Note that the structure of this file is very specific and alterations may not work.
		
		Available options:

		ts : Exclude the timestamp of the currently playing song."""
		delay = self.settings.getServerStat(ctx.guild, "MusicDeleteDelay", 20)
		player = self.bot.wavelink.players.get(ctx.guild.id,None)
		if player == None or not player.is_connected:
			return await Message.EmbedText(title="♫ Not connected to a voice channel!",color=ctx.author,delete_after=delay).send(ctx)
		# Get the options
		timestamp = True
		time = 0
		for x in options.split():
			if x.lower() == "ts": timestamp = False
		# Let's save the playlist
		current = self.data.get(str(ctx.guild.id),None)
		queue = [x for x in self.queue.get(str(ctx.guild.id),[])]
		if current and (player.is_playing or player.is_paused):
			if timestamp and current.info.get("uri"):
				current.info["seek"] = int(player.last_position/1000)
			queue.insert(0,current)
		if not len(queue):
			return await Message.EmbedText(title="♫ No playlist to save!",color=ctx.author,delete_after=delay).send(ctx)
		message = await Message.EmbedText(title="♫ Gathering info...",color=ctx.author).send(ctx)
		songs = []
		for x in queue:
			if x.uri == None: continue # No link
			# Strip the added by and ctx keys
			x.info.pop("added_by",None)
			x.info.pop("ctx",None)
			x.info["id"] = x.id
			songs.append(x.info)
		await Message.EmbedText(title="♫ Saving and uploading...",color=ctx.author).edit(ctx,message)
		temp = tempfile.mkdtemp()
		temp_json = os.path.join(temp,"playlist.json")
		try:
			json.dump(songs,open(temp_json,"w"),indent=2)
			await ctx.send(file=discord.File(temp_json))
		except Exception as e:
			return await Message.EmbedText(title="♫ An error occurred creating the playlist!",description=str(e),color=ctx.author).edit(ctx,message)
		finally:
			shutil.rmtree(temp,ignore_errors=True)
		return await Message.EmbedText(title="♫ Uploaded playlist!",color=ctx.author).edit(ctx,message)

	async def _load_playlist_from_url(self, url, ctx, shuffle = False):
		delay = self.settings.getServerStat(ctx.guild, "MusicDeleteDelay", 20)
		player = self.bot.wavelink.players.get(ctx.guild.id,None)
		if player == None or not player.is_connected:
			return await Message.EmbedText(title="♫ Not connected to a voice channel!",color=ctx.author,delete_after=delay).send(ctx)
		if url == None and len(ctx.message.attachments) == 0:
			return await ctx.send("Usage: `{}loadpl [url or attachment]`".format(ctx.prefix))
		if url == None:
			url = ctx.message.attachments[0].url
		message = await Message.EmbedText(title="♫ Downloading...",color=ctx.author).send(ctx)
		path = await self.download(url)
		if not path:
			return await Message.EmbedText(title="♫ Couldn't download playlist!",color=ctx.author).edit(ctx,message)
		try:
			playlist = json.load(open(path))
		except Exception as e:
			return await Message.EmbedText(title="♫ Couldn't serialize playlist!",description=str(e),color=ctx.author,delete_after=delay).edit(ctx,message)
		finally:
			shutil.rmtree(os.path.dirname(path),ignore_errors=True)
		if not len(playlist): return await Message.EmbedText(title="♫ Playlist is empty!",color=ctx.author).edit(ctx,message)
		if not isinstance(playlist,list): return await Message.EmbedText(title="♫ Playlist json is incorrectly formatted!",color=ctx.author).edit(ctx,message)
		if shuffle:
			random.shuffle(playlist)
		# Let's walk the items and add them
		queue = self.queue.get(str(ctx.guild.id),[])
		for x in playlist:
			if not "id" in x or not isinstance(x["id"],str): continue # id missing or not string - skip
			x["added_by"] = ctx.author
			x["ctx"] = ctx
			queue.append(wavelink.Track(x["id"],x))
		# Reset the queue as needed
		self.queue[str(ctx.guild.id)] = queue
		await Message.EmbedText(title="♫ Added {} {}song{} from playlist!".format(len(playlist),"shuffled " if shuffle else "", "" if len(playlist) == 1 else "s"),color=ctx.author,delete_after=delay).edit(ctx,message)
		if not player.is_playing and not player.is_paused:
			self.bot.dispatch("next_song",ctx)

	@commands.command()
	async def loadpl(self, ctx, *, url = None):
		"""Loads the passed playlist json data.  Accepts a url - or picks the first attachment.
		
		Note that the structure of this file is very specific and alterations may not work.
		
		Only files dumped via the savepl command are supported."""
		await self._load_playlist_from_url(url, ctx)

	@commands.command()
	async def shufflepl(self, ctx, *, url = None):
		"""Loads and shuffles the passed playlist json data.  Accepts a url - or picks the first attachment.
		
		Note that the structure of this file is very specific and alterations may not work.
		
		Only files dumped via the savepl command are supported."""
		await self._load_playlist_from_url(url, ctx, shuffle=True)

	@commands.command()
	async def summon(self, ctx, *, channel = None):
		"""Joins the summoner's voice channel."""
		await ctx.invoke(self.join,channel=channel)

	@commands.command()
	async def join(self, ctx, *, channel = None):
		"""Joins a voice channel."""

		delay = self.settings.getServerStat(ctx.guild, "MusicDeleteDelay", 20)
		if channel == None:
			if not ctx.author.voice:
				return await Message.EmbedText(title="♫ You need to pass a voice channel for me to join!",color=ctx.author,delete_after=delay).send(ctx)
			channel = ctx.author.voice.channel
		else:
			channel = DisplayName.channelForName(channel, ctx.guild, "voice")
		if not channel:
			return await Message.EmbedText(title="♫ I couldn't find that voice channel!",color=ctx.author,delete_after=delay).send(ctx)
		player = self.bot.wavelink.get_player(ctx.guild.id)
		if player.is_connected:
			if not (player.is_paused or player.is_playing):
				await player.connect(channel.id)
				return await Message.EmbedText(title="♫ Ready to play music in {}!".format(channel),color=ctx.author,delete_after=delay).send(ctx)
			else:
				return await Message.EmbedText(title="♫ I'm already playing music in {}!".format(ctx.guild.get_channel(int(player.channel_id))),color=ctx.author,delete_after=delay).send(ctx)
		await player.connect(channel.id)
		await Message.EmbedText(title="♫ Ready to play music in {}!".format(channel),color=ctx.author,delete_after=delay).send(ctx)

	@commands.command()
	async def play(self, ctx, *, url = None):
		"""Plays from a url (almost anything youtube_dl supports) or resumes a currently paused song."""

		delay = self.settings.getServerStat(ctx.guild, "MusicDeleteDelay", 20)
		player = self.bot.wavelink.get_player(ctx.guild.id)
		if not player.is_connected:
			return await Message.EmbedText(title="♫ I am not connected to a voice channel!",color=ctx.author,delete_after=delay).send(ctx)
		if player.is_paused and url == None:
			# We're trying to resume
			await player.set_pause(False)
			data = self.data.get(str(ctx.guild.id))
			return await Message.EmbedText(title="♫ Resumed: {}".format(data.title),color=ctx.author,delete_after=delay).send(ctx)
		if url == None:
			return await Message.EmbedText(title="♫ You need to pass a url or search term!",color=ctx.author,delete_after=delay).send(ctx)
		# Add our url to the queue
		await self.resolve_search(ctx, url)

	@commands.command()
	async def pause(self, ctx):
		"""Pauses the currently playing song."""

		delay = self.settings.getServerStat(ctx.guild, "MusicDeleteDelay", 20)
		player = self.bot.wavelink.players.get(ctx.guild.id,None)
		if player == None or not player.is_connected:
			return await Message.EmbedText(title="♫ Not connected to a voice channel!",color=ctx.author,delete_after=delay).send(ctx)
		if player.is_paused: # Just toggle play
			return await ctx.invoke(self.play)
		if not player.is_playing:
			return await Message.EmbedText(title="♫ Not playing anything!",color=ctx.author,delete_after=delay).send(ctx)
		# Pause the track
		await player.set_pause(True)
		data = self.data.get(str(ctx.guild.id))
		await Message.EmbedText(title="♫ Paused: {}".format(data.title),color=ctx.author,delete_after=delay).send(ctx)

	@commands.command()
	async def paused(self, ctx, *, moons = None):
		"""Lists whether or not the player is paused.  Synonym of the playing command."""
		
		await ctx.invoke(self.playing,moons=moons)

	@commands.command()
	async def resume(self, ctx):
		"""Resumes the song if paused."""

		delay = self.settings.getServerStat(ctx.guild, "MusicDeleteDelay", 20)
		player = self.bot.wavelink.players.get(ctx.guild.id,None)
		if player == None or not player.is_connected:
			return await Message.EmbedText(title="♫ I am not connected to a voice channel!",color=ctx.author,delete_after=delay).send(ctx)
		if not player.is_paused:
			return await Message.EmbedText(title="♫ Not currently paused!",color=ctx.author,delete_after=delay).send(ctx)
		# We're trying to resume
		await player.set_pause(False)
		data = self.data.get(str(ctx.guild.id))
		await Message.EmbedText(title="♫ Resumed: {}".format(data.title),color=ctx.author,delete_after=delay).send(ctx)

	@commands.command()
	async def unplay(self, ctx, *, song_number = None):
		"""Removes the passed song number from the queue.  You must be the requestor, or an admin to remove it.  Does not include the currently playing song."""
		
		delay = self.settings.getServerStat(ctx.guild, "MusicDeleteDelay", 20)
		player = self.bot.wavelink.players.get(ctx.guild.id,None)
		if player == None or not player.is_connected:
			return await Message.EmbedText(title="♫ I am not connected to a voice channel!",color=ctx.author,delete_after=delay).send(ctx)
		queue = self.queue.get(str(ctx.guild.id),[])
		if not len(queue):
			# No songs in queue
			return await Message.EmbedText(title="♫ No songs in queue!", description="If you want to bypass a currently playing song, use `{}skip` instead.".format(ctx.prefix),color=ctx.author,delete_after=delay).send(ctx)
		try:
			song_number = int(song_number)-1
		except:
			return await Message.EmbedText(title="♫ Not a valid song number!",color=ctx.author,delete_after=delay).send(ctx)
		if song_number < 0 or song_number > len(queue):
			return await Message.EmbedText(title="♫ Out of bounds!  Song number must be between 2 and {}.".format(len(queue)),color=ctx.author,delete_after=delay).send(ctx)
		# Get the song at the index
		song = queue[song_number]
		if song.info.get("added_by",None) == ctx.author or Utils.is_bot_admin(ctx):
			queue.pop(song_number)
			return await Message.EmbedText(title="♫ Removed {} at position {}!".format(song.title,song_number+1),color=ctx.author,delete_after=delay).send(ctx)
		await Message.EmbedText(title="♫ You can only remove songs you requested!", description="Only {} or an admin can remove that song!".format(song["added_by"].mention),color=ctx.author,delete_after=delay).send(ctx)

	@commands.command()
	async def unqueue(self, ctx):
		"""Removes all songs you've added from the queue (does not include the currently playing song).  Admins remove all songs from the queue."""

		delay = self.settings.getServerStat(ctx.guild, "MusicDeleteDelay", 20)
		player = self.bot.wavelink.players.get(ctx.guild.id,None)
		if player == None or not player.is_connected:
			return await Message.EmbedText(title="♫ I am not connected to a voice channel!",color=ctx.author,delete_after=delay).send(ctx)
		queue = self.queue.get(str(ctx.guild.id),[])
		if not len(queue):
			# No songs in queue
			return await Message.EmbedText(title="♫ No songs in queue!", description="If you want to bypass a currently playing song, use `{}skip` instead.".format(ctx.prefix),color=ctx.author,delete_after=delay).send(ctx)
		removed = 0
		new_queue = []
		for song in queue:
			if song.info.get("added_by",None) == ctx.author or Utils.is_bot_admin(ctx):
				removed += 1
			else:
				new_queue.append(song)
		self.queue[str(ctx.guild.id)] = new_queue
		if removed > 0:
			return await Message.EmbedText(title="♫ Removed {} song{} from queue!".format(removed,"" if removed == 1 else "s"),color=ctx.author,delete_after=delay).send(ctx)
		await Message.EmbedText(title="♫ You can only remove songs you requested!", description="Only an admin can remove all queued songs!",color=ctx.author,delete_after=delay).send(ctx)

	@commands.command()
	async def shuffle(self, ctx, *, url = None):
		"""Shuffles the current queue. If you pass a playlist url or search term, it first shuffles that, then adds it to the end of the queue."""

		delay = self.settings.getServerStat(ctx.guild, "MusicDeleteDelay", 20)
		player = self.bot.wavelink.players.get(ctx.guild.id,None)
		if player == None or not player.is_connected:
			if url == None: # No need to connect to shuffle nothing
				return await Message.EmbedText(title="♫ I am not connected to a voice channel!",color=ctx.author,delete_after=delay).send(ctx)
			if not ctx.author.voice:
				return await Message.EmbedText(title="♫ You are not connected to a voice channel!",color=ctx.author,delete_after=delay).send(ctx)
			await player.connect(ctx.author.voice.channel.id)
		if url == None:
			queue = self.queue.get(str(ctx.guild.id),[])
			if not len(queue):
				# No songs in queue
				return await Message.EmbedText(title="♫ No songs in queue!",color=ctx.author,delete_after=delay).send(ctx)
			random.shuffle(queue)
			self.queue[str(ctx.guild.id)] = queue
			return await Message.EmbedText(title="♫ Shuffled {} song{}!".format(len(queue),"" if len(queue) == 1 else "s"),color=ctx.author,delete_after=delay).send(ctx)
		# We're adding a new song/playlist/search shuffled to the queue
		await self.resolve_search(ctx, url, shuffle=True)

	@commands.command()
	async def playing(self, ctx, *, moons = None):
		"""Lists the currently playing song if any."""

		delay = self.settings.getServerStat(ctx.guild, "MusicDeleteDelay", 20)
		player = self.bot.wavelink.players.get(ctx.guild.id,None) if ctx.guild.id in self.bot.wavelink.players else None
		if player == None or not player.is_connected or not (player.is_playing or player.is_paused):
			# No client - and we're not playing or paused
			return await Message.EmbedText(
				title="♫ Currently Playing",
				color=ctx.author,
				description="Not playing anything.",
				delete_after=delay
			).send(ctx)
		data = self.data.get(str(ctx.guild.id))
		play_text = "Playing" if (player.is_playing and not player.is_paused) else "Paused"
		cv = int(player.volume*2)
		await Message.Embed(
			title="♫ Currently {}: {}".format(play_text,data.title),
			description="Requested by {} -- Volume at {}%".format(data.info["added_by"].mention,cv),
			color=ctx.author,
			fields=[
				{"name":"Elapsed","value":self.format_elapsed(player,data),"inline":False},
				{"name":"Progress","value":self.progress_moon(player,data) if moons and moons.lower() in ["moon","moons","moonme","moon me"] else self.progress_bar(player,data),"inline":False}
			],
			url=data.uri,
			thumbnail=data.thumb,
			delete_after=delay
		).send(ctx)

	@commands.command()
	async def playingin(self, ctx):
		"""Shows the number of servers the bot is currently playing music in."""

		delay = self.settings.getServerStat(ctx.guild, "MusicDeleteDelay", 20)
		server_list = []
		for x in self.bot.wavelink.players:
			server = self.bot.get_guild(int(x))
			if not server: continue
			p = self.bot.wavelink.get_player(x)
			if p.is_playing and not p.is_paused:
				server_list.append({"name":server.name,"value":p.current.info.get("title","Unknown title")})
		msg = "♫ Playing music in {:,} of {:,} server{}.".format(len(server_list), len(self.bot.guilds), "" if len(self.bot.guilds) == 1 else "s")
		if len(server_list): await PickList.PagePicker(title=msg,list=server_list,ctx=ctx).pick()
		else: await Message.EmbedText(title=msg,color=ctx.author,delete_after=delay).send(ctx)

	@commands.command(aliases=["queue"])
	async def playlist(self, ctx):
		"""Lists the queued songs in the playlist."""

		delay = self.settings.getServerStat(ctx.guild, "MusicDeleteDelay", 20)
		player = self.bot.wavelink.players.get(ctx.guild.id,None)
		if player == None or not player.is_connected or not (player.is_playing or player.is_paused):
			return await Message.EmbedText(
				title="♫ Current Playlist",
				color=ctx.author,
				description="Not playing anything.",
				delete_after=delay
			).send(ctx)
		data = self.data.get(str(ctx.guild.id))
		play_text = "Playing" if player.is_playing else "Paused"
		queue = self.queue.get(str(ctx.guild.id),[])
		fields = [{"name":"{}".format(data.title),"value":"Currently {} - at {} - Requested by {} - [Link]({})".format(
			play_text,
			self.format_elapsed(player,data),
			data.info["added_by"].mention,
			data.uri),"inline":False},
		]
		if len(queue):
			total_time = 0
			total_streams = 0
			time_string = stream_string = ""
			for x in queue:
				t = x.duration
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
			x += 1 # brings this up to the proper numbering
			fields.append({
				"name":"{}. {}".format(x,y.title),
				"value":"{} - Requested by {} - [Link]({})".format(self.format_duration(y.duration,y),y.info["added_by"].mention,y.uri),
				"inline":False})
		if self.loop.get(str(ctx.guild.id),False):
			pl_string = " - Repeat Enabled"
		else:
			pl_string = ""
		if len(fields) <= 11:
			await Message.Embed(
				title="♫ Current Playlist{}".format(pl_string),
				color=ctx.author,
				fields=fields,
				delete_after=delay,
				pm_after=15
			).send(ctx)
		else:
			page,message = await PickList.PagePicker(title="♫ Current Playlist{}".format(pl_string),list=fields,timeout=60 if not delay else delay,ctx=ctx).pick()
			if delay:
				await message.delete()

	@commands.command()
	async def unskip(self, ctx):
		"""Removes your vote to skip the current song."""
		
		delay = self.settings.getServerStat(ctx.guild, "MusicDeleteDelay", 20)
		player = self.bot.wavelink.players.get(ctx.guild.id,None)
		if player == None or player == None or not player.is_connected:
			return await Message.EmbedText(title="♫ Not connected to a voice channel!",color=ctx.author,delete_after=delay).send(ctx)
		if not player.is_playing:
			return await Message.EmbedText(title="♫ Not playing anything!",color=ctx.author,delete_after=delay).send(ctx)
		
		skips = self.skips.get(str(ctx.guild.id),[])
		if not ctx.author.id in skips: return await Message.EmbedText(title="♫ You haven't voted to skip this song!".format(len(new_skips),needed_skips),color=ctx.author,delete_after=delay).send(ctx)
		# We did vote - remove that
		skips.remove(ctx.author.id)
		self.skips[str(ctx.guild.id)] = skips
		channel = ctx.guild.get_channel(int(player.channel_id))
		if not channel:
			return await Message.EmbedText(title="♫ Something went wrong!",description="That voice channel doesn't seem to exist anymore...",color=ctx.author,delete_after=delay).send(ctx)
		# Let's get the number of valid skippers
		skippers = [x for x in channel.members if not x.bot]
		needed_skips = math.ceil(len(skippers)/2)
		await Message.EmbedText(title="♫ You have removed your vote to skip - {}/{} votes entered - {} more needed to skip!".format(len(skips),needed_skips,needed_skips-len(skips)),color=ctx.author,delete_after=delay).send(ctx)

	@commands.command()
	async def skip(self, ctx):
		"""Adds your vote to skip the current song.  50% or more of the non-bot users need to vote to skip a song.  Original requestors and admins can skip without voting."""

		delay = self.settings.getServerStat(ctx.guild, "MusicDeleteDelay", 20)
		player = self.bot.wavelink.players.get(ctx.guild.id,None)
		if player == None or not player.is_connected:
			return await Message.EmbedText(title="♫ Not connected to a voice channel!",color=ctx.author,delete_after=delay).send(ctx)
		if not player.is_playing:
			return await Message.EmbedText(title="♫ Not playing anything!",color=ctx.author,delete_after=delay).send(ctx)
		# Check for added by first, then check admin
		data = self.data.get(str(ctx.guild.id))
		if Utils.is_bot_admin(ctx):
			self.skip_pop(ctx)
			return await Message.EmbedText(title="♫ Admin override activated - skipping!",color=ctx.author,delete_after=delay).send(ctx)	
		if data.info.get("added_by",None) == ctx.author:
			self.skip_pop(ctx)
			return await Message.EmbedText(title="♫ Requestor chose to skip - skipping!",color=ctx.author,delete_after=delay).send(ctx)
		# At this point, we're not admin, and not the requestor, let's make sure we're in the same vc
		if not ctx.author.voice or not ctx.author.voice.channel.id == int(player.channel_id):
			return await Message.EmbedText(title="♫ You have to be in the same voice channel as me to use that!",color=ctx.author,delete_after=delay).send(ctx)
		
		# Do the checking here to validate we can use this and etc.
		skips = self.skips.get(str(ctx.guild.id),[])
		# Relsolve the skips
		new_skips = []
		channel = ctx.guild.get_channel(int(player.channel_id))
		if not channel:
			return await Message.EmbedText(title="♫ Something went wrong!",description="That voice channel doesn't seem to exist anymore...",color=ctx.author,delete_after=delay).send(ctx)
		for x in skips:
			member = ctx.guild.get_member(x)
			if not member or member.bot:
				continue
			if not member in channel.members:
				continue
			# Got a valid user who's in the skip list and the voice channel
			new_skips.append(x)
		# Check if we're not already in the skip list
		if not ctx.author.id in new_skips:
			new_skips.append(ctx.author.id)
		# Let's get the number of valid skippers
		skippers = [x for x in channel.members if not x.bot]
		needed_skips = math.ceil(len(skippers)/2)
		if len(new_skips) >= needed_skips:
			# Got it!
			self.skip_pop(ctx)
			return await Message.EmbedText(title="♫ Skip threshold met ({}/{}) - skipping!".format(len(new_skips),needed_skips),color=ctx.author,delete_after=delay).send(ctx)
		# Update the skips
		self.skips[str(ctx.guild.id)] = new_skips
		await Message.EmbedText(title="♫ Skip threshold not met - {}/{} skip votes entered - need {} more!".format(len(new_skips),needed_skips,needed_skips-len(new_skips)),color=ctx.author,delete_after=delay).send(ctx)

	@commands.command()
	async def seek(self, ctx, position = None):
		"""Seeks to the passed position in the song if possible.  Position should be in seconds or in HH:MM:SS format."""

		if position == None or position.lower() in ["moon","moons","moonme","moon me"]: # Show the playing status
			return await ctx.invoke(self.playing,moons=position)
		delay = self.settings.getServerStat(ctx.guild, "MusicDeleteDelay", 20)
		player = self.bot.wavelink.players.get(ctx.guild.id,None)
		if player == None or not player.is_connected:
			return await Message.EmbedText(title="♫ Not connected to a voice channel!",color=ctx.author,delete_after=delay).send(ctx)
		if not player.is_playing:
			return await Message.EmbedText(title="♫ Not playing anything!",color=ctx.author,delete_after=delay).send(ctx)
		# Try to resolve the position - first in seconds, then with the HH:MM:SS format
		vals = position.split(":")
		seconds = 0
		multiplier = [3600,60,1]
		vals = ["0"] * (len(multiplier)-len(vals)) + vals if len(vals) < len(multiplier) else vals # Ensure we have 3 values
		for index,mult in enumerate(multiplier):
			try: seconds += mult * float("".join([x for x in vals[index] if x in "0123456789."])) # Try to avoid h, m, s suffixes
			except: return await Message.EmbedText(title="♫ Malformed seek value!",description="Please make sure the seek time is in seconds, or using HH:MM:SS format.",color=ctx.author,delete_after=delay).send(ctx)
		ms = int(seconds*1000)
		await player.seek(ms)
		return await Message.EmbedText(title="♫ Seeking to {}!".format(self.format_duration(ms)),color=ctx.author,delete_after=delay).send(ctx)

	@commands.command()
	async def volume(self, ctx, volume = None):
		"""Changes the player's volume (0-150%)."""

		delay = self.settings.getServerStat(ctx.guild, "MusicDeleteDelay", 20)
		player = self.bot.wavelink.players.get(ctx.guild.id,None)
		if player == None or not player.is_connected:
			return await Message.EmbedText(title="♫ Not connected to a voice channel!",color=ctx.author,delete_after=delay).send(ctx)
		if not player.is_playing and not player.is_paused:
			return await Message.EmbedText(title="♫ Not playing anything!",color=ctx.author,delete_after=delay).send(ctx)
		if volume == None:
			# We're listing the current volume
			cv = int(player.volume*2)
			return await Message.EmbedText(title="♫ Current volume at {}%.".format(cv),color=ctx.author,delete_after=delay).send(ctx)
		try:
			volume = float(volume)
			volume = int(volume) if volume - int(volume) < 0.5 else int(volume)+1
		except:
			return await Message.EmbedText(title="♫ Volume must be an integer between 0-150.",color=ctx.author,delete_after=delay).send(ctx)
		# Ensure our volume is between 0 and 150
		volume = 150 if volume > 150 else 0 if volume < 0 else volume
		self.vol[str(ctx.guild.id)] = volume
		await player.set_volume(volume/2)
		# Save it to the server stats with range 10-100
		self.settings.setServerStat(ctx.guild, "MusicVolume", 10 if volume < 10 else 100 if volume > 100 else volume)
		await Message.EmbedText(title="♫ Changed volume to {}%.".format(volume),color=ctx.author,delete_after=delay).send(ctx)

	@commands.command()
	async def geteq(self, ctx):
		"""Prints the current equalizer settings."""

		player = self.bot.wavelink.players.get(ctx.guild.id,None)
		delay = self.settings.getServerStat(ctx.guild, "MusicDeleteDelay", 20)
		if player == None or not player.is_connected:
			return await Message.EmbedText(title="♫ Not connected to a voice channel!",color=ctx.author,delete_after=delay).send(ctx)
		if not player.is_playing and not player.is_paused:
			return await Message.EmbedText(title="♫ Not playing anything!",color=ctx.author,delete_after=delay).send(ctx)
		# Get the current eq
		eq_text = self.print_eq(player.eq.raw)
		return await Message.EmbedText(title="♫ Current Equalizer Settings",description=eq_text,color=ctx.author,delete_after=delay).send(ctx)

	@commands.command()
	async def seteq(self, ctx, *, bands = None):
		"""Sets the equalizer to the passed 15 space-delimited values from -5 (silent) to 5 (double volume)."""
		
		player = self.bot.wavelink.players.get(ctx.guild.id,None)
		delay = self.settings.getServerStat(ctx.guild, "MusicDeleteDelay", 20)
		if player == None or not player.is_connected:
			return await Message.EmbedText(title="♫ Not connected to a voice channel!",color=ctx.author,delete_after=delay).send(ctx)
		if not player.is_playing and not player.is_paused:
			return await Message.EmbedText(title="♫ Not playing anything!",color=ctx.author,delete_after=delay).send(ctx)
		if bands == None: 
			return await Message.EmbedText(title="♫ Please specify the eq values!",description="15 numbers separated by a space from -5 (silent) to 5 (double volume)",color=ctx.author,delete_after=delay).send(ctx)
		try:
			band_ints = [int(x) for x in bands.split()]
		except:
			return await Message.EmbedText(title="♫ Invalid eq values passed!",description="15 numbers separated by a space from -5 (silent) to 5 (double volume)",color=ctx.author,delete_after=delay).send(ctx)
		if not len(band_ints) == 15: return await Message.EmbedText(title="♫ Incorrect number of eq values! ({} - need 15)".format(len(band_ints)),description="15 numbers separated by a space from -5 (silent) to 5 (double volume)",color=ctx.author,delete_after=delay).send(ctx)
		eq_list = [(x,float(0.25 if y/20 > 0.25 else -0.25 if y/20 < -0.25 else y/20)) for x,y in enumerate(band_ints)]
		eq = wavelink.eqs.Equalizer.build(levels=eq_list)
		await player.set_eq(eq)
		player._equalizer = eq # Dirty hack to fix a bug in wavelink
		eq_text = self.print_eq(player.eq.raw)
		self.settings.setServerStat(ctx.guild, "MusicEqualizer", player.eq.raw)
		return await Message.EmbedText(title="♫ Set equalizer to Custom preset!",description=eq_text,color=ctx.author,delete_after=delay).send(ctx)

	@commands.command()
	async def setband(self, ctx, band_number = None, value = None):
		"""Sets the value of the passed eq band (1-15) to the passed value from -5 (silent) to 5 (double volume)."""

		player = self.bot.wavelink.players.get(ctx.guild.id,None)
		delay = self.settings.getServerStat(ctx.guild, "MusicDeleteDelay", 20)
		if player == None or not player.is_connected:
			return await Message.EmbedText(title="♫ Not connected to a voice channel!",color=ctx.author,delete_after=delay).send(ctx)
		if not player.is_playing and not player.is_paused:
			return await Message.EmbedText(title="♫ Not playing anything!",color=ctx.author,delete_after=delay).send(ctx)
		if band_number == None or value == None:
			return await Message.EmbedText(title="♫ Please specify a band and value!",description="Bands can be between 1 and 15, and eq values from -5 (silent) to 5 (double volume)",color=ctx.author,delete_after=delay).send(ctx)
		try:
			band_number = int(band_number)
			assert 0 < band_number < 16
		except:
			return await Message.EmbedText(title="♫ Invalid band passed!",description="Bands can be between 1 and 15, and eq values from -5 (silent) to 5 (double volume)",color=ctx.author,delete_after=delay).send(ctx)
		try:
			value = int(value)
			value = -5 if value < -5 else 5 if value > 5 else value
		except:
			return await Message.EmbedText(title="♫ Invalid eq value passed!",description="Bands can be between 1 and 15, and eq values from -5 (silent) to 5 (double volume)",color=ctx.author,delete_after=delay).send(ctx)
		new_bands = [(band_number-1,float(value/20)) if x == band_number-1 else (x,y) for x,y in player.eq.raw]
		eq = wavelink.eqs.Equalizer.build(levels=new_bands)
		await player.set_eq(eq)
		player._equalizer = eq # Dirty hack to fix a bug in wavelink
		eq_text = self.print_eq(player.eq.raw)
		self.settings.setServerStat(ctx.guild, "MusicEqualizer", player.eq.raw)
		return await Message.EmbedText(title="♫ Set band {} to {}!".format(band_number,value),description=eq_text,color=ctx.author,delete_after=delay).send(ctx)

	@commands.command()
	async def reseteq(self, ctx):
		"""Resets the current eq to the flat preset."""
		
		await ctx.invoke(self.eqpreset, preset="flat")

	@commands.command()
	async def eqpreset(self, ctx, preset = None):
		"""Sets the current eq to one of the following presets:  Boost, Flat, Metal"""

		player = self.bot.wavelink.players.get(ctx.guild.id,None)
		delay = self.settings.getServerStat(ctx.guild, "MusicDeleteDelay", 20)
		if player == None or not player.is_connected:
			return await Message.EmbedText(title="♫ Not connected to a voice channel!",color=ctx.author,delete_after=delay).send(ctx)
		if not player.is_playing and not player.is_paused:
			return await Message.EmbedText(title="♫ Not playing anything!",color=ctx.author,delete_after=delay).send(ctx)
		if preset == None or not preset.lower() in ("boost","flat","metal"):
			return await Message.EmbedText(title="♫ Please specify a valid eq preset!",description="Options are:  Boost, Flat, Metal",color=ctx.author,delete_after=delay).send(ctx)
		eq = wavelink.eqs.Equalizer.boost() if preset.lower() == "boost" else wavelink.eqs.Equalizer.flat() if preset.lower() == "flat" else wavelink.eqs.Equalizer.metal()
		await player.set_eq(eq)
		player._equalizer = eq # Dirty hack to fix a bug in wavelink
		eq_text = self.print_eq(player.eq.raw)
		self.settings.setServerStat(ctx.guild, "MusicEqualizer", player.eq.raw)
		return await Message.EmbedText(title="♫ Set equalizer to {} preset!".format(preset.lower().capitalize()),description=eq_text,color=ctx.author,delete_after=delay).send(ctx)

	@commands.command()
	async def repeat(self, ctx, *, yes_no = None):
		"""Checks or sets whether to repeat the current playlist."""

		delay = self.settings.getServerStat(ctx.guild, "MusicDeleteDelay", 20)
		player = self.bot.wavelink.players.get(ctx.guild.id,None)
		if player == None or not player.is_connected:
			return await Message.EmbedText(title="♫ Not connected to a voice channel!",color=ctx.author,delete_after=delay).send(ctx)
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
		await Message.EmbedText(title="♫ "+msg,color=ctx.author,delete_after=delay).send(ctx)

	@commands.command()
	async def autodeleteafter(self, ctx, seconds = None):
		"""Lists or sets the current delay before auto-deleting music related messages (max of 300 seconds).  Set to an integer less than 10 to disable auto-deletion.  Requires bot-admin or admin to set."""
		
		if not Utils.is_bot_admin(ctx): seconds = None
		delay = self.settings.getServerStat(ctx.guild, "MusicDeleteDelay", 20)
		if seconds == None:
			# List the delay
			if delay == None:
				return await Message.EmbedText(title="♫ Music related messages are not auto-deleted!",color=ctx.author).send(ctx)
			else:
				return await Message.EmbedText(title="♫ Music related messages are auto-deleted after {} second{}!".format(delay, "" if delay == 1 else "s"),color=ctx.author,delete_after=delay).send(ctx)
		# Attempting to set it
		try:
			real = int(seconds)
		except:
			return await Message.EmbedText(title="♫ Seconds must be an integer!",color=ctx.author,delete_after=delay).send(ctx)
		if real < 10:
			self.settings.setServerStat(ctx.guild, "MusicDeleteDelay", None)
			return await Message.EmbedText(title="♫ Music related messages will not be auto-deleted!",color=ctx.author).send(ctx)
		real = 300 if real > 300 else real
		self.settings.setServerStat(ctx.guild, "MusicDeleteDelay", real)
		return await Message.EmbedText(title="♫ Music related messages will be auto-deleted after {} second{}!".format(real, "" if real == 1 else "s"),color=ctx.author,delete_after=real).send(ctx)

	@commands.command()
	async def stop(self, ctx):
		"""Stops and empties the current playlist."""
		
		delay = self.settings.getServerStat(ctx.guild, "MusicDeleteDelay", 20)
		# Remove the per-server temp settings
		self.dict_pop(ctx)
		player = self.bot.wavelink.players.get(ctx.guild.id,None)
		if player != None:
			if player.is_playing or player.is_paused:
				await player.stop()
				return await Message.EmbedText(title="♫ Music stopped and playlist cleared!",color=ctx.author,delete_after=delay).send(ctx)
			else:
				return await Message.EmbedText(title="♫ Not playing anything!",color=ctx.author,delete_after=delay).send(ctx)
		await Message.EmbedText(title="♫ Not connected to a voice channel!",color=ctx.author,delete_after=delay).send(ctx)

	@commands.command(hidden=True)
	async def okbye(self, ctx):
		"""Do you wanna build a snowman?"""

		await ctx.invoke(self.leave)

	@commands.command(aliases=["disconnect"])
	async def leave(self, ctx):
		"""Stops and disconnects the bot from voice."""

		delay = self.settings.getServerStat(ctx.guild, "MusicDeleteDelay", 20)
		# Remove the per-server temp settings
		self.dict_pop(ctx)
		player = self.bot.wavelink.players.get(ctx.guild.id,None)
		if player != None:
			await player.destroy()
			return await Message.EmbedText(title="♫ I've left the voice channel!",color=ctx.author,delete_after=delay).send(ctx)
		await Message.EmbedText(title="♫ Not connected to a voice channel!",color=ctx.author,delete_after=delay).send(ctx)

	@commands.command()
	async def stopall(self, ctx):
		"""Stops and disconnects the bot from all voice channels in all servers (owner-only)."""

		if not await Utils.is_owner_reply(ctx): return
		delay = self.settings.getServerStat(ctx.guild, "MusicDeleteDelay", 20)
		players = 0
		for guild in self.bot.guilds:
			# Remove the per-server temp settings
			self.dict_pop(guild)
			player = self.bot.wavelink.players.get(guild.id,None)
			if player != None:
				players += 1
				await player.destroy()
		await Message.EmbedText(title="♫ I've left all voice channels ({:,}/{:,})!".format(players,len(self.bot.guilds)),color=ctx.author,delete_after=delay).send(ctx)

	@commands.command()
	async def disableplay(self, ctx, *, yes_no = None):
		"""Enables/Disables the music commands.  Helpful in case Youtube is rate limiting to avoid extra api calls and allow things to calm down.  Owners can still access music commands (owner only)."""
		
		if not await Utils.is_owner_reply(ctx): return
		await ctx.send(Utils.yes_no_setting(ctx,"Music player lock out","DisableMusic",yes_no,is_global=True))

	async def cog_before_invoke(self, ctx):
		# We don't need to ensure extra for the following commands:
		if ctx.command.name in ("playingin","autodeleteafter","disableplay","stopall","searchlist","playing","playlist"): return
		# General checks for all music player commands - with specifics filtered per command
		# If Youtube ratelimits - you can disable music globally so only owners can use it
		player = self.bot.wavelink.players.get(ctx.guild.id,None)
		delay = self.settings.getServerStat(ctx.guild, "MusicDeleteDelay", 20)
		if self.settings.getGlobalStat("DisableMusic",False) and not Utils.is_owner(ctx):
			# Music is off - and we're not an owner - disconnect if connected, then send the bad news :(
			self.dict_pop(ctx)
			if player: await player.destroy()
			await Message.EmbedText(title="♫ Music player is currently disabled!",color=ctx.author,delete_after=delay).send(ctx)
			raise commands.CommandError("Music Cog: Music disabled.")
		# Music is enabled - let's make sure we have the right role
		if not await self._check_role(ctx):
			raise commands.CommandError("Music Cog: Missing DJ roles.")
		# If we're just using the join command - we don't need extra checks - they're done in the command itself
		if ctx.command.name in ("join","summon"): return
		# We've got the role - let's join the author's channel if we're playing/shuffling and not connected
		if ctx.command.name in ("play","shuffle","loadpl","shufflepl") and ctx.author.voice:
			if player == None: player = self.bot.wavelink.get_player(ctx.guild.id)
			if not player.is_connected: return await player.connect(ctx.author.voice.channel.id)
		# Let's ensure the bot is connected to voice
		if player == None or not player.is_connected:
			await Message.EmbedText(title="♫ Not connected to a voice channel!",color=ctx.author,delete_after=delay).send(ctx)
			raise commands.CommandError("Music Cog: Not connected to a voice channel.")
		# Let's make sure the caller is connected to voice and the same channel as the bot - or a bot-admin
		if Utils.is_bot_admin(ctx): return # We good - have enough perms to override whatever
		if not ctx.author.voice or player == None or not ctx.author.voice.channel.id == int(player.channel_id):
			await Message.EmbedText(title="♫ You have to be in the same voice channel as me to use that!",color=ctx.author,delete_after=delay).send(ctx)
			raise commands.CommandError("Music Cog: Author not connected to the bot's voice channel.")
