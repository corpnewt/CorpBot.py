import asyncio, discord, pomice, re, random, math, tempfile, json, os, shutil, aiohttp
from discord.ext import commands
from Cogs import Utils, Message, DisplayName, PickList, DL

# This file was originally based on Rapptz's basic_voice.py:
# https://github.com/Rapptz/discord.py/blob/master/examples/basic_voice.py

def setup(bot):
	settings = bot.get_cog("Settings")
	bot.add_cog(Music(bot,settings))

class CorpPlayer(pomice.Player):
	def __init__(self,*args,**kwargs):
		pomice.Player.__init__(self,*args,**kwargs)
		self.queue = pomice.Queue()
		self.failure_count = 0
		self.failed_tracks = {}
		self._vol_set = False
		self._vol = kwargs.get("volume",100)
		self._vol_real = kwargs.get("real_volume",100)
		self._vol_ratio = kwargs.get("volume_ratio",0.75)

	async def set_vol(self, volume=100):
		# Adjusts the volume to a 0-150% scale while applying
		# the ratio
		self._vol = volume # Save the raw percent for reporting
		# Apply the ratio, and round to the nearest whole number
		adj_volume = volume * self._vol_ratio
		self._vol_real = int(adj_volume)+(1 if adj_volume-int(adj_volume)>=0.5 else 0)
		await self.set_volume(self._vol_real)
		self._vol_set = True

	def get_vol(self, ctx):
		# Gets the volume in percent based on the last set value
		if not self._vol_set:
			# Get the default volume for the passed server
			settings = ctx.bot.get_cog("Settings")
			if settings:
				return settings.getServerStat(ctx.guild,"MusicVolume",100)
			return None
		return self._vol

	def get_real_vol(self):
		# Gets the true volume value
		return self._vol_real if self._vol_set else None

	async def move_to(self, channel=None):
		# Needless wrapper for something that should work as-is?
		if channel is None:
			await self.disconnect()
			return
		# Attempt to move to the passed channel
		await self.guild.change_voice_state(channel=channel)
		self.channel = channel
		self._is_connected = True

	@property
	def track(self):
		return self.current

class CorpTrack(pomice.objects.Track):
	# Create a shell subclass to keep horrible practices going
	def __init__(self,track,radio=False,to_remove=False,search_type=None):
		if isinstance(track,pomice.objects.Track):
			track = {
				"track_id":track.track_id,
				"info":track.info,
				"ctx":track.ctx,
				"track_type":track.track_type,
				"filters":track.filters,
				"timestamp":track.timestamp,
				"requester":track.requester,
				"thumbnail":track.thumbnail
			}
		# Resolve the encoded id if possible - should be
		if "encoded" in track or "id" in track and not "track_id" in track:
			track["track_id"] = track.get("encoded",track.get("id"))
		# Resolve some local vars
		info       = track.get("info",track)
		track_id   = track.get("track_id")
		uri        = info.get("uri","")
		track_type = track.get("track_type",track.get("sourceName"))
		# Set up the track_type if it's not already a pomice TrackType
		if not track_type:
			# Check if our uri starts with the track_id
			if uri.endswith(track_id):
				# Check if the uri matches one of our regexes
				for r,t in (
					(pomice.enums.URLRegex.SPOTIFY_URL,pomice.enums.TrackType.SPOTIFY),
					(pomice.enums.URLRegex.AM_URL,pomice.enums.TrackType.APPLE_MUSIC)
				):
					if r.match(uri):
						# It's a match - retain the type
						track_type = t
						break
		elif not isinstance(track_type,pomice.enums.TrackType):
			# Wrap it in one of the enum values - or set it to None if not found
			try: track_type = pomice.enums.TrackType(track_type)
			except: track_type = None
		# Build our new object - this is tedious but lets us add custom props
		pomice.objects.Track.__init__(
			self,
			track_id=track_id,
			info=info,
			ctx=track.get("ctx"),
			track_type=track_type,
			filters=track.get("filters"),
			timestamp=track.get("timestamp"),
			requester=track.get("requester")
		)
		# Setup our custom properties
		self.seek = track.get("position",0)
		self.radio = radio
		self.to_remove = to_remove
		self.did_fail = False
		self.thumb = track.get("thumbnail")
		self.search_type = search_type
		if not self.thumb and track_type == pomice.enums.TrackType.YOUTUBE: # Try to build our own thumbnail
			try: self.thumb = "https://img.youtube.com/vi/{}/maxresdefault.jpg".format(track.get("identifier",track["info"].get("identifier")))
			except: self.thumb = None

