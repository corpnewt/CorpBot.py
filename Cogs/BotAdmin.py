import discord, re, random, time
from   operator import itemgetter
from   discord.ext import commands
from   Cogs import Utils, DisplayName, Message, PickList

def setup(bot):
	# Add the bot and deps
	settings = bot.get_cog("Settings")
	bot.add_cog(BotAdmin(bot, settings))

class BotAdmin(commands.Cog):

	# Init with the bot reference, and a reference to the settings var
	def __init__(self, bot, settings):
		self.bot = bot
		self.settings = settings
		self.dregex =  re.compile(r"(?i)(discord(\.gg|app\.com)\/)(?!attachments)([^\s]+)")
		self.mention_re = re.compile(r"<?@?!?[0-9]{17,21}>?")
		self.removal = re.compile(r"(?i)-?r(em(ove|oval)?)?=\d+")
		self.max_last = 50 # Semi-arbitrary limit for the number of resolved last=[time] members
		global Utils, DisplayName
		Utils = self.bot.get_cog("Utils")
		DisplayName = self.bot.get_cog("DisplayName")

	def _is_submodule(self, parent, child):
		return parent == child or child.startswith(parent + ".")

	@commands.Cog.listener()
	async def on_loaded_extension(self, ext):
		# See if we were loaded
		if not self._is_submodule(ext.__name__, self.__module__):
			return
		await self.bot.wait_until_ready()
		if not self.settings: return # No settings to check
		print("Verifying ignore lists...")
		t = time.time()
		updated = []
		for guild in self.bot.guilds:
			old_ignore = self.settings.getServerStat(guild,"IgnoredUsers",[])
			if old_ignore and not all((isinstance(x,str) for x in old_ignore)):
				# We have a list - and not all elements are strings.
				updated.append(guild)
				# First we walk all elements and pull the ID values out of the dicts
				new_ignore = [x if isinstance(x,str) else str(x.get("ID",0)) for x in old_ignore if isinstance(x,(str,dict))]
				# Then we gather all valid elments and reset the settings
				self.settings.setServerStat(guild,"IgnoredUsers",[x for x in new_ignore if x])
		print("Ignore list verified - {:,} guild{} updated - took {} seconds.".format(len(updated),"" if len(updated)==1 else "s",time.time()-t))

	async def message_edit(self, before_message, message):
		# Pipe the edit into our message func to ignore if needed
		return await self.message(message)
		
	async def message(self, message):
		if message.author.bot: return {} # Just bail
		ctx = await self.bot.get_context(message)
		# Save our delete value based on whether or not we have an invite, and are looking for one
		# Should only affect non-(bot-)admin users
		is_admin = Utils.is_bot_admin(ctx)
		delete = False if is_admin else self.dregex.search(message.content) and self.settings.getServerStat(ctx.guild,"RemoveInviteLinks",False)
		ignore = False
		if not Utils.is_owner(ctx): # Only check for ignoring if we're not owner - never ignore the owners
			if self.settings.getGlobalStat("OwnerLock",False):
				ignore = True # Owner locked - ignore everyone else
			elif not is_admin: # Check if admin locked or ignored
				ignore = self.settings.getServerStat(ctx.guild,"AdminLock",False) or str(ctx.author.id) in self.settings.getServerStat(ctx.guild,"IgnoredUsers",[])
		return {"Ignore":ignore,"Delete":delete} # Return our ignore and delete status

	@commands.command()
	async def removeinvitelinks(self, ctx, *, yes_no = None):
		"""Enables/Disables auto-deleting discord invite links in chat (bot-admin only)."""
		if not await Utils.is_bot_admin_reply(ctx): return
		await ctx.send(Utils.yes_no_setting(ctx,"Remove discord invite links","RemoveInviteLinks",yes_no))

	@commands.command()
	async def setuserparts(self, ctx, member : discord.Member = None, *, parts : str = None):
		"""Set another user's parts list (owner only)."""
		# Only allow owner
		isOwner = self.settings.isOwner(ctx.author)
		if isOwner == None:
			msg = 'I have not been claimed, *yet*.'
			return await ctx.send(msg)
		elif isOwner == False:
			msg = 'You are not the *true* owner of me.  Only the rightful owner can use this command.'
			return await ctx.send(msg)
			
		if member == None:
			msg = 'Usage: `{}setuserparts [member] "[parts text]"`'.format(ctx.prefix)
			return await ctx.send(msg)

		if type(member) is str:
			try:
				member = discord.utils.get(ctx.guild.members, name=member)
			except:
				return await ctx.send("That member does not exist")

		if not parts:
			parts = ""
			
		self.settings.setGlobalUserStat(member, "Parts", parts)
		msg = '*{}\'s* parts have been set to:\n{}'.format(DisplayName.name(member), parts)
		await ctx.send(Utils.suppressed(ctx,msg))
		
	@setuserparts.error
	async def setuserparts_error(self, error, ctx):
		# do stuff
		msg = 'setuserparts Error: {}'.format(error)
		await ctx.send(msg)

	@commands.command()
	async def ignore(self, ctx, *, member = None):
		"""Adds a member to the bot's "ignore" list (bot-admin only)."""
		if not await Utils.is_bot_admin_reply(ctx): return
		if not member: return await ctx.send("Usage: `{}ignore [member]`".format(ctx.prefix))

		if type(member) is str:
			memberName = member
			member = DisplayName.memberForName(memberName, ctx.guild)
			if not member: return await ctx.send(Utils.suppressed(ctx,"I couldn't find *{}*...".format(memberName)))

		ignoreList = self.settings.getServerStat(ctx.guild,"IgnoredUsers",[])
		if str(member.id) in ignoreList: return await ctx.send("*{}* is already being ignored.".format(DisplayName.name(member)))
		ignoreList.append(str(member.id))
		self.settings.setServerStat(ctx.guild,"IgnoredUsers",ignoreList)
		await ctx.send('*{}* is now being ignored.'.format(DisplayName.name(member)))


	@commands.command()
	async def listen(self, ctx, *, member = None):
		"""Removes a member from the bot's "ignore" list (bot-admin only)."""
		if not await Utils.is_bot_admin_reply(ctx): return
		if not member: return await ctx.send("Usage: `{}listen [member]`".format(ctx.prefix))

		if type(member) is str:
			memberName = member
			member = DisplayName.memberForName(memberName, ctx.guild)
			if not member: return await ctx.send(Utils.suppressed(ctx,"I couldn't find *{}*...".format(memberName)))

		ignoreList = self.settings.getServerStat(ctx.guild,"IgnoredUsers",[])
		if not str(member.id) in ignoreList: return await ctx.send("*{}* wasn't being ignored...".format(DisplayName.name(member)))
		self.settings.setServerStat(ctx.guild,"IgnoredUsers",[x for x in ignoreList if x != str(member.id)])
		await ctx.send("*{}* is no longer being ignored.".format(DisplayName.name(member)))


	@commands.command()
	async def listenall(self,ctx):
		"""Clears the bot's ignore list (bot-admin only)."""
		if not await Utils.is_bot_admin_reply(ctx): return

		ignore_list = self.settings.getServerStat(ctx.guild,"IgnoredUsers",[])
		if not ignore_list: return await ctx.send("I'm not currently ignoring anyone.")

		self.settings.setServerStat(ctx.guild,"IgnoredUsers",[])
		return await ctx.send("*{:,}* user{} no longer being ignored.".format(len(ignore_list)," is" if len(ignore_list)==1 else "s are"))

	@commands.command()
	async def ignored(self, ctx):
		"""Lists the users currently being ignored."""
		ignoreList = [ctx.guild.get_member(int(x)) for x in self.settings.getServerStat(ctx.guild,"IgnoredUsers",[])]
		ignoreList = sorted([x for x in ignoreList if x],key=lambda x:x.name.lower()) # Skip all None values
		if not ignoreList: return await ctx.send("I'm not currently ignoring anyone.")
		desc = "\n".join(["{}. {} ({})".format(i,Utils.suppressed(ctx,str(x)),x.id) for i,x in enumerate(ignoreList,start=1)])
		return await PickList.PagePicker(
			title="Ignored Users ({:,} total)".format(len(ignoreList)),
			description=desc,
			ctx=ctx
		).pick()


	def get_seconds(self, time_string=None):
		if not isinstance(time_string,str): return 0
		allowed = {"w":604800,"d":86400,"h":3600,"m":60,"s":1}
		total_seconds = 0
		last_time = ""
		for char in time_string:
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

	
	async def kick_ban(self, ctx, members_and_reason = None, command_name = "kick"):
		# Helper method to handle the lifting for kick and ban
		if not await Utils.is_bot_admin_reply(ctx): return
		if not members_and_reason:
			return await ctx.send('Usage: `{}{} [space delimited member mention/id] [reason]`'.format(ctx.prefix, command_name))
		is_admin = Utils.is_admin(ctx)
		is_server_owner = False if not ctx.guild else ctx.guild.owner.id == ctx.author.id
		def member_exception(m):
			# Helper to check if this member cannot be banned/kicked
			if not isinstance(m,discord.Member):
				# Only check members - discord.User isn't in the server,
				# so they have no reason to be excluded
				return False
			if m.id == self.bot.user.id or m.id == ctx.author.id:
				# Can't ban/kick the bot or ourselves
				return True
			if is_server_owner:
				# The server owner should be able to ban/kick anyone - no exception
				return False
			if is_admin and not Utils.is_admin(ctx,m):
				# Admins can ban anyone who isn't admin
				return False
			if Utils.is_bot_admin(ctx,m):
				# Can't ban other bot-admins
				return True
			return False
		# Force a mention - we don't want any ambiguity
		args = members_and_reason.split()
		# Get our list of targets
		targets = []
		missed = []
		unable = []
		skipped = []
		last = []
		reason = ""
		days = self.settings.getServerStat(ctx.guild,"BanMessageRemoveDays",1) if command_name.lower() in ("ban","klean") else None
		try: days = int(days)
		except: days = None
		footer = "Message Removal: {:,} day{}".format(days,"" if days==1 else "s") if command_name.lower() in ("ban","klean") else None
		for index,item in enumerate(args):
			if self.mention_re.fullmatch(item): # Check if it's a mention
				# Resolve the member
				mem_id = int(re.sub(r'\W+', '', item))
				member = ctx.guild.get_member(mem_id)
				if member is None and command_name.lower() in ("ban","unban","klean"): # Didn't get a valid member, let's allow a pre-ban/unban if we can resolve them
					try: member = await self.bot.fetch_user(mem_id)
					except: pass
				# If we have an invalid mention, save it to report later
				if member is None:
					missed.append(str(mem_id))
					continue
				# Let's check if we have a valid member and make sure it's not:
				# 1. The bot, 2. The command caller, 3. Another bot-admin/admin
				if member_exception(member):
					unable.append(member.mention)
					continue
				if not member in targets: targets.append(member) # Only add them if we don't already have them
			else:
				# Check for the last=timestamp keyword - and append matching valid members
				if item.lower().startswith("last="):
					# Check the timestamp
					seconds = self.get_seconds(item.split("=")[-1])
					if seconds: # We got a valid time - let's walk the users
						t = time.time()
						for member in ctx.guild.members:
							if member.joined_at and t-member.joined_at.timestamp() <= seconds:
								# Check if we *can* kick/ban them first
								if member_exception(member):
									unable.append(str(member))
									continue
								# Check our counter
								if len(last) >= self.max_last:
									skipped.append(member)
								else:
									if not member in last: last.append(member)
									if not member in targets: targets.append(member)
					continue
				# Check if we're banning - and if so, check the rest of the args for `-r=#`
				# then apply that override and remove from the reason
				if command_name.lower() in ("ban","klean"):
					for i,x in enumerate(args[index:]):
						if self.removal.match(x):
							try:
								days = int(x.split("=")[-1])
								assert 0<=days<8
							except:
								continue
							args.pop(index+i)
							footer="Message Removal Override: {:,} day{}".format(days,"" if days==1 else "s")
							break
					# Bail if we don't have any args left for a reason
					if index >= len(args): break
				# Not a mention - must be the reason, dump the rest of the items into a string
				# separated by a space
				reason = " ".join(args[index:])
				break
		reason = reason if len(reason) else "No reason provided."
		if not len(targets):
			msg = "**With reason:**\n\n{}{}{}{}".format(
				reason,
				"" if not len(missed) else "\n\n**Unmatched ID{}:**\n\n{}".format("" if len(missed) == 1 else "s", "\n".join(missed)),
				"" if not len(unable) else "\n\n**Unable to {}:**\n\n{}".format(command_name,"\n".join(unable)),
				"" if not len(skipped) else "\n\n{:,} skipped - can only {} {:,} with last keyword".format(len(skipped),command_name,self.max_last)
			)
			return await Message.EmbedText(title="No valid members passed!",description=msg,color=ctx.author,footer=footer).send(ctx)
		# We should have a list of targets, and the reason - let's list them for confirmation
		# then generate a 4-digit confirmation code that the original requestor needs to confirm
		# in order to follow through
		confirmation_code = "".join([str(random.randint(0,9)) for x in range(4)])
		msg = "**To {} the following {}:**\n\n{}\n\n**With reason:**\n\n\"{}\"\n\n**Please type:**\n\n`{}`{}{}{}".format(
			command_name,
			"member" if len(targets) == 1 else "{:,} members".format(len(targets)),
			"\n".join([str(x) for x in targets]),
			reason if len(reason) else "None",
			confirmation_code,
			"" if not len(missed) else "\n\n**Unmatched ID{}:**\n\n{}".format("" if len(missed) == 1 else "s", "\n".join(missed)),
			"" if not len(unable) else "\n\n**Unable to {}:**\n\n{}".format(command_name,"\n".join(unable)),
			"" if not len(skipped) else "\n\n**{:,} skipped** - can only {} {:,} with `last=` keyword".format(len(skipped),command_name,self.max_last)
			)
		confirmation_message = await Message.EmbedText(title="{} Confirmation".format(command_name.capitalize()),description=msg,color=ctx.author,footer=footer).send(ctx)
		def check_confirmation(message):
			return message.channel == ctx.channel and ctx.author == message.author # Just making sure it's the same user/channel
		try: confirmation_user = await self.bot.wait_for('message', timeout=60, check=check_confirmation)
		except: confirmation_user = ""
		# Delete the confirmation message
		await confirmation_message.delete()
		# Verify the confirmation
		if getattr(confirmation_user,"content",None) != confirmation_code: return await ctx.send("{} cancelled!".format(command_name.capitalize()))
		# We got the authorization!
		message = await Message.EmbedText(
			title="{}ing...".format(
				"Bann" if command_name.lower() == "ban" else "Unbann" if command_name.lower() == "unban" else command_name.capitalize()
			),color=ctx.author,footer=footer
		).send(ctx)
		canned = []
		cant = []
		command = {
			"ban":(ctx.guild.ban,),
			"kick":(ctx.guild.kick,),
			"unban":(ctx.guild.unban,),
			"klean":(ctx.guild.ban,ctx.guild.unban)
		}.get(command_name.lower(),ctx.guild.kick)
		for c in command:
			for target in targets:
				try:
					args = {"reason":"{}{}: {}".format(
						"(Klean) " if command_name.lower() == "klean" else "",
						ctx.author,
						reason
					)}
					if days is not None and c == ctx.guild.ban: args["delete_message_seconds"] = days * 86400 # Get the number of seconds per the day count
					await c(target,**args)
					if not target in canned: # Avoid double adding
						canned.append(target)
				except Exception as e:
					print(e)
					if not target in cant:
						cant.append(target)
		# Make sure any that showed up in cant override those in canned
		canned = [x for x in canned if not x in cant]
		msg = ""
		if len(canned):
			msg += "**I was ABLE to {}:**\n\n{}\n\n".format(command_name,"\n".join([str(x) for x in canned]))
		if len(cant):
			msg += "**I was UNABLE to {}:**\n\n{}\n\n".format(command_name,"\n".join([str(x) for x in cant]))
		await Message.EmbedText(title="{} Results".format(command_name.capitalize()),description=msg,footer=footer).edit(ctx,message)

	@commands.command(aliases=["yeet"])
	async def kick(self, ctx, *, members = None, reason = None):
		"""Kicks the passed members for the specified reason.
		All kick targets must be mentions or ids to avoid ambiguity (bot-admin only).

		eg:  $kick @user1#1234 @user2#5678 @user3#9012 for spamming

		Accepts last=[time] to kick all valid members that joined in that time (up to 50).
		The [time] format allows for w=Weeks, d=Days, h=Hours, m=Minutes, s=Seconds.
		
		eg:  $kick last=10m30s raid"""
		await self.kick_ban(ctx,members,"kick")
		
		
	@commands.command(aliases=["yote","bean"])
	async def ban(self, ctx, *, members = None, reason = None):
		"""Bans the passed members for the specified reason.
		All ban targets must be mentions or ids to avoid ambiguity (bot-admin only).
		
		eg:  $ban @user1#1234 @user2#5678 @user3#9012 for spamming
		
		Accepts r=#, rem=#, remove=# or removal=# (optionally prefixed with -) within the reason to specify the number of days worth of the banned users' messages to remove.
		This is limited to 0-7 days, and will override the value set by the rembanmessages command.

		eg:  $ban @user1#1234 @user2#5678 @user3#9012 for spamming -rem=5

		Accepts last=[time] to kick all valid members that joined in that time (up to 50).
		The [time] format allows for w=Weeks, d=Days, h=Hours, m=Minutes, s=Seconds.

		eg:  $ban last=10m30s raid"""
		await self.kick_ban(ctx,members,"ban")

	@commands.command(aliases=["scam"])
	async def klean(self, ctx, *, members = None, reason = None):
		"""Bans the passed members for the specified reason, then unbans them in order to remove messages without permanently banning the account.
		All klean targets must be mentions or ids to avoid ambiguity (bot-admin only).
		
		eg:  $klean @user1#1234 @user2#5678 @user3#9012 for spamming
		
		Accepts r=#, rem=#, remove=# or removal=# (optionally prefixed with -) within the reason to specify the number of days worth of the kleaned users' messages to remove.
		This is limited to 0-7 days, and will override the value set by the rembanmessages command.

		eg:  $klean @user1#1234 @user2#5678 @user3#9012 for spamming -rem=5

		Accepts last=[time] to kick all valid members that joined in that time (up to 50).
		The [time] format allows for w=Weeks, d=Days, h=Hours, m=Minutes, s=Seconds.

		eg:  $klean last=10m30s raid"""
		await self.kick_ban(ctx,members,"klean")

	@commands.command()
	async def unban(self, ctx, *, members = None, reason = None):
		"""Unbans the passed members for the specified reason.
		All unban targets must be mentions or ids to avoid ambiguity (bot-admin only).
		
		eg:  $unban @user1#1234 @user2#5678 @user3#9012 because we're nice"""
		await self.kick_ban(ctx,members,"unban")

	@commands.command()
	async def banned(self, ctx, *, user_id = None):
		"""Queries the guild's ban list for the passed user id and responds with whether they've been banned and the reason.
		Use with no user_id to show all bans and reasons (bot-admin only)."""
		if not await Utils.is_bot_admin_reply(ctx): return

		try: all_bans = [entry async for entry in ctx.guild.bans()]
		except:
			try: all_bans = await ctx.guild.bans()
			except: return await ctx.send("I couldn't get the ban list :(")
		
		if not len(all_bans): return await Message.EmbedText(title="Ban List",description="No bans found",color=ctx.author).send(ctx)

		orig_user = user_id
		try: user_id = int(user_id) if user_id != None else None
		except: user_id = -1 # Use -1 to indicate unresolved

		entries = []
		for i,ban in enumerate(all_bans,start=1):
			entries.append({"name":"{}. {} ({})".format(i,ban.user,ban.user.id),"value":ban.reason if ban.reason else "No reason provided"})
			if user_id != None and user_id == ban.user.id:
				# Got a match - display it
				return await Message.Embed(
					title="Ban Found For {}".format(user_id),
					fields=[entries[-1]], # Send the last found entry
					color=ctx.author
				).send(ctx)
		if orig_user is None:
			# Just passed None - show the whole ban list
			return await PickList.PagePicker(title="Ban List ({:,} total)".format(len(entries)),list=entries,ctx=ctx).pick()
		# We searched for something and didn't find it
		return await Message.Embed(title="Ban List ({:,} total)".format(len(entries)),description="No match found for '{}'.".format(orig_user),color=ctx.author).send(ctx)

	@commands.command()
	async def rembanmessages(self, ctx, number_of_days = None):
		"""Gets or sets the default number of days worth of messages to remove when banning a user.  Must be between 0-7 and uses a default of 1 (bot-admin only)."""
		if not await Utils.is_bot_admin_reply(ctx): return
		if number_of_days == None: # No setting passed, just output the current
			days = self.settings.getServerStat(ctx.guild,"BanMessageRemoveDays",1)
			return await ctx.send("Banning a user will remove {:,} day{} worth of messages.".format(days,"" if days==1 else "s"))
		# Try to cast the days as an int - and ensure they're between 0 and 7
		try:
			days = int(number_of_days)
			assert 0<=days<8
		except:
			return await ctx.send("Number of days must be an integer between 0 and 7!")
		# At this point, we should have the default number of days - let's tell the user!
		self.settings.setServerStat(ctx.guild,"BanMessageRemoveDays",days)
		return await ctx.send("Banning a user will now remove {:,} day{} worth of messages.".format(days,"" if days==1 else "s"))
