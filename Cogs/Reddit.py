import asyncio, discord, random, time, string, re, mimetypes, math
from   datetime import datetime
from   urllib.parse import quote
from   html.parser import HTMLParser
from   discord.ext import commands
from   Cogs import Utils, Message, DL, PickList
try:
	from html import unescape
except ImportError:
	pass

def setup(bot):
	# Add the bot and deps
	settings = bot.get_cog("Settings")
	bot.add_cog(Reddit(bot, settings))

# This module grabs Reddit posts and selects one at random

class Reddit(commands.Cog):

	# Init with the bot reference, and a reference to the settings var
	def __init__(self, bot, settings):
		self.bot = bot
		self.settings = settings
		# Add our bot's id to the User-Agent to ensure it's unique
		self.ua = 'CorpNewt DeepThoughtBot ({})'.format(self.bot.user.id)
		self.re_youtube_url = re.compile(r"(?i)^(https?:\/\/)?((www\.)?youtube\.com\/((watch\?|shorts\/|playlist\?))|youtu\.be\/)[\w\-?=&]+")
		self.is_current = False # Used for stopping loops
		self.subreddit_cache  = {} # Rudimentary cache in memory
		self.sub_about_cache  = {} # Subreddit about.json cache
		self.user_about_cache = {} # User about.json cache
		# Grab info from our settings_dict.json - and fall back on defaults as needed.
		self.loop_mins     = bot.settings_dict.get("reddit_loop_update_minutes", 60)     # Check once per hour
		self.initial_start = bot.settings_dict.get("reddit_loop_initial_start", None)    # HH:MM 24-hour time string to denote the initial loop start
		self.settle_time   = bot.settings_dict.get("reddit_server_settle_time", 10)       # Additional seconds to wait for Reddit servers to settle before querying
		self.minimum_wait  = bot.settings_dict.get("reddit_minimum_wait_minutes",60)     # 1 hour minimum wait for non-owners
		self.maximum_subs  = bot.settings_dict.get("reddit_maximum_watched_subs",10)     # 10 sub max for non-owners
		self.post_limit    = bot.settings_dict.get("reddit_default_query_limit", 25)     # Default limit for query URLs (1-100)
		self.cache_expires = bot.settings_dict.get("reddit_about_cache_expires",86400*7) # Default to a week for user/sub about cache
		self.title_flair   = bot.settings_dict.get("reddit_flair_in_title",False)        # Append flair to the post title
		self.author_flair  = bot.settings_dict.get("reddit_flair_in_author",False)       # Append flair to the post author
		self.user_icons    = bot.settings_dict.get("reddit_get_user_icons",True)         # Allows getting custom icons for users, but > requests
		# ############################################################################################# #
		# TODO: Remove this when done - just a convenience for spamming while testing in production :)  #
		# ############################################################################################# #
		self.spam = bot.settings_dict.get("reddit_logging_spam",False)
		# ############################################################################################# #
		# ############################################################################################# #
		self.next_loop     = 0 # Populated with a timestamp for the next loop
		self.first_loop    = 0 # Populated with a teimstamp for the last loop
		self.ratelimit_end = 0 # Timestamp for the expected end of an existing rate limit
		self.re_whitespace_line = re.compile(r"^\s+$")
		self.re_whitespace_start = re.compile(r"^\s{4,}")
		self.re_whitespace_sub = re.compile(r"\s+")
		self.re_whitespace_indent = re.compile(r"^(\s*)")
		self.re_single_newline = re.compile(r"(?<!\n)\n(?!\n)")
		self.re_multi_newline = re.compile(r"\n{2,}")
		self.re_table_separator = re.compile(r":*\-+:*")
		self.re_quote_sub = re.compile(r"^\s{,3}(>+!?)")
		self.re_spoiler_search = re.compile(r"((?:^|[^\\])(?:\\{2})*)(>!|!<)")
		self.re_vanity_escape_sub = re.compile(r"(?P<prefix>(?:^|[^\\])(?:\\{2})*)\\(?P<escaped>\(|\)|\[|\])")
		self.re_hyperlink_md = re.compile(r"(?i)\[\s*(?P<vanity>([^\]]|(?<!\\)\\(?:\\{2})*\](?!\\))+)\s*\]\(\s*<?(?P<url>https?:\/\/(www\.)?[^\s\[\]\(\)]+\.[^\s\[\]\(\)]+)>?\s*\)")
		self.re_redditlink_md = re.compile(r"(?i)\[\s*(?P<vanity>([^\]]|(?<!\\)\\(?:\\{2})*\](?!\\))+)\s*\]\(\s*<?(?P<url>(r|u(ser)?)?\/[^\s]+)>?\s*\)")
		self.re_escaped_url = re.compile(r"(http|ftp|https)://([\\\w_-]+(?:(?:\.[\\\w_-]+)+))([\\\w.,@?^=%&:/~+#-]*[\\\w@?^=%&/~+#-])?")
		self.re_number_list = re.compile(r"^\d+\. ")
		self.re_line = re.compile(r"^\s{0,3}(\*{3,}|\-{3,}|_{3,})\s*$")
		self.re_hashes = re.compile(r"^\s{0,3}(?P<hashes>#{1,})\s*(?P<content>[^\s]+.*)$")
		self.re_comment_url = re.compile(r"(?i)^(?P<url>(https?:\/\/)?(www\.)?reddit\.com\/r\/[a-z0-9][\w]{1,20}\/comments\/[\w]+).*$")
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
		self.is_current = True
		# Start our sub watcher loop
		self.bot.loop.create_task(self.sub_watcher())

	def _check_time_string(self,time_string=None):
		if time_string is None:
			time_string = self.initial_start
		try:
			hour,minute = map(int,time_string.split(":"))
			# Ensure they're within a valid range
			assert -1 < hour < 24
			assert -1 < minute < 60 
		except:
			return None
		return (hour,minute)

	def _get_last_next_loop_time(self,time_string=None,start_time=None,loop_mins=None,use_current=True):
		# Helper to process our initial_start and return the last and
		# next loop timestamps
		if loop_mins is None:
			loop_mins = self.loop_mins
		if start_time is None:
			start_time = time.time()
		start = self._check_time_string(time_string=time_string)
		if start is None:
			# No time_string - or invalid, use the current
			# time as the hour/minute
			time_date = datetime.fromtimestamp(start_time)
			hour,minute = time_date.hour,time_date.minute
		else:
			# Expand the vars
			hour,minute = start
		# We have a proper hour:minute value, let's get the timestamp
		# for today at that time.
		target_timestamp = datetime.now().replace(
			hour=hour,
			minute=minute,
			second=0,
			microsecond=0,
		).timestamp()
		loops = 1 # Initialize at 1
		if target_timestamp > start_time:
			# We haven't passed our timestamp for today, roll
			# back to yesterday
			target_timestamp -= 86400
		# Get the difference between our current timestamp and that
		if start_time > target_timestamp:
			# Get the number of loops from the target timestamp to exceed the current
			# time
			loops = ((start_time-target_timestamp)//(loop_mins*60))+1
		# Ensure we loop at least once
		loops = max(1,loops)
		# Apply our loop adjustment to the target timestamp
		next_loop = target_timestamp+(loop_mins*60)*loops
		# Check if we also need to bridge gaps to our current time - allows for
		# a time_string -> start_time -> current_time logic flow
		if use_current not in (None,False):
			# use_current can be a passed timestamp, or
			# anything non-None/False to verify
			if not isinstance(use_current,bool) \
			and isinstance(use_current,(float,int)):
				# It's not a boolean, and is a number - use as-is
				current_time = use_current
			else:
				current_time = time.time()
			if current_time > next_loop:
				extra_loops = ((current_time-next_loop)//(loop_mins*60))+1
				next_loop += (loop_mins*60)*max(1,extra_loops)
		# Get our prior timestamp too
		prior_loop = next_loop-(loop_mins*60)
		# Return both, cast as integers
		return (int(prior_loop),int(next_loop))

	async def _get_json_data(self,url):
		# Wrapper to fetch a response and check the headers as well
		if self.ratelimit_end > time.time():
			# We're still rate limited - return None
			return None
		try:
			if self.spam:
				print("{}: Fetching url: {}".format(
					datetime.now().time().isoformat(),
					url
				))
			data,headers = await DL.async_json(
				url,
				headers={"User-Agent":self.ua},
				return_headers=True,
				assert_status=0 # Allow non-200 statuses
			)
			assert data and headers
		except:
			return None
		ratelimit_used = ratelimit_reset = 0
		ratelimit_remaining = 100
		try:
			ratelimit_used      = int(float(headers.get("x-ratelimit-used","0")))
			ratelimit_remaining = int(float(headers.get("x-ratelimit-remaining","100")))
			ratelimit_reset     = int(float(headers.get("x-ratelimit-reset","0")))
		except:
			pass
		if self.spam:
			print("{}: Ratelimit info:\n - Used: {}\n - Remaining: {}\n - Reset: {}".format(
				datetime.now().time().isoformat(),
				ratelimit_used,
				ratelimit_remaining,
				ratelimit_reset
			))
		if ratelimit_remaining <= 0:
			self.ratelimit_end = time.time() + ratelimit_reset
			if self.spam:
				print("{}: We're rate limited for {}s".format(
					datetime.now().time().isoformat(),
					ratelimit_reset
				))
			return None
		return data

	def unescape(self,text):
		try:
			u = unescape
		except NameError:
			h = HTMLParser()
			u = h.unescape
		return u(text)

	def _verify_sub_name(self, sub):
		try:
			# Ensure reddit.com/r/ is split off from the sub name if it exists as
			# well as any trailing info after a forward slash
			sub = re.split(r"(?i)reddit\.com",sub)[-1]
			sub = re.sub(r"(?i)^/?r/","",sub).split("/")[0]
			# Subreddit name can only be letters, numbers and underscores - but can't
			# start with an underscore - and can only have 2-21 characters
			assert sub[0] != "_"
			assert all(x in string.ascii_letters+string.digits+"_" for x in sub)
			assert 1 < len(sub) < 22
		except:
			return None
		return sub

	async def _get_sub_about(self, sub, force=False):
		# Helper to return info about the passed subreddit name
		if force:
			sub_data = {
				"name_prefixed":"Unknown Subreddit",
				"name":"Unknown Subreddit",
				"title":"Unknown Subreddit",
				"icon":"https://www.reddit.com/favicon.ico",
				"over_18":False
			}
		else:
			sub_data = {}
		try:
			sub = self._verify_sub_name(sub)
			sub_lower = sub.lower()
			assert sub # Ensure it's a valid name
			# Check if it's in the cache
			if sub_lower in self.sub_about_cache:
				# Check if it has expired (update caches once per day if needed)
				cache_expires = self.sub_about_cache[sub_lower].get("cache_expires",0)
				if cache_expires > time.time():
					# It's present, and not expired - return the cached data
					return self.sub_about_cache[sub_lower].get("data",sub_data)
			# Get the subreddit's name and ensure it exists by loading the about endpoint
			about_url = "https://www.reddit.com/r/{}/about.json".format(sub)
			about = await self._get_json_data(about_url)
			# Set our values - fall back on the favicon if there's no
			# community icon set
			sub_data["name_prefixed"] = self.unescape(about["data"]["display_name_prefixed"])
			sub_data["name"]          = self.unescape(about["data"]["display_name"])
			sub_data["title"]         = self.unescape(about["data"]["title"])
			sub_data["icon"]          = self.unescape(about["data"]["community_icon"]).split("?")[0] \
			                            or "https://www.reddit.com/favicon.ico"
			sub_data["over_18"]       = about["data"].get("over18",False)
			# If we got here - cache the data with an expiration of a day from now
			self.sub_about_cache[sub_lower] = {
				"data":sub_data,
				"cache_expires":time.time()+self.cache_expires
			}
		except:
			pass
		return sub_data

	async def _get_user_about(self, user, force=False):
		# Helper to return info about the passed user
		if not self.user_icons or force:
			# If we're not getting user icons, or we're forcing
			# a value, even if rate limited - build this info
			user_data = {
				"name":"u/{}".format(user),
				"url":"https://www.reddit.com/user/{}".format(user),
				# Fall back on a random default avatar 1-7
				"icon_url":"https://www.redditstatic.com/avatars/defaults/v2/avatar_default_{}.png".format(
					random.randint(1,7)
				)
			}
			# If we're not getting icons - just return the dict
			# This limits requests hugely
			if not self.user_icons:
				return user_data
		else:
			user_data = {}
		try:
			user_lower = user.lower()
			# Check if it's in the cache
			if user_lower in self.user_about_cache:
				# Check if it has expired (update caches once per day if needed)
				cache_expires = self.user_about_cache[user_lower].get("cache_expires",0)
				if cache_expires > time.time():
					# It's present, and not expired - return the cached data
					return self.user_about_cache[user_lower].get("data",user_data)
			# Get the subreddit's name and ensure it exists by loading the about endpoint
			about_url = "https://www.reddit.com/user/{}/about.json".format(user)
			about = await self._get_json_data(about_url)
			# Set our values - fall back on the favicon if there's no
			# community icon set
			name = self.unescape(about["data"]["name"])
			user_data["name"] = "u/{}".format(name)
			user_data["url"]  = "https://www.reddit.com/user/{}".format(name)
			if about["data"]["icon_img"]:
				user_data["icon_url"] = self.unescape(about["data"]["icon_img"]).split("?")[0]
			else:
				# Fall back on a random default avatar 1-7
				user_data["icon_url"] = "https://www.redditstatic.com/avatars/defaults/v2/avatar_default_{}.png".format(
					random.randint(1,7)
				)
			# If we got here - cache the data with an expiration of a day from now
			self.user_about_cache[user_lower] = {
				"data":user_data,
				"cache_expires":time.time()+self.cache_expires
			}
		except:
			pass
		return user_data

	async def _get_sub_data(self, sub=None, limit=None, url_override=None):
		# Gather our sub about for icons and such
		# Make sure we have a sub or URL override
		if sub is None and url_override is None:
			return None
		# Fall back on our default limit if none passed
		limit = limit or self.post_limit
		# Ensure our limit is between 1 and 100
		limit = min(100,max(1,limit))
		# Get the data we need
		url = url_override or "https://www.reddit.com/r/{}/new.json?limit={}".format(sub,limit)
		try:
			results = await self._get_json_data(url)
			if isinstance(results,list) and results:
				results = results[0] # Unwrap the first element if it's a list
		except:
			results = None
		if not isinstance(results,dict) or not results.get("data",{}).get("children"):
			# No data, or incorrect data - bail
			return None
		# Set up a data value and extract what we need
		data = []
		crosspost_from = None
		for child in results["data"]["children"]:
			if not "data" in child:
				continue
			d = child["data"]
			# Ensure we have required keys
			if not all(x in d for x in ("author","permalink","thumbnail","title","selftext","created")):
				continue
			# Check if this was crossposted - and if so, copy over the parent
			# data
			if d.get("crosspost_parent_list"):
				# Assume the first crosspost parent is what we want for now
				try:
					c = d["crosspost_parent_list"][0]
					# Update data related keys
					for k in ("gallery_data","media","media_metadata","preview","selftext","thumbnail"):
						if not c.get(k): continue
						# Overwrite with the parent data
						d[k] = c[k]
					# Save a reference to it for our footer later
					crosspost_from = c["subreddit_name_prefixed"]
				except:
					pass
			# If there's no thumbnail, it defaults to "self" - override with None
			thumbnails = Utils.get_urls(d["thumbnail"])
			thumbnail = thumbnails[0] if thumbnails else None
			image = None
			is_video = False
			is_gallery = False
			# Check for an image extension first
			if "url" in d or "url_overridden_by_dest" in d:
				url = self.unescape(d.get("url_overridden_by_dest",d.get("url","")))
				# First thing's first - check for YouTube links
				if self.re_youtube_url.match(url):
					# Very likely a video
					is_video = True
				else:
					# Get the mimetype based on the URL
					content_type = mimetypes.guess_type(url)[0] or ""
					if content_type.startswith("image/"):
						# We got an image
						image = url
					elif content_type.startswith("video/"):
						# We got a video
						is_video = True
			# Check for an image gallery next
			if image is None and "media_metadata" in d and "gallery_data" in d:
				# Figure out which is first via gallery data - then get
				# that entry's url
				try:
					key = d["gallery_data"]["items"][0]["media_id"]
					image = d["media_metadata"][key]["s"]["u"]
					if len(d["gallery_data"]["items"]) > 1:
						is_gallery = True
				except:
					pass
			# Only check for a preview if we don't have a source image
			if image is None and d.get("preview"):
				# Got a preview - get the first image
				try:
					image = d["preview"]["images"][0]["source"]["url"]
					if len(d["preview"]["images"]) > 1:
						# Possible gallery as there's more than one preview
						is_gallery = True
				except:
					pass
			# Check for media to see if we got a video
			if d.get("media"):
				is_video = True
				# If we don't have a thumbnail or image - try to rip it from the
				# media dict.
				if image is None or thumbnail is None:
					try:
						thumbnail_url = next(
							(x["thumbnail_url"] for x in d["media"].values() if x.get("thumbnail_url")),
							None
						)
					except:
						thumbnail_url = None
					if thumbnail_url:
						# Update any that are missing
						image = image or thumbnail_url
						thumbnail = thumbnail or thumbnail_url
			if is_video:
				# If we got a video, we can't also have a gallery
				is_gallery = False
			# Append the needed data
			data.append({
				"author":d["author"],
				"flair":d["link_flair_text"],
				"url":"https://www.reddit.com"+d["permalink"],
				"thumbnail":thumbnail if image is None else None,
				"image":image,
				"is_video":is_video,
				"is_gallery":is_gallery,
				"title":d["title"],
				"timestamp":datetime.fromtimestamp(d["created"]),
				"created":d["created"],
				"over_18":d["over_18"],
				"description":d["selftext"],
				"score":d.get("score",0),
				"num_comments":d.get("num_comments",0),
				"upvote_ratio":d.get("upvote_ratio",1.0),
				"crosspost_from":crosspost_from
			})
		return data

	def _process_markdown(self, text):
		# 2+ newlines = a single newline
		#   2+ spaces = a single space
		#     newline = a single space
		#         tab = a single space
		# If a line starts with 4 spaces, it's a code block - but only
		# if it's the first line, or the previous line is a newline/whitespace

		def is_whitespace(line):
			# Returns true/false depending on whether the
			# line of text passed is all whitespace
			return not line or self.re_whitespace_line.fullmatch(line)

		def is_codeblock(line):
			# Returns true/false depending on whether the line of text
			# passed is not all whitespace, but starts with 4 spaces
			return not is_whitespace(line) and self.re_whitespace_start.match(line)

		def merge_chunks(chunks, chunk_lines):
			if not chunks: return chunk_lines
			# Join by newlines - then replace all
			chunk_text = "\n".join(chunks)
			# Replace any single newlines with spaces
			# Then any multiple newlines with a single newline
			chunk_text = self.re_single_newline.sub(" ",chunk_text)
			chunk_text = self.re_multi_newline.sub("\n",chunk_text)
			chunk_lines.append(chunk_text)
			return chunk_lines

		def trim_row(line):
			# Strip pipes if needed at either end
			if line[0] == "|":
				line = line[1:]
			if line.rstrip()[-1] == "|":
				line = line.rstrip()[:-1]
			return line

		def get_table_row(line, table_rows):
			# We need to qualify our line based on context
			if not line.strip() or not "|" in line:
				# Only whitespace, empty line, single pipe char, etc
				return None
			if len(table_rows) == 0:
				# We're qualifying a starting line
				# Can start with | followed by whatever
				# If it doesn't start with |, it cannot start
				# with #
				if line.strip() == "|" or line[0] == "#":
					return None
				# Not a header - let's see if we got pipes at either end
				line = trim_row(line)
				# Now split the pipes we have and return the stripped segments
				return [x.strip() for x in line.split("|")]
			elif len(table_rows) == 1:
				# We're qualifying the separator line
				# The number of columns *needs* to be >= the column headers.
				# The considered columns can only contain |, -, and whitespace,
				# chars, and only in the order of pipe, whitespace, hypen, whitespace
				line = trim_row(line)
				cols = []
				for col in line.split("|"):
					col = col.strip()
					if not self.re_table_separator.fullmatch(col):
						break
					cols.append("-")
				# Make sure we got enough
				target_length = len(table_rows[0])
				if len(cols) < target_length:
					return None
				# We should have what we need here, return only
				# what we need
				return cols[:target_length]
			else:
				# We're qualifying a content line
				line = trim_row(line)
				cols = [x.strip() for x in line.split("|")]
				# Make sure we got enough
				target_length = len(table_rows[0])
				if len(cols) < target_length:
					# Pad the list to the right length as needed
					cols += [""]*(target_length-len(cols))
				# Return only what we need
				return cols[:target_length]
		
		def dump_table_rows(table_rows):
			# Formats a table into rows
			rows = []
			for i,row in enumerate(table_rows):
				if i == 1:
					# Separator row
					row = ("⎯"*10,)
				# Join the parts
				rows.append("| {} |".format(" | ".join(row)))
			return "\n\n".join(rows)

		# Walk the text line by line and try to stay
		# sane.
		new_lines = []
		code_block = ""
		list_block = ""
		list_depth = [] # Holds padding for depth
		plain_text = ""
		in_table   = False
		table_rows = []
		list_pad   = "" # The pad for the top level list item
		last_line  = ""
		quoting    = False
		text_lines = text.split("\n")
		line_count = len(text_lines)
		lines_proc = () # Placeholder for lines to process
		# Strip carriage returns and convert tabs to spaces first
		text = text.replace("\t","    ").replace("\r","")
		for i,line in enumerate(text_lines):
			# Retain surrounding lines for context
			last_line = "" if i==0 else text_lines[i-1]
			next_line = text_lines[i+1] if i+1<line_count else ""
			if code_block:
				if is_whitespace(line) or is_codeblock(line):
					# We are in a code block, and are adding more lines
					code_block += "\n"+line[4:]
					continue # Move to the next line
				else:
					# We were in a code block, but aren't anymore.  Strip
					# any trailing whitespace and cap the codeblock
					# Append it to the new_lines list with a True for code block
					new_lines.append((
						True,
						code_block.rstrip()+"\n```"
					))
					# Reset our block
					code_block = ""
					# Don't continue to the next line here - as we have to parse
					# our line still
			elif list_block:
				if is_whitespace(line):
					# Just skip these for now
					continue
				elif line.strip().startswith(("* ","- ")) or self.re_number_list.match(line.strip()):
					# Got a list element - find out if it's top or second level
					indent = self.re_whitespace_indent.match(line).group(1)
					# Try to figure out our depth
					index,matching_indent = next(
						((i,x) for i,x in enumerate(list_depth) if x==len(indent)),
						(None,None)
					)
					if index is not None:
						# Got a matching indent - let's shed any after
						list_depth = list_depth[:index+1]
					else:
						# Ensure we're not beyond our max
						past_max = (len(list_depth)+1)*4
						l_indent = len(indent)
						if l_indent >= past_max:
							# Past the max depth, append to the prior line
							list_block = list_block+" "+line.strip()
							continue
						# Just base it on depth - if we increased depth,
						# assume we've indented.  If we decreased in depth,
						# assume we've unindented.
						while True:
							if not list_depth or list_depth[-1] < l_indent:
								# Can't unindent anymore
								break
							# Remove the last indent
							del list_depth[-1]
						# Add our indent
						list_depth.append(l_indent)
					# Set up our pad - use 2 spaces as it seems to be
					# the least troublesome, especially with mixed
					# bullet point/numbered lists
					pad = "  "*(len(list_depth)-1)
					list_block += "\n\n"+pad+line.strip()
					continue
				else:
					# No longer in a list block - maybe... Check if the last line
					# was whitespace or a line separator
					if self.re_line.fullmatch(line) or is_whitespace(last_line):
						# Save our list block
						new_lines.append((
							False,
							list_block+"\n"
						))
						# Reset it - and don't continue
						list_block = list_pad = ""
					else:
						# Not whitespace - or we're the first entry somehow?
						# We just append this to the prior line with a single space
						list_block += " "+line.strip()
						continue
			# We need to verify if we have a table *first* - that way we can
			# process each column as its own line with its own formatting
			# There are some rules to this - and they're a little wonky, so
			# let's do our best.
			if in_table:
				# Check if we got a valid table row
				_row = get_table_row(line,table_rows)
				if _row:
					# Got a row - replace our line with that
					line = _row
				else:
					# We didn't get a valid row - save all the existing table rows to
					# a text block and append it
					# Add to our text
					new_lines.append((
						False,
						"\n"+dump_table_rows(table_rows)+"\n"
					))
					# Reset our vars
					table_rows = []
					in_table = False
			else:
				# Check for rows in the current and next lines
				_row = get_table_row(line,table_rows)
				if _row:
					# Pass _row in a tuple as a temp table_rows var
					# to allow context checking
					_next = get_table_row(next_line,(_row,))
					if _next:
						# Got some rows
						in_table = True
						# Now we pass the rows we got
						line = _row
			quote_sub = self.re_quote_sub.sub("",line)
			if quoting and is_whitespace(quote_sub):
				# No longer quoting - just got some whitespace (even quoted
				# whitespace counts here)
				quoting = False
				line = quote_sub
			if isinstance(line,str):
				# Wrap in a tuple to iterate
				line = (line,)
			new_row = []
			for l in line:
				# We have a basic line to process here - check if it's the start of
				# a code block.
				# Needs to start with 4 spaces, not be all whitespace, and either the
				# first line, or the prior line needs to be whitespace
				if is_codeblock(l) and is_whitespace(last_line):
					# Start of a new code block
					code_block = "```\n"+l[4:]
				# Check if we have a list - we have 2 levels of depth we can incorporate
				# so we'll need to find out what the first one is - if any
				elif (l.lstrip().startswith(("* ","- ")) or self.re_number_list.match(l.strip())) \
				and is_whitespace(last_line):
					# Start a new list block
					list_pad = self.re_whitespace_indent.match(l).group(1)
					list_depth = [len(list_pad)]
					list_block = l.strip()
				else:
					# Not a code or list block - check if the line ends with 2+ spaces.
					# If it does - that's some other way of saying "everything else on
					# the next line" for some reason (?)
					suffix = "\n" if l.endswith("  ") else ""
					prefix = ""
					# Check if we start with multi-quotes
					l = l.strip()
					quote_match = self.re_quote_sub.match(l)
					if not in_table and quote_match:
						# Strip out the multi-quotes, but not in tables
						# Let's see if our match ends with >!
						repl = ""
						group = quote_match.group(0)
						if group.endswith(">!"):
							# It's a spoiler - save that
							repl = ">!"
						l = self.re_quote_sub.sub(repl,l)
						if not quoting and (not l.startswith(">!") or not "!<" in l):
							# First quoted element that isn't a spoiler
							# Ensure we prefix appropriately
							quoting = True
							l = "> "+l
					if l.lower() in ("-","&nbsp;","&#x200b;","#"):
						l = "" # Just a newline placeholder
					if self.re_line.match(l):
						l = "⎯"*10 # Originally a line separator
						# Check if we need to pad it on either end based on the
						# surrounding lines
						if not is_whitespace(last_line):
							prefix = "\n" # Pad the previous line
						if not is_whitespace(next_line):
							suffix = "\n" # Pad the next line
					hash_match = self.re_hashes.match(l)
					if not in_table and hash_match:
						# We got a header of sorts.  Discord allows for up to 4 hash
						# tags to create headers.  Reddit allows 5, 6 creates an
						# underlined header - and 7+ are a part of the header
						hashes = hash_match.group("hashes")
						if len(hashes) <= 5:
							# We're creating a header - cap the length to 5
							l = "#"*min(3,len(hashes))+" "+hash_match.group("content")
						else:
							# We need to underline our content - find out how
							# many hashes past 6 we have
							hash_add = max(0,len(hashes)-6)
							l = "__{}{}__".format(("#"*hash_add),hash_match.group("content"))
						# Check if we need to pad it on either end based on the
						# surrounding lines
						if not is_whitespace(last_line):
							prefix = "\n" # Pad the previous line
						if not is_whitespace(next_line):
							suffix = "\n" # Pad the next line
					if not in_table:
						# Append to our lines if we're not in a table
						new_lines.append((
						False,
						prefix+self.re_whitespace_sub.sub(" ",l)+suffix
					))
				if in_table:
					# Ignore prefix and suffix so we don't
					# add erroneous newlines
					new_row.append(
						self.re_whitespace_sub.sub(" ",l)
					)
			if in_table:
				# Add the new row to our table if we got something
				table_rows.append(new_row)
		# Ensure we save any remaining code, list, or table block
		# lines that are left
		if code_block:
			new_lines.append((
				True,
				code_block.rstrip()+"\n```"
			))
		if list_block:
			new_lines.append((
				False,
				list_block+"\n"
			))
		if in_table:
			new_lines.append((
				False,
				"\n"+dump_table_rows(table_rows)+"\n"
			))
		# Walk our chunks and build the final text
		chunk_lines = []
		chunks = []
		for block,chunk in new_lines:
			if block:
				# Check if we have chunks to manipulate
				chunk_lines = merge_chunks(chunks, chunk_lines)
				chunks = [] # Reset our chunks
				# Now add our chunk as-is to the lines
				chunk_lines.append(chunk)
			else:
				# Append the chunk to our chunks
				chunks.append(chunk)
		# Make sure we catch any remaining chunks
		if chunks:
			chunk_lines = merge_chunks(chunks, chunk_lines)
		pre_final_lines = "\n".join(chunk_lines).strip().split("\n")
		# One final run through of the lines to ensure we swap
		# out spoiler tags with || as needed
		spoilered_lines = []
		for line in pre_final_lines:
			# Try to walk the line and replace individual entries
			spoiler_start = line.startswith((">!","> >!"))
			matches = []
			for match in self.re_spoiler_search.finditer(line):
				if match.group(2) == ">!" and len(matches) % 2 \
				or match.group(2) == "!<" and not len(matches) % 2:
					# Got an out of order match - skip
					continue
				# We got a valid match save it to our matches list
				matches.append(match)
			# Ensure our matches are in pairs
			if len(matches) % 2:
				if spoiler_start:
					# We got an odd number - but started with a spoiler
					# Let's just tack || at the end to close it
					line += "||"
				else:
					# An odd number, strip the last open spoiler
					matches = matches[:-1]
			# Iterate the matches and replace them with || chars
			for match in matches:
				repl = match.group(0).replace(">!","||").replace("!<","||")
				line = line[:match.start()]+repl+line[match.end():]
			spoilered_lines.append(line)
		final_text = "\n".join(spoilered_lines)
		# Walk the final text and fill in reddit specific hyperlinks
		# i.e. [CorpNewt](/u/corpnewt) would become
		# [CorpNewt](https://www.reddit.com/u/corpnewt)
		i_adjust = 0
		for m in self.re_redditlink_md.finditer(final_text):
			try:
				assert m.group("vanity") and m.group("url")
			except:
				continue
			# Prepend https://www.reddit.com to the url
			new_string = "[{}](https://www.reddit.com{}{})".format(
				m.group("vanity"),
				"/" if m.group("url")[0] != "/" else "",
				m.group("url")
			)
			final_text = final_text[0:m.start()+i_adjust]+new_string+final_text[i_adjust+m.end():]
			i_adjust += len(new_string)-len(m.group(0))
		# Walk the final text and strip out any hyperlink
		# markdown where the vanity portion is also a URL
		i_adjust = 0
		for m in self.re_hyperlink_md.finditer(final_text):
			try:
				assert m.group("vanity") and m.group("url")
			except:
				continue
			new_text = None
			if Utils.get_urls(m.group("vanity")):
				# We got a URL in the vanity link - replace it
				new_text = m.group("url")
			else:
				# Check if we got any escaped parenthesis in the vanity string
				vanity_subbed = self.re_vanity_escape_sub.sub(
					r"\g<prefix>\g<escaped>",
					m.group("vanity")
				)
				new_text = "[{}]({})".format(
					vanity_subbed,
					m.group("url")
				)
			if new_text is None or new_text == m.group(0):
				continue
			# Update our final text with the new text
			final_text = final_text[0:m.start()+i_adjust]+new_text+final_text[i_adjust+m.end():]
			i_adjust += len(new_text)-len(m.group(0))
		i_adjust = 0
		for m in self.re_escaped_url.finditer(final_text):
			new_text = m.group(0).replace("\\","")
			final_text = final_text[0:m.start()+i_adjust]+new_text+final_text[i_adjust+m.end():]
			i_adjust += len(new_text)-len(m.group(0))
		return final_text

	async def _sub_scheduler(
		self,
		guild,
		channel,
		sub,
		sub_freq,
		scheduled,
		loop_cache,
		allow_over_18 = None,
		additional_wait = 0,
		max_timestamp = 0
	):
		# Helper to schedule retrieval with consideration for rate limits
		key = "{}-{}".format(guild.id,sub)
		if self.spam:
			print("{}: Sub scheduled {}".format(
				datetime.now().time().isoformat(),
				key
			))
		if isinstance(additional_wait,(int,float)) and additional_wait > 0:
			# Optional additional wait time - can be helpful to let reddit's
			# servers gather remaining posts
			if self.spam:
				print("{}: Waiting an additional {}s...".format(
					datetime.now().time().isoformat(),
					additional_wait
				))
			await asyncio.sleep(additional_wait)
		if allow_over_18 is None:
			allow_over_18 = self.settings.getServerStat(guild,"AllowNsfwWatchedSubreddits",False)
		while True:
			if not self.is_current:
				return # Not the current instance - bail
			remaining = self.ratelimit_end-time.time()
			if remaining > 0:
				if self.spam:
					print("{}: Waiting {:,} seconds for rate limited {} post...".format(
						datetime.now().time().isoformat(),
						remaining,
						sub
					))
				# Wait until the rate limit should be done,
				# then check again
				await asyncio.sleep(remaining)
				continue
			# We should be rate-limit free here
			if self.subreddit_cache.get(key,{}).get("scheduled",0) > scheduled:
				if self.spam:
					print("{}: Deferred {} scheduler expired - main loop has surpassed.".format(
						datetime.now().time().isoformat(),
						key
					))
				# We've run the main loop since we've been
				# waiting.  Just bail
				return
			# We can try to get our loop cache info
			if sub in loop_cache and loop_cache[sub].get("run",0):
				about    = loop_cache[sub].get("about",{})
				data     = loop_cache[sub].get("data", [])
				last_run = loop_cache[sub].get("run",int(time.time()))
			else:
				# Doesn't exist - get it anew.  Start with the subreddit info
				about = await self._get_sub_about(sub)
				if not about:
					# Doesn't exist?  Check for a rate limit
					if self.ratelimit_end > time.time():
						continue
					return
				# Retain the last successful run time
				last_run = int(time.time())
				data = await self._get_sub_data(sub=sub)
				if data is None:
					# Didn't get anything - check for a rate limit
					if self.ratelimit_end > time.time():
						continue
					return
				# Update the loop cache
				loop_cache[sub] = {
					"about":about,
					"data":data,
					"run":last_run
				}
			# Check if it's an NSFW sub and whether or not we allow that
			if about.get("over_18") and not allow_over_18:
				if self.spam:
					print("{}: {} is NSFW and that is not allowed - bail.".format(
						datetime.now().time().isoformat(),
						about.get("name_prefixed",sub)
					))
				return
			# Make sure the main loop didn't run in this time
			if self.subreddit_cache.get(key,{}).get("scheduled",0) > scheduled:
				if self.spam:
					print("{}: Deferred {} scheduler expired - main loop has surpassed.".format(
						datetime.now().time().isoformat(),
						key
					))
				# We've run the main loop since we've been
				# waiting.  Just bail
				return
			# Get our previous data, if any
			last_list = self.subreddit_cache.get(key,{}).get("data",[])
			last_created = max([x["created"] for x in last_list]) if last_list \
			               else self.subreddit_cache.get(key,{}).get("last_created",0)
			# Update our cache with the data and last run time - fall back on the
			# scheduled time for last_created if none is available to account for
			# potential wait time.
			self.subreddit_cache[key] = {
				"about":about,
				"data":data,
				"frequency":sub_freq,
				"scheduled":scheduled,
				"run":last_run,
				"last_created":max([x["created"] for x in data]) if data else scheduled
			}
			# Check for any missing posts - and make sure they were created
			# since the last run
			permalinks = [x["url"] for x in last_list]
			missing_posts = [
				# Get newer posts that we haven't seen yet which don't break our
				# NSFW rules - if any
				x for x in data if (allow_over_18 or not x.get("over_18")) \
				and (x["created"]) >= last_created and not x["url"] in permalinks
			]
			# Restrict it further if we have a max timestamp
			if isinstance(max_timestamp,(int,float)) and max_timestamp > 0:
				# Cast it to an integer value
				if isinstance(max_timestamp,float):
					max_timestamp = int(max_timestamp)
				if self.spam:
					print("{}: Max post timestamp limited to {} ({}).".format(
						datetime.now().time().isoformat(),
						datetime.fromtimestamp(max_timestamp).time().isoformat(),
						max_timestamp
					))
				missing_posts = [x for x in missing_posts if x["created"] < max_timestamp]
			if not missing_posts:
				# We have nothing to send - carry on
				return
			# Schedule message sending tasks to allow multiple guilds
			# to send mostly simultaneously
			self.bot.loop.create_task(self.send_posts(
				missing_posts,
				channel,
				about=about
			))
			return

	async def wait_until(self, timestamp):
		# Get an intial time value
		t = time.time()
		if self.spam:
			print("{}: Waiting for {}s until {}".format(
				datetime.now().time().isoformat(),
				timestamp-t,
				datetime.fromtimestamp(timestamp).time().isoformat()
			))
		while True:
			if t >= timestamp:
				break
			# Wait until our time has elapsed
			await asyncio.sleep(timestamp-t)
			# Update the time var
			t = time.time()
		if self.spam:
			print("{}: Done waiting!".format(
				datetime.now().time().isoformat()
			))
		# Return the timestamp - for.. reasons?
		return t

	async def sub_watcher(self):
		await self.bot.wait_until_ready()
		self.first_loop,self.next_loop = self._get_last_next_loop_time()
		print("{}: Starting subreddit watch loop at {}\n - Repeats every {:,} minute{}...".format(
			datetime.now().time().isoformat(),
			datetime.fromtimestamp(self.next_loop).time().isoformat(),
			self.loop_mins,
			"" if self.loop_mins==1 else "s"
		))
		# Wait until the next loop would start
		await self.wait_until(self.next_loop)
		while not self.bot.is_closed():
			if not self.is_current:
				# Bail if we're not the current instance
				return
			loop_cache = {}
			loop_start = time.perf_counter()
			loop_time_start = time.time()
			# Iterate our servers and check for any subs
			for guild in self.bot.guilds:
				subs = self.settings.getServerStat(guild,"WatchedSubreddits",{})
				if not subs:
					continue # Nothing there
				allow_over_18 = self.settings.getServerStat(guild,"AllowNsfwWatchedSubreddits",False)
				# Iterate the list of subs and cache them as needed
				for sub in subs:
					channel = DisplayName.channelForName(subs[sub]["channel"],guild)
					if not channel:
						# Doesn't exist - skip
						continue
					key = "{}-{}".format(guild.id,sub)
					schedule  = int(time.time())
					last_dict = self.subreddit_cache.get(key,{})
					sub_freq  = subs[sub]["frequency"]
					sub_freq  = max(sub_freq,self.loop_mins)
					# Make sure it's a multiple of our loop_mins too
					if sub_freq % self.loop_mins:
						sub_freq = ((sub_freq // self.loop_mins) + 1) * self.loop_mins
					# Get the last time it was scheduled - if any
					last_scheduled = last_dict.get("scheduled")
					if last_scheduled is None:
						if self._check_time_string() is not None:
							# We need to get our last loop relative to the
							# first_loop timestamp, not the current time
							last_scheduled,_ = self._get_last_next_loop_time(
								start_time=self.first_loop,
								loop_mins=sub_freq
							)
							if abs(schedule-last_scheduled) < 30:
								# We're withing 30 seconds of the last scheduled
								# loop threshold - go back another loop
								last_scheduled -= sub_freq*60
						else:
							# Fall back on whenever we started the loop
							last_scheduled = self.first_loop
					run_mins = max(0,(schedule-last_scheduled)/60)
					if last_scheduled and sub_freq-run_mins > 0.5:
						# We're more than 30 seconds away from our target time,
						# keep waiting.
						continue
					# Got a channel - let's schedule a check
					if self.spam:
						print("{}: Scheduling {}...".format(
							datetime.now().time().isoformat(),
							key
						))
					sub_data = self.subreddit_cache.get(key,{})
					sub_data["scheduled"] = schedule
					if sub_data.get("last_created") is None:
						# We haven't scheduled/run yet - so consider any
						# that would have been from a prior loop
						sub_data["last_created"] = int(last_scheduled)
					# Ensure the sub_data persists
					self.subreddit_cache[key] = sub_data
					# Schedule the check
					self.bot.loop.create_task(
						self._sub_scheduler(
							guild,
							channel,
							sub,
							sub_freq,
							schedule,
							loop_cache,
							allow_over_18=allow_over_18,
							# Allow Reddit servers to "settle" in order for
							# entries to populate in the JSON responses
							additional_wait=self.settle_time,
							# Restrict gathered entries to our current
							# scheduled timestamp
							max_timestamp=schedule
						)
					)
			# Get how long our loop took
			loop_time = time.perf_counter()-loop_start
			# Try to round our next loop start to hopefully prevent drift
			self.next_loop = round(loop_time_start+(self.loop_mins*60))
			# Our next_wait will be our next_loop_time_start
			next_wait = self.next_loop-time.time()
			if self.spam:
				print("{}: Loop took {}s".format(
					datetime.now().time().isoformat(),
					loop_time
				))
			# Ensure we wait long enough
			await self.wait_until(self.next_loop)

	async def send_post(
		self,
		post,
		channel,
		ctx=None,
		about=None,
		score_comments=False,
		message=None
	):
		# Send an individual post using some context clues
		try:
			# Check if we got an about - and if not, extract it from
			# the post URL itself
			about = about or await self._get_sub_about(post["url"],force=True)
			# Let's build our footer
			suffix = " (video)" if post["is_video"] else " (gallery)" if post["is_gallery"] else ""
			# Check if it was crossposted
			xpost = " | {}".format(post["crosspost_from"]) if post["crosspost_from"] else ""
			footer = {
				"text": "{}{}{}{}".format(
					about["name_prefixed"],
					suffix,
					xpost,
					"" if not score_comments else " | Score: {:,} ({}%) | Comments: {:,}".format(
						post["score"],
						int(post["upvote_ratio"]*100),
						post["num_comments"]
					)
				),
				"icon_url":about["icon"]
			}
			# Resolve the color - or use None if we can't
			if ctx:
				color = ctx.author
			elif channel and channel.guild:
				color = channel.guild.me
			else:
				color = None
			if not post.get("strings_processed"):
				# Unescape string-based values
				for k in post:
					if isinstance(post.get(k),str):
						try:
							post[k] = self.unescape(post[k])
							if k == "description":
								# Process the markdown
								post[k] = self._process_markdown(post[k])
						except:
							post[k] = post[k]
					else:
						post[k] = post[k]
				# See if we got a flair we can append to the title
				if self.title_flair and post["flair"] and post["title"]:
					post["title"] = "{} [{}]".format(
						post["title"],
						post["flair"]
					)
				# Try to resolve the author data
				post["author"] = await self._get_user_about(post["author"],force=True)
				# See if we need to append to the author
				if self.author_flair and post["flair"]:
					post["author"]["name"] = "{} - [{}]".format(
						post["author"]["name"],
						post["flair"]
					)
				# Set the key needed to show we've processed the args
				# to avoid double processing
				post["strings_processed"] = True
			if ctx is None or not post["description"]:
				# No context object was passed or we have no description
				# to page pick.
				# We also need to truncate the description as needed.
				# Send the info using a regular Embed
				await Message.Embed(
					title=post["title"],
					description=Utils.truncate_string(
						post["description"],
						limit=2048,
						replace_newlines=False
					),
					thumbnail=post["thumbnail"],
					image=post["image"],
					timestamp=post["timestamp"],
					url=post["url"],
					author=post["author"],
					color=color,
					footer=footer
				).send(channel,message)
			else:
				# We can use a page picker for this as we have a
				# sender.  We will want to schedule this via the
				# bot's event loop, so that multiple messages are
				# watched individually though.
				picker = PickList.PagePicker(
					title=post["title"],
					description=post["description"],
					thumbnail=post["thumbnail"],
					image=post["image"],
					timestamp=post["timestamp"],
					url=post["url"],
					author=post["author"],
					timeout=600, # Allow 10 minutes before we stop watching the picker
					ctx=ctx,
					message=message,
					color=color,
					footer=footer
				)
				# Schedule the pick function as a standalone task
				# to allow independent interaction with it
				self.bot.loop.create_task(picker.pick())
		except Exception as e:
			print(e)
			pass

	async def send_posts(
		self,
		post_list,
		channel,
		ctx=None,
		about=None,
		score_comments=False,
		message=None
	):
		# Try to resolve the about dict first - force it to update, so
		# even if this is a borked post_list, we have *something* for the
		# needed values
		about = about or self._get_sub_about(post_list[0],force=True)
		# Sort oldest -> newest by created date
		for post in sorted(post_list,key=lambda x:x.get("created",0)):
			if not self.is_current:
				# Bail if we're not the current instance
				return
			await self.send_post(
				post,
				channel,
				ctx=ctx,
				about=about,
				score_comments=score_comments,
				message=message
			)

	async def send_random_top_post(
		self,
		ctx,
		subreddit,
		limit=50,
		min_posts=5,
		image=None,
		video=None,
		remove_description=False,
		allow_over_18=None
	):
		# Convenience function to automate
		# send_matching_post
		return await self.send_matching_post(
			ctx,
			subreddit,
			sort="top",
			limit=limit,
			min_posts=min_posts,
			randomize=True,
			image=image,
			video=video,
			remove_description=remove_description,
			allow_over_18=allow_over_18
		)

	async def send_newest_post(
		self,
		ctx,
		subreddit,
		limit=50,
		min_posts=5,
		image=None,
		video=None,
		remove_description=False,
		allow_over_18=None
	):
		return await self.send_matching_post(
			ctx,
			subreddit,
			sort="new",
			limit=limit,
			min_posts=min_posts,
			randomize=False,
			image=image,
			video=video,
			remove_description=remove_description,
			allow_over_18=allow_over_18
		)

	async def send_matching_post(
		self,
		ctx,
		subreddit,
		sort="top",
		limit=50,
		min_posts=5,
		randomize=False,
		image=None,
		video=None,
		remove_description=False,
		allow_over_18=None
	):
		# Sends a random top post from the passed sub to the ctx channel
		# Also verifies if we're admin/bot-admin for nsfw subs - unless
		# allow_over_18 is explicitly True or False.
		# Will send a status message if no data was found.
		sub = self._verify_sub_name(subreddit)
		if not sub:
			return await Message.Embed(
				title="Could not resolve subreddit!",
				description="\"{}\" does not appear to be a valid subreddit.".format(
					subreddit
				),
				color=ctx.author
			).send(ctx)
		# Send a status message
		message = await Message.Embed(
			title="Fumbling through reddit posts...",
			color=ctx.author
		).send(ctx)
		# Get our over 18 info as needed
		if allow_over_18 is None:
			if ctx.guild:
				# Check if we're admin/bot-admin
				allow_over_18 = Utils.is_bot_admin(ctx)
			else:
				# Check if we're owner or allowed to use NSFW commands
				# in dm.
				allow_over_18 = Utils.is_owner(ctx) or \
				self.settings.getGlobalStat("AllowNsfwSubredditsDm",False)
		# Gather our top data
		data = await self.get_matching_post(
			sub,
			sort=sort,
			limit=limit,
			min_posts=min_posts,
			randomize=randomize,
			image=image,
			video=video,
			remove_description=remove_description,
			allow_over_18=allow_over_18
		)
		if data is False:
			return await Message.Embed(
				title="Insufficient privileges!",
				description="You do not have sufficient privileges to access nsfw subreddits."
			).send(ctx,message)
		elif not data:
			desc = None
			if self.ratelimit_end > time.time():
				desc = "It looks like I'm rate limited. Please try again <t:{}:R>".format(
					math.ceil(self.ratelimit_end),
				)
			return await Message.Embed(
				title="Whoops! I couldn't find a post from r/{} matching that criteria.".format(
					sub
				),
				description=desc
			).send(ctx,message)
		# Got some data - send it!
		await self.send_post(
			data,
			ctx,
			ctx=ctx,
			score_comments=True,
			message=message
		)			
	
	async def get_matching_post(
		self,
		subreddit,
		sort="top",
		limit=50,
		min_posts=5,
		randomize=True,
		image=None,
		video=None,
		remove_description=False,
		allow_over_18=False
	):
		# Gets a random post from the top week, month, or year
		sub = self._verify_sub_name(subreddit)
		if not sub:
			return None
		# Pre-check if the sub is over 18 if we're explicitly disallowing
		# that.
		if allow_over_18 is False:
			about = await self._get_sub_about(sub)
			if about.get("over_18"):
				# We don't have perms to view this
				return False
		# Ensure our min_posts do not exceed our limit
		min_posts = min(min_posts,limit)
		# Format our baseline subreddit url
		url = "https://www.reddit.com/r/{}/{}.json?limit={}".format(
			sub,
			sort,
			limit
		)
		return_type = None
		for t in ("week","month","year",""):
			u = url
			if t:
				# Append our time frame if it's not
				# top of all time
				u += "&t={}".format(t)
			# Get our data and return it if we got something
			data = await self.get_post(
				u,
				min_posts=min_posts,
				randomize=randomize,
				image=image,
				video=video,
				remove_description=remove_description,
				allow_over_18=allow_over_18
			)
			if data is False:
				# Retain NSFW returns for feedback purposes
				return_type = False
			elif not data and self.ratelimit_end > time.time():
				# We're being rate limited - bail
				break
			elif data:
				return data
		# Nothing found
		return return_type

	async def get_post(
		self,
		url,
		min_posts=5,
		randomize=True,
		image=None,
		video=None,
		remove_description=False,
		allow_over_18=False
	):
		# First check if url is a dict - and if so, assume
		# it was valid data passed
		if isinstance(url,dict):
			data = url
		else:
			# Get the data from the passed url
			try:
				data = await self._get_sub_data(url_override=url)
				assert data
				if min_posts > 0:
					# Make sure we got enough posts
					assert len(data) >= min_posts
			except Exception as e:
				return None
		# We should have data here - shuffle if random
		if randomize:
			random.shuffle(data)
		# Get the first post that meets our requirements
		return_type = None
		for post in data:
			# Check if it's over 18 and we don't allow that
			if post.get("over_18") and not allow_over_18:
				return_type = False # Retain this for feedback purposes
				continue # No dice - onto the next
			# Check video first - as they'll also have preview
			# images
			elif video is True and not post.get("is_video"):
				# We need a video, and this doesn't have one
				continue
			elif video is False and post.get("is_video"):
				# We cannot have a video, and this post has one
				continue
			elif image is True and not post.get("image"):
				# We *require* an image, and this post doesn't have one
				continue
			elif image is False and post.get("image"):
				# We cannot have an image, and this post has one
				continue
			# Strip the description if needed.  Useful for title-only, or
			# image/video only posts.
			if remove_description or ((image or video) and remove_description is None):
				post["description"] = ""
			# At this point we should have something!
			return post
		# If we got here, we didn't find what we needed - bail
		return return_type
	
	@commands.command()
	async def ruser(self, ctx, *, user_name = None):
		"""Gets some info on the passed username - attempts to use your username if none provided."""
		user_name = user_name or ctx.author.display_name
		# Get the info
		url = "https://www.reddit.com/user/{}/about.json?raw_json=1".format(quote(user_name))
		# Giving a 200 response for some things that aren't found
		try:
			theJSON = await self._get_json_data(url)
		except:
			# Assume that we couldn't find that user
			return await Message.EmbedText(
				title="An error occurred!",
				description="Make sure you're passing a valid reddit username.",
				color=ctx.author
			).send(ctx)
		# Returns:  {"message": "Not Found", "error": 404}  if not found
		if "message" in theJSON:
			error = theJSON.get("error", "An error has occurred.")
			return await Message.EmbedText(title=theJSON["message"], description=str(error), color=ctx.author).send(ctx)
		# Build our embed
		e = { 
			"title" : "/u/" + theJSON["data"]["name"],
			"url" : "https://www.reddit.com/user/" + theJSON["data"]["name"],
			"color" : ctx.author, 
			"fields" : [] }

		# Get the unix timestamp for the account creation
		ts = int(theJSON["data"]["created_utc"])
		created_string = "<t:{}> (<t:{}:R>)".format(ts,ts)

		e["fields"].append({ "name" : "Created", "value" : created_string, "inline" : True })
		e["fields"].append({ "name" : "Link Karma", "value" : "{:,}".format(theJSON["data"]["link_karma"]), "inline" : True })
		e["fields"].append({ "name" : "Comment Karma", "value" : "{:,}".format(theJSON["data"]["comment_karma"]), "inline" : True })
		e["fields"].append({ "name" : "Has Gold", "value" : str(theJSON["data"]["is_gold"]), "inline" : True })
		e["fields"].append({ "name" : "Is Mod", "value" : str(theJSON["data"]["is_mod"]), "inline" : True })
		e["fields"].append({ "name" : "Verified Email", "value" : str(theJSON["data"]["has_verified_email"]), "inline" : True })
		# Send the embed
		await Message.Embed(**e).send(ctx)

	@commands.command()
	async def nosleep(self, ctx):
		"""I hope you're not tired..."""
		await self.send_random_top_post(ctx,"nosleep")

	@commands.command()
	async def joke(self, ctx):
		"""Let's see if reddit can be funny..."""
		await self.send_random_top_post(ctx,"jokes")
	
	@commands.command()
	async def lpt(self, ctx):
		"""Become a pro - AT LIFE."""
		await self.send_random_top_post(ctx,"LifeProTips")
		
	@commands.command()
	async def shittylpt(self, ctx):
		"""Your advice is bad, and you should feel bad."""
		await self.send_random_top_post(ctx,"ShittyLifeProTips")

	@commands.command()
	async def thinkdeep(self, ctx):
		"""Spout out some intellectual brilliance."""
		await self.send_random_top_post(ctx,"Showerthoughts")

	@commands.command()
	async def brainfart(self, ctx):
		"""Spout out some uh... controversial brilliance..."""
		await self.send_random_top_post(ctx,"Showerthoughts",sort="controversial")

	@commands.command()
	async def nocontext(self, ctx):
		"""Spout out some out of context brilliance."""
		await self.send_random_top_post(ctx,"nocontext")
		
	@commands.command()
	async def withcontext(self, ctx):
		"""Spout out some contextual brilliance."""
		await self.send_random_top_post(ctx,"evenwithcontext")

	@commands.command()
	async def question(self, ctx):
		"""Spout out some interstellar questioning... ?"""
		await self.send_random_top_post(ctx,"NoStupidQuestions")

	@commands.command(aliases=["rimage"])
	async def redditimage(self, ctx, subreddit = None, *, flags = None):
		"""Equivalent to $reddit, but adds the "image" flag."""
		flags = "image "+flags if flags else "image"
		await ctx.invoke(self.reddit,subreddit=subreddit,flags=flags)
	
	@commands.command(aliases=["rvideo"])
	async def redditvideo(self, ctx, subreddit = None, *, flags = None):
		"""Equivalent to $reddit, but adds the "video" flag."""
		flags = "video "+flags if flags else "video"
		await ctx.invoke(self.reddit,subreddit=subreddit,flags=flags)

	@commands.command()
	async def reddit(self, ctx, subreddit = None, *, flags = None):
		"""Try to grab a random top post from the passed subreddit.
		
		Available flags:
		
		(no)image - to force (or prevent) an image result
		(no)video - to force (or prevent) a video result
		new       - to get the latest post instead of top
		
		e.g. To get the latest image post from r/Aww:
		$reddit r/Aww image new"""
		sub = self._verify_sub_name(subreddit)
		if not sub:
			return await ctx.send("You need to pass a valid subreddit name.")
		# Get our flags
		image = video = None
		sort = "top"
		if flags:
			flags = flags.lower()
			if "novideo" in flags:
				video = False
			elif "video" in flags:
				video = True
			if "noimage" in flags:
				image = False
			elif "image" in flags:
				image = True
			sort  = "new" if "new" in flags else "top"
		# Check if we're using top or new, and pipe the data
		# where it needs to go
		if sort == "top":
			await self.send_random_top_post(
				ctx,
				sub,
				image=image,
				video=video
			)
		elif sort == "new":
			# Get the last entry
			await self.send_newest_post(
				ctx,
				sub,
				image=image,
				video=video
			)

	'''@commands.command()
	async def beeple(self, ctx):
		"""A new image every day... for years."""
		await self.send_random_top_post(ctx,"beeple",image=True)'''
	
	@commands.command()
	async def macsetup(self, ctx):
		"""Feast your eyes upon these setups."""
		await self.send_random_top_post(ctx,"macsetups",image=True)
		
	@commands.command()
	async def pun(self, ctx):
		"""I don't know, don't ask..."""
		await self.send_random_top_post(ctx,"puns")
	
	@commands.command()
	async def carmod(self, ctx):
		"""Marvels of modern engineering."""
		await self.send_random_top_post(ctx,"Shitty_Car_Mods",image=True)
	
	@commands.command()
	async def battlestation(self, ctx):
		"""Let's look at some pretty stuff."""
		await self.send_random_top_post(ctx,"battlestations",image=True)
		
	@commands.command()
	async def shittybattlestation(self, ctx):
		"""Let's look at some shitty stuff."""
		await self.send_random_top_post(ctx,"shittybattlestations",image=True)

	@commands.command()
	async def dankmeme(self, ctx):
		"""Only the dankest."""
		await self.send_random_top_post(ctx,"dankmemes",image=True)

	@commands.command()
	async def cablefail(self, ctx):
		"""Might as well be a noose..."""
		await self.send_random_top_post(ctx,"cablefail",image=True)

	@commands.command()
	async def techsupport(self, ctx):
		"""Tech support irl."""
		await self.send_random_top_post(ctx,"techsupportgore",image=True)

	@commands.command()
	async def software(self, ctx):
		"""I uh... I wrote it myself."""
		await self.send_random_top_post(ctx,"softwaregore",image=True)

	@commands.command()
	async def meirl(self, ctx):
		"""Me in real life."""
		await self.send_random_top_post(ctx,"me_irl",image=True)

	@commands.command()
	async def starterpack(self, ctx):
		"""Starterpacks."""
		await self.send_random_top_post(ctx,"starterpacks",image=True)

	@commands.command()
	async def earthporn(self, ctx):
		"""Earth is good."""
		await self.send_random_top_post(ctx,"EarthPorn",image=True)
		
	@commands.command()
	async def wallpaper(self, ctx):
		"""Get something pretty to look at."""
		await self.send_random_top_post(ctx,"wallpapers",image=True)
		
	@commands.command()
	async def abandoned(self, ctx):
		"""Get something abandoned to look at."""
		await self.send_random_top_post(ctx,"abandonedporn",image=True)

	@commands.command()
	async def dragon(self, ctx):
		"""From the past - when great winged beasts soared the skies."""
		await self.send_random_top_post(ctx,"BeardedDragons",image=True)

	@commands.command()
	async def aww(self, ctx):
		"""Whenever you're down - uppify."""
		await self.send_random_top_post(ctx,"aww",image=True)
	
	@commands.command()
	async def randomdog(self, ctx):
		"""Bark if you know whassup."""
		await self.send_random_top_post(ctx,"dogpictures",image=True)
		
	@commands.command()
	async def randomcat(self, ctx):
		"""Meow."""
		await self.send_random_top_post(ctx,"cats",image=True)

	def _get_sub_link(self, sub_dict, name=None, suffix="", allow_over_18=False, preview=False):
		if not sub_dict.get("name_prefixed"):
			return "Unknown Subreddit"
		if not allow_over_18 and sub_dict.get("over_18"):
			# Don't create a link to this one
			return sub_dict["name_prefixed"]
		# Either not NSFW, or we allow that - link it
		return "[{}]({}https://www.reddit.com/{}{}{})".format(
			name or sub_dict["name_prefixed"],
			"" if preview else "<",
			sub_dict["name_prefixed"],
			suffix,
			"" if preview else ">"
		)

	async def _can_watch_sub_reply(self, ctx, is_owner=None):
		# Helper to check if watching subs is owner only, and if we're
		# owner.
		if self.settings.getGlobalStat("WatchedSubredditsOwnerOnly",True):
			if is_owner is None:
				# We need to figure out if we're the owner
				is_owner = Utils.is_owner(ctx)
			if not is_owner:
				# Not an owner when we need to be - inform the user
				if ctx.command:
					comm_name = "`{}{}`".format(ctx.prefix,ctx.command.name)
				else:
					comm_name = "That command"
				await ctx.send("{} is currently owner-only.".format(comm_name))
				return False
		# Either not owner-only, or we're an owner
		return True

	@commands.command()
	async def watchsub(self, ctx, subreddit_name = None, frequency_minutes = None, channel = None):
		"""Adds a watcher for the passed subreddit that checks at the passed frequency for new posts,
		and sends them in the passed channel (bot-admin only).
		
		Arguments:

		subreddit_name    - The subreddit or name to watch
		frequency_minutes - How long in minutes to wait between checks in increments of 60
							(reddit_loop_update_minutes in the settings_dict.json can override
							this)
							Minimum of 60 for admins/bot-admins (reddit_minimum_wait_minutes
							in the settings_dict.json can override this)
		channel           - The target text channel where the new posts will be sent"""
		if not await Utils.is_bot_admin_reply(ctx): return
		is_owner = Utils.is_owner(ctx)
		if not await self._can_watch_sub_reply(ctx,is_owner=is_owner): return

		# First check if we're currently rate limited and report that.
		if self.ratelimit_end > time.time():
			return await ctx.send("It looks like I'm rate limited. Please try again <t:{}:R>".format(
				math.ceil(self.ratelimit_end),
			))

		# Get our minimum wait time - set to the loop time if we're owner,
		# otherwise set to the non-owner minimum
		min_wait = self.loop_mins if is_owner else self.minimum_wait

		# Validate our vars if possible
		subreddit_name = self._verify_sub_name(subreddit_name)

		try:
			# Ensure we wait at least the minimum - whether owner or not
			frequency_minutes = max(min_wait,int(frequency_minutes))
			if frequency_minutes % self.loop_mins:
				# Round up to the next loop increment
				frequency_minutes += self.loop_mins - frequency_minutes % self.loop_mins
		except:
			frequency_minutes = None
		try:
			channel = DisplayName.channelForName(channel,ctx.guild)
		except:
			channel = None

		if any(x is None for x in (subreddit_name,frequency_minutes,channel)):
			return await ctx.send("Usage: `{}watchsub [subreddit_name] [frequency_minutes] [channel]`".format(ctx.prefix))

		# If we got here - we have a valid setting.  Let's get our other settings and see
		# if our subreddit_name matches any others - as we're just updating that one.
		subs = self.settings.getServerStat(ctx.guild,"WatchedSubreddits",{})
		if not is_owner and len(subs) >= self.maximum_subs:
			return await ctx.send("Only owners can add more than {:,} sub{}.  You're currently at {:,}.".format(
				self.maximum_subs,
				"" if self.maximum_subs == 1 else "s",
				len(subs)
			))
		# Make sure we can send messages in the target channel
		perms = channel.permissions_for(ctx.guild.me)
		can_send = True
		if hasattr(discord,"threads") and isinstance(channel,discord.threads.Thread):
			# We got a thread - make sure we can send messages there
			can_send = perms.send_messages_in_threads
		else:
			can_send = perms.send_messages
		if not can_send:
			return await ctx.send("I don't have permissions to send messages in that channel.")
		# Get the subreddit's name and ensure it exists by loading the about endpoint
		message = await ctx.send("Gathering info...")
		try:
			about = await self._get_sub_about(subreddit_name)
			subreddit_name = about["name"]
		except:
			return await message.edit(content="That subreddit may be private, or it doesn't exist.")
		allow_over_18 = self.settings.getServerStat(ctx.guild,"AllowNsfwWatchedSubreddits",False)
		if not allow_over_18 and about.get("over_18"):
			# We're trying to watch an NSFW subreddit, but haven't
			# allowed that yet.
			return await message.edit(
				content="Your current settings disallow watching NSFW subreddits.  " \
				"You can change that with the `{}watchsubnsfw` command".format(
					ctx.prefix
				)
			)
		name_lower = subreddit_name.lower()
		updating = name_lower in subs
		subs[name_lower] = {
			"name_prefixed":about["name_prefixed"],
			"name":subreddit_name,
			"frequency":frequency_minutes,
			"channel":channel.id,
			"over_18":about.get("over_18",False)
		}
		self.settings.setServerStat(ctx.guild,"WatchedSubreddits",subs)
		# We need to get our next run based on our initial
		# loop time and current time
		_,next_run = self._get_last_next_loop_time(
			start_time=self.first_loop,
			loop_mins=frequency_minutes
		)
		await message.edit(
			content="{0} watcher for {1} - will check every {2:,} minute{3}, and send new posts in {4}.\nNext run will happen <t:{5}> (<t:{5}:R>)".format(
				"Updated" if updating else "Created",
				self._get_sub_link(about),
				frequency_minutes,
				"" if frequency_minutes == 1 else "s",
				channel.mention,
				math.ceil(next_run)
			)
		)

	@commands.command()
	async def unwatchsub(self, ctx, subreddit_name = None):
		"""Removes the watcher for the passed subreddit if it exists (bot-admin only)."""
		if not await Utils.is_bot_admin_reply(ctx): return

		# Validate our vars if possible
		subreddit_name = self._verify_sub_name(subreddit_name)

		if subreddit_name is None:
			return await ctx.send("Usage: `{}unwatchsub [subreddit_name]`".format(ctx.prefix))
		
		# If we got here - we have a valid setting.  Let's get our other settings and see
		# if our subreddit_name matches any others - as we're just updating that one.
		subs = self.settings.getServerStat(ctx.guild,"WatchedSubreddits",{})
		removed = subs.pop(subreddit_name.lower(), None)
		# Only print we removed it if it was present in the watched subs list
		if removed:
			self.settings.setServerStat(ctx.guild,"WatchedSubreddits",subs)
			return await ctx.send("Removed watcher for {}.".format(
				self._get_sub_link(removed)
			))
		await ctx.send("Could not find watcher for {}.".format(subreddit_name))

	@commands.command()
	async def unwatchallsubs(self, ctx):
		"""Removes all watchers for all subreddits (bot-admin only)."""
		if not await Utils.is_bot_admin_reply(ctx): return

		subs = self.settings.getServerStat(ctx.guild,"WatchedSubreddits",{})
		self.settings.setServerStat(ctx.guild,"WatchedSubreddits",{})
		return await ctx.send("Removed {:,} subreddit watcher{}.".format(
			len(subs),
			"" if len(subs) == 1 else "s"
		))

	@commands.command()
	async def watchedsubs(self, ctx):
		"""Lists all watchers for all subreddits."""
		subs = self.settings.getServerStat(ctx.guild,"WatchedSubreddits",{})
		if not subs:
			required = "A bot owner" if self.settings.getGlobalStat("WatchedSubredditsOwnerOnly",True) else "An admin or bot-admin"
			return await ctx.send("No subreddits are being watched.  {} can add some with `{}watchsub`".format(required,ctx.prefix))
		# Get our boolean that determines whether we can watch NSFW subs
		allow_over_18 = self.settings.getServerStat(ctx.guild,"AllowNsfwWatchedSubreddits",False)
		# We got something here - let's generate a list
		items = []
		# Retain the next loop value in case it changes while parsing
		for i,x in enumerate(subs,start=1):
			# Get info for the next run from the cache
			key = "{}-{}".format(ctx.guild.id,x)
			# Ensure if our sub frequency is lower than our loop
			# we account for that and display accordingly
			sub_freq = subs[x]["frequency"]
			sub_freq = max(sub_freq,self.loop_mins)
			# Make sure it's a multiple of our loop_mins too
			if sub_freq % self.loop_mins:
				sub_freq = ((sub_freq // self.loop_mins) + 1) * self.loop_mins
			last_run = self.subreddit_cache.get(key,{}).get("scheduled")
			if last_run is None:
				# We need to get our next run based on our initial
				# loop time and current time
				_,next_run = self._get_last_next_loop_time(
					start_time=self.first_loop,
					loop_mins=sub_freq
				)
			else:
				# We got a last_run time - get our next run based
				# on that.
				next_run = math.ceil(sub_freq*60+last_run)
			over_18 = subs[x].get("over_18",False)
			if over_18:
				# Keep a placeholder, but explain why
				links = "`    Links:` `[ NOT SHOWN FOR NSFW SUBS ]`"
			else:
				# Set up our links
				hot = self._get_sub_link(subs[x],name="Hot")
				new = self._get_sub_link(subs[x],name="New",suffix="/new")
				top = self._get_sub_link(subs[x],name="Top",suffix="/top")
				links = "`    Links:` {}, {}, {}".format(hot,new,top)
			items.append({
				"name":"{}. {}{}".format(
					i,
					subs[x]["name_prefixed"],
					" (NSFW)" if subs[x].get("over_18") else ""
				),
				"value":"`Frequency:` Every {0:,} minute{1}\n" \
				        "`  Channel:` <#{2}>\n" \
						"` Next Run:` <t:{3}> (<t:{3}:R>){4}".format(
					sub_freq,
					"" if sub_freq == 1 else "s",
					subs[x]["channel"],
					math.ceil(next_run),
					"\n"+links if links else ""
				)
			})
		return await PickList.PagePicker(
			title="Current Subreddit Watchers ({:,} Total)".format(len(subs)),
			ctx=ctx,
			list=items
		).pick()

	@commands.command()
	async def watchsubnsfw(self, ctx, *, yes_no = None):
		"""Gets or sets whether watched subs allow NSFW content (bot-admin only)."""
		if not await Utils.is_bot_admin_reply(ctx): return

		await ctx.send(Utils.yes_no_setting(
			ctx,
			"NSFW posts in watched subreddits",
			"AllowNsfwWatchedSubreddits",
			yes_no,
			default=False
		))

	@commands.command()
	async def dmsubnsfw(self, ctx, *, yes_no = None):
		"""Gets or sets whether reddit commands in dm allow NSFW content (owner-only)."""
		if not await Utils.is_owner_reply(ctx): return

		await ctx.send(Utils.yes_no_setting(
			ctx,
			"NSFW subreddits in dms",
			"AllowNsfwSubredditsDm",
			yes_no,
			default=False,
			is_global=True
		))

	@commands.command()
	async def watchsubowneronly(self, ctx, *, yes_no = None):
		"""Gets or sets if the subreddit watching functions are owner-only (owner-only, ofc)."""
		if not await Utils.is_owner_reply(ctx): return

		await ctx.send(Utils.yes_no_setting(
			ctx,
			"Owner-only subreddit watching",
			"WatchedSubredditsOwnerOnly",
			yes_no,
			default=True,
			is_global=True
		))

	@commands.command(hidden=True,aliases=["testwatchsub"])
	async def watchsubtest(self, ctx, subreddit_name=None, limit=None, *, extras=""):
		"""Command to send an embed of the last submission(s) of the passed subreddit in the current channel (owner-only).
		
		The extras variable is a string that can contain any of the following:
		"ctx"     = don't pass the context object - forces an Embed instead of a PagePicker
		"message" = DO edit the "Sending specific post from X subreddit..." message
		"score"   = don't include the score and comment count in the footer"""
		if not await Utils.is_owner_reply(ctx): return

		full_url = None
		try:
			urls = Utils.get_urls(subreddit_name)
			if urls:
				# Got a direct link - use that
				full_url = self.re_comment_url.fullmatch(urls[0]).group("url")+".json"
		except:
			pass
		# Validate the name
		subreddit_name = self._verify_sub_name(subreddit_name)
		# Validate the limit
		if limit is None:
			limit = 1
		try:
			limit = min(self.post_limit,int(limit))
		except:
			limit = None
		if subreddit_name is None or limit is None:
			return await ctx.send("Usage: `{}watchsubtest [subreddit_name] [limit]`".format(ctx.prefix))
		# Get the last entry
		# Get the subreddit's name and ensure it exists by loading the about endpoint
		message = await ctx.send("Gathering info...")
		try:
			about = await self._get_sub_about(subreddit_name)
			subreddit_name = about["name"]
		except:
			return await message.edit(content="That subreddit may be private, or it doesn't exist.")
		# Get the last entries up to our limit
		data = await self._get_sub_data(subreddit_name,limit=limit,url_override=full_url)
		if not data:
			return await message.edit(content="No data was returned for that subreddit.")
		await message.edit(content="Sending {} from {}...".format(
			"specific post" if full_url else "the last {:,} post{}".format(
				len(data),
				"" if len(data) == 1 else "s"
			),
			about["name_prefixed"]
		))
		# We got data - let's have the bot send it in the current channel
		await self.send_posts(
			data,
			ctx,
			about=about,
			ctx=None if "ctx" in extras.lower() else ctx,
			score_comments="score" not in extras.lower(),
			message=message if "message" in extras.lower() else None
		)

	@commands.command(hidden=True,aliases=["redditmd"])
	async def redditmarkdown(self, ctx, *, markdown = None):
		"""Testing function to convert reddit markdown to discord markdown (owner-only)."""

		if not await Utils.is_owner_reply(ctx): return
		if markdown is None:
			return await ctx.send("Usage: `{}redditmarkdown [markdown]`".format(ctx.prefix))
		
		# Get the markdown
		md = self._process_markdown(markdown)
		print(("-"*10)+" Reddit Markdown Test "+("-"*10))
		print(md)
		print("-"*42)
		# Send an embed with the info
		try:
			await Message.EmbedText(
				title="Markdown Test",
				description=md,
				color=ctx.author
			).send(ctx)
		except Exception as e:
			await ctx.send("Something went wrong: {}".format(e))

	@commands.command(hidden=True,aliases=["ratelimited"])
	async def ratelimit(self, ctx, seconds=None):
		"""Testing function to impose a rate limit of the passed number of seconds (owner-only).
		If given a range of seconds (min-max) it will pick a random number between them.
		If run without any options it will list any current rate limit in effect."""

		if not await Utils.is_owner_reply(ctx): return
		if seconds is None:
			remain = math.ceil(self.ratelimit_end-time.time())
			if remain <= 0:
				return await ctx.send("There is no rate limit in effect currently.")
			return await ctx.send("We are rate limited for {:,} second{} - will expire <t:{}:R>".format(
				remain,
				"" if remain==1 else "s",
				math.ceil(self.ratelimit_end)
			))
		
		# Try to resolve the seconds value
		if "-" in seconds:
			try:
				v1,v2 = map(int,seconds.split("-"))
			except:
				return await ctx.send("Ranges must be formatted as min-max (i.e. 1-25).")
			# Generate our random ratelimit
			ratelimit = random.randint(
				min(v1,v2),
				max(v1,v2)
			)
		else:
			try:
				ratelimit = int(float(seconds))
			except:
				return await ctx.send("Seconds must be a valid integer.")
		self.ratelimit_end = time.time()+ratelimit
		if ratelimit <= 0:
			return await ctx.send("Rate limit removed.")
		await ctx.send("Rate limit imposed for {:,} second{} - will expire <t:{}:R>".format(
			ratelimit,
			"" if ratelimit==1 else "s",
			math.ceil(self.ratelimit_end)
		))
