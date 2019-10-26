import asyncio, discord
from   operator import itemgetter
from   discord.ext import commands
from   Cogs import Utils, DisplayName

def setup(bot):
	# Add the bot and deps
	settings = bot.get_cog("Settings")
	bot.add_cog(BotAdmin(bot, settings))

class BotAdmin(commands.Cog):

	# Init with the bot reference, and a reference to the settings var
	def __init__(self, bot, settings):
		self.bot = bot
		self.settings = settings

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


	@commands.command(pass_context=True)
	async def kick(self, ctx, *, member : str = None):
		"""Kicks the selected member (bot-admin only)."""
		if not await Utils.is_bot_admin_reply(ctx): return
		
		if not member:
			return await ctx.send('Usage: `{}kick [member]`'.format(ctx.prefix))
		
		# Resolve member name -> member
		newMem = DisplayName.memberForName(member, ctx.guild)
		if not newMem:
			msg = 'I couldn\'t find *{}*.'.format(member)
			return await ctx.send(Utils.suppressed(ctx,msg))
		
		# newMem = valid member
		member = newMem
		
		if member.id == ctx.author.id:
			return await ctx.send('Stop kicking yourself.  Stop kicking yourself.')

		# Check if we're kicking the bot
		if member.id == self.bot.user.id:
			return await ctx.send('Oh - you probably meant to kick *yourself* instead, right?')
		
		# Check if the targeted user is admin
		if await Utils.is_bot_admin_reply(ctx,member=member,message="You can't kick other admins or bot-admins.",message_when=True): return
		
		# We can kick
		await ctx.send('If this were live - you would have **kicked** *{}*'.format(DisplayName.name(member)))
		
		
	@commands.command(pass_context=True)
	async def ban(self, ctx, *, member : str = None):
		"""Bans the selected member (bot-admin only)."""
		if not await Utils.is_bot_admin_reply(ctx): return
		
		if not member:
			return await ctx.send('Usage: `{}ban [member]`'.format(ctx.prefix))
		
		# Resolve member name -> member
		newMem = DisplayName.memberForName(member, ctx.guild)
		if not newMem:
			msg = 'I couldn\'t find *{}*.'.format(member)
			return await ctx.send(Utils.suppressed(ctx,msg))
		
		# newMem = valid member
		member = newMem
		
		if member.id == ctx.author.id:
			return await ctx.send('Ahh - the ol\' self-ban.  Good try.')

		# Check if we're banning the bot
		if member.id == self.bot.user.id:
			return await ctx.send('Oh - you probably meant to ban *yourself* instead, right?')
		
		# Check if the targeted user is admin
		if await Utils.is_bot_admin_reply(ctx,member=member,message="You can't ban other admins or bot-admins.",message_when=True): return
		
		# We can ban
		await ctx.send('If this were live - you would have **banned** *{}*'.format(DisplayName.name(member)))
		