class Music(commands.Cog):

	__slots__ = ("bot","settings","ll_host","ll_port","ll_pass","NodePool","player_attrs","player_clear","vol_ratio","reconnect_wait","gc")

	def __init__(self, bot, settings):
		self.bot      = bot
		self.settings = settings
		# Get the Lavalink info as needed
		self.ll_host = bot.settings_dict.get("lavalink_host","127.0.0.1")
		self.ll_port = bot.settings_dict.get("lavalink_port",2333)
		self.ll_pass = bot.settings_dict.get("lavalink_password","youshallnotpass")
		# Get Spotify info as needed
		self.spotify_client_id = bot.settings_dict.get("spotify_client_id")
		self.spotify_client_secret = bot.settings_dict.get("spotify_client_secret")
		# Get whether or not to enable Apple Music
		self.use_apple_music = bot.settings_dict.get("use_apple_music",False)
		# Monkey patch out some regex - maybe find a way to include it via setting later
		pomice.URLRegex.YOUTUBE_VID_IN_PLAYLIST = re.compile(r"a^",)
		self.YOUTUBE_VID_IN_PLAYLIST = re.compile(r"(?P<video>^.*?v.*?)(?P<list>&list.*)")
		# Set up regex for the new spotify.link/id URLs
		self.spotify_link_regex = re.compile(r"(?i)https?:\/\/spotify\.link\/?(?P<id>[a-zA-Z0-9]+)")
		# Set up bandcamp regex
		self.bandcamp_regex = re.compile(r"(?i)https:\/\/[^\s]+\.bandcamp\.com\/(album|track)\/[^\s]+")
		# Retain a list of *next command names
		self.next_commands = ["playnext","radionext","shufflenext","loadplnext","shuffleplnext"]
		# Setup pomice defaults
		self.NodePool = pomice.NodePool()
		# Setup player specifics to remember
		self.player_attrs = ("skips","ctx","track_ctx","track_seek","repeat","vol","eq")
		self.player_clear = [x for x in self.player_attrs if not x in ("ctx","repeat","vol","eq")] # Attributes to strip on start
		# Ratio to equalize volume - can be useful to account for changes in the pomice module
		# which used to use 0 -> 100, and now uses 0.0 -> 1.0 for 0 to 100% volume
		# Has now been changed to 0 -> 1000 where 1000 is 100%, so I guess it's x 10?
		# They really need to get their shit together with this...
		self.vol_ratio = 0.75
		self.reconnect_wait = 0.5 # Number of seconds to wait before reconnecting
		# Save our failure thresholds
		self.player_failure_threshold = 5 # >= we stop music
		self.track_failure_threshold = 2 # >= we clear out that track
		# Regex fun
		self.message_regex = re.compile(r"(?i)https:\/\/(www\.)?(\w+\.)*discord(app)?\.com\/channels\/(@me|\d+)\/\d+\/\d+")
		self.range_regex = re.compile(r"(?i)(\b|-)r(ange)?=(?P<range>[\[\]:\d,-]+)")
		# Graphing char set - allows for theming-type overrides
		self.gc = bot.settings_dict.get("music_graph_chars",{})
		'''	"b"  :"│",  # "║" # Bar outline
			"tl" :"┌",  # "╔" # Top left outline
			"tr" : "┐", # "╗" # Top right outline
			"bl" : "└", # "╚" # Bottom left outline
			"br" : "┘", # "╝" # Bottom right oultine
			"cp" : "─", # "═" # Top/bottom cap
			"ep" : " ", #       Empty space
			"in" : " ", #       Inner fill char
			"se" : "─", # "═" # Netral Separator
			"su" : "┴", # "╩" # Separator up
			"sd" : "┬", # "╦" # Separator down
			"lp" : ""   #       Left pad'''
		global Utils, DisplayName
		Utils = self.bot.get_cog("Utils")
		DisplayName = self.bot.get_cog("DisplayName")
		self.bot.loop.create_task(self.start_nodes())

	async def start_nodes(self):
		# Start up the nodes when the bot starts - this prevents issues
		# with the session ids not resolving early enough.
		await self.bot.wait_until_ready()
		max_wait = 10
		time_sleep = 0.25
		time_so_far = 0
		while self.NodePool.nodes:
			# Wait for nodes to disconnect if we relaunched the Music module
			await asyncio.sleep(time_sleep)
			# Make sure we don't deadlock
			time_so_far += time_sleep
			if time_so_far > max_wait:
				print("!! Waited too long for nodes to shut down - bailing...")
				return
			# Try to shut the nodes down forcefully
			try: await self.NodePool.disconnect()
			except: pass
		try:
			# No existing nodes - start fresh
			await self.NodePool.create_node(
				bot=self.bot,
				host=self.ll_host,
				port=self.ll_port,
				identifier=None,
				password=self.ll_pass,
				spotify_client_id=self.spotify_client_id,
				spotify_client_secret=self.spotify_client_secret,
				apple_music=self.use_apple_music
			)
		except pomice.exceptions.NodeConnectionFailure as e:
			if not self.bot.settings_dict.get("suppress_disabled_warnings"):
				print("\n!! Music Cog has been disabled !!")
				print("* Failed to connect to Lavalink: {}".format(e))
				print("* You can get the latest release of Lavalink here:")
				print("   https://github.com/lavalink-devs/Lavalink/releases")
				print("* Or the latest Lavalink-Updater here:")
				print("   https://github.com/corpnewt/Lavalink-Updater\n")
			self.bot.unload_extension("Cogs.Music")

	def get_node(self):
		# Try to get the best node - if any, otherwise create one
		try:
			return self.NodePool.get_best_node(algorithm=pomice.enums.NodeAlgorithm.by_ping)
		except pomice.exceptions.NoNodesAvailable:
			return None

	def get_player(self,guild):
		# Get (or create) a node, and return the guild's player (if any).
		# Returns either the player, or None if none exists.
		node = self.get_node()
		if not node: return None
		return node.get_player(getattr(guild,"id",guild))

	def _is_submodule(self, parent, child):
		return parent == child or child.startswith(parent + ".")

	@commands.Cog.listener()
	async def on_unloaded_extension(self, ext):
		# Called to shut things down
		if not self._is_submodule(ext.__name__, self.__module__):
			return
		# Disconnect and cleanup all nodes and their current players
		nodes = list(self.NodePool.nodes.values())
		for node in nodes:
			# Disconnect all players, then disconnect the node
			for player in list(node.players.values()):
				await self._stop(player,clear_attrs=True,clear_queue=True,disconnect=True)
			if not hasattr(node,"_spotify_client"):
				# More filthy hacks to work around bugs
				node._spotify_client = None
		try: await self.NodePool.disconnect()
		except: pass

	@commands.Cog.listener()
	async def on_check_play(self,player):
		# Helper to see if we should play the next song.

		# Player either doesn't exist, or isn't connected - bail.
		if not player or not player.is_connected: return
		# Player is already doing something or has nothing to do - bail.
		if player.is_playing or player.is_paused: return
		if player.queue.is_empty: return
		# Should be connected, and not already playing, let's strip any unwanted attributes
		# from our player
		self._clear_player(player)
		# Check for the "eq" attr - and if we don't have it, check if we're preserving EQ
		# and apply as needed - or reset to flat
		if not hasattr(player,"eq"):
			if self.settings.getServerStat(player.guild,"PreserveLastEQ"): # We are looking to apply the last settings
				eq = self.settings.getServerStat(player.guild,"LastEQ",self.flat_eq())
				player.eq = eq
			else:
				eq = self.flat_eq()
			await self.apply_filters(player,eq,name="equalizer",setting_name="LastEQ")
		if hasattr(player,"timescale"):
			# We just remove it as Lavalink doesn't retain it on new songs
			delattr(player,"timescale")
		# let's get our next track
		# and context and send the resulting message.
		track = player.queue.get()
		# Retain the local context and seek if needed
		if hasattr(track,"ctx"): player.track_ctx = track.ctx
		# We only want to pull the seek value from the current track.
		if hasattr(track,"seek"): player.track_seek = track.seek
		bound_channel = getattr(player,"bound_channel",None)
		ctx = getattr(player,"ctx",getattr(player,"track_ctx",None))
		# Lazy load if needed
		if not track.track_id and (track.uri or track.info.get("lazy_load_url")):
			info = track.info
			node = self.get_node()
			try:
				track = await node.get_tracks(query=track.info.get("lazy_load_url",track.uri),ctx=ctx,search_type=None)
			except Exception as e:
				self.bot.dispatch("pomice_track_exception",player,track,e)
			if isinstance(track,list):
				track = track[0]
			# Wrap it into a new CorpTrack
			track = CorpTrack(track)
			# Update local info - both in the info dict, and attributes
			for key in info:
				track.info[key] = info[key]
				try: setattr(track,key,info[key])
				except: pass
		# Make sure volume is setup properly
		try: volume = player.get_vol(ctx) or self.settings.getServerStat(ctx.guild,"MusicVolume",100)
		except: volume = 100 # Fall back on 100 if we don't have anything else
		if ctx: # Got context, can send the resulting message
			delay = self.settings.getServerStat(ctx.guild, "MusicDeleteDelay", 20)
			fields = [{"name":"Duration","value":self.format_duration(track.length,track),"inline":False}]
			if getattr(player,"track_seek",None) and getattr(track,"is_seekable",False): # Check both if we have the attr, and that it evaluates to true
				fields.append({"name":"Starting At","value":self.format_duration(player.track_seek),"inline":False})
			await Message.Embed(
				title="♫ Now Playing: {}".format(self.get_track_title(track)),
				fields=fields,
				description="Requested by {}{}\n-- Volume at {}%{}".format(
					ctx.author.mention,
					" (via radio)" if track.radio else "",
					player.get_vol(ctx),
					"\n-- Repeat Enabled" if getattr(player,"repeat",False) else ""
				),
				color=ctx.author,
				url=track.uri,
				thumbnail=getattr(track,"thumb",None),
				delete_after=delay
			).send(bound_channel or ctx)
		# Regardless of whether we can post, set volume and go to the next song.
		await player.set_vol(volume)
		try:
			await player.play(track,start=int(getattr(player,"track_seek",0)))
		except Exception as e:
			self.bot.dispatch("pomice_track_exception",player,track,e)

	@commands.Cog.listener()
	async def on_pomice_track_end(self,player,track,reason):
		player_failed = track_failed = False
		if getattr(track,"did_fail",False):
			# Incrememnt our failure counts
			try:
				player.failed_tracks[track.track_id] = player.failed_tracks.get(track.track_id,0)+1
				if player.failed_tracks[track.track_id] >= self.track_failure_threshold:
					track_failed = True
				player.failure_count += 1
				if player.failure_count >= self.player_failure_threshold:
					player_failed = True
			except: pass
		else:
			# Clear our failure counts
			try:
				player.failure_count = 0
				player.failed_tracks.pop(track.track_id,None)
			except: pass
		# Get our context
		# If attached to the player, it's bound to the starting track - if we only have it on the
		# track, then we're just replying to the last queued element.
		ctx = getattr(player,"ctx",getattr(player,"track_ctx",None))
		color_ctx = getattr(player,"track_ctx",ctx)
		# Check for failures
		if player_failed:
			# Clear attributes to prevent triggering the event again
			self._clear_player(player,[x for x in self.player_clear+["ctx"]])
			await self._stop(player,clear_attrs=False,clear_queue=True,disconnect=False)
			return await Message.Embed(
				title="♫ Failure Threshold Exceeded!",
				description="{:,} or more track{} failed to play in a row - cleared queue and stopped playing to prevent spam.".format(
					self.player_failure_threshold,"" if self.player_failure_threshold==1 else "s"
				),
				color=color_ctx.author
			).send(ctx)
		if track_failed:
			# We need to remove all instances of this track from the queue
			track.to_remove = True
			if not player.queue.is_empty:
				# Strip other instances of the failed track
				queue = [t for t in player.queue if t.track_id != track.track_id]
				player.queue.clear()
				await self.add_to_queue(player,queue)
			await Message.Embed(
				title="♫ Track Failure Threshold Exceeded!",
				description="{} has exceeded the allowed failure threshold - all instances have been removed from the current queue to prevent spam.".format(
					self.get_track_title(track)
				),
				url=track.uri,
				thumbnail=getattr(track,"thumb",None),
				color=color_ctx.author
			).send(ctx)
		await self._stop(player,clear_attrs=False,clear_queue=False,disconnect=False) # Stop the player - prevents issues with it thinking it's still playing
		# print("TRACK ENDED",player)
		# print(track)
		# print(reason)
		if getattr(player,"repeat",False) and not getattr(track,"to_remove",False) and not track_failed:
			# We're repeating tracks - add it to the end
			if not hasattr(player,"track_ctx"): return # No context - probably stopped.
			track = self._track_fill(track, ctx=player.track_ctx)
			if hasattr(player,"track_seek"): track.seek = player.track_seek # Restore the seek position
			await self.add_to_queue(player,track)
		if player.queue.is_empty:
			if not ctx: return # Nothing left to play, and nowhere to post our end message.
			delay = self.settings.getServerStat(ctx.guild, "MusicDeleteDelay", 20)
			return await Message.Embed(title="♫ End of playlist!",color=color_ctx.author,delete_after=delay).send(ctx)
		# Dispatch our check play command
		self.bot.dispatch("check_play",player)

	async def _print_track_issue(self,issue,player,track,error):
		ctx = getattr(player,"ctx",getattr(player,"track_ctx",None))
		color_ctx = getattr(player,"track_ctx",ctx)
		if not ctx: return # Nowhere to post our error message.
		# Attempt to format the dict as json if needed
		if isinstance(error,dict):
			try: error = "```json\n{}\n```".format(json.dumps(error,indent=2))
			except: pass
		desc = "Something went wrong playing \"{}\".\n\n{}".format(self.get_track_title(track),error)
		if len(desc) > 2048:
			# Truncate
			if desc.endswith("\n```"):
				desc = desc[:2048-7]+"...\n```"
			else:
				desc = desc[:2048-3]+"..."
		return await Message.Embed(
			title="♫ Track {}!".format(str(issue).capitalize()),
			description=desc,
			url=track.uri,
			thumbnail=getattr(track,"thumb",None),
			color=color_ctx.author
		).send(ctx)

	@commands.Cog.listener()
	async def on_pomice_track_exception(self,player,track,error):
		print("TRACK EXCEPTION",player)
		print(track)
		print(error)
		track.did_fail = True
		await self._print_track_issue("Exception",player,track,error)
		await self._stop(player,clear_attrs=False,clear_queue=False,disconnect=False) # Stop the player - prevents issues with it thinking it's still playing

	@commands.Cog.listener()
	async def on_pomice_track_stuck(self,player,track):
		print("TRACK STUCK",player)
		print(track)
		track.did_fail = True
		await self._print_track_issue("Stuck",player,track,"The track got stuck - you may need to skip it if the issue persists.")
		await self._stop(player,clear_attrs=False,clear_queue=False,disconnect=False) # Stop the player - prevents issues with it thinking it's still playing

	@commands.Cog.listener()
	async def on_voice_state_update(self, user, before, after):
		if not user.guild or not before.channel or (user.bot and user.id != self.bot.user.id):
			return # No guild, someone joined, or the user is a bot that's not us
		player = self.get_player(before.channel.guild)
		if player is None:
			return # Player is borked or not connected - just bail
		if player.channel and player.channel != before.channel:
			return # No player to worry about, or someone left a different channel - ignore
		if user.id == self.bot.user.id:
			if not after.channel:
				# We were disconnected somehow - try to reconnect and keep playing
				#
				##  Dirty workaround for what seems like a bug in pomice  ##
				#
				#   If you manually disconnect the from vc via right click and then try to
				#   have it join a voice channel, it throws an exception stating that it's
				#   already connected to a voice channel.
				#   As a workaround - we manually update the voice state and reconnect to
				#   the prior channel.
				# return await before.channel.connect(cls=CorpPlayer)
				# Allow this to happen as we haven't been randomly disconnecting lately,
				# using "pass" also allows us to clean up the player via _stop()
				pass
			else:
				# We were moved - allow this
				return
		elif len([x for x in before.channel.members if not x.bot]) > 0:
			return # At least one non-bot user
		if not self.settings.getServerStat(user.guild, "LeaveVCWhenAlone", True):
			return # We're configured to stay in VC, even alone
		# if we made it here - then we're alone, and not allowed to be - disconnect and destroy
		await self._stop(player,clear_attrs=True,clear_queue=True,disconnect=True)

	def _clear_player(self, player, attrs=None):
		if attrs is True: # Clear all if True
			attrs = self.player_attrs
		elif not isinstance(attrs,(list,tuple)): # Clear standard if not a list/tuple
			attrs = self.player_clear
		for x in attrs:
			if hasattr(player,x):
				try: delattr(player,x)
				except: pass

	def _check_mc(self, ctx):
		mcArray = self.settings.getServerStat(ctx.guild, "MCArray", [])
		for role in mcArray:
			if ctx.guild.get_role(int(role["ID"])) in ctx.author.roles:
				return True
		return False

	async def _check_role(self, ctx):
		# Checks if we have the required credentials to use the music player.
		if Utils.is_bot_admin(ctx) or self._check_mc(ctx):
			return True
		djArray = self.settings.getServerStat(ctx.guild, "DJArray", [])
		delay = self.settings.getServerStat(ctx.guild, "MusicDeleteDelay", 20)
		if not len(djArray):
			await Message.Embed(title="♫ There are no DJ roles set yet.  Use `{}adddj [role]` to add some.".format(ctx.prefix),color=ctx.author,delete_after=delay).send(ctx)
			return None
		for role in djArray:
			if ctx.guild.get_role(int(role["ID"])) in ctx.author.roles:
				return True
		await Message.Embed(title="♫ You need a DJ role to do that!",color=ctx.author,delete_after=delay).send(ctx)
		return False

	async def _stop(self, player, clear_attrs=True, clear_queue=True, disconnect=False):
		# Helper to stop the player and optionally clear queue and disconnect.
		if not player: return
		# First we clear custom attributes added to the player
		if clear_attrs:
			self._clear_player(player,attrs=self.player_attrs)
		# Then we clear the queue if needed
		if clear_queue and not player.queue.is_empty:
			player.queue.clear()
		# Then we stop if playing/paused
		if player.is_paused:
			await player.set_pause(False)
		if player.is_playing:
			await player.stop()
		# Finally we disconnect if needed
		if disconnect and player.is_connected:
			await player.disconnect()
			await player.destroy()

	def get_tracks_from_data(self, data, check_start=True, check_seek=True, ctx=None):
		if not data or not isinstance(data,dict):
			# Something's wrong - return an empty list
			return []
		starting_track = 0 # Set the default
		if check_start: # We need to extract the starting point
			info = data.get("playlistInfo",{})
			# Get the starting track within limits
			starting_track = max(min(len(data["tracks"])-1, info.get("selectedTrack",0)), 0)
		new_tracks = []
		for x in data.get("tracks",[])[starting_track:]:
			new_track = self.get_track_with_info(x,check_seek=check_seek,ctx=ctx)
			if not new_track: continue # Skip if botched
			new_tracks.append(new_track)
		return new_tracks

	def get_track_with_info(self, info, check_seek=True, ctx=None):
		if isinstance(info,pomice.objects.Track): # Already a track - let's add needed info and return
			return self._track_fill(info,ctx)
		if not info or not isinstance(info,dict): return None # Not the right kind of info
		if all((x in info for x in ("track","info"))):
			# Should have the *actual* info dict now - create a track and return it
			new_track = CorpTrack(info["info"])
			if check_seek:
				if info["info"].get("seek"):
					new_track.seek = info["info"]["seek"]*1000 # Legacy method for old saves
				elif info["info"].get("position"):
					new_track.seek = info["info"]["position"]*1000
		elif "id" in info or "encoded" in info: # It's a json track
			if not "encoded" in info: info["encoded"] = info["id"]
			new_track = CorpTrack(info)
			if check_seek:
				if info.get("seek"):
					new_track.seek = info["seek"]*1000
				elif info.get("position"):
					new_track.seek = info["position"]*1000
		else: # Missing info - bail
			return None
		return self._track_fill(new_track,ctx)

	def _track_fill(self, track, ctx=None):
		# Helper to add ctx options to a track - as well as flesh out the thumbnail if needed
		if not isinstance(track,pomice.objects.Track): return track # Make no changes if it's the wrong type
		if hasattr(track,"info"): # Let's gather info and set things up if possible
			if track.info.get("sourceName") in ("youtube","ytmusic") and "identifier" in track.info:
				# We have the proper sourceName, and we have an identifier - let's build the thumb URL
				try:
					for x in ("thumb","thumbnail"):
						setattr(track,x,"https://img.youtube.com/vi/{}/maxresdefault.jpg".format(track.info["identifier"]))
				except: pass
			# Setup missing info from the dict as needed
			for x in ("id","identifier","uri","title","length","author"):
				if x in track.info:
					try: setattr(track,x,track.info[x])
					except: pass # Couldn't set it - probably already set
		if ctx: track.ctx = ctx # Append our ctx-based data if provided
		return track

	async def get_recommendations(self, ctx, url, recommend_count, search_type = None):
		# Gather youtube recommendations based on the passed video URL or search term
		urls = Utils.get_urls(url)
		if urls:
			url = urls[0]
			for r in (pomice.enums.URLRegex.SPOTIFY_URL,pomice.enums.URLRegex.YOUTUBE_URL):
				if r.match(url):
					# Got a match - check if it's a YT playlist and extract the video
					if r == pomice.enums.URLRegex.YOUTUBE_URL:
						pl_url = self.YOUTUBE_VID_IN_PLAYLIST.match(url)
						if pl_url:
							url = pl_url.group("video") # Get the video identifier
					break # Leave the loop
			else:
				return None # Not found
		node = self.get_node()
		# Here we either have a video identifier - or a search term
		starting_track = await node.get_tracks(query=url,ctx=ctx,search_type=search_type or "ytsearch")
		if not isinstance(starting_track,list):
			return None # Something went wrong loading this
		starting_track = starting_track[0]
		# Load the recommendations
		tracks = None
		last_count = -1
		while True:
			# Check for Spotify tracks first
			if starting_track.track_type == pomice.enums.TrackType.SPOTIFY:
				playlist = await node.get_recommendations(track=starting_track,ctx=ctx)
				if not isinstance(playlist,list):
					return playlist
				# Create a Playlist object for this - so we can retrieve the tracks later
				playlist = pomice.objects.Playlist(
					playlist_info={"name":"Mix - {}".format(self.get_track_title(starting_track))},
					playlist_type=pomice.enums.PlaylistType.SPOTIFY,
					tracks=[starting_track]+playlist # Include the original track in the search
				)
			else:
				# Assume it's a YT track - the recommendations function is broken for those - roll our own
				playlist = await node.get_tracks(
					query="https://www.youtube.com/watch?v=[[id]]&list=RD[[id]]".replace("[[id]]",starting_track.identifier),
					ctx=ctx,
					search_type=search_type or "ytsearch"
				)
				if not isinstance(playlist,pomice.objects.Playlist): # Not a playlist object
					return playlist # Return as-is
			if not tracks: # Set up our playlist
				tracks = playlist
			else: # We already have a playlist started - just add to it
				tracks.tracks.extend(playlist.tracks[1:])
			if len(tracks.tracks) >= recommend_count or len(tracks.tracks) == last_count:
				break # We got enough or no new tracks were added
			last_count = len(tracks.tracks) # Update the running count to avoid dead loops
			# Reset our starting track to load the next set
			starting_track = playlist.tracks[-1]
		if isinstance(tracks,pomice.objects.Playlist): # Ensure we only take between 2 and 100
			tracks.tracks = tracks.tracks[:min(max(2,recommend_count),100)]
		return tracks

	def get_seek(self, url):
		try:
			adj_dict = {"h":3600,"m":60,"s":1}
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
				total_time += int(x)*adj_dict.get(last_type,0) # Default to 0 if not a valid type
			seek_pos = total_time*1000
		except:
			seek_pos = 0
		return seek_pos

	def get_track_range(self, url, tracks):
		new_tracks = None
		if url:
			try:
				# Extract the last range listed, if any
				range_str = list(self.range_regex.finditer(url))[-1].group("range")
				if not range_str:
					return tracks
				elif ":" in range_str:
					# Got slice notation
					start = stop = step = None
					vals = range_str.replace("[","").replace("]","").split(":")
					try: start = int(vals[0])
					except: pass
					try: stop = int(vals[1])
					except: pass
					try: step = int(vals[2])
					except: pass
					# Let's attempt to apply the settings
					new_tracks = tracks[start:stop:step]
				else:
					# Got A,B,C-F notation
					song_numbers = []
					song_strings = range_str.replace(","," ").split()
					for num in song_strings:
						if "-" in num: # Got a range
							l,b = map(int,num.split("-"))
							assert 0 < l <= len(tracks) and 0 < b <= len(tracks)
							song_numbers.extend(list(range(min(l,b)-1,max(l,b))))
						else: # Assume it's just a number
							n = int(num)
							assert 0 < n <= len(tracks)
							song_numbers.append(n-1)
					song_numbers = sorted(list(set(song_numbers))) # Strip dupes, reorder
					# Let's build our new list of songs
					new_tracks = [tracks[x] for x in song_numbers]
			except:
				pass
		return new_tracks or tracks

	async def resolve_search(self, ctx, url, message = None, shuffle = False, range_str = "", recommend = False, recommend_count = 25, search_type = None):
		# Helper method to search for songs/resolve urls and add the contents to the queue
		url = url.strip('<>')
		# Check if url - if not, remove /
		urls = Utils.get_urls(url)
		seek_pos = 0
		node = self.get_node()
		try:
			if urls: # Need to load via node get_tracks/get_playlist
				url = urls[0] # Get the first URL
				try:
					# Check if it's using the new youtube.com/live/id URL approach
					yt_url = pomice.URLRegex.YOUTUBE_URL.match(url)
					if yt_url and yt_url.group(5).lower() == "live":
						# Reformat the URL to use the prior approach
						url = "https://www.youtube.com/watch?v={}".format(yt_url.group(6).lstrip("/"))
				except: pass
				try:
					# Check if we have a spotify.link and attempt to chase the redirects
					if self.spotify_link_regex.match(url):
						async with aiohttp.ClientSession() as session:
							async with session.get(url, allow_redirects=False) as response:
								url = str(response).split("Location': \'")[1].split("\'")[0]
				except: pass
				try:
					# Check for a bandcamp URL and try to rip info
					if self.bandcamp_regex.match(url):

						def process_duration(duration):
							# Helper to convert ISO8601 date string to ms
							total = 0
							check = {"h":3600,"m":60,"s":1}
							current = ""
							for char in duration.lower():
								if char.isdigit():
									current += char
								else:
									# Check for valid chars
									if char in check: # Got it
										if current:
											try: current = int(current)
											except: current = 0
										if current != 0:
											total += check[char]*current
									current = ""
							total *= 1000
							return total

						def get_track_dict(ctx,data,artist,image):
							dur = process_duration(data.get("item",{}).get("duration",data.get("duration","0")))
							return {
								"author":artist,
								"image":image,
								"thumb":image,
								"thumbnail":image,
								"title":data.get("item",{}).get("name",data.get("name","Unknown Title")),
								"length":dur,
								"timestamp":dur,
								"sourceName":"http",
								"track_type":"http",
								"uri":data.get("item",{}).get("@id",data.get("@id")),
								"ctx":ctx
							}

						seek_pos = self.get_seek(url)
						bandcamp_html = await DL.async_text(url)
						# Walk the html looking for a particular string
						track_urls = []
						track_dicts = []
						artist = album = image = None
						html_lines = bandcamp_html.split("\n")
						for i,line in enumerate(html_lines):
							# Bandcamp gives us some JSON data that has plenty of useful info
							if '<script type="application/ld+json">' in line:
								json_data = json.loads(html_lines[i+1].strip().replace("\r","").replace("\n",""))
								artist = json_data["byArtist"]["name"]
								image  = json_data["image"]
								if "track" in json_data:
									# It's an album
									for x in json_data["track"]["itemListElement"]:
										track_dicts.append(get_track_dict(ctx,x,artist,image))
									album = json_data["name"]
								else:
									# It's an individual song
									track_dicts.append(get_track_dict(ctx,json_data,artist,image))
									# album = json_data["inAlbum"]["name"]
								continue
							# Let's search for our mp3 streams
							if "&quot;https://t4.bcbits.com/stream/" in line:
								parts = line.split("&quot;https://t4.bcbits.com/stream/")[1:]
								for part in parts:
									# Get the important URL info and strip unneeded stuff
									t_url = "https://t4.bcbits.com/stream/{}".format(part.split("&quot;}")[0])
									track_urls.append(t_url)
								continue
							if track_urls and track_dicts:
								# Leave if we have both fields already
								break
						assert len(track_urls) == len(track_dicts) # Make sure we got the right number of tracks
						tracks = []
						for i,td in enumerate(track_dicts):
							# Rewrap the tracks as CorpTracks to allow custom attributes
							td["lazy_load_url"] = track_urls[i]
							tracks.append(CorpTrack(td))
						# Check for r=[x:y:z] or r=a,b,c-f style ranges
						tracks = self.get_track_range(range_str,tracks)
						if seek_pos > 0: setattr(tracks[0],"seek",seek_pos)
						if shuffle: random.shuffle(tracks)
						return {"tracks":tracks, "playlist":album, "search":url.split("?")[0]} if album else {"tracks":tracks[0]}
				except: pass
				if recommend:
					tracks = await self.get_recommendations(ctx,url,recommend_count,search_type=search_type)
				else:
					tracks = await node.get_tracks(query=url,ctx=ctx,search_type=search_type or "ytsearch")
				# Get the first hit if it's not a playlist
				if isinstance(tracks,list):
					tracks = tracks[0]
				else: # We got a playlist - try to find out the index of the selected song if any
					if getattr(tracks,"selected_track",None):
						# First scrape for an ?/&index=X value
						index = 0
						try: index = int(next((x[6:] for x in url.split("?")[1].split("&") if x.lower().startswith("index=")),"0"))-1
						except: pass
						# Gather all occurrences of the selected song
						matches = [i for i,x in enumerate(tracks.tracks) if x == tracks.selected_track]
						# Take the song at the index if both match - or else take the first occurrence
						# If we didn't match - just leave the tracks as-is
						if index in matches: # We can take the index to the end
							tracks.tracks = tracks.tracks[index:]
						elif matches: # Let's just start at the first match
							tracks.tracks = tracks.tracks[matches[0]:]
				# Let's also get the seek position if needed
				seek_pos = self.get_seek(url)
			else: # Got a search term - let's search
				tracks = await node.get_tracks(query=url,ctx=ctx,search_type=search_type or "ytsearch")
				if isinstance(tracks,pomice.objects.Playlist): tracks = tracks.tracks
				if self.settings.getServerStat(ctx.guild, "YTMultiple", False):
					delay = self.settings.getServerStat(ctx.guild, "MusicDeleteDelay", 20)
					# We want to let the user pick
					list_show = "Please select the number of the track you'd like to add:"
					index, message = await PickList.Picker(
						title=list_show,
						list=[x.info['title'] for x in tracks[:5]],
						ctx=ctx,
						message=message
					).pick()
					if index < 0:
						if index == -3: await message.edit(content="Something went wrong :(",delete_after=delay)
						elif index == -2: await message.edit(content="Times up!  We can search for music another time.",delete_after=delay)
						else: await message.edit(content="Aborting!  We can search for music another time.",delete_after=delay)
						return False
					tracks = tracks[index]
				else:
					# We only want the first entry
					tracks = tracks[0]
				# Check if we're gathering recommendations
				if recommend:
					tracks = await self.get_recommendations(ctx,tracks.identifier,recommend_count)
		except Exception as e:
			tracks = None # Clear it out as something went wrong
			print("Error resolving search:\n{}".format(repr(e)))
		# We need to figure out if we've loaded a playlist
		if isinstance(tracks,pomice.objects.Playlist):
			# Check for range notation and limit the results as needed
			tracks.tracks = self.get_track_range(range_str,tracks.tracks)
			# Rewrap the tracks as CorpTracks to allow custom attributes
			tracks.tracks = [CorpTrack(track,radio=False if i==0 else recommend,search_type=None if urls else search_type or "ytsearch") for i,track in enumerate(tracks.tracks)]
			if seek_pos > 0: setattr(tracks.tracks[0],"seek",seek_pos)
			if shuffle: random.shuffle(tracks.tracks)
			return {
				"data":tracks.playlist_info,
				"tracks":tracks.tracks,
				"playlist":tracks.name,
				"search":tracks.uri
			}
		elif isinstance(tracks,pomice.objects.Track):
			# Rewrap the track as a CorpTrack to allow custom attributes
			track = CorpTrack(tracks,radio=recommend,search_type=None if urls else search_type or "ytsearch")
			if seek_pos > 0: track.seek = seek_pos
			return {"tracks":track,"search":url}

	def format_scale(self, player, prefix="", hide_100=True):
		# Returns a percent for the time scale
		timescale = getattr(player,"timescale",self.default_timescale())
		ts_perc = math.ceil(timescale.get("speed",1.0)/timescale.get("rate",1.0)*100)
		if hide_100 and ts_perc==100: return ""
		return "{}{:,}%".format(prefix,ts_perc)

	def apply_scale(self, player, time_value, reversed=False):
		if not isinstance(time_value,(int,float)): return time_value
		# Helper to get the current player's timescale and apply it to whatever passed time
		timescale = getattr(player,"timescale",self.default_timescale())
		if reversed: return time_value * timescale.get("speed",1.0) * timescale.get("rate",1.0)
		return time_value / timescale.get("speed",1.0) / timescale.get("rate",1.0)
	
	def format_duration(self, dur, track=None):
		if isinstance(track,pomice.objects.Track) and getattr(track,"is_stream",None):
			# Might be a fleshed out pomice.Track, might not.  We check as much as we can
			# to determine if it's a stream first.
			return "[Live Stream]"
		dur = int(dur/1000)
		hours = int(dur//3600)
		minutes = int((dur%3600)//60)
		seconds = int(dur%60)
		return "{:02d}h:{:02d}m:{:02d}s".format(hours, minutes, seconds)

	def format_elapsed(self, player, track):
		progress = player.position # self.apply_scale(player,player.position)
		total    = self.apply_scale(player,track.length)
		return "{} -- {}".format(self.format_duration(progress),self.format_duration(total,track))

	def progress_bar(self,player,track,bar_width=31,show_percent=True,include_time=False):
		# Returns a [#####-----] XX.x% style progress bar
		progress = player.position # self.apply_scale(player,player.position)
		total    = self.apply_scale(player,track.length) if not hasattr(track,"is_stream") or not track.is_stream else 0
		bar = ""
		# Account for the brackets
		bar_width = 10 if bar_width-2 < 10 else bar_width-2
		if total == 0:
			# We don't know how long the song is - or it's a stream
			# return a progress bar of [//////////////] instead
			bar = "[`{}`]".format("/"*bar_width)
		else:
			# Calculate the progress vs total
			p = int(round((progress/total*bar_width)))
			bar = "[`{}{}`]".format("■"*p,"-"*(bar_width-p))
		if show_percent:
			bar += " --%" if total == 0 else " {}%".format(int(round(progress/total*100)))
		if include_time:
			time_prefix = "{} - {}\n".format(self.format_duration(progress),self.format_duration(total,track))
			bar = time_prefix + bar
		return bar

	def progress_moon(self,player,track,moon_count=10,show_percent=True,include_time=False):
		# Make some shitty moon memes or something... thanks Midi <3
		progress = player.position # self.apply_scale(player,player.position)
		total    = self.apply_scale(player,track.length) if not hasattr(track,"is_stream") or not track.is_stream else 0
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

	async def add_to_queue(self, player, song_list, position=-1):
		# Add songs as long as they're applicable - returns number added
		added = 0
		if not isinstance(song_list,(list,tuple)):
			# Ensure it's in a list or tuple
			song_list = [song_list]
		for song in (song_list[::-1] if position >= 0 else song_list):
			if isinstance(song,pomice.objects.Track):
				if position >= 0:
					# If we're adding it to a specific position, use _insert()
					player.queue._insert(position,song)
				else:
					# We're just adding it to the end - use put()
					player.queue.put(song)
				added += 1
		return added

	def get_track_title(self,track):
		# If we have a non-YouTube track, format the title as "Artist - Title"
		if track.track_type != pomice.enums.TrackType.YOUTUBE or track.search_type == "ytmsearch":
			return "{} - {}".format(track.author,track.title)
		return track.title

	async def state_added(self,ctx,songs,message=None,shuffled=False,queue=None,recommend=False,position=-1):
		# Helper to state songs added, whether or not they were shuffled - and to
		# edit a passed message (if any).
		delay = self.settings.getServerStat(ctx.guild, "MusicDeleteDelay", 20)
		if not "tracks" in songs: return None # Missing info
		desc = "Requested by {}{}".format(
			ctx.author.mention,
			" (via radio)" if recommend else ""
		)
		if isinstance(songs["tracks"],list): # Added a playlist
			# Get the track positions in the queue
			if queue:
				start_pos = len(queue)-len(songs["tracks"])+1 if position < 0 else position+1
				end_pos   = start_pos + len(songs["tracks"])-1
				desc = "At positions {} through {} in the playlist\n{}".format(
					start_pos,
					end_pos,
					desc
				)
			embed = Message.Embed(
				title="♫ Added {}{} song{} from {}".format(
					len(songs["tracks"]),
					" shuffled" if shuffled else "",
					"" if len(songs["tracks"])==1 else "s",
					songs.get("playlist","Unknown Playlist")
				),
				description=desc,
				url=songs.get("search"),
				delete_after=delay,
				color=ctx.author
			)
		elif isinstance(songs["tracks"],pomice.objects.Track): # Only added one track
			# Get the track position in the queue
			if not shuffled and queue:
				desc = "{} in the playlist\n{}".format(
					"Next" if position==0 or len(queue)==1 else "At position {}".format(len(queue) if position < 0 else position+1),
					desc
				)
			track = songs["tracks"]
			fields = [{"name":"Duration","value":self.format_duration(track.length,track),"inline":False}]
			if getattr(track,"seek",None):
				fields.append({"name":"Starting At","value":self.format_duration(track.seek),"inline":False})
			embed = Message.Embed(
				title="♫ Enqueued: {}".format(self.get_track_title(track)),
				description=desc,
				fields=fields,
				color=ctx.author,
				thumbnail=getattr(track,"thumb",None),
				url=track.uri,
				delete_after=delay
			)
		else:
			return None # Wrong type :(
		# Edit if we need to - otherwise send a new message
		if message: return await embed.edit(ctx,message)
		return await embed.send(ctx)

	async def _get_playlist_data(self,player,timestamp=True):
		# Helper method to save the passed player's playlist to native objects for json serialization
		current = player.track.info
		current["encoded"] = player.track.track_id
		current["id"] = current["encoded"] # Retained for backwards compat
		queue = []
		for x in player.queue.copy():
			x.info["encoded"] = x.track_id
			x.info["id"] = x.info["encoded"] # Retained for backwards compat
			queue.append(x.info)
		if current and (player.is_playing or player.is_paused):
			if timestamp: current["position"] = player.position/1000
			queue.insert(0,current)
		return queue

	async def _load_playlist_data(self,ctx,player,playlist_data=[],position=-1):
		# Helper method to apply loaded json data to the passed player
		valid_tracks = self.get_tracks_from_data({"tracks":playlist_data},check_start=False,check_seek=True,ctx=ctx)
		added_tracks = await self.add_to_queue(player,valid_tracks,position=position)
		return (valid_tracks,added_tracks)

	async def _load_playlist_from_url(self, message, ctx, shuffle = False, range_str = "", position = -1):
		delay = self.settings.getServerStat(ctx.guild, "MusicDeleteDelay", 20)
		player = self.get_player(ctx.guild)
		url = await Utils.get_message_content(message)
		if not player or not player.is_connected:
			return await Message.Embed(title="♫ Not connected to a voice channel!",color=ctx.author,delete_after=delay).send(ctx)
		if not url and not message.attachments:
			return await ctx.send("Usage: `{}{} [url or attachment]`".format(ctx.prefix,"shufflepl" if shuffle else "loadpl"))
		url = message.attachments[0].url if message.attachments else url
		m = await Message.Embed(title="♫ Downloading...",color=ctx.author).send(ctx)
		try:
			playlist = await DL.async_json(url.strip("<>"))
		except Exception as e:
			return await Message.Embed(title="♫ Couldn't serialize playlist!",description=str(e),color=ctx.author,delete_after=delay).edit(ctx,m)
		if not len(playlist): return await Message.Embed(title="♫ Playlist is empty!",color=ctx.author).edit(ctx,m)
		if not isinstance(playlist,list): return await Message.Embed(title="♫ Playlist json is incorrectly formatted!",color=ctx.author).edit(ctx,m)
		# Check for range notation and limit the results as needed
		playlist = self.get_track_range(range_str,playlist)
		if shuffle: random.shuffle(playlist)
		# Let's walk the items and add them
		valid_tracks,added_tracks = await self._load_playlist_data(ctx,player,playlist_data=playlist,position=position)
		await Message.Embed(title="♫ Added {:,}/{:,} {}song{} from playlist!".format(added_tracks,len(valid_tracks),"shuffled " if shuffle else "", "" if len(playlist) == 1 else "s"),color=ctx.author,delete_after=delay).edit(ctx,m)
		self.bot.dispatch("check_play",player)

	async def _resolve_message(self, message):
		# Helper to check the passed message for a discord message link - or a replied to message.
		# Will return the target message - if found, otherwise the original
		if message.reference:
			# Resolve the replied to reference to a message object
			try:
				m = await Utils.get_replied_to(message)
				if m.content or m.attachments:
					message = m
			except: pass			
		# Check if we have any attachments - if so, those take priority
		if message.content is None and message.attachments:
			return message
		# Check if the message contains a discord message URL
		m_match = self.message_regex.search(message.content)
		if not m_match:
			return message
		# We got a match - let's try to get the server, channel, and message
		ctx = await self.bot.get_context(message)
		m = await Utils.get_message_from_url(m_match.group(),ctx=ctx)
		return m or message

	def _get_search_type(self, ctx, url):
		# Check for a specific search type set
		url_parts = []
		search_type = None
		for u in url.split():
			if u.lower() in ("st=ytsearch","st=ytmsearch","st=scsearch","st=yt","st=ytm","st=sc"):
				search_type = u.lower().split("=")[-1]
				if not search_type.endswith("search"):
					search_type += "search" # Ensure it's set to a valid value
			else:
				url_parts.append(u)
		url = " ".join(url_parts) # Rejoin the parts - skipping any search queries
		# if we don't have a specified search, let's fall back to the server's setting
		if not search_type:
			search_type = self.settings.getServerStat(ctx.guild, "MusicSearchType", "ytsearch")
		return (url,search_type)

	def _get_range_str(self,url):
		# Check for a range argument
		range_str = ""
		if url: # Only process if we got something
			url_parts = []
			for u in url.split():
				m = self.range_regex.match(u)
				if m: range_str = m.group(0)
				else: url_parts.append(u)
			url = " ".join(url_parts)
		return (url,range_str)

	@commands.command(aliases=["bindplayer","bindmusic","bindto","boundto"])
	async def rebind(self, ctx, channel = None):
		"""Re-binds the music related status messages to the passed channel - or prints the current if no channel is passed."""
		delay = self.settings.getServerStat(ctx.guild, "MusicDeleteDelay", 20)
		player = self.get_player(ctx.guild)
		if not player or not player.is_connected:
			return await Message.Embed(title="♫ Not connected to a voice channel!",color=ctx.author,delete_after=delay).send(ctx)
		if channel is None:
			# Just print the current channel
			channel = getattr(player,"bound_channel",None)
			if not channel:
				player_ctx = getattr(player,"ctx",getattr(player,"track_ctx",None))
				if not player_ctx:
					return await Message.Embed(title="♫ I couldn't get the player's bound channel!",color=ctx.author,delete_after=delay).send(ctx)
				else:
					channel = player_ctx.channel
			return await Message.Embed(
				title="♫ Player currently bound to:",
				description=channel.mention,
				color=ctx.author,
				delete_after=delay
			).send(ctx)
		# Try to resolve it to a channel
		channel = DisplayName.channelForName(channel,ctx.guild)
		if not channel:
			return await Message.Embed(title="♫ I couldn't find that channel!",color=ctx.author,delete_after=delay).send(ctx)
		# Ensure it's a channel where messages can be sent
		if isinstance(channel,discord.CategoryChannel):
			return await Message.Embed(title="♫ You can only pass text channels!",color=ctx.author,delete_after=delay).send(ctx)
		# Make sure the author can send messages in this channel
		perms = channel.permissions_for(ctx.author)
		if not (perms.send_messages or perms.send_messages_in_threads):
			return await Message.Embed(title="♫ You can only bind the player to channels where you can send messages!",color=ctx.author,delete_after=delay).send(ctx)
		# Bind the player to the new channel
		player.bound_channel = channel
		await Message.Embed(
			title="♫ Player now bound to:",
			description=channel.mention,
			color=ctx.author,
			delete_after=delay
		).send(ctx)

	@commands.command(aliases=["recon","rec"])
	async def reconnect(self, ctx):
		"""Attempts to have the bot save the current playlist to memory, leave the voice chat, reconnect, and reload the playlist.
		May help if the bot states it is playing, but makes no sound."""
		delay = self.settings.getServerStat(ctx.guild, "MusicDeleteDelay", 20)
		player = self.get_player(ctx.guild)
		if not player or not player.is_connected:
			return await Message.Embed(title="♫ Not connected to a voice channel!",color=ctx.author,delete_after=delay).send(ctx)
		# We have a connected player - let's save the playlist
		playlist = await self._get_playlist_data(player)
		channel = player.channel # Preserve the channel the player was using
		await self._stop(player,clear_attrs=True,clear_queue=True,disconnect=True)
		await asyncio.sleep(self.reconnect_wait) # Wait to let everything settle
		await channel.connect(cls=CorpPlayer)
		# Get a new player
		player = self.get_player(ctx.guild)
		# Load the playlist data we had saved from before and dispatch the check_play event
		await self._load_playlist_data(ctx,player,playlist_data=playlist)
		self.bot.dispatch("check_play",player)

	@commands.command()
	async def loadpl(self, ctx, *, url = None):
		"""Loads the passed playlist json data.  Accepts a url - or picks the first attachment.
		
		Note that the structure of this file is very specific and alterations may not work.
		
		Only files dumped via the savepl command are supported.
		
		Can take an optional -range=X argument which denotes which tracks to include.
		e.g. To load the 1st, 3rd, and 5th through 7th tracks: -range=1,3,5-7
		
		Python's slice notation can also be used for ranges.
		e.g. To load every other track starting with the 4th through 10 from the end: -range=[3:-10:2]"""
		url,range_str = self._get_range_str(url)
		message = await self._resolve_message(ctx.message)
		await self._load_playlist_from_url(message, ctx, range_str=range_str)

	@commands.command(aliases=["loadpln"])
	async def loadplnext(self, ctx, *, url = None):
		"""Loads the passed playlist json data.  Accepts a url - or picks the first attachment.
		Adds songs to the beginning of the queue if enabled by the allowplaynext command.
		
		Note that the structure of this file is very specific and alterations may not work.
		
		Only files dumped via the savepl command are supported.
		
		Can take an optional -range=X argument which denotes which tracks to include.
		e.g. To load the 1st, 3rd, and 5th through 7th tracks: -range=1,3,5-7
		
		Python's slice notation can also be used for ranges.
		e.g. To load every other track starting with the 4th through 10 from the end: -range=[3:-10:2]"""
		url,range_str = self._get_range_str(url)
		message = await self._resolve_message(ctx.message)
		await self._load_playlist_from_url(message, ctx, range_str=range_str, position=0)

	@commands.command()
	async def shufflepl(self, ctx, *, url = None):
		"""Loads and shuffles the passed playlist json data.  Accepts a url - or picks the first attachment.
		
		Note that the structure of this file is very specific and alterations may not work.
		
		Only files dumped via the savepl command are supported.
		
		Can take an optional -range=X argument which denotes which tracks to include.
		e.g. To load the 1st, 3rd, and 5th through 7th tracks: -range=1,3,5-7
		
		Python's slice notation can also be used for ranges.
		e.g. To load every other track starting with the 4th through 10 from the end: -range=[3:-10:2]"""
		url,range_str = self._get_range_str(url)
		message = await self._resolve_message(ctx.message)
		await self._load_playlist_from_url(message, ctx, shuffle=True, range_str=range_str)

	@commands.command(aliases=["shufflepln"])
	async def shuffleplnext(self, ctx, *, url = None):
		"""Loads and shuffles the passed playlist json data.  Accepts a url - or picks the first attachment.
		Adds songs to the beginning of the queue if enabled by the allowplaynext command.
		
		Note that the structure of this file is very specific and alterations may not work.
		
		Only files dumped via the savepl command are supported.
		
		Can take an optional -range=X argument which denotes which tracks to include.
		e.g. To load the 1st, 3rd, and 5th through 7th tracks: -range=1,3,5-7
		
		Python's slice notation can also be used for ranges.
		e.g. To load every other track starting with the 4th through 10 from the end: -range=[3:-10:2]"""
		url,range_str = self._get_range_str(url)
		message = await self._resolve_message(ctx.message)
		await self._load_playlist_from_url(message, ctx, shuffle=True, range_str=range_str, position=0)

	@commands.command()
	async def savepl(self, ctx, *, options = ""):
		"""Saves the current playlist to a json file that can be loaded later.
		
		Note that the structure of this file is very specific and alterations may not work.
		
		Available options:

		ts : Exclude the timestamp of the currently playing song.
		
		Any other options passed will be used as the file name."""
		delay = self.settings.getServerStat(ctx.guild, "MusicDeleteDelay", 20)
		player = self.get_player(ctx.guild)
		if not player or not player.is_connected:
			return await Message.Embed(title="♫ Not connected to a voice channel!",color=ctx.author,delete_after=delay).send(ctx)
		# Get the options
		timestamp = True
		remaining = []
		for x in options.split():
			if re.fullmatch(r"-?(no?-?)?t(s|imestamp|ime)?(=(no?|off|disabled?|false))?",x):
				timestamp = False
			else:
				remaining.append(x)
		filename = "playlist.json"
		if remaining: # Let's sanitize and see what we end up with
			# Join without spaces - and only allow alphanumeric or _, and - chars
			temp_name = "".join([x for x in "_".join(remaining) if x.isalnum() or x in "_-."])
			# Strip duplicate _ and - chars
			temp_name = re.sub("-{2,}","-",temp_name)
			temp_name = re.sub("_{2,}","_",temp_name)
			# Strip the extension
			if temp_name.lower().endswith(".json"):
				temp_name = temp_name[:-5]
			# Ensure our name length
			if len(temp_name) > 123:
				temp_name = temp_name[:123]
			# Add the extension if we have something to add
			if temp_name.replace("-","").replace("_",""):
				filename = temp_name+".json"
		message = await Message.Embed(title="♫ Gathering info...",color=ctx.author).send(ctx)
		# Let's save the playlist
		queue = await self._get_playlist_data(player,timestamp=timestamp)
		if not len(queue):
			return await Message.Embed(title="♫ No playlist to save!",color=ctx.author,delete_after=delay).send(ctx,message)
		await Message.Embed(title="♫ Saving and uploading...",color=ctx.author).edit(ctx,message)
		temp = tempfile.mkdtemp()
		temp_json = os.path.join(temp,filename)
		try:
			json.dump(queue,open(temp_json,"w"),indent=2)
			await ctx.send(file=discord.File(temp_json))
		except Exception as e:
			return await Message.Embed(title="♫ An error occurred creating the playlist!",description=str(e),color=ctx.author).edit(ctx,message)
		finally:
			shutil.rmtree(temp,ignore_errors=True)
		return await Message.Embed(title="♫ Uploaded playlist!",color=ctx.author).edit(ctx,message)

	@commands.command(aliases=["summon"])
	async def join(self,ctx,*,channel=None):
		"""Joins a passed voice channel, or the author's if none passed."""

		delay = self.settings.getServerStat(ctx.guild, "MusicDeleteDelay", 20)
		if channel is None:
			if not ctx.author.voice:
				return await Message.Embed(title="♫ You need to pass a voice channel for me to join!",color=ctx.author,delete_after=delay).send(ctx)
			channel = ctx.author.voice.channel
		else:
			channel = DisplayName.channelForName(channel,ctx.guild,"voice")
		if not channel:
			return await Message.Embed(title="♫ I couldn't find that voice channel!",color=ctx.author,delete_after=delay).send(ctx)
		player = self.get_player(ctx.guild)
		if player and player.is_connected:
			if not (player.is_paused or player.is_playing):
				if player.channel != channel: # Only move if we need to
					await player.move_to(channel)
					return await Message.Embed(title="♫ Ready to play music in {}!".format(channel),color=ctx.author,delete_after=delay).send(ctx)
				else: # We're already there - whine
					return await Message.Embed(title="♫ I'm already in {}!".format(channel),color=ctx.author,delete_after=delay).send(ctx)
			else:
				return await Message.Embed(title="♫ I'm already playing music in {}!".format(player.channel),color=ctx.author,delete_after=delay).send(ctx)
		await channel.connect(cls=CorpPlayer)
		await Message.Embed(title="♫ Ready to play music in {}!".format(channel),color=ctx.author,delete_after=delay).send(ctx)

	@commands.command(aliases=["disconnect","okbye"])
	async def leave(self, ctx):
		"""Stops and disconnects the bot from voice."""

		delay = self.settings.getServerStat(ctx.guild, "MusicDeleteDelay", 20)
		player = self.get_player(ctx.guild)
		if player and player.is_connected:
			await self._stop(player,clear_attrs=True,clear_queue=True,disconnect=True)
			return await Message.Embed(title="♫ I've left the voice channel!",color=ctx.author,delete_after=delay).send(ctx)
		await Message.Embed(title="♫ Not connected to a voice channel!",color=ctx.author,delete_after=delay).send(ctx)

	async def _play(self, ctx, url, position=-1):
		# Helper to search for and queue up songs as the passed position
		delay = self.settings.getServerStat(ctx.guild, "MusicDeleteDelay", 20)
		player = self.get_player(ctx.guild)
		if not player or not player.is_connected:
			return await Message.Embed(title="♫ I am not connected to a voice channel!",color=ctx.author,delete_after=delay).send(ctx)
		if url is None and ctx.message.attachments: # Get the first attachment as the URL
			url = ctx.message.attachments[0].url
		if player.is_paused and url is None:
			# We're trying to resume
			return await ctx.invoke(self.resume)
		if url is None:
			return await Message.Embed(title="♫ You need to pass a url or search term!",color=ctx.author,delete_after=delay).send(ctx)
		# Gather the search type
		url,search_type = self._get_search_type(ctx,url)
		# Process and strip out any range values
		url,range_str = self._get_range_str(url)
		# Build our search - and only use it if we don't have a URL
		search_provider = None
		if not Utils.get_urls(url.strip('<>')):
			search_provider = {"ytmsearch":" YouTube Music","scsearch":" Sound Cloud"}.get(search_type," YouTube")
		message = await Message.Embed(
			title="♫ Searching{} For: {}".format(search_provider or "",url.strip("<>")),
			color=ctx.author
			).send(ctx)
		# Add our url to the queue
		songs = await self.resolve_search(ctx,url,message=message,range_str=range_str,search_type=search_type)
		# Take the songs we got back - if any - and add them to the queue
		if not songs or not "tracks" in songs: # Got nothing :(
			return await Message.Embed(title="♫ I couldn't find anything for that search!",description="Try using more specific search terms, or pass a url instead.",color=ctx.author,delete_after=delay).edit(ctx,message)
		await self.add_to_queue(player,songs["tracks"],position=position)
		await self.state_added(ctx,songs,message,shuffled=False,queue=player.queue,recommend=False,position=position)
		self.bot.dispatch("check_play",player) # Dispatch the event to check if we should start playing

	@commands.command(aliases=["p"])
	async def play(self, ctx, *, url = None):
		"""Plays from a url (almost anything Lavalink supports) or resumes a currently paused song.
		Adds songs to the end of the queue.
		You can control what search type is used by passing one of the following as an arg:
		
		st=ytsearch (searches YouTube)
		st=ytmsearch (searches YouTube Music)
		st=scsearch (searches SoundCloud)
		
		Can take an optional -range=X argument which denotes which tracks to include.
		e.g. To load the 1st, 3rd, and 5th through 7th tracks: -range=1,3,5-7
		
		Python's slice notation can also be used for ranges.
		e.g. To load every other track starting with the 4th through 10 from the end: -range=[3:-10:2]"""

		await self._play(ctx, url)

	@commands.command(aliases=["pn","pnext","playn"])
	async def playnext(self, ctx, *, url = None):
		"""Plays from a url (almost anything Lavalink supports) or resumes a currently paused song.
		Adds songs to the beginning of the queue if enabled by the allowplaynext command.
		You can control what search type is used by passing one of the following as an arg:
		
		st=ytsearch (searches YouTube)
		st=ytmsearch (searches YouTube Music)
		st=scsearch (searches SoundCloud)
		
		Can take an optional -range=X argument which denotes which tracks to include.
		e.g. To load the 1st, 3rd, and 5th through 7th tracks: -range=1,3,5-7
		
		Python's slice notation can also be used for ranges.
		e.g. To load every other track starting with the 4th through 10 from the end: -range=[3:-10:2]"""

		await self._play(ctx, url, position=0)

	@commands.command(aliases=["suggestcount","recommendcount","rcount"])
	async def radiocount(self, ctx, *, count = None):
		"""Gets or sets the default number of recommended songs returned from 2 to 25 (bot-admin only)."""

		delay = self.settings.getServerStat(ctx.guild, "MusicDeleteDelay", 20)
		if count is None or not await Utils.is_bot_admin_reply(ctx):
			# Just report the current value
			count = self.settings.getServerStat(ctx.guild,"RecommendCountDefault",25)
			return await Message.Embed(title="♫ Recommended playlists currently include {} song{}.".format(count,"" if count==1 else "s"),color=ctx.author,delete_after=delay).send(ctx)
		# Should be bot-admin with a value
		try:
			count = int(count)
			assert 1 < count < 26
		except:
			return await Message.Embed(title="♫ Count must be an integer between 2 and 25!",color=ctx.author,delete_after=delay).send(ctx)
		self.settings.setServerStat(ctx.guild,"RecommendCountDefault",count)
		return await Message.Embed(title="♫ Recommended playlists will include {} song{}.".format(count,"" if count==1 else "s"),color=ctx.author,delete_after=delay).send(ctx)

	async def _radio(self, ctx, url, position=-1):
		delay = self.settings.getServerStat(ctx.guild, "MusicDeleteDelay", 20)
		player = self.get_player(ctx.guild)
		if not player or not player.is_connected:
			return await Message.Embed(title="♫ I am not connected to a voice channel!",color=ctx.author,delete_after=delay).send(ctx)
		if url is None:
			return await Message.Embed(title="♫ You need to pass a search term or YouTube link!",color=ctx.author,delete_after=delay).send(ctx)
		# Let's scrape the input for "-t #" or "t=#"
		primed = False
		pre_prime = None
		arg_list = []
		num = self.settings.getServerStat(ctx.guild,"RecommendCountDefault",25)
		for arg in url.split():
			if arg.lower() == "-t":
				pre_prime = arg
				primed = True
				continue
			elif arg.lower().startswith(("-t=","t=")) or primed:
				# Split and check
				try:
					test_num = int(arg.split("=")[-1])
					assert 1 < test_num < 101 # Allow an override of up to 100 songs
					num = test_num
					continue
				except: pass
				if pre_prime: # We have a placeholder to add
					arg_list.append(pre_prime)
					pre_prime = None
			arg_list.append(arg)
		url = " ".join(arg_list)
		# Gather the search type
		url,search_type = self._get_search_type(ctx,url)
		# Process and strip out any range values
		url,range_str = self._get_range_str(url)
		message = await Message.Embed(
			title="♫ Gathering Recommendations For: {}".format(url.strip("<>")),
			color=ctx.author
			).send(ctx)
		# Add our url to the queue
		songs = await self.resolve_search(ctx,url,message=message,range_str=range_str,recommend=True,recommend_count=num,search_type=search_type)
		# Take the songs we got back - if any - and add them to the queue
		if not songs or not "tracks" in songs: # Got nothing :(
			return await Message.Embed(title="♫ I couldn't find anything for that search!",description="Try using more specific search terms, or pass a YouTube link instead.",color=ctx.author,delete_after=delay).edit(ctx,message)
		await self.add_to_queue(player,songs["tracks"],position=position)
		await self.state_added(ctx,songs,message,shuffled=False,queue=player.queue,recommend=True,position=position)
		self.bot.dispatch("check_play",player) # Dispatch the event to check if we should start playing

	@commands.command(aliases=["suggest","r","recommend"])
	async def radio(self, ctx, *, url = None):
		"""Queues up recommendations for the passed search term, YouTube URL, or Spotify URL.
		
		Can take an optional -range=X argument which denotes which tracks to include.
		e.g. To load the 1st, 3rd, and 5th through 7th tracks: -range=1,3,5-7
		
		Python's slice notation can also be used for ranges.
		e.g. To load every other track starting with the 4th through 10 from the end: -range=[3:-10:2]"""

		await self._radio(ctx, url)

	@commands.command(aliases=["suggestnext","rn","recommendnext"])
	async def radionext(self, ctx, *, url = None):
		"""Queues up recommendations for the passed search term, YouTube URL, or Spotify URL.
		Adds songs to the beginning of the queue if enabled by the allowplaynext command.
		
		Can take an optional -range=X argument which denotes which tracks to include.
		e.g. To load the 1st, 3rd, and 5th through 7th tracks: -range=1,3,5-7
		
		Python's slice notation can also be used for ranges.
		e.g. To load every other track starting with the 4th through 10 from the end: -range=[3:-10:2]"""

		await self._radio(ctx, url, position=0)

	@commands.command(aliases=["unp"])
	async def unplay(self, ctx, *, song_number = None):
		"""Removes the passed song number from the queue.  You must be the requester, or an admin to remove it.  Does not include the currently playing song."""
		
		delay = self.settings.getServerStat(ctx.guild, "MusicDeleteDelay", 20)
		player = self.get_player(ctx.guild)
		if not player or not player.is_connected:
			return await Message.Embed(title="♫ I am not connected to a voice channel!",color=ctx.author,delete_after=delay).send(ctx)
		if player.queue.is_empty:
			# No songs in queue
			return await Message.Embed(title="♫ No songs in queue!", description="If you want to bypass a currently playing song, use `{}skip` instead.".format(ctx.prefix),color=ctx.author,delete_after=delay).send(ctx)
		try:
			song_strings = song_number.replace(","," ").split()
			song_numbers = []
			for num in song_strings:
				if "-" in num: # Got a range
					l,b = map(int,num.split("-"))
					assert l > 0 and b > 0
					song_numbers.extend(list(range(min(l,b)-1,max(l,b))))
				else: # Assume it's just a number
					song_numbers.append(int(num)-1)
			song_numbers = sorted(list(set(song_numbers))) # Strip dupes, reorder
			assert song_numbers # Make sure we have *something*
		except:
			return await Message.Embed(title="♫ Not a valid song number!",color=ctx.author,delete_after=delay).send(ctx)
		if any((x < 0 or x >= len(player.queue) for x in song_numbers)):
			return await Message.Embed(title="♫ Out of bounds!  Song number must be between 1 and {}.".format(len(player.queue)),color=ctx.author,delete_after=delay).send(ctx)
		# Get the tracks outlined
		tracks = [(i,player.queue[i]) for i in song_numbers]
		# Get any that don't belong to us (if we're not bot-admin)
		not_ours = [] if Utils.is_bot_admin(ctx) else [track for track in tracks if track[1].ctx.author != ctx.author]
		# Find out which we can remove - and get their indices separately
		can_rem = [track for track in tracks if not track in not_ours]
		if can_rem:
			# We have at least one we can unplay - get the tracks that don't match the indices
			can_rem_nums = [x[0] for x in can_rem]
			new_tracks = [t for i,t in enumerate(player.queue) if i not in can_rem_nums]
			# Clear the player's queue and reload
			player.queue.clear()
			await self.add_to_queue(player,new_tracks)
			if len(can_rem)==1:
				i,t=can_rem[0]
				fields = [{
					"name":"{}. {}".format(i+1,self.get_track_title(t)),
					"value":"{}{} - Requested by {}{} - [Link]({})".format(
						self.format_duration(t.seek,t)+" -> " if hasattr(t,"seek") else "",
						self.format_duration(t.length,t),
						t.ctx.author.mention,
						" (via radio)" if t.radio else "",
						t.uri
					),
					"inline":False
				}]
				await Message.Embed(
					title="♫ Unplayed the following track!".format("" if len(can_rem)==1 else "s"),
					fields=fields,
					delete_after=delay,
					color=ctx.author
				).send(ctx)
			else:
				await Message.Embed(
					title="♫ Unplayed {:,} tracks!".format(len(can_rem)),
					delete_after=delay,
					color=ctx.author
				).send(ctx)
		if not_ours:
			await Message.Embed(
				title="♫ Could not unplay {:,} track{}!".format(len(not_ours),"" if len(not_ours)==1 else "s"),
				description="Tracks can only be unplayed by the user that requested them or an admin.",
				delete_after=delay,
				color=ctx.author
			).send(ctx)

	@commands.command(aliases=["unq"])
	async def unqueue(self, ctx, *, unqueue_from = None):
		"""Removes all songs you've added from the queue (does not include the currently playing song).
		Admins and bot-admins can pass a user to remove all of that user's queued songs, or 'all' to remove all songs from the queue."""

		delay = self.settings.getServerStat(ctx.guild, "MusicDeleteDelay", 20)
		player = self.get_player(ctx.guild)
		if not player or not player.is_connected:
			return await Message.Embed(title="♫ I am not connected to a voice channel!",color=ctx.author,delete_after=delay).send(ctx)
		if player.queue.is_empty:
			# No songs in queue
			return await Message.Embed(title="♫ No songs in queue!",description="If you want to bypass a currently playing song, use `{}skip` instead.".format(ctx.prefix),color=ctx.author,delete_after=delay).send(ctx)
		clear_from = ctx.author # Default to the author
		if unqueue_from: # We got something passed here - check for "all" first, as that has priority - and user next
			if unqueue_from.lower() in ("-all","all"):
				clear_from = True # Use "true" as a placeholder for everyone
			else: # Check if a user was passed
				check_user = DisplayName.memberForName(unqueue_from,ctx.guild)
				if check_user: # Got one - set it
					clear_from = check_user
		if Utils.is_bot_admin(ctx) or clear_from == ctx.author:
			queue = player.queue.copy()
			new_queue = [] if clear_from is True else [song for song in queue if song.ctx.author!=clear_from]
			removed = len(queue)-len(new_queue)
			if removed:
				player.queue.clear()
				if new_queue: await self.add_to_queue(player,new_queue)
				return await Message.Embed(title="♫ Removed {} song{} from queue!".format(removed,"" if removed == 1 else "s"),color=ctx.author,delete_after=delay).send(ctx)
			title = "♫ No songs in queue!" if clear_from is True else "♫ {} has no songs in the queue!".format(DisplayName.name(clear_from))
			return await Message.Embed(
				title=title,
				description="If you want to bypass a currently playing song, use `{}skip` instead.".format(ctx.prefix),
				color=ctx.author,
				delete_after=delay
			).send(ctx)
		await Message.Embed(title="♫ You can only remove songs you requested!", description="Only an admin or bot-admin can remove all queued songs or those requested by other users!",color=ctx.author,delete_after=delay).send(ctx)

	async def _shuffle(self, ctx, url, position=-1):
		delay = self.settings.getServerStat(ctx.guild, "MusicDeleteDelay", 20)
		player = self.get_player(ctx.guild)
		if not player or not player.is_connected:
			if url is None: # No need to connect to shuffle nothing
				return await Message.Embed(title="♫ I am not connected to a voice channel!",color=ctx.author,delete_after=delay).send(ctx)
			if not ctx.author.voice:
				return await Message.Embed(title="♫ You are not connected to a voice channel!",color=ctx.author,delete_after=delay).send(ctx)
			await player.connect(ctx.author.voice.channel.id)
		if url is None:
			if player.queue.is_empty:
				# No songs in queue
				return await Message.Embed(title="♫ No songs in queue!",color=ctx.author,delete_after=delay).send(ctx)
			# Get a list of current items, clear the existing queue, shuffle and add back
			queue = list(player.queue)
			random.shuffle(queue)
			player.queue.clear()
			await self.add_to_queue(player,queue)
			return await Message.Embed(title="♫ Shuffled {} song{}!".format(len(queue),"" if len(queue) == 1 else "s"),color=ctx.author,delete_after=delay).send(ctx)
		# Gather the search type
		url,search_type = self._get_search_type(ctx,url)
		# Process and strip out any range values
		url,range_str = self._get_range_str(url)
		# Build our search - and only use it if we don't have a URL
		search_provider = None
		if not Utils.get_urls(url.strip('<>')):
			search_provider = {"ytmsearch":" YouTube Music","scsearch":" Sound Cloud"}.get(search_type," YouTube")
		# We're adding a new song/playlist/search shuffled to the queue
		message = await Message.Embed(
			title="♫ Searching{} For: {}".format(search_provider or "",url.strip("<>")),
			color=ctx.author
			).send(ctx)
		# Add our url to the queue
		songs = await self.resolve_search(ctx,url,message=message,shuffle=True,range_str=range_str,search_type=search_type)
		# Take the songs we got back - if any - and add them to the queue
		if not songs or not "tracks" in songs: # Got nothing :(
			return await Message.Embed(title="♫ I couldn't find anything for that search!",description="Try using more specific search terms, or pass a url instead.",color=ctx.author,delete_after=delay).edit(ctx,message)
		await self.add_to_queue(player,songs["tracks"],position=position)
		await self.state_added(ctx,songs,message,shuffled=True,queue=player.queue,recommend=False,position=position)
		self.bot.dispatch("check_play",player) # Dispatch the event to check if we should start playing

	@commands.command()
	async def shuffle(self, ctx, *, url = None):
		"""Shuffles the current queue. If you pass a playlist url or search term, it first shuffles that, then adds it to the end of the queue.
		You can control what search type is used by passing one of the following as an arg:
		
		st=ytsearch (searches YouTube)
		st=ytmsearch (searches YouTube Music)
		st=scsearch (searches SoundCloud)
		
		Can take an optional -range=X argument which denotes which tracks to include.
		e.g. To load the 1st, 3rd, and 5th through 7th tracks: -range=1,3,5-7
		
		Python's slice notation can also be used for ranges.
		e.g. To load every other track starting with the 4th through 10 from the end: -range=[3:-10:2]"""

		await self._shuffle(ctx, url)

	@commands.command(aliases=["shufflen"])
	async def shufflenext(self, ctx, *, url = None):
		"""Shuffles the current queue. If you pass a playlist url or search term, it first shuffles that, then adds it to the beginning of the queue if enabled by the allowplaynext command.
		You can control what search type is used by passing one of the following as an arg:
		
		st=ytsearch (searches YouTube)
		st=ytmsearch (searches YouTube Music)
		st=scsearch (searches SoundCloud)
		
		Can take an optional -range=X argument which denotes which tracks to include.
		e.g. To load the 1st, 3rd, and 5th through 7th tracks: -range=1,3,5-7
		
		Python's slice notation can also be used for ranges.
		e.g. To load every other track starting with the 4th through 10 from the end: -range=[3:-10:2]"""

		await self._shuffle(ctx, url, position=0)

	@commands.command()
	async def pause(self, ctx):
		"""Pauses the currently playing song."""

		delay = self.settings.getServerStat(ctx.guild, "MusicDeleteDelay", 20)
		player = self.get_player(ctx.guild)
		if not player or not player.is_connected:
			return await Message.Embed(title="♫ Not connected to a voice channel!",color=ctx.author,delete_after=delay).send(ctx)
		if player.is_paused: # Just toggle play
			return await ctx.invoke(self.resume)
		if not player.is_playing:
			return await Message.Embed(title="♫ Not playing anything!",color=ctx.author,delete_after=delay).send(ctx)
		# Pause the track
		await player.set_pause(True)
		track = player.track
		track_ctx = getattr(player,"track_ctx",None)
		desc = "-- Volume at {}%{}".format(
			player.get_vol(ctx),
			"\n-- Repeat Enabled" if getattr(player,"repeat",False) else ""
		)
		if track_ctx:
			desc = "Requested by {}{}\n{}".format(
				track_ctx.author.mention,
				" (via radio)" if track.radio else "",
				desc
			)
		await Message.Embed(
			title="♫ Paused: {}".format(self.get_track_title(track)),
			fields=[{"name":"Elapsed","value":self.format_elapsed(player,track),"inline":False}],
			description=desc,
			color=ctx.author,
			url=track.uri,
			thumbnail=getattr(track,"thumb",None),
			delete_after=delay
		).send(ctx)

	@commands.command()
	async def paused(self, ctx, *, moons = None):
		"""Lists whether or not the player is paused.  Synonym of the playing command."""
		
		await ctx.invoke(self.playing,moons=moons)

	@commands.command()
	async def resume(self, ctx):
		"""Resumes the song if paused."""

		delay = self.settings.getServerStat(ctx.guild, "MusicDeleteDelay", 20)
		player = self.get_player(ctx.guild)
		if not player or not player.is_connected:
			return await Message.Embed(title="♫ I am not connected to a voice channel!",color=ctx.author,delete_after=delay).send(ctx)
		if not player.is_paused:
			return await Message.Embed(title="♫ Not currently paused!",color=ctx.author,delete_after=delay).send(ctx)
		# We're trying to resume
		await player.set_pause(False)
		track = player.track
		track_ctx = getattr(player,"track_ctx",None)
		desc = "-- Volume at {}%{}".format(
			player.get_vol(ctx),
			"\n-- Repeat Enabled" if getattr(player,"repeat",False) else ""
		)
		if track_ctx:
			desc = "Requested by {}{}\n{}".format(
				track_ctx.author.mention,
				" (via radio)" if track.radio else "",
				desc
			)
		await Message.Embed(
			title="♫ Resumed: {}".format(self.get_track_title(track)),
			fields=[{"name":"Elapsed","value":self.format_elapsed(player,track),"inline":False}],
			description=desc,
			color=ctx.author,
			url=track.uri,
			thumbnail=getattr(track,"thumb",None),
			delete_after=delay
		).send(ctx)

	@commands.command()
	async def seek(self, ctx, position = None):
		"""Seeks to the passed position in the song if possible.  Position should be in seconds or in HH:MM:SS format.  Prepend a + or - to seek relative to the current position."""

		if position is None or position.lower() in ["moon","moons","moonme","moon me"]: # Show the playing status
			return await ctx.invoke(self.playing,moons=position)
		delay = self.settings.getServerStat(ctx.guild, "MusicDeleteDelay", 20)
		player = self.get_player(ctx.guild)
		if not player or not player.is_connected:
			return await Message.Embed(title="♫ Not connected to a voice channel!",color=ctx.author,delete_after=delay).send(ctx)
		if not (player.is_playing or player.is_paused):
			return await Message.Embed(title="♫ Not playing anything!",color=ctx.author,delete_after=delay).send(ctx)
		track = player.track
		if not track:
			return await Message.Embed(title="♫ No current track!",color=ctx.author,delete_after=delay).send(ctx)
		if getattr(track,"is_stream",None):
			return await Message.Embed(title="♫ Streams cannot seek!",color=ctx.author,delete_after=delay).send(ctx)
		# Try to resolve the position - first in seconds, then with the HH:MM:SS format
		relative = False
		positive = True
		current = player.position/1000 # Seconds
		if position.startswith(("-","+")):
			relative = True
			positive = position.startswith("+")
			position = position[1:]
		vals = position.split(":")
		seconds = 0
		multiplier = [3600,60,1]
		vals = ["0"] * (len(multiplier)-len(vals)) + vals if len(vals) < len(multiplier) else vals # Ensure we have 3 values
		for index,mult in enumerate(multiplier):
			try: seconds += mult * float("".join([x for x in vals[index] if x in "0123456789."])) # Try to avoid h, m, s suffixes
			except: return await Message.Embed(title="♫ Malformed seek value!",description="Please make sure the seek time is in seconds, or using HH:MM:SS format.",color=ctx.author,delete_after=delay).send(ctx)
		if relative:
			if not positive: seconds *= -1
			seconds += current
			if seconds < 0: seconds = 0
		ms = seconds*1000
		# Ensure we seek to somewhere between 0 -> track.length
		ms = max(0,min(ms,track.length))
		await player.seek(int(ms))
		return await Message.Embed(title="♫ Seeking to {}!".format(self.format_duration(ms)),color=ctx.author,delete_after=delay).send(ctx)

	@commands.command(aliases=["movesong","mvtrack","movetrack"])
	async def mvsong(self, ctx, song_index = None, target_index = None):
		"""Moves the song at song_index in the queue to the target_index (bot-admin only)."""

		if not await Utils.is_bot_admin_reply(ctx): return
		delay = self.settings.getServerStat(ctx.guild, "MusicDeleteDelay", 20)
		player = self.get_player(ctx.guild)
		if player.queue.is_empty:
			# No songs in queue
			return await Message.Embed(title="♫ No songs in queue!",color=ctx.author,delete_after=delay).send(ctx)
		elif len(player.queue) == 1:
			# Nowehere to move things
			return await Message.Embed(title="♫ Only one song in queue - order cannot be changed!",color=ctx.author,delete_after=delay).send(ctx)
		# Let's check our variables
		try:
			song_index = int(song_index)
			target_index = int(target_index)
			assert 0 < song_index <= len(player.queue)
			assert 0 < target_index <= len(player.queue)
		except:
			return await Message.Embed(title="♫ Invalid index passed!",description="Indices must be between 1 and {:,}".format(len(player.queue)),color=ctx.author,delete_after=delay).send(ctx)
		# Make sure we're not moving the song to the same spot
		if song_index == target_index:
			return await Message.Embed(title="♫ Invalid index passed!",description="Indices cannot be the same",color=ctx.author,delete_after=delay).send(ctx)
		# Should have 2 valid indices - let's move the song at song_index to the target_index
		track = player.queue[song_index-1]
		player.queue._queue.insert(target_index-1,player.queue._queue.pop(song_index-1))
		# Report that the move was successful
		return await Message.Embed(
			title="♫ Track Moved to Position {:,} in the Queue".format(target_index),
			fields=[{
				"name":"{}".format(self.get_track_title(track)),
				"value":"{}{} - Requested by {}{} - [Link]({})".format(
					self.format_duration(track.seek,track)+" -> " if hasattr(track,"seek") else "",
					self.format_duration(track.length,track),
					track.ctx.author.mention,
					" (via radio)" if track.radio else "",
					track.uri
				),
				"inline":False}],
			color=ctx.author,
			delete_after=delay
		).send(ctx)

	@commands.command(aliases=["swapsongs","swaptracks","swtracks"])
	async def swsongs(self, ctx, song1_index = None, song2_index = None):
		"""Swaps the songs at song1_index and song2_index in the queue.  You must have requested both songs - or be a bot-admin to swap them."""

		delay = self.settings.getServerStat(ctx.guild, "MusicDeleteDelay", 20)
		player = self.get_player(ctx.guild)
		if player.queue.is_empty:
			# No songs in queue
			return await Message.Embed(title="♫ No songs in queue!",color=ctx.author,delete_after=delay).send(ctx)
		elif len(player.queue) == 1:
			# Nowehere to move things
			return await Message.Embed(title="♫ Only one song in queue - order cannot be changed!",color=ctx.author,delete_after=delay).send(ctx)
		# Let's check our variables
		try:
			song1_index = int(song1_index)
			song2_index = int(song2_index)
			assert 0 < song1_index <= len(player.queue)
			assert 0 < song2_index <= len(player.queue)
		except:
			return await Message.Embed(title="♫ Invalid index passed!",description="Indices must be between 1 and {:,}".format(len(player.queue)),color=ctx.author,delete_after=delay).send(ctx)
		# Make sure we're not moving the song to the same spot
		if song1_index == song2_index:
			return await Message.Embed(title="♫ Invalid index passed!",description="Indices cannot be the same",color=ctx.author,delete_after=delay).send(ctx)
		# Should have 2 valid indices - let's verify we're either bot admin, or requested both songs
		track1 = player.queue[song1_index-1]
		track2 = player.queue[song2_index-1]
		if not Utils.is_bot_admin(ctx) and not track1.ctx.author==track2.ctx.author==ctx.author:
			return await Message.Embed(title="♫ You cannot swap songs you did not request!",color=ctx.author,delete_after=delay).send(ctx)
		player.queue._queue[song2_index-1],player.queue._queue[song1_index-1] = player.queue._queue[song1_index-1],player.queue._queue[song2_index-1]
		# Report that the move was successful
		fields = []
		for track,index in sorted(((track1,song2_index),(track2,song1_index)),key=lambda x: x[1]):
			fields.append({
				"name":"{}. {}".format(index,self.get_track_title(track)),
				"value":"{}{} - Requested by {}{} - [Link]({})".format(
					self.format_duration(track.seek,track)+" -> " if hasattr(track,"seek") else "",
					self.format_duration(track.length,track),
					track.ctx.author.mention,
					" (via radio)" if track.radio else "",
					track.uri
				),
				"inline":False
			})
		return await Message.Embed(
			title="♫ Tracks {:,} and {:,} swapped!".format(song1_index,song2_index),
			fields=fields,
			color=ctx.author,
			delete_after=delay
		).send(ctx)

	@commands.command()
	async def lavalink(self, ctx):
		"""Lists info about the Lavalink version connected to."""
		node = self.get_node()
		if not node:
			return await Message.Embed(
				title="♫ Missing Information",
				color=ctx.author,
				description="No nodes were returned - I may not be connected to Lavalink."
			).send(ctx)
		# We have a node we can communicate with - get the versioning info
		info = await node.send(
			method="GET",
			path="info"
		)
		if not info:
			return await Message.Embed(
				title="♫ Missing Information",
				color=ctx.author,
				description="No version information was returned - I may not be connected to Lavalink."
			).send(ctx)
		# Let's build our description
		java_version = info.get("jvm","UNKNOWN")
		lavalink_version = info.get("version",{}).get("semver","UNKNOWN")
		lavaplayer_version = info.get("lavaplayer","UNKNOWN")
		plugins = []
		for plug in info.get("plugins",[]):
			plugins.append(" - {}: {}".format(
				plug.get("name","UNKNOWN PLUGIN"),
				plug.get("version","UNKNOWN VERSION")
			))
		desc = "Java Runtime: {}\nLavalink:     {}\nLavaPlayer:   {}\nPlugins:      {}".format(
			java_version,
			lavalink_version,
			lavaplayer_version,
			"None" if not plugins else "\n"+"\n".join(plugins)
		)
		# Display the results in a codeblock
		await PickList.PagePicker(
			title="♫ Current Lavalink Version Info",
			description=desc,
			color=ctx.author,
			d_header="```\n",
			d_footer="```",
			ctx=ctx,
		).pick()

	@commands.command(aliases=["nowplaying"])
	async def playing(self, ctx, *, moons = None):
		"""Lists the currently playing song if any."""

		delay = self.settings.getServerStat(ctx.guild, "MusicDeleteDelay", 20)
		player = self.get_player(ctx.guild)
		if not player or not player.is_connected or not (player.is_playing or player.is_paused) or not player.track:
			# No client - and we're not playing or paused
			return await Message.Embed(
				title="♫ Currently Playing",
				color=ctx.author,
				description="Not playing anything.",
				delete_after=delay
			).send(ctx)
		play_text = "Playing" if (player.is_playing and not player.is_paused) else "Paused"
		track = player.track
		track_ctx = getattr(player,"track_ctx",None)
		if not track_ctx:
			return await Message.Embed(
				title="Missing information!",
				description="Could not get the context for the currently playing song.",
				color=ctx.author,
				delete_after=delay
			).send(ctx)
		await Message.Embed(
			title="♫ Currently {}: {}".format(play_text,self.get_track_title(track)),
			description="Requested by {}{}\n -- Volume at {}%{}".format(
				track_ctx.author.mention,
				" (via radio)" if track.radio else "",
				player.get_vol(ctx),
				"\n-- Repeat Enabled" if getattr(player,"repeat",False) else ""
			),
			color=ctx.author,
			fields=[
				{"name":"Elapsed","value":self.format_elapsed(player,track),"inline":False},
				{"name":"Progress","value":self.progress_moon(player,track) if moons and moons.lower() in ["moon","moons","moonme","moon me"] else self.progress_bar(player,track),"inline":False}
			],
			url=track.uri,
			thumbnail=getattr(track,"thumb",None),
			delete_after=delay
		).send(ctx)

	@commands.command(aliases=["queue","q"])
	async def playlist(self, ctx):
		"""Lists the queued songs in the playlist."""

		delay = self.settings.getServerStat(ctx.guild, "MusicDeleteDelay", 20)
		player = self.get_player(ctx.guild)
		if not player or not player.is_connected or not (player.is_playing or player.is_paused):
			return await Message.Embed(
				title="♫ Current Playlist",
				color=ctx.author,
				description="Not playing anything.",
				delete_after=delay
			).send(ctx)
		play_text = "Playing" if player.is_playing else "Paused"
		track = player.track
		track_ctx = getattr(player,"track_ctx",None)
		thumb = getattr(track,"thumb",None)
		if not track_ctx:
			return await Message.Embed(
				title="Missing information!",
				description="Could not get the context for the currently playing song.",
				color=ctx.author,
				delete_after=delay
			).send(ctx)
		desc = "**{}**\nCurrently {} - at {} - Requested by {}{} - [Link]({})\n-- Volume at {}%{}".format(
			self.get_track_title(track),
			play_text,
			self.format_elapsed(player,track),
			track_ctx.author.mention,
			" (via radio)" if track.radio else "",
			track.uri,
			player.get_vol(ctx),
			"\n-- Repeat Enabled" if getattr(player,"repeat",False) else ""
		)
		fields = []
		if not player.queue.is_empty:
			total_time = 0
			total_streams = 0
			time_string = ""
			for x in player.queue:
				if x.length: total_time+=x.length-getattr(x,"seek",0)
				else: total_streams+=1
			if total_time:
				# Got time at least
				time_string += "{} total -- ".format(self.format_duration(total_time))
			if total_streams:
				# Got at least one stream
				time_string += "{:,} Stream{} -- ".format(total_streams, "" if total_streams == 1 else "s")
			q_text = "-- {:,} Song{} in Queue -- {}".format(len(player.queue), "" if len(player.queue) == 1 else "s", time_string)
			desc += "\n\n**♫ Up Next**\n{}".format(q_text)
		for x,y in enumerate(player.queue,start=1):
			t_ctx = getattr(y,"ctx",None)
			fields.append({
				"name":"{}. {}".format(x,self.get_track_title(y)),
				"value":"{}{} - Requested by {}{} - [Link]({})".format(
					self.format_duration(y.seek,y)+" -> " if hasattr(y,"seek") else "",
					self.format_duration(y.length,y),
					t_ctx.author.mention if t_ctx else "Unknown",
					" (via radio)" if y.radio else "",
					y.uri
				),
				"inline":False})
		pl_string = " - Repeat Enabled" if getattr(player,"repeat",False) else ""
		if len(fields) <= 11:
			await Message.Embed(
				title="♫ Current Playlist{}".format(pl_string),
				description=desc,
				color=ctx.author,
				fields=fields,
				delete_after=delay,
				pm_after_fields=15,
				thumbnail=thumb
			).send(ctx)
		else:
			page,message = await PickList.PagePicker(
				title="♫ Current Playlist{}".format(pl_string),
				description=desc,
				list=fields,
				max=8,
				timeout=60 if not delay else delay,
				ctx=ctx,
				thumbnail=thumb
			).pick()
			if delay:
				await message.delete()

	@commands.command()
	async def skip(self, ctx, *, remove = None):
		"""Adds your vote to skip the current song.  50% or more of the non-bot users need to vote to skip a song.  Original requesters and admins can skip without voting.
		
		Passing "remove" as an argument to this command if you're the original requester or a bot-admin will remove the song from the queue if repeat is enabled."""

		delay = self.settings.getServerStat(ctx.guild, "MusicDeleteDelay", 20)
		player = self.get_player(ctx.guild)
		to_skip = False
		if not player or not player.is_connected:
			return await Message.Embed(title="♫ Not connected to a voice channel!",color=ctx.author,delete_after=delay).send(ctx)
		if not player.is_playing:
			return await Message.Embed(title="♫ Not playing anything!",color=ctx.author,delete_after=delay).send(ctx)
		# Check for added by first, then check admin
		to_remove = remove is not None and remove.lower() in ("r","rem","remove","unplay","unp","unqueue","unq")
		if Utils.is_bot_admin(ctx):
			await Message.Embed(
				title="♫ Admin override activated - skipping{}!".format(" and removing" if to_remove else ""),
				color=ctx.author,
				delete_after=delay
			).send(ctx)
			to_skip = True
		elif hasattr(player,"track_ctx") and player.track_ctx.author == ctx.author:
			await Message.Embed(
				title="♫ Requester chose to skip - skipping{}!".format(" and removing" if to_remove else ""),
				color=ctx.author,
				delete_after=delay
			).send(ctx)
			to_skip = True
		else:
			# Override to_remove here - as we cannot remove it if we're not the original
			# requester or a bot-admin
			to_remove = False
			# Do the checking here to validate we can use this and etc.
			skips = getattr(player,"skips",[]) # Get the existing skips - or an empty list if none
			# Relsolve the skips
			new_skips = []
			if not player.channel:
				return await Message.Embed(title="♫ Something went wrong!",description="That voice channel doesn't seem to exist anymore...",color=ctx.author,delete_after=delay).send(ctx)
			for x in skips: # Walk the skips - removing bots and users no longer present
				member = ctx.guild.get_member(x)
				if not member or member.bot or not member in player.channel.members:
					continue
				# Got a valid user who's in the skip list and the voice channel
				new_skips.append(x)
			# Check if we're not already in the skip list
			if not ctx.author.id in new_skips:
				new_skips.append(ctx.author.id)
			# Let's get the number of valid skippers
			skippers = [x for x in player.channel.members if not x.bot]
			needed_skips = math.ceil(len(skippers)/2)
			if len(new_skips) >= needed_skips:
				# Got it!
				to_skip = True
				await Message.Embed(title="♫ Skip threshold met ({}/{}) - skipping!".format(len(new_skips),needed_skips),color=ctx.author,delete_after=delay).send(ctx)
			else:
				# Update the skips
				player.skips = new_skips
				await Message.Embed(title="♫ Skip threshold not met - {}/{} skip votes entered - need {} more!".format(len(new_skips),needed_skips,needed_skips-len(new_skips)),color=ctx.author,delete_after=delay).send(ctx)
		if to_skip:
			if to_remove: # Only remove if we're skipping
				player.track.to_remove = True
			player.skips = [] # Reset the skips
			await self._stop(player,clear_attrs=False,clear_queue=False,disconnect=False) # Stop the current song

	@commands.command()
	async def unskip(self, ctx):
		"""Removes your vote to skip the current song."""
		
		delay = self.settings.getServerStat(ctx.guild, "MusicDeleteDelay", 20)
		player = self.get_player(ctx.guild)
		if not player or not player.is_connected:
			return await Message.Embed(title="♫ Not connected to a voice channel!",color=ctx.author,delete_after=delay).send(ctx)
		if not player.is_playing:
			return await Message.Embed(title="♫ Not playing anything!",color=ctx.author,delete_after=delay).send(ctx)
		
		skips = getattr(player,"skips",[])
		if not ctx.author.id in skips: return await Message.Embed(title="♫ You haven't voted to skip this song!",color=ctx.author,delete_after=delay).send(ctx)
		# We did vote - remove that
		skips.remove(ctx.author.id)
		player.skips = skips
		if not player.channel:
			return await Message.Embed(title="♫ Something went wrong!",description="That voice channel doesn't seem to exist anymore...",color=ctx.author,delete_after=delay).send(ctx)
		# Let's get the number of valid skippers
		skippers = [x for x in player.channel.members if not x.bot]
		needed_skips = math.ceil(len(skippers)/2)
		await Message.Embed(title="♫ You have removed your vote to skip - {}/{} votes entered - {} more needed to skip!".format(len(skips),needed_skips,needed_skips-len(skips)),color=ctx.author,delete_after=delay).send(ctx)

	@commands.command(aliases=["skipped"])
	async def skips(self, ctx, user = None):
		"""Lists the number of skips for the currently playing song."""
		
		delay = self.settings.getServerStat(ctx.guild, "MusicDeleteDelay", 20)
		user = ctx.author if user is None else DisplayName.memberForName(user,ctx.guild)
		if user is None: return await Message.Embed(title="♫ I couldn't find that user!",color=ctx.author,delete_after=delay).send(ctx)
		player = self.get_player(ctx.guild)
		if not player or not player.is_connected:
			return await Message.Embed(title="♫ Not connected to a voice channel!",color=ctx.author,delete_after=delay).send(ctx)
		if not player.is_playing:
			return await Message.Embed(title="♫ Not playing anything!",color=ctx.author,delete_after=delay).send(ctx)
		
		if not player.channel:
			return await Message.Embed(title="♫ Something went wrong!",description="That voice channel doesn't seem to exist anymore...",color=ctx.author,delete_after=delay).send(ctx)
		# Let's get the number of valid skippers
		skips = getattr(player,"skips",[])
		skippers = [x for x in player.channel.members if not x.bot]
		needed_skips = math.ceil(len(skippers)/2)
		# Now we build our embed
		await Message.Embed(
			title="♫ {}/{} votes - {} more needed to skip!".format(len(skips),needed_skips,needed_skips-len(skips)),
			description="{} **has{}** voted to skip this song.".format(user.mention,"" if user.id in skips else " not"),
			color=ctx.author,
			delete_after=delay
		).send(ctx)

	@commands.command()
	async def stop(self, ctx):
		"""Stops and empties the current playlist."""
		
		delay = self.settings.getServerStat(ctx.guild, "MusicDeleteDelay", 20)
		player = self.get_player(ctx.guild)
		if player:
			if player.is_playing or player.is_paused:
				# Clear context to prevent end of playlist spam
				self._clear_player(player,[x for x in self.player_clear+["ctx"]])
				await self._stop(player,clear_attrs=False,clear_queue=True,disconnect=False)
				return await Message.Embed(title="♫ Music stopped and playlist cleared!",color=ctx.author,delete_after=delay).send(ctx)
			else:
				return await Message.Embed(title="♫ Not playing anything!",color=ctx.author,delete_after=delay).send(ctx)
		await Message.Embed(title="♫ Not connected to a voice channel!",color=ctx.author,delete_after=delay).send(ctx)

	@commands.command(aliases=["v","vol"])
	async def volume(self, ctx, volume = None):
		"""Changes the player's volume (0-150%)."""

		delay = self.settings.getServerStat(ctx.guild, "MusicDeleteDelay", 20)
		player = self.get_player(ctx.guild)
		if player is None or not player.is_connected:
			return await Message.Embed(title="♫ Not connected to a voice channel!",color=ctx.author,delete_after=delay).send(ctx)
		cv = player.get_vol(ctx)
		if volume is None:
			# We're just listing the current volume
			return await Message.Embed(title="♫ Current volume at {}%.".format(cv),color=ctx.author,delete_after=delay).send(ctx)
		try: # Round volume up or down as needed
			volume = float(volume)
			volume = int(volume) if volume - int(volume) < 0.5 else int(volume)+1
		except:
			return await Message.Embed(title="♫ Volume must be an integer between 0-150.",color=ctx.author,delete_after=delay).send(ctx)
		# Ensure our volume is between 0 and 150
		volume = max(min(150,volume),0)
		await player.set_vol(volume)
		# Save it to the server stats with range 10-100
		self.settings.setServerStat(ctx.guild, "MusicVolume", max(min(100,volume),10))
		title="♫ Changed volume from {}% to {}%.".format(cv,volume) if cv!=volume else "♫ Volume remains {}%.".format(volume)
		await Message.Embed(title=title,color=ctx.author,delete_after=delay).send(ctx)

	async def _adjust_volume(self, ctx, amount, increment=True):
		if amount is None:
			amount = 10
		else:
			try:
				amount = int(amount)
			except:
				return await Message.Embed(
					title="♫ Amount must be an integer between 1-150.",
					color=ctx.author,
					delete_after=delay
				).send(ctx)
		player = self.get_player(ctx.guild)
		cv = None
		if player:
			cv = player.get_vol(ctx)
			if increment:
				cv += amount
			else:
				cv -= amount
			cv = max(min(150,cv),1)
		await ctx.invoke(self.volume,volume=cv)

	@commands.command(aliases=["loud"])
	async def louder(self, ctx, amount = None):
		"""Increases the volume by the passed amount, or by 10%."""
		await self._adjust_volume(ctx,amount)

	@commands.command(aliases=["quiet"])
	async def quieter(self, ctx, amount = None):
		"""Decreases the volume by the passed amount, or by 10%."""
		await self._adjust_volume(ctx,amount,increment=False)

	@commands.command()
	async def repeat(self, ctx, *, yes_no = None):
		"""Checks or sets whether to repeat the current playlist."""

		delay = self.settings.getServerStat(ctx.guild, "MusicDeleteDelay", 20)
		player = self.get_player(ctx.guild)
		if not player or not player.is_connected:
			return await Message.Embed(title="♫ Not connected to a voice channel!",color=ctx.author,delete_after=delay).send(ctx)
		current = getattr(player,"repeat",False)
		setting_name = "Repeat"
		if yes_no is None:
			msg = "{} currently {}!".format(setting_name,"enabled" if current else "disabled")
		elif yes_no.lower() in [ "yes", "on", "true", "enabled", "enable" ]:
			yes_no = True
			msg = '{} {} enabled!'.format(setting_name,"remains" if current else "is now")
		elif yes_no.lower() in [ "no", "off", "false", "disabled", "disable" ]:
			yes_no = False
			msg = '{} {} disabled!'.format(setting_name,"is now" if current else "remains")
		else:
			msg = "That's not a valid setting!"
			yes_no = current
		if yes_no is not None and yes_no != current:
			player.repeat = yes_no
		await Message.Embed(title="♫ "+msg,color=ctx.author,delete_after=delay).send(ctx)

	@commands.command()
	async def playingin(self, ctx):
		"""Shows the number of servers the bot is currently playing music in."""

		delay = self.settings.getServerStat(ctx.guild, "MusicDeleteDelay", 20)
		server_list = []
		nodes = list(self.NodePool.nodes.values())
		for node in nodes:
			for p in node.players.values():
				if p.is_playing and not p.is_paused:
					server_list.append({
						"name":"{} ({}){}".format(
							p.guild.name,
							p.guild.id,
							" ({:,} more in queue)".format(len(p.queue)
							) if len(p.queue) else ""
						),
						"value":"{} - at {} - Requested by {}{} - [Link]({})".format(
							self.get_track_title(p.track),
							self.format_elapsed(p,p.track),
							p.track.ctx.author.mention,
							" (via radio)" if p.track.radio else "",
							p.track.uri),
						"inline":False
					})
		msg = "♫ Playing music in {:,} of {:,} server{}.".format(len(server_list), len(self.bot.guilds), "" if len(self.bot.guilds) == 1 else "s")
		if server_list: await PickList.PagePicker(title=msg,list=server_list,ctx=ctx).pick()
		else: await Message.Embed(title=msg,color=ctx.author,delete_after=delay).send(ctx)

	@commands.command()
	async def stopall(self, ctx):
		"""Stops and disconnects the bot from all voice channels in all servers (owner-only)."""

		if not await Utils.is_owner_reply(ctx): return
		delay = self.settings.getServerStat(ctx.guild, "MusicDeleteDelay", 20)
		players = 0
		for guild in self.bot.guilds:
			# Remove the per-server temp settings
			player = self.get_player(guild)
			if player:
				players += 1
				await self._stop(player,clear_attrs=True,clear_queue=True,disconnect=True)
		await Message.Embed(title="♫ I've left all voice channels ({:,}/{:,})!".format(players,len(self.bot.guilds)),color=ctx.author,delete_after=delay).send(ctx)

	@commands.command()
	async def autodeleteafter(self, ctx, seconds = None):
		"""Lists or sets the current delay before auto-deleting music related messages (max of 300 seconds).  Set to an integer less than 10 to disable auto-deletion.  Requires bot-admin or admin to set."""
		
		if not Utils.is_bot_admin(ctx): seconds = None
		delay = self.settings.getServerStat(ctx.guild, "MusicDeleteDelay", 20)
		if seconds is None:
			# List the delay
			if delay is None:
				return await Message.Embed(title="♫ Music related messages are not auto-deleted!",color=ctx.author).send(ctx)
			else:
				return await Message.Embed(title="♫ Music related messages are auto-deleted after {} second{}!".format(delay, "" if delay == 1 else "s"),color=ctx.author,delete_after=delay).send(ctx)
		# Attempting to set it
		try:
			real = int(seconds)
		except:
			return await Message.Embed(title="♫ Seconds must be an integer!",color=ctx.author,delete_after=delay).send(ctx)
		if real < 10:
			self.settings.setServerStat(ctx.guild, "MusicDeleteDelay", None)
			return await Message.Embed(title="♫ Music related messages will not be auto-deleted!",color=ctx.author).send(ctx)
		real = 300 if real > 300 else real
		self.settings.setServerStat(ctx.guild, "MusicDeleteDelay", real)
		return await Message.Embed(title="♫ Music related messages will be auto-deleted after {} second{}!".format(real, "" if real == 1 else "s"),color=ctx.author,delete_after=real).send(ctx)

	@commands.command()
	async def leavewhenalone(self, ctx, yes_no = None):
		"""Lists or sets whether the bot leaves the voice channel when the last non-bot disconnects.  Requires bot-admin or admin to set."""
		
		if not Utils.is_bot_admin(ctx): yes_no = None
		await ctx.send(Utils.yes_no_setting(ctx,"Leave VC when alone","LeaveVCWhenAlone",yes_no,default=True))
		
	@commands.command()
	async def searchlist(self, ctx, yes_no = None):
		"""Gets or sets whether or not the server will show a list of options when searching with the play command - or if it'll just pick the first (admin only)."""
		
		if not await Utils.is_admin_reply(ctx): return
		await ctx.send(Utils.yes_no_setting(ctx,"Music player search list","YTMultiple",yes_no))

	@commands.command()
	async def searchtype(self, ctx, search_type = None):
		"""Gets or sets the default search type used.  Can be ytsearch, ytmsearch, or scsearch (default is ytsearch).  Requires bot-admin or admin to set."""

		if not Utils.is_bot_admin(ctx): search_type = None
		st_provider = {"ytsearch":"YouTube","ytmsearch":"YouTube Music","scsearch":"Sound Cloud"}
		if search_type is None: # Just getting the default search type
			st = self.settings.getServerStat(ctx.guild, "MusicSearchType", "ytsearch")
			return await ctx.send("Current search type is `{}` ({}).".format(st,st_provider.get(st)))
		# Setting it - make sure the value is in our list
		search_type = search_type.lower()
		if not search_type in ("ytsearch","ytmsearch","scsearch","yt","ytm","sc"):
			return await ctx.send("Invalid search type.  Can only be `ytsearch`, `ytmsearch`, or `scsearch`.")
		# Ensure it ends with "searcH"
		if not search_type.endswith("search"):
			search_type += "search"
		# Set it
		self.settings.setServerStat(ctx.guild, "MusicSearchType", search_type)
		return await ctx.send("Search type set to `{}` ({}).".format(search_type,st_provider.get(search_type)))

	@commands.command()
	async def lasteq(self, ctx, yes_no = None):
		"""Gets or sets whether the current EQ settings are preserved between music sessions (bot-admin only)."""
		
		if not await Utils.is_bot_admin_reply(ctx): return
		await ctx.send(Utils.yes_no_setting(ctx,"Preserving EQ settings between sessions","PreserveLastEQ",yes_no))

	@commands.command()
	async def allowplaynext(self, ctx, yes_no = None):
		"""Gets or sets whether playnext, shufflenext, radionext, loadplnext, and shuffleplnext can queue songs at the beginning of the current playlist."""

		if not Utils.is_bot_admin(ctx):
			yes_no = None
		comm_format = ", ".join(["`{}{}`".format(ctx.prefix,x) for x in self.next_commands])
		await ctx.send(Utils.yes_no_setting(ctx,"Queuing songs at the beginning of the playlist with {} commands".format(comm_format),"AllowPlayNext",yes_no))

	@commands.command()
	async def disableplay(self, ctx, *, yes_no = None):
		"""Enables/Disables the music commands.  Helpful in case Youtube is rate limiting to avoid extra api calls and allow things to calm down.  Owners can still access music commands (owner only)."""
		
		if not await Utils.is_owner_reply(ctx): return
		await ctx.send(Utils.yes_no_setting(ctx,"Music player lock out","DisableMusic",yes_no,is_global=True))

	async def cog_before_invoke(self, ctx):
		# We don't need to ensure extra for the following commands:
		exempt_commands = (
			"playingin",
			"autodeleteafter",
			"leavewhenalone",
			"disableplay",
			"stopall",
			"searchlist",
			"lasteq",
			"playing",
			"playlist",
			"radiocount",
			"searchtype",
			"allowplaynext",
			"lavalink"
		)
		if ctx.command.name in exempt_commands: return
		# General checks for all music player commands - with specifics filtered per command
		# If Youtube ratelimits - you can disable music globally so only owners can use it
		player = self.get_player(ctx.guild)
		delay = self.settings.getServerStat(ctx.guild,"MusicDeleteDelay",20)
		if self.settings.getGlobalStat("DisableMusic",False) and not Utils.is_owner(ctx):
			# Music is off - and we're not an owner - disconnect if connected, then send the bad news :(
			if player: await player.disconnect()
			await Message.Embed(title="♫ Music player is currently disabled!",color=ctx.author,delete_after=delay).send(ctx)
			raise commands.CommandError("Music Cog: Music disabled.")
		# Music is enabled - let's make sure we have the right role
		if not await self._check_role(ctx):
			raise commands.CommandError("Music Cog: Missing DJ roles.")
		# If we're just using the join command - we don't need extra checks - they're done in the command itself
		if ctx.command.name in ("join",): return
		# Let's make sure we're running an allowed command
		if ctx.command.name in self.next_commands and not Utils.is_bot_admin(ctx) and not self.settings.getServerStat(ctx.guild,"AllowPlayNext"):
			await ctx.send("`{0}{1}` is not currently enabled.  An admin or bot-admin can enable it with `{0}allowplaynext True`".format(ctx.prefix,ctx.command.name))
			raise commands.CommandError("Music Cog: AllowPlayNext not enabled.")
		# We've got the role - let's join the author's channel if we're playing/shuffling and not connected
		if ctx.command.name in ["play","radio","shuffle","loadpl","shufflepl"]+self.next_commands and ctx.author.voice:
			if not player or not player.is_connected:
				return await ctx.author.voice.channel.connect(cls=CorpPlayer)
		# Let's ensure the bot is connected to voice
		if not player or not player.is_connected:
			await Message.Embed(title="♫ Not connected to a voice channel!",color=ctx.author,delete_after=delay).send(ctx)
			raise commands.CommandError("Music Cog: Not connected to a voice channel.")
		# Let's make sure the caller is connected to voice and the same channel as the bot - or a bot-admin
		if Utils.is_bot_admin(ctx) or self._check_mc(ctx): return # We good - have enough perms to override whatever
		if not ctx.author.voice or not player or not ctx.author.voice.channel == player.channel:
			await Message.Embed(title="♫ You have to be in the same voice channel as me to use that!",color=ctx.author,delete_after=delay).send(ctx)
			raise commands.CommandError("Music Cog: Author not connected to the bot's voice channel.")


	###
	### HORRIBLY cursed filter functions hacked together for reasons.
	### Hidden below everything else because cursed, ofc.
	###

	async def apply_filters(self,player,filter_data,name=None,fast_apply=False,setting_name=None):
		# Helper to apply filters to the passed player
		# Here, we basically just rip the functionality directly from pomice's
		# player class - whenever it sends info to the websocked.  We just imitate
		# that, but using our own filter data.
		if not player._node._session_id: # The node was not properly initialized?
			return
		if setting_name and player.guild: # We're saving it as a server stat
			self.settings.setServerStat(player.guild,setting_name,filter_data)
		if not filter_data: # Got... nothing
			return
		if name: # Wrap it in a dict
			filter_data = {name:filter_data}

		# Send the payload to the websocket and pray
		await player._node.send(
			method="PATCH",
			path=player._player_endpoint_uri,
			guild_id=player._guild.id,
			data={"filters":filter_data},
		)
		# Apply the filter instantly by seeking to the same location - only if player is playing
		if fast_apply and player.is_playing: await player.seek(int(player.position))

	def _draw_band(self, band, max_len=5):
		v = max(min(float(band),1.),-1.) # Get the value as a float and force -1 to 1 range
		ep = self.gc.get("ep"," ")
		se = self.gc.get("se","─")
		ab = math.ceil(abs(v)*max_len)
		l = self.gc.get("tl","┌") if v>0 else self.gc.get("bl","└")
		r = self.gc.get("tr","┐") if v>0 else self.gc.get("bl","┘")
		s = self.gc.get("su","┴") if v>0 else self.gc.get("sd","┬")
		c = self.gc.get("cp","─")
		i = self.gc.get("in"," ")
		b = self.gc.get("b","│")
		# Iterate and draw
		return [
			# Draws top->down; Empty, Cap, Fill, Sep, Fill, Cap, Empty
			"{}{}{}{}{}{}{}".format(
				ep*(max_len-(ab if v>0 else 0)),
				t[0]*(1 if v>0 else 0),
				t[1]*(ab-1 if v>0 else 0),
				t[2] if v!=0 else se,
				t[1]*(ab-1 if v<0 else 0),
				t[0]*(1 if v<0 else 0),
				ep*(max_len-(ab if v<0 else 0))
			)
			for t in ((l,b,s),(c,i,se),(r,b,s))
		]

	def print_eq(self, eq, max_len=5):
		# EQ values are from -0.25 (muted) to 0.25 (doubled)
		eq_list  = []
		vals = ""
		se = self.gc.get("se","─")
		lp = self.gc.get("lp","")
		for entry in eq:
			value = entry.get("gain",.0)*4. # Quadrupled for -1 to 1 range
			eq_list.extend(self._draw_band(value,max_len=max_len))
			vals += str(math.ceil(abs(value)*max_len)*(1 if value>0 else -1)).rjust(2)+" "
		# Rotate the eq 90 degrees
		graph = "```\n{}\n{}\n{}\n{}\n{}\n{}\n{}\n```".format(
			"Bands".center(len(vals),se),
			" ".join([str(x+1).rjust(2) for x in range(len(eq))]),
			se*(len(vals)),
			"\n".join([lp+x+lp for x in map("".join, zip(*eq_list))]),
			"Values".center(len(vals),se),
			vals,
			se*(len(vals))
		)
		return graph

	##
	## Presets taken from the older pomice repo:
	## https://github.com/PythonistaGuild/pomice/blob/3e11c16516dd89791c1247032045385979736554/pomice/eqs.py#L82-L128
	##

	def flat_eq(self):
		# Function to return an initialized eq; 15 numbered bands of 0 gain
		return [{"band":x,"gain":0.0} for x in range(15)]

	def boost_eq(self):
		return [
			{"band": 0, "gain": -0.075},
			{"band": 1, "gain": 0.125},
			{"band": 2, "gain": 0.125},
			{"band": 3, "gain": 0.1},
			{"band": 4, "gain": 0.1},
			{"band": 5, "gain": 0.05},
			{"band": 6, "gain": 0.075},
			{"band": 7, "gain": 0.0},
			{"band": 8, "gain": 0.0},
			{"band": 9, "gain": 0.0},
			{"band": 10, "gain": 0.0},
			{"band": 11, "gain": 0.0},
			{"band": 12, "gain": 0.125},
			{"band": 13, "gain": 0.15},
			{"band": 14, "gain": 0.05}
		]

	def metal_eq(self):
		return [
			{"band": 0, "gain": 0.0},
			{"band": 1, "gain": 0.1},
			{"band": 2, "gain": 0.1},
			{"band": 3, "gain": 0.15},
			{"band": 4, "gain": 0.13},
			{"band": 5, "gain": 0.1},
			{"band": 6, "gain": 0.0},
			{"band": 7, "gain": 0.125},
			{"band": 8, "gain": 0.175},
			{"band": 9, "gain": 0.175},
			{"band": 10, "gain": 0.125},
			{"band": 11, "gain": 0.125},
			{"band": 12, "gain": 0.1},
			{"band": 13, "gain": 0.075},
			{"band": 14, "gain": 0.0}
		]

	def piano_eq(self):
		return [
			{"band": 0, "gain": -0.25},
			{"band": 1, "gain": -0.25},
			{"band": 2, "gain": -0.125},
			{"band": 3, "gain": 0.0},
			{"band": 4, "gain": 0.25},
			{"band": 5, "gain": 0.25},
			{"band": 6, "gain": 0.0},
			{"band": 7, "gain": -0.25},
			{"band": 8, "gain": -0.25},
			{"band": 9, "gain": 0.0},
			{"band": 10, "gain": 0.0},
			{"band": 11, "gain": 0.25},
			{"band": 12, "gain": 0.25},
			{"band": 13, "gain": -0.025}
		]

	def default_timescale(self):
		return {
			"speed":1.0,
			"pitch":1.0,
			"rate":1.0
		}

	def print_timescale(self,timescale):
		return "```\nSpeed: {}\nPitch: {}\nRate:  {}\n```".format(
			timescale.get("speed","Unknown"),
			timescale.get("pitch","Unknown"),
			timescale.get("rate","Unknown")
		)

	'''@commands.command(aliases=["ts","tscale"])
	async def timescale(self, ctx, *, speed = None, pitch = None, rate = None):
		"""Gets or sets the current player's time scale values.  Speed, pitch, and rate can be any number between 0 and 10 with 1 being default."""
		# All values just get dumped into speed
		player = self.get_player(ctx.guild)
		delay = self.settings.getServerStat(ctx.guild, "MusicDeleteDelay", 20)
		if not player or not player.is_connected:
			return await Message.Embed(title="♫ Not connected to a voice channel!",color=ctx.author,delete_after=delay).send(ctx)
		ts = getattr(player,"timescale",self.default_timescale())
		if speed is None: # Print the current settings
			return await Message.Embed(title="♫ Current Timescale Settings",description=self.print_timescale(ts),color=ctx.author,delete_after=delay).send(ctx)
		# We got... something.  Let's try to parse it
		try:
			for i,x in enumerate(speed.replace(",","").lower().split()):
				if "=" in x: # Let's see if we are setting a specific value
					y,x = x.split("=")
					i = ["s","p","r"].index(y[0].lower())
				x = float(x)
				ts[list(ts)[i]]=x
		except:
			return await Message.Embed(title="♫ Invalid Timescale Value",description="Valid speed, pitch, and rate values are numbers from 0 to 10 with 1 being default.",color=ctx.author,delete_after=delay).send(ctx)
		await self.apply_filters(player,ts,name="timescale")
		player.timescale = ts # Set the player's timescale value
		return await Message.Embed(
			title="♫ Timescale Settings Updated!",
			description=self.print_timescale(ts),
			color=ctx.author,
			delete_after=delay,
			footer="Filter changes may take a bit to apply"
		).send(ctx)

	@commands.command(aliases=["rts","resetts"])
	async def resettimescale(self, ctx):
		"""Resets the current player's time scale values."""

		player = self.get_player(ctx.guild)
		delay = self.settings.getServerStat(ctx.guild, "MusicDeleteDelay", 20)
		if not player or not player.is_connected:
			return await Message.Embed(title="♫ Not connected to a voice channel!",color=ctx.author,delete_after=delay).send(ctx)
		ts = self.default_timescale()
		await self.apply_filters(player,ts,name="timescale")
		player.timescale = ts # Set the player's timescale value
		return await Message.Embed(
			title="♫ Timescale Settings Updated!",
			description=self.print_timescale(ts),
			color=ctx.author,
			delete_after=delay,
			footer="Filter changes may take a bit to apply"
		).send(ctx)'''

	@commands.command(aliases=["eq"])
	async def geteq(self, ctx):
		"""Prints the current equalizer settings."""

		player = self.get_player(ctx.guild)
		delay = self.settings.getServerStat(ctx.guild, "MusicDeleteDelay", 20)
		if not player or not player.is_connected:
			return await Message.Embed(title="♫ Not connected to a voice channel!",color=ctx.author,delete_after=delay).send(ctx)
		# Get the current eq
		eq = getattr(player,"eq",self.flat_eq())
		return await Message.Embed(title="♫ Current Equalizer Settings",description=self.print_eq(eq),color=ctx.author,delete_after=delay).send(ctx)
	
	@commands.command(aliases=["seq"])
	async def seteq(self, ctx, *, bands = None):
		"""Sets the equalizer to the passed 15 space-delimited values from -5 (silent) to 5 (double volume)."""
		
		player = self.get_player(ctx.guild)
		delay = self.settings.getServerStat(ctx.guild, "MusicDeleteDelay", 20)
		if not player or not player.is_connected:
			return await Message.Embed(title="♫ Not connected to a voice channel!",color=ctx.author,delete_after=delay).send(ctx)
		if bands is None: 
			return await Message.Embed(title="♫ Please specify the eq values!",description="15 numbers separated by a space from -5 (silent) to 5 (double volume)",color=ctx.author,delete_after=delay).send(ctx)
		try:
			band_ints = [int(x) for x in bands.split()]
		except:
			return await Message.Embed(title="♫ Invalid eq values passed!",description="15 numbers separated by a space from -5 (silent) to 5 (double volume)",color=ctx.author,delete_after=delay).send(ctx)
		if not len(band_ints) == 15: return await Message.Embed(title="♫ Incorrect number of eq values! ({:,} - need 15)".format(len(band_ints)),description="15 numbers separated by a space from -5 (silent) to 5 (double volume)",color=ctx.author,delete_after=delay).send(ctx)
		eq = [{"band":x,"gain":float(0.25 if y/20 > 0.25 else -0.25 if y/20 < -0.25 else y/20)} for x,y in enumerate(band_ints)]
		await self.apply_filters(player,eq,name="equalizer",setting_name="LastEQ")
		player.eq = eq # Set the player's eq value to the list
		return await Message.Embed(
			title="♫ Set equalizer to Custom preset!",
			description=self.print_eq(eq),
			color=ctx.author,
			delete_after=delay,
			footer="Filter changes may take a bit to apply"
		).send(ctx)

	@commands.command(aliases=["sb"])
	async def setband(self, ctx, band_number = None, value = None):
		"""Sets the value of the passed eq band (1-15) to the passed value from -5 (silent) to 5 (double volume)."""

		player = self.get_player(ctx.guild)
		delay = self.settings.getServerStat(ctx.guild, "MusicDeleteDelay", 20)
		if not player or not player.is_connected:
			return await Message.Embed(title="♫ Not connected to a voice channel!",color=ctx.author,delete_after=delay).send(ctx)
		if band_number is None or value is None:
			return await Message.Embed(title="♫ Please specify a band and value!",description="Bands can be between 1 and 15, and eq values from -5 (silent) to 5 (double volume)",color=ctx.author,delete_after=delay).send(ctx)
		try:
			band_number = int(band_number)
			assert 0 < band_number < 16
		except:
			return await Message.Embed(title="♫ Invalid band passed!",description="Bands can be between 1 and 15, and eq values from -5 (silent) to 5 (double volume)",color=ctx.author,delete_after=delay).send(ctx)
		try:
			value = int(value)
			value = -5 if value < -5 else 5 if value > 5 else value
		except:
			return await Message.Embed(title="♫ Invalid eq value passed!",description="Bands can be between 1 and 15, and eq values from -5 (silent) to 5 (double volume)",color=ctx.author,delete_after=delay).send(ctx)
		eq = getattr(player,"eq",self.flat_eq())
		eq[band_number-1]["gain"] = float(value/20)
		await self.apply_filters(player,eq,name="equalizer",setting_name="LastEQ")
		player.eq = eq
		return await Message.Embed(
			title="♫ Set band {} to {}!".format(band_number,value),
			description=self.print_eq(eq),
			color=ctx.author,
			delete_after=delay,
			footer="Filter changes may take a bit to apply"
		).send(ctx)

	@commands.command(aliases=["req"])
	async def reseteq(self, ctx):
		"""Resets the current eq to the flat preset."""

		player = self.get_player(ctx.guild)
		delay = self.settings.getServerStat(ctx.guild, "MusicDeleteDelay", 20)
		if not player or not player.is_connected:
			return await Message.Embed(title="♫ Not connected to a voice channel!",color=ctx.author,delete_after=delay).send(ctx)
		
		eq = self.flat_eq()
		await self.apply_filters(player,eq,name="equalizer",setting_name="LastEQ")
		player.eq = eq
		return await Message.Embed(
			title="♫ Reset equalizer!",
			description=self.print_eq(eq),
			color=ctx.author,
			delete_after=delay,
			footer="Filter changes may take a bit to apply"
		).send(ctx)

	@commands.command(aliases=["eqp"])
	async def eqpreset(self, ctx, preset = None):
		"""Sets the current eq to one of the following presets:  Boost, Flat, Metal"""

		player = self.get_player(ctx.guild)
		delay = self.settings.getServerStat(ctx.guild, "MusicDeleteDelay", 20)
		if not player or not player.is_connected:
			return await Message.Embed(title="♫ Not connected to a voice channel!",color=ctx.author,delete_after=delay).send(ctx)
		if preset is None or not preset.lower() in ("boost","flat","metal","piano"):
			return await Message.Embed(title="♫ Please specify a valid eq preset!",description="Options are:  Boost, Flat, Metal, Piano",color=ctx.author,delete_after=delay).send(ctx)
		preset = preset.lower()
		eq = self.flat_eq() if preset=="flat" else self.boost_eq() if preset=="boost" else self.metal_eq() if preset=="metal" else self.piano_eq()
		await self.apply_filters(player,eq,name="equalizer",setting_name="LastEQ")
		player.eq = eq
		return await Message.Embed(
			title="♫ Set equalizer to {} preset!".format(preset.capitalize()),
			description=self.print_eq(eq),
			color=ctx.author,
			delete_after=delay,
			footer="Filter changes may take a bit to apply"
		).send(ctx)

	@commands.command(aliases=["freq"])
	async def setfreq(self, ctx, freq_family=None, value=None):
		"""Sets the frequency family to the passed value.  Valid families are bass, mid, treble."""

		player = self.get_player(ctx.guild)
		delay = self.settings.getServerStat(ctx.guild, "MusicDeleteDelay", 20)
		if not player or not player.is_connected:
			return await Message.Embed(title="♫ Not connected to a voice channel!",color=ctx.author,delete_after=delay).send(ctx)
		if not freq_family or not freq_family[0].lower() in ("b","l","m","t","h"): # Bass/Low, Middle, High/Treble
			return await Message.Embed(title="♫ Please specify a valid frequency family!",description="Options are:  Bass, Mid, Treble",color=ctx.author,delete_after=delay).send(ctx)
		# Normalize to the first letter - and change h->t and l->b
		freq_family = freq_family[0].lower()
		if freq_family in ("h","l"): freq_family = "t" if freq_family=="h" else "b"
		try:
			value = int(value)
			value = -5 if value < -5 else 5 if value > 5 else value
		except:
			return await Message.Embed(title="♫ Invalid value passed!",description="Frequency family eq values can be between -5 (silent) to 5 (double volume)",color=ctx.author,delete_after=delay).send(ctx)
		# Get the current eq
		eq = getattr(player,"eq",self.flat_eq())
		# [0  1  2  3  4]  5  6  7  8  9  [10 11 12 13 14]
		merge_values = (0,4) if freq_family=="b" else (5,9) if freq_family=="m" else (10,14)
		for entry in eq:
			if merge_values[0]<=entry["band"]<=merge_values[1]:
				# Adjust
				entry["gain"] = float(value/20)
			elif merge_values[0]-entry["band"]==1 or entry["band"]-merge_values[1]==1:
				# Next nearest - go half
				entry["gain"] = (entry["gain"]+float(value/20))/2
		await self.apply_filters(player,eq,name="equalizer",setting_name="LastEQ")
		player.eq = eq
		f_name = {"b":"Bass","m":"Mid Range","t":"Treble"}
		return await Message.Embed(
			title="♫ Set {} to {}!".format(f_name.get(freq_family,"Unknown Family"),value),
			description=self.print_eq(eq),
			color=ctx.author,
			delete_after=delay,
			footer="Filter changes may take a bit to apply"
		).send(ctx)
		
