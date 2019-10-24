import asyncio, discord, time, parsedatetime
from   datetime import datetime
from   operator import itemgetter
from   discord.ext import commands
from   Cogs import Utils, Settings, ReadableTime, DisplayName

def setup(bot):
	# Add the bot and deps
	settings = bot.get_cog("Settings")
	mute     = bot.get_cog("Mute")
	bot.add_cog(BotAdmin(bot, settings, mute))

class BotAdmin(commands.Cog):

	# Init with the bot reference, and a reference to the settings var
	def __init__(self, bot, settings, muter):
		self.bot = bot
		self.settings = settings
		self.muter = muter

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
	async def mute(self, ctx, *, member = None, cooldown = None):
		"""Prevents a member from sending messages in chat (bot-admin only)."""
		if not await Utils.is_bot_admin_reply(ctx): return

		if member == None:
			msg = 'Usage: `{}mute [member] [cooldown]`'.format(ctx.prefix)
			await ctx.send(msg)
			return

		if cooldown == None:
			# Either a cooldown wasn't set - or it's the last section
			if type(member) is str:
				# It' a string - the hope continues
				# Let's search for a name at the beginning - and a time at the end
				parts = member.split()
				for j in range(len(parts)):
					# Reverse search direction
					i = len(parts)-1-j
					memFromName = None
					endTime     = None
					# Name = 0 up to i joined by space
					nameStr = ' '.join(parts[0:i+1])
					# Time = end of name -> end of parts joined by space
					timeStr = ' '.join(parts[i+1:])
					memFromName = DisplayName.memberForName(nameStr, ctx.guild)
					if memFromName:
						# We got a member - let's check for time
						# Get current time - and end time
						try:
							# Get current time - and end time
							currentTime = int(time.time())
							cal         = parsedatetime.Calendar()
							time_struct, parse_status = cal.parse(timeStr)
							start       = datetime(*time_struct[:6])
							end         = time.mktime(start.timetuple())

							# Get the time from now to end time
							endTime = end-currentTime
						except:
							pass
							
						if not endTime == None:
							# We got a member and a time - break
							break
				
				if memFromName == None:
					# We couldn't find one or the other
					msg = 'Usage: `{}mute [member] [cooldown]`'.format(ctx.prefix)
					return await ctx.send(msg)
				
				cooldown = None if endTime == 0 else endTime
				member   = memFromName

		# Check if we're muting ourself
		if member is ctx.author:
			msg = 'It would be easier for me if you just *stayed quiet all by yourself...*'
			return await ctx.send(msg)
		
		# Check if we're muting the bot
		if member.id == self.bot.user.id:
			msg = 'How about we don\'t, and *pretend* we did...'
			return await ctx.send(msg)

		# Check if member is admin or bot admin
		if await Utils.is_bot_admin_reply(ctx,member=member,message="You can't mute other admins or bot-admins.",message_when=True): return

		# Set cooldown - or clear it
		if type(cooldown) is int or type(cooldown) is float:
			if cooldown < 0:
				msg = 'Cooldown cannot be a negative number!'
				return await ctx.send(msg)
			currentTime = int(time.time())
			cooldownFinal = currentTime+cooldown
		else:
			cooldownFinal = None
		mess = await ctx.send("Muting...")
		# Do the actual muting
		await self.muter.mute(member, ctx.guild, cooldownFinal)

		if cooldown:
			mins = "minutes"
			checkRead = ReadableTime.getReadableTimeBetween(currentTime, cooldownFinal)
			msg = '*{}* has been **Muted** for *{}*.'.format(DisplayName.name(member), checkRead)
			pm  = 'You have been **Muted** by *{}* for *{}*.\n\nYou will not be able to send messages on *{}* until either that time has passed, or you have been **Unmuted**.'.format(DisplayName.name(ctx.author), checkRead, Utils.suppressed(ctx, ctx.guild.name))
		else:
			msg = '*{}* has been **Muted** *until further notice*.'.format(DisplayName.name(member))
			pm  = 'You have been **Muted** by *{}* *until further notice*.\n\nYou will not be able to send messages on *{}* until you have been **Unmuted**.'.format(DisplayName.name(ctx.author), Utils.suppressed(ctx, ctx.guild.name))

		await mess.edit(content=Utils.suppressed(ctx,msg))
		try:
			await member.send(pm)
		except Exception:
			pass
		
	@mute.error
	async def mute_error(self, error, ctx):
		# do stuff
		msg = 'mute Error: {}'.format(error)
		await ctx.send(msg)
		
		
	@commands.command(pass_context=True)
	async def unmute(self, ctx, *, member = None):
		"""Allows a muted member to send messages in chat (bot-admin only)."""
		if not await Utils.is_bot_admin_reply(ctx): return
			
		if member == None:
			msg = 'Usage: `{}unmute [member]`'.format(ctx.prefix)
			return await ctx.send(msg)

		if type(member) is str:
			memberName = member
			member = DisplayName.memberForName(memberName, ctx.guild)
			if not member:
				msg = 'I couldn\'t find *{}*...'.format(memberName)
				return await ctx.send(Utils.suppressed(ctx,msg))
			
		mess = await ctx.send("Unmuting...")
		await self.muter.unmute(member, ctx.guild)

		pm = 'You have been **Unmuted** by *{}*.\n\nYou can send messages on *{}* again.'.format(DisplayName.name(ctx.author), Utils.suppressed(ctx, ctx.guild.name))
		msg = '*{}* has been **Unmuted**.'.format(DisplayName.name(member))

		await mess.edit(content=msg)
		try:
			await member.send(pm)
		except Exception:
			pass

	@unmute.error
	async def unmute_error(self, error, ctx):
		# do stuff
		msg = 'unmute Error: {}'.format(error)
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
		
