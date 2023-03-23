import asyncio, discord, os, re, time
from   datetime import datetime
from   discord.ext import commands
from   Cogs import Utils, Message, PCPP, Nullify

def setup(bot):
	# Add the bot and deps
	settings = bot.get_cog("Settings")
	bot.add_cog(Server(bot, settings))

# This module sets/gets some server info

class Server(commands.Cog):

	# Init with the bot reference, and a reference to the settings var and xp var
	def __init__(self, bot, settings):
		self.bot = bot
		self.settings = settings
		# Regex for extracting urls from strings
		self.regex = re.compile(r"(http|ftp|https)://([\w_-]+(?:(?:\.[\w_-]+)+))([\w.,@?^=%&:/~+#-]*[\w@?^=%&/~+#-])?")
		self.loop_list = []
		global Utils, DisplayName
		Utils = self.bot.get_cog("Utils")
		DisplayName = self.bot.get_cog("DisplayName")

	def _is_submodule(self, parent, child):
		return parent == child or child.startswith(parent + ".")

	@commands.Cog.listener()
	async def on_unloaded_extension(self, ext):
		# Called to shut things down
		if not self._is_submodule(ext.__name__, self.__module__): return
		for task in self.loop_list:
			task.cancel()

	@commands.Cog.listener()
	async def on_loaded_extension(self, ext):
		# See if we were loaded
		if not self._is_submodule(ext.__name__, self.__module__): return
		self.bot.loop.create_task(self.start_loading())

	@commands.Cog.listener()	
	async def on_member_join(self, member):
		join_id = self.settings.getServerStat(member.guild,"JoinRole",None)
		if not join_id: return # Nothing to do
		join_role = DisplayName.roleForName(join_id,member.guild)
		if not join_role: return # Again, nothing to do
		# We have a role to apply - let's attempt to do that
		self.settings.role.add_roles(member,[join_role])

	async def start_loading(self):
		await self.bot.wait_until_ready()
		await self.bot.loop.run_in_executor(None, self.check_polls)

	def check_polls(self):
		# Check all polls - and start timers
		print("Checking polls...")
		t = time.time()
		for guild in self.bot.guilds:
			for poll in self.settings.getServerStat(guild, "Polls", []):
				self.loop_list.append(self.bot.loop.create_task(self.check_poll(guild,poll)))
		print("Polls checked - took {} seconds.".format(time.time() - t))

	async def check_poll(self, guild, poll):
		# Get our current task
		task = getattr(asyncio.Task,"current_task",asyncio.current_task)()
		# Get our current task's countdown
		count_down = int(poll["end"])-int(time.time())
		# Check if we have remaining time
		if count_down > 0: await asyncio.sleep(count_down)
		# We've waited long enough - let's remove our current task from the list
		if task in self.loop_list: self.loop_list.remove(task)
		# At this point - we need to recheck if our poll's task has already been removed
		# and if so, ignore it.  If not - we remove it, then tally the results.
		polls = self.settings.getServerStat(guild,"Polls",[])
		if not poll in polls: return # Not here - nothing to do.
		# We have a valid poll, let's remove it from the settings, and update stats.
		self.settings.setServerStat(guild,"Polls",[x for x in polls if x != poll])
		# Let's make sure the message still exists
		c,m = poll["message_ids"].split() # Assumes "channel_id message_id" string pair
		try: channel = guild.get_channel(int(c))
		except: channel = None
		if not channel: return # No channel - likely deleted.
		try: message = await channel.fetch_message(int(m))
		except: message = None
		if not message: return # No message - likely deleted.
		ctx = await self.bot.get_context(message)
		# Get the original embed
		if not message.embeds: return # None - bail.
		embed = message.embeds[0] # Get the first embed
		embed_dict = embed.to_dict()
		if not embed_dict.get("description"): return # Broken embed :(
		if not "color" in embed_dict:
			# Attempt to get the original poller's color
			try: embed_dict["color"] = guild.get_member(poll["author_id"])
			except: pass
		# Gather the valid reactions - then see what corresponds with the message
		valid_reactions = self.get_reactions(poll["options"])
		reactions = {}
		for reaction in message.reactions:
			if not reaction.emoji in valid_reactions: continue # Ignore if not valid
			# Keep a list of all non-bot users that reacted with this valid reaction
			reactions[reaction.emoji] = [user async for user in reaction.users() if not user.bot]
		# At this point, we have all the non-bot users that have reacted with all the valid
		# reactions.  We need to check if we omit any users that reacted to more than one.
		if not poll["allow_multiple"]:
			# Let's build a set of unique users first
			user_list = []
			for v in reactions.values(): user_list.extend(v)
			user_set = set(user_list)
			# Now we walk unique users and see if they show up in more than one list
			omit_users = [user for user in user_set if user_list.count(user) > 1]
			# Finally - we walk each reaction and strip the omitted users
			for reaction in reactions:
				reactions[reaction] = [user for user in reactions[reaction] if not user in omit_users]
		# Let's count each finalized reaction total and tally everything up
		totals = {}
		for reaction in reactions:
			totals[reaction] = len(reactions[reaction])
		total = sum((len(reactions[x]) for x in reactions))
		# Now that we have our totals - let's update the description
		desc_lines = embed_dict["description"].split("\n")
		# We can find out if we have a title by looking at the 6th item in desc_lines
		# and ensuring it's "" if it exists
		has_title = len(desc_lines)>5 and not desc_lines[5]
		# The title is at index 0
		desc_lines[0] = desc_lines[0].replace("New","Finished")
		# The time limit is at index 2
		desc_lines[2] = "Ended <t:{}>".format(poll["end"])
		# At this point - we see if we have 2 or more options - and tally up
		sort_lines = []
		if poll["options"] > 1:
			for i,r in enumerate(list(totals)[::-1]):
				test_line = " - ".join(desc_lines[-(i+1)].split(" - ")[1:])
				if total: sort_lines.append("{} - ({}/{}: {}%) {}".format(r,totals[r],total,self.get_perc(totals[r]/total*100),test_line))
				else: sort_lines.append("{} - (0/0: 0%) {}".format(r,test_line))
			# Remove the original lines
			desc_lines = desc_lines[:-poll["options"]]
		else: # Should just be thumbs up or thumbs down
			# Add a newline for padding
			desc_lines.append("")
			for r in totals:
				if total: sort_lines.append("{} - {}/{}: {}%".format(r,totals[r],total,self.get_perc(totals[r]/total*100)))
				else: sort_lines.append("{} - 0/0: 0%".format(r))
		# Sort our results by most votes
		desc_lines.extend(sorted(sort_lines,key=lambda x: (-int(x.replace("~","").split(": ")[1].split("%")[0]),x)))
		# Update the footer
		embed_dict["footer"] = {
			"text":embed_dict["footer"].get("text","").replace("can","could").replace("counts","counted").replace("react","reacted")
		}
		# Update the target embed
		embed_dict["description"] = "\n".join(desc_lines)
		await Message.Embed(**embed_dict).edit(ctx,message)
		# Check if we need to ping the original creator
		if poll.get("ping_reminder"):
			# Resolve the author
			try: author = guild.get_member(poll["author_id"])
			except: return
			# Send a reminder
			await channel.send("{} - your timed poll has ended!  You can view the results here:\nhttps://discord.com/channels/{}/{}/{}".format(
				author.mention,
				guild.id,
				channel.id,
				message.id
			),allowed_mentions=discord.AllowedMentions.all())

	def get_perc(self, value):
		# Helper to take a float and round to the nearest decimal if needed,
		# or to truncate to an int if possible.
		if value == int(value): # No rounding - drop the decimal
			return str(int(value))
		if value - int(value) > 0.5:
			return "~"+str(int(value+1))
		return "~"+str(int(value))

	def get_reactions(self, option_count = 0):
		return ("👍","👎") if option_count<2 else ["{}\N{COMBINING ENCLOSING KEYCAP}".format(i+1) if i<9 else "🔟" for i in range(min(option_count,10))]

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

	@commands.command(aliases=["vote"])
	async def poll(self, ctx, *, poll_options = None):
		"""Starts a poll - which can take a custom prompt/question, as well as one or up to 10 options.

		You can provide an optional poll prompt as your first option by ending it with a colon (:).

		Poll options are separated by commas - if only one option is present, the poll will use thumbs up/down reactions.
		If 2-10 options are present, the poll will use numbered reactions for each.

		You can add a time limit to the poll with t=WwDdHhMmSs where:
			w = Weeks
			d = Days
			h = Hours
			m = Minutes
			s = Seconds

		By default, users' votes in polls with time limits only count if they choose a single option.
		You can allow multiple choices by passing -multi or -multiple to the $poll command as well.
		Passing -r(emind) to a timed poll will have the bot ping the poll creator in the same channel where the poll was created when it is done.

		Note:  -multi(ple) is only interpreted if a t= time limit is set.

		If you need to use commas, =, -, or a colon in your prompt or options, you can use a backslash to escape them.

		Note:  A colon followed by / (for example, in a URL) will also not be interpreted as a prompt.
		       You can escape the first forward slash after your colon to have it interpreted (eg. some_prompt:\//option1,option2...)
			   For the sake of preserving emojis - the format <a:name:01234> is also reserved.
		
		Examples:
		- Thumbs up/down poll:
		    $poll Who likes pizza?
		- Multi-option poll:
		    $poll macOS, Windows, Linux
		- Thumbs up/down poll with a prompt:
		    $poll Days of the week:  Wednesday is the best
		- Multi-option poll with a prompt:
		    $poll Favorite day of the weekend?: Saturday, Sunday
		- Thumbs up/down poll using escaped comma:
		    $poll April\, May\, and June are the best months
		- Multi-option poll with prompt with escaped colon:
		    $poll Escaped\: Rest of Prompt: option 1, option 2, option 3
		- Multi-option poll with a 2 week, 15 hour, 30 second time limit:
		    $poll t=2w15h30s Blue, Purple, Yellow
		- Multi-option, 2 day poll that allows users to react multiple times:
		    $poll -multiple Fast, Medium, Slow t=2d
		"""

		if not poll_options: return await ctx.send("Usage: `{}poll (-mutli -remind t=)(prompt:)[option 1(, option 2, option 3...)]`".format(ctx.prefix))
		
		# Helper to replace escaped characters
		def replace_escaped(val,esc = ",:/=-"):
			for e in esc: val = val.replace("\\"+e,e)
			return val

		def get_seconds(time):
			allowed = {"w":604800,"d":86400,"h":3600,"m":60,"s":1}
			total_seconds = 0
			last_time = ""
			for char in time:
				# Check if we have a number
				if char.isdigit():
					last_time += char
					continue
				# Check if it's a valid suffix and we have a time so far
				if char.lower() in allowed and last_time:
					total_seconds += int(last_time)*allowed[char.lower()]
				last_time = ""
			# Check if we have any left - and add it
			if last_time: total_seconds += int(last_time) # Assume seconds at this point
			return total_seconds

		poll_options = poll_options.replace("\n"," ")
		desc = "**__New Poll by {}__**\n\n".format(ctx.author.mention)
		# Let's get any timestamps or -multi(ple) strings, and strip them out as needed.
		time_check = re.compile(r"(?i)-?t=(\d+w|\d+d|\d+h|\d+m|\d+s?)+")
		try: poll_time_str = time_check.search(poll_options).group(0)
		except: poll_time_str = ""
		poll_time = end_time = 0
		allow_multiple = ping_reminder = False
		if poll_time_str: # We have a time frame - let's strip - and then process it
			poll_options = re.sub(time_check,"",poll_options,count=1) # Only strip the first occurrence though
			poll_time = get_seconds(poll_time_str)
		if poll_time: # We got a valid time string - let's check for -multi(ple)
			end_time = int(time.time())+poll_time
			desc += "Ending <t:{}:R>\n\n".format(end_time)
			poll_list = poll_options.split()
			multi = next((x for x in poll_list if x.lower() in ("-m","-multi","-multiple")),None)
			if multi: # We got a hit - let's remove the first match
				allow_multiple = True
				poll_list.remove(multi)
			remind = multi = next((x for x in poll_list if x.lower() in ("-r","-remind","-remindme")),None)
			if remind: # Same as above
				ping_reminder = True
				poll_list.remove(remind)
			poll_options = " ".join(poll_list)
		# Let's strip by whitespace, and rejoin with single spaces
		poll_options = " ".join([x for x in poll_options.split() if x])
		# Now that we have our functional elements taken care of - we check for a title
		title_check = [x for x in re.split(r"(?<![\\<a]):(?![\/\d])",poll_options) if x]
		if len(title_check) > 1: # We have a valid title
			p_check = poll_options[len(title_check[0])+1:].strip()
			if p_check: # We have something left - parse
				# Add the title to our desc with escaped vars replaced
				desc += "{}:\n\n".format(replace_escaped(title_check[0]))
				# Update our poll options to skip the title
				poll_options = p_check
		# Let's see how many poll_options we have
		options = [replace_escaped(option.strip()) for option in re.split(r"(?<!\\),",poll_options) if option.strip()]
		if len(options) <= 10: # Have the right amount
			reactions = self.get_reactions(len(options))
			if len(options) == 1:
				desc += poll_options
			else:
				for i,x in enumerate(options):
					reactions.append("{}\N{COMBINING ENCLOSING KEYCAP}".format(i+1) if i < 9 else "🔟")
					desc += "{} - {}\n".format(reactions[i],x.strip())
		else:
			return await ctx.send("Polls max out at 10 options.")
		# Check for any image attachments or embeds in the source message
		image = None
		if ctx.message.attachments:
			# We have some attachments to work through
			for a in ctx.message.attachments:
				# Add each attachment by name as a link to its own url
				if not a.filename.lower().endswith((".jpg",".jpeg",".png",".gif")): continue
				# We got the first image in the attachment list - set it
				image = a.url
				break
		if image is None and ctx.message.embeds:
			# We have embeds to look at too, and we haven't set an image yet
			for e in ctx.message.embeds:
				d = e.to_dict()
				i = d.get("thumbnail",d.get("video",d.get("image",{}))).get("url",None)
				if not i: continue
				image = i
				break
		# Remove the original message first
		try: await ctx.message.delete()
		except: pass # Maybe we don't have perms?  Ignore and continue
		message = await Message.Embed(
			description=desc,
			color=ctx.author,
			thumbnail=Utils.get_avatar(ctx.author),
			image=image,
			footer=None if not poll_time else "You can vote for multiple items" if allow_multiple else "Your vote only counts if you react once."
		).send(ctx)
		# Check if we have a timer
		if poll_time > 0:
			# Build our task - and add it to the servers Polls list
			poll_task = {
				"author_id": ctx.author.id,
				"message_ids": "{} {}".format(message.channel.id,message.id),
				"options": len(options),
				"allow_multiple": allow_multiple,
				"ping_reminder": ping_reminder,
				"end": end_time
			}
			polls = self.settings.getServerStat(ctx.guild,"Polls",[])
			polls.append(poll_task)
			self.settings.setServerStat(ctx.guild,"Polls",polls)
			# Add it to the task queue
			self.loop_list.append(self.bot.loop.create_task(self.check_poll(ctx.guild, poll_task)))
		# Add our poll reactions
		for r in reactions:
			await message.add_reaction(r)

	@commands.command(aliases=["pollend","epoll","endp","endvote","endv"])
	async def endpoll(self, ctx, *, message_url = None):
		"""Ends the poll that resides at the passed message url.  Must be either the original poll author, or a bot-admin."""
		if not message_url: return await ctx.send("Usage: `{}endpoll [message_url]`".format(ctx.prefix))
		# We are setting a message - let's split the url and get the last 2 integers - then save them.
		polls = self.settings.getServerStat(ctx.guild,"Polls",[])
		if not polls: return await ctx.send("I'm not currently watching any polls.")
		parts = [x for x in message_url.replace("/"," ").split() if len(x)]
		try: channel,message = [int(x) for x in parts[-2:]]
		except: return await ctx.send("Improperly formatted message url!")
		check_string = "{} {}".format(channel,message)
		poll = next((x for x in polls if x.get("message_ids")==check_string),None)
		if not poll: return await ctx.send("I'm not currently watching a poll attached to that message.")
		# We have a poll - let's see if we're either the author - or a bot-admin
		if not ctx.author.id == poll.get("author_id") and not Utils.is_bot_admin(ctx):
			return await ctx.send("You can only end your own polls.")
		# We're the author - or at least have authorization to end it.
		# Let's change the end time and set a timer for it.
		poll["end"] = int(time.time())
		# Make sure we save our changes - or else the original will also trigger edits
		self.settings.setServerStat(ctx.guild,"Polls",polls)
		# Add our adjusted poll to the task list
		self.loop_list.append(self.bot.loop.create_task(self.check_poll(ctx.guild, poll)))
		await ctx.send("Poll has ended.")

	@commands.command()
	async def setjoinrole(self, ctx, *, role = None):
		"""Sets the role to apply to each new user that joins (admin only)."""
		if not await Utils.is_admin_reply(ctx): return
		if role is None:
			self.settings.setServerStat(ctx.guild, "JoinRole", None)
			return await ctx.send("New users will **not** be given a join role.")
		roleName = role
		role = DisplayName.roleForName(roleName, ctx.guild)
		if not role:
			return await ctx.send("I couldn't find *{}*...".format(Nullify.escape_all(roleName)))
		self.settings.setServerStat(ctx.guild, "JoinRole", role.id)
		await ctx.send("New users will be given **{}** when joining.".format(Nullify.escape_all(role.name)))

	@commands.command(aliases=["joinrole"])
	async def getjoinrole(self, ctx):
		"""Gets the role applied to each new user that joins (admin only)."""
		if not await Utils.is_admin_reply(ctx): return
		join_id = self.settings.getServerStat(ctx.guild, "JoinRole", None)
		if join_id is None:
			# No join setup
			return await ctx.send("There is **no** join role set.")
		join_role = DisplayName.roleForName(join_id, ctx.guild)
		if join_role is None:
			# Not a role anymore
			return await ctx.send("The join role with id {} no longer exists.".format(join_id))
		await ctx.send("New users will be given **{}** when joining.".format(Nullify.escape_all(join_role.name)))
		
	@commands.command(pass_context=True)
	async def setprefix(self, ctx, *, prefix : str = None):
		"""Sets the bot's prefix (bot-admin only)."""
		if not await Utils.is_bot_admin_reply(ctx): return
		# We're admin
		if not prefix:
			self.settings.setServerStat(ctx.guild, "Prefix", None)
			msg = 'Custom server prefix *removed*.'
		elif prefix in ['@everyone','@here']:
			return await ctx.send("Yeah, that'd get annoying *reaaaal* fast.  Try another prefix.")
		else:
			self.settings.setServerStat(ctx.guild, "Prefix", prefix)
			msg = 'Custom server prefix is now: {}'.format(prefix)
		await ctx.send(msg)

	@commands.command(pass_context=True)
	async def getprefix(self, ctx):
		"""Output's the server's prefix - custom or otherwise."""
		# Get the current prefix
		prefix = await self.bot.command_prefix(self.bot, ctx.message)
		prefixlist = ", ".join([x for x in prefix if not x == "<@!{}> ".format(self.bot.user.id)])
		msg = 'Prefix{}: {}'.format("es are" if len(prefix) > 1 else " is",prefixlist)
		await ctx.send(msg)
	
	@commands.command(pass_context=True)
	async def autopcpp(self, ctx, *, setting : str = None):
		"""Sets the bot's auto-pcpartpicker markdown if found in messages (admin-only). Setting can be normal, md, mdblock, bold, bolditalic, or nothing."""
		if not await Utils.is_admin_reply(ctx): return
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
		await ctx.send(msg)

	@commands.command(pass_context=True)
	async def setinfo(self, ctx, *, word : str = None):
		"""Sets the server info (bot-admin only)."""
		if not await Utils.is_bot_admin_reply(ctx): return
		# We're admin
		word = None if not word else word
		self.settings.setServerStat(ctx.guild,"Info",word)
		msg = "Server info *{}*.".format("updated" if word else "removed")
		await ctx.send(msg)

	@commands.command(pass_context=True)
	async def info(self, ctx):
		"""Displays the server info if any."""
		serverInfo = self.settings.getServerStat(ctx.guild, "Info")
		msg = 'I have no info on *{}* yet.'.format(ctx.guild.name)
		if serverInfo:
			msg = '*{}*:\n\n{}'.format(ctx.guild.name, serverInfo)
		await ctx.send(Utils.suppressed(ctx,msg))

	@commands.command(pass_context=True)
	async def dumpservers(self, ctx):
		"""Dumps a timpestamped list of servers into the same directory as the bot (owner only)."""
		if not await Utils.is_owner_reply(ctx): return
		timeStamp = datetime.today().strftime("%Y-%m-%d %H.%M")
		serverFile = 'ServerList-{}.txt'.format(timeStamp)
		message = await ctx.author.send('Saving server list to *{}*...'.format(serverFile))
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
		await ctx.author.send(file=discord.File(serverFile))
		await message.edit(content='Uploaded *{}!*'.format(serverFile))
		os.remove(serverFile)

	@commands.command(pass_context=True)
	async def leaveserver(self, ctx, *, targetServer = None):
		"""Leaves a server - can take a name or id (owner only)."""
		if not await Utils.is_owner_reply(ctx): return
		if targetServer == None:
			# No server passed
			msg = 'Usage: `{}leaveserver [id/name]`'.format(ctx.prefix)
			return await ctx.send(msg)
		# Check id first, then name
		guild = next((x for x in self.bot.guilds if str(x.id) == str(targetServer)),None)
		if not guild:
			guild = next((x for x in self.bot.guilds if x.name.lower() == targetServer.lower()),None)
		if guild:
			await guild.leave()
			try:
				await ctx.send("Alright - I left that server.")
			except:
				pass
			return
		await ctx.send("I couldn't find that server.")
