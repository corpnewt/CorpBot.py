import asyncio, discord, re, random
from   operator import itemgetter
from   discord.ext import commands
from   Cogs import Utils, DisplayName, Message

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
		self.mention_re = re.compile(r"\<\@!{0,1}[0-9]+\>")
		global Utils, DisplayName
		Utils = self.bot.get_cog("Utils")
		DisplayName = self.bot.get_cog("DisplayName")

	async def message(self, message):
		# Check for discord invite links and remove them if found - per server settings
		if not self.dregex.search(message.content): return None # No invite in the passed message - nothing to do
		# Got an invite - let's see if we care
		if not self.settings.getServerStat(message.guild,"RemoveInviteLinks",False): return None # We don't care
		# We *do* care, let's see if the author is admin/bot-admin as they'd have power to post invites
		ctx = await self.bot.get_context(message)
		if Utils.is_bot_admin(ctx): return None # We are immune!
		# At this point - we need to delete the message
		return { 'Ignore' : True, 'Delete' : True}

	@commands.command(pass_context=True)
	async def removeinvitelinks(self, ctx, *, yes_no = None):
		"""Enables/Disables auto-deleting discord invite links in chat (bot-admin only)."""
		if not await Utils.is_bot_admin_reply(ctx): return
		await ctx.send(Utils.yes_no_setting(ctx,"Remove discord invite links","RemoveInviteLinks",yes_no))

	@commands.command(pass_context=True)
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

	@commands.command(pass_context=True)
	async def ignore(self, ctx, *, member = None):
		"""Adds a member to the bot's "ignore" list (bot-admin only)."""
		if not await Utils.is_bot_admin_reply(ctx): return
			
		if member == None:
			msg = 'Usage: `{}ignore [member]`'.format(ctx.prefix)
			return await ctx.send(msg)

		if type(member) is str:
			memberName = member
			member = DisplayName.memberForName(memberName, ctx.guild)
			if not member:
				msg = 'I couldn\'t find *{}*...'.format(memberName)
				return await ctx.send(Utils.suppressed(ctx,msg))

		ignoreList = self.settings.getServerStat(ctx.guild, "IgnoredUsers")

		for user in ignoreList:
			if str(member.id) == str(user["ID"]):
				# Found our user - already ignored
				return await ctx.send('*{}* is already being ignored.'.format(DisplayName.name(member)))
		# Let's ignore someone
		ignoreList.append({ "Name" : member.name, "ID" : member.id })
		self.settings.setServerStat(ctx.guild, "IgnoredUsers", ignoreList)

		await ctx.send('*{}* is now being ignored.'.format(DisplayName.name(member)))
		
	@ignore.error
	async def ignore_error(self, error, ctx):
		# do stuff
		msg = 'ignore Error: {}'.format(error)
		await ctx.send(msg)


	@commands.command(pass_context=True)
	async def listen(self, ctx, *, member = None):
		"""Removes a member from the bot's "ignore" list (bot-admin only)."""
		if not await Utils.is_bot_admin_reply(ctx): return
			
		if member == None:
			return await ctx.send('Usage: `{}listen [member]`'.format(ctx.prefix))

		if type(member) is str:
			memberName = member
			member = DisplayName.memberForName(memberName, ctx.guild)
			if not member:
				msg = 'I couldn\'t find *{}*...'.format(memberName)
				return await ctx.send(Utils.suppressed(ctx,msg))

		ignoreList = self.settings.getServerStat(ctx.guild, "IgnoredUsers")

		for user in ignoreList:
			if str(member.id) == str(user["ID"]):
				# Found our user - already ignored
				ignoreList.remove(user)
				self.settings.setServerStat(ctx.guild, "IgnoredUsers", ignoreList)
				return await ctx.send("*{}* is no longer being ignored.".format(DisplayName.name(member)))

		await ctx.send('*{}* wasn\'t being ignored...'.format(DisplayName.name(member)))
		
	@listen.error
	async def listen_error(self, error, ctx):
		# do stuff
		msg = 'listen Error: {}'.format(error)
		await ctx.send(msg)


	@commands.command(pass_context=True)
	async def ignored(self, ctx):
		"""Lists the users currently being ignored."""
		ignoreArray = self.settings.getServerStat(ctx.guild, "IgnoredUsers")
		promoSorted = sorted(ignoreArray, key=itemgetter('Name'))
		if not len(promoSorted):
			return await ctx.send("I'm not currently ignoring anyone.")
		ignored = ["*{}*".format(DisplayName.name(ctx.guild.get_member(int(x["ID"])))) for x in promoSorted if ctx.guild.get_member(int(x["ID"]))]
		await ctx.send("Currently Ignored Users:\n{}".format("\n".join(ignored)))

	
	async def kick_ban(self, ctx, members_and_reason = None, command_name = "kick"):
		# Helper method to handle the lifting for kick and ban
		if not await Utils.is_bot_admin_reply(ctx): return
		if not members_and_reason:
			return await ctx.send('Usage: `{}{} [space delimited member mention] [reason]`'.format(ctx.prefix, command_name))
		# Force a mention - we don't want any ambiguity
		args = members_and_reason.split()
		# Get our list of targets
		targets = []
		reason = ""
		for index,item in enumerate(args):
			if self.mention_re.search(item): # Check if it's a mention
				# Resolve the member
				member = ctx.guild.get_member(int(re.sub(r'\W+', '', item)))
				# If we have an invalid mention - bail - no ambiguity
				if member is None: return await ctx.send("Invalid mention passed!")
				# We should have a valid member - let's make sure it's not:
				# 1. The bot, 2. The command caller, 3. Another bot-admin/admin
				if member.id == self.bot.user.id: return await ctx.send("I don't think I want to {} myself...".format(command_name))
				if member.id == ctx.author.id: return await ctx.send("I don't think you really want to {} yourself...".format(command_name))
				if Utils.is_bot_admin(ctx,member): return await ctx.send("You cannot {} other admins!".format(command_name))
				targets.append(member)
			else:
				# Not a mention - must be the reason, dump the rest of the items into a string
				# separated by a space
				reason = " ".join(args[index:])
				break
		if not len(targets): return await ctx.send("No valid members passed!")
		if len(targets) > 5: return await ctx.send("You can only {} up to 5 members at once!".format(command_name))
		if not len(reason): return await ctx.send("Reason is required!")
		# We should have a list of targets, and the reason - let's list them for confirmation
		# then generate a 4-digit confirmation code that the original requestor needs to confirm
		# in order to follow through
		confirmation_code = "".join([str(random.randint(0,9)) for x in range(4)])
		msg = "**To {} the following member{}:**\n\n{}\n\n**With reason:**\n\n\"{}\"\n\n**Please type:**\n\n`{}`".format(
			command_name,
			"" if len(targets) == 1 else "s",
			"\n".join([x.name+"#"+x.discriminator for x in targets]),
			reason,
			confirmation_code
			)
		confirmation_message = await Message.EmbedText(title="{} Confirmation".format(command_name.capitalize()),description=msg,color=ctx.author).send(ctx)
		def check_confirmation(message):
			return message.channel == ctx.channel and ctx.author == message.author # Just making sure it's the same user/channel
		try: confirmation_user = await self.bot.wait_for('message', timeout=60, check=check_confirmation)
		except: confirmation_user = ""
		# Delete the confirmation message
		await confirmation_message.delete()
		# Verify the confirmation
		if not confirmation_user.content == confirmation_code: return await ctx.send("{} cancelled!".format(command_name.capitalize()))
		# We got the authorization!
		message = await Message.EmbedText(title="{}ing...".format("Bann" if command_name == "ban" else "Kick"),color=ctx.author).send(ctx)
		canned = []
		cant = []
		command = ctx.guild.ban if command_name == "ban" else ctx.guild.kick
		for target in targets:
			try:
				await command(target,reason="{}#{}: {}".format(ctx.author.name,ctx.author.discriminator,reason))
				canned.append(target)
			except: cant.append(target)
		msg = ""
		if len(canned):
			msg += "**I was ABLE to {}:**\n\n{}\n\n".format(command_name,"\n".join([x.name+"#"+x.discriminator for x in canned]))
		if len(cant):
			msg += "**I was UNABLE to {}:**\n\n{}\n\n".format(command_name,"\n".join([x.name+"#"+x.discriminator for x in cant]))
		await Message.EmbedText(title="{} Results".format(command_name.capitalize()),description=msg).edit(ctx,message)

	@commands.command(pass_context=True)
	async def kick(self, ctx, *, members = None, reason = None):
		"""Kicks the passed members for the specified reason.
		All kick targets must be mentions to avoid ambiguity.
		You can kick up to 5 members at once.
		The reason is required (bot-admin only).
		
		eg:  $kick @user1#1234 @user2#5678 @user3#9012 for spamming"""
		await self.kick_ban(ctx,members, "kick")
		
		
	@commands.command(pass_context=True)
	async def ban(self, ctx, *, members = None, reason = None):
		"""Bans the passed members for the specified reason.
		All ban targets must be mentions to avoid ambiguity.
		You can ban up to 5 members at once.
		The reason is required (bot-admin only).
		
		eg:  $ban @user1#1234 @user2#5678 @user3#9012 for spamming"""
		await self.kick_ban(ctx,members, "ban")

	@commands.command(pass_context=True)
	async def blacklist(self, ctx, userid, reason = None):
		"""Bans a target who is NOT currently on the server via userid
		This can only blacklist one member at a time.
		All blacklists are stored in a | seperated list in a file where the bot is stored
		"""
		await self.settings.BlacklistUser(userid)
