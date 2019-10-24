import asyncio, discord, random
from   discord.ext import commands
from   Cogs import Utils, Xp, DisplayName, CheckRoles

def setup(bot):
	# Add the bot and deps
	settings = bot.get_cog("Settings")
	bot.add_cog(Feed(bot, settings))

# This is the feed module.  It allows the bot to be fed,
# get hungry, die, be resurrected, etc.

class Feed(commands.Cog):

	# Init with the bot reference, and a reference to the settings var and xp var
	def __init__(self, bot, settings):
		self.bot = bot
		self.settings = settings
		self.loop_list = []

	# Proof of concept stuff for reloading cog/extension
	def _is_submodule(self, parent, child):
		return parent == child or child.startswith(parent + ".")

	def _can_xp(self, user, server):
		# Checks whether or not said user has access to the xp system
		requiredXP  = self.settings.getServerStat(server, "RequiredXPRole")
		promoArray  = self.settings.getServerStat(server, "PromotionArray")
		userXP      = self.settings.getUserStat(user, server, "XP")
		if not requiredXP:
			return True

		for checkRole in user.roles:
			if str(checkRole.id) == str(requiredXP):
				return True
		# Still check if we have enough xp
		for role in promoArray:
			if str(role["ID"]) == str(requiredXP):
				if userXP >= role["XP"]:
					return True
				break
		return False

	@commands.Cog.listener()
	async def on_unloaded_extension(self, ext):
		# Called to shut things down
		if not self._is_submodule(ext.__name__, self.__module__):
			return
		for task in self.loop_list:
			task.cancel()

	@commands.Cog.listener()
	async def on_loaded_extension(self, ext):
		# See if we were loaded
		if not self._is_submodule(ext.__name__, self.__module__):
			return
		self.loop_list.append(self.bot.loop.create_task(self.getHungry()))
		
	async def message(self, message):
		# Check the message and see if we should allow it.
		current_ignore = self.settings.getServerStat(message.guild, "IgnoreDeath")
		if current_ignore:
			return { 'Ignore' : False, 'Delete' : False }
		ignore = delete = False
		hunger = int(self.settings.getServerStat(message.guild, "Hunger"))
		hungerLock = self.settings.getServerStat(message.guild, "HungerLock")
		isKill = self.settings.getServerStat(message.guild, "Killed")
		# Get any commands in the message
		context = await self.bot.get_context(message)
		if (isKill or hunger >= 100 and hungerLock):
			ignore = not context.command or not context.command.name in [ "iskill", "resurrect", "hunger", "feed" ]
		# Check if admin and override
		if Utils.is_bot_admin(context):
			ignore = delete = False	
		return { 'Ignore' : ignore, 'Delete' : delete}

	async def getHungry(self):
		await self.bot.wait_until_ready()
		while not self.bot.is_closed():
			# Add The Hunger
			await asyncio.sleep(900) # runs every 15 minutes
			for server in self.bot.guilds:
				# Iterate through the servers and add them
				isKill = self.settings.getServerStat(server, "Killed")
				if not isKill:
					hunger = int(self.settings.getServerStat(server, "Hunger"))
					# Check if hunger is 100% and increase by 1 if not
					hunger += 1
					hunger = 100 if hunger > 100 else hunger
					self.settings.setServerStat(server, "Hunger", hunger)

	@commands.command(pass_context=True)
	async def ignoredeath(self, ctx, *, yes_no = None):
		"""Sets whether the bot ignores its own death and continues to respond post-mortem (bot-admin only; always off by default)."""
		if not await Utils.is_bot_admin_reply(ctx): return
		await ctx.send(Utils.yes_no_setting(ctx,"Ignore death","IgnoreDeath",yes_no))

	@commands.command(pass_context=True)
	async def hunger(self, ctx):
		"""How hungry is the bot?"""
		hunger = int(self.settings.getServerStat(ctx.guild, "Hunger"))
		isKill = self.settings.getServerStat(ctx.guild, "Killed")
		overweight = hunger * -1
		if hunger <= -1:
			msg = 'I\'m stuffed ({:,}% overweight)... maybe I should take a break from eating...'.format(overweight)
		elif hunger <= -10:
			msg = 'I\'m pudgy ({:,}% overweight)... I may get fat if I keeps going.'.format(overweight)
		elif hunger <= -25:
			msg = 'I am, well fat ({:,}% overweight)... Diet time?'.format(overweight)
		elif hunger <= -50:
			msg = 'I\'m obese ({:,}% overweight)... Eating is my enemy right now.'.format(overweight)
		elif hunger <= -75:
			msg = 'I look fat to an extremely unhealthy degree ({:,}% overweight)... maybe you should think about *my* health?'.format(overweight)
		elif hunger <= -100:
			msg = 'I am essentially dead from over-eating ({:,}% overweight).  I hope you\'re happy.'.format(overweight)
		elif hunger <= -150:
			msg = 'I *AM* dead from over-eating ({:,}% overweight).  You will have to `{}resurrect` me to get me back.'.format(overweight, ctx.prefix)
		elif hunger == 0:
			msg = 'I\'m full ({:,}%).  You are safe.  *For now.*'.format(hunger)
		elif hunger <= 15:
			msg = 'I feel mostly full ({:,}%).  I am appeased.'.format(hunger)
		elif hunger <= 25:
			msg = 'I feel a bit peckish ({:,}%).  A snack is in order.'.format(hunger)
		elif hunger <= 50:
			msg = 'I\'m hungry ({:,}%).  Present your offerings.'.format(hunger)
		elif hunger <= 75:
			msg = 'I\'m *starving* ({:,}%)!  Do you want me to starve to death?'.format(hunger)
		else:
			msg = 'I\'m ***hangry*** ({:,}%)!  Feed me or feel my *wrath!*'.format(hunger)
		if isKill and hunger > -150:
			msg = 'I *AM* dead.  Likely from *lack* of care.  You will have to `{}resurrect` me to get me back.'.format(overweight, ctx.prefix)
		await ctx.send(msg)
		
	@commands.command(pass_context=True)
	async def feed(self, ctx, food : int = None):
		"""Feed the bot some xp!"""
		# feed the bot, and maybe you'll get something in return!
		msg = 'Usage: `{}feed [xp reserve feeding]`'.format(ctx.prefix)
		if food == None:
			return await channel.send(msg)
			
		if not type(food) == int:
			return await channel.send(msg)

		isAdmin    = Utils.is_admin(ctx)
		isBotAdmin = Utils.is_bot_admin_only(ctx)
		botAdminAsAdmin = self.settings.getServerStat(ctx.guild, "BotAdminAsAdmin")
		adminUnlim = self.settings.getServerStat(ctx.guild, "AdminUnlimited")
		reserveXP  = self.settings.getUserStat(ctx.author, ctx.guild, "XPReserve")
		minRole    = self.settings.getServerStat(ctx.guild, "MinimumXPRole")
		requiredXP = self.settings.getServerStat(ctx.guild, "RequiredXPRole")
		isKill     = self.settings.getServerStat(ctx.guild, "Killed")
		hunger     = int(self.settings.getServerStat(ctx.guild, "Hunger"))
		xpblock    = self.settings.getServerStat(ctx.guild, "XpBlockArray")

		approve = True
		decrement = True

		# Check Food

		if food > int(reserveXP):
			approve = False
			msg = 'You can\'t feed me *{:,}*, you only have *{:,}* xp reserve!'.format(food, reserveXP)
			
		if food < 0:
			msg = 'You can\'t feed me less than nothing! You think this is funny?!'
			approve = False
			# Avoid admins gaining xp
			decrement = False
			
		if food == 0:
			msg = 'You can\'t feed me *nothing!*'
			approve = False

		# RequiredXPRole
		if not self._can_xp(ctx.author, ctx.guild):
			approve = False
			msg = 'You don\'t have the permissions to feed me.'

		# Check bot admin
		if isBotAdmin and botAdminAsAdmin:
			# Approve as admin
			approve = True
			if adminUnlim:
				# No limit
				decrement = False
			else:
				if food < 0:
					# Don't decrement if negative
					decrement = False
				if food > int(reserveXP):
					# Don't approve if we don't have enough
					msg = 'You can\'t feed me *{:,}*, you only have *{:,}* xp reserve!'.format(food, reserveXP)
					approve = False
			
		# Check admin last - so it overrides anything else
		if isAdmin:
			# No limit - approve
			approve = True
			if adminUnlim:
				# No limit
				decrement = False
			else:
				if food < 0:
					# Don't decrement if negative
					decrement = False
				if food > int(reserveXP):
					# Don't approve if we don't have enough
					msg = 'You can\'t feed me *{:,}*, you only have *{:,}* xp reserve!'.format(food, reserveXP)
					approve = False
			
		# Check if we're blocked
		if ctx.author.id in xpblock:
			msg = "You can't feed the bot!"
			approve = False
		else:
			if any(x for x in ctx.author.roles if x.id in xpblock):
				msg = "Your role cannot feed the bot!"
				approve = False

		if approve:
			# Feed was approved - let's take the XPReserve right away
			# Apply food - then check health
			hunger -= food
			
			self.settings.setServerStat(ctx.guild, "Hunger", hunger)
			takeReserve = -1*food
			if decrement:
				self.settings.incrementStat(ctx.author, ctx.guild, "XPReserve", takeReserve)

			if isKill:
				# Bot's dead...
				msg = '*{}* carelessly shoves *{:,} xp* into the carcass of *{}*... maybe resurrect them first next time?'.format(DisplayName.name(ctx.author), food, DisplayName.serverNick(self.bot.user, ctx.guild))
				return await ctx.send(msg)
			
			# Bet more, less chance of winning, but more winnings!
			chanceToWin = 50
			payout = int(food*2)
			
			# 1/chanceToWin that user will win - and payout is double the food
			randnum = random.randint(1, chanceToWin)
			if randnum == 1:
				# YOU WON!!
				self.settings.incrementStat(ctx.author, ctx.guild, "XP", int(payout))
				msg = '*{}\'s* offering of *{:,}* has made me feel *exceptionally* generous.  Please accept this *magical* package with *{:,} xp!*'.format(DisplayName.name(ctx.author), food, int(payout))
				
				# Got XP - let's see if we need to promote
				await CheckRoles.checkroles(ctx.author, ctx.channel, self.settings, self.bot)
			else:
				msg = '*{}* fed me *{:,} xp!* Thank you, kind soul! Perhaps I\'ll spare you...'.format(DisplayName.name(ctx.author), food)
		
			if hunger <= -150:
				# Kill the bot here
				self.settings.setServerStat(ctx.guild, "Killed", True)
				self.settings.setServerStat(ctx.guild, "KilledBy", ctx.author.id)
				msg = '{}\n\nI am kill...\n\n*{}* did it...'.format(msg, DisplayName.name(ctx.author))			
			elif hunger <= -100:
				msg = '{}\n\nYou *are* going to kill me...  Stop *now* if you have a heart!'.format(msg)
			elif hunger <= -75:
				msg = '{}\n\nI\'m looking fat to an extremely unhealthy degree... maybe you should think about *my* health?'.format(msg)
			elif hunger <= -50:
				msg = '{}\n\nI\'m obese :( ... Eating is my enemy right now.'.format(msg)
			elif hunger <= -25:
				msg = '{}\n\nI\'m kinda fat... Diet time?'.format(msg)	
			elif hunger <= -10:
				msg = '{}\n\nI\'m getting pudgy... I may get fat if you keep going.'.format(msg)
			elif hunger <= -1:
				msg = '{}\n\nI\'m getting stuffed... maybe I should take a break from eating...'.format(msg)
			elif hunger == 0:
				msg = '{}\n\nIf you keep feeding me, I *may* get fat...'.format(msg)
		
		await ctx.send(msg)
		
	@commands.command(pass_context=True)
	async def kill(self, ctx):
		"""Kill the bot... you heartless soul."""
		# Check for role requirements
		requiredRole = self.settings.getServerStat(ctx.guild, "RequiredKillRole")
		if requiredRole == "":
			#admin only
			if not await Utils.is_admin_reply(ctx): return
		else:
			#role requirement
			if not any(x for x in ctx.author.roles if str(x.id) == str(requiredRole)) and not Utils.is_admin(ctx):
				return await ctx.send("You do not have sufficient privileges to access this command.")

		iskill = self.settings.getServerStat(ctx.guild, "Killed")
		if iskill:
			killedby = self.settings.getServerStat(ctx.guild, "KilledBy")
			killedby = DisplayName.memberForID(killedby, ctx.guild)
			return await ctx.send('I am *already* kill...\n\n*{}* did it...'.format(DisplayName.name(killedby)))
		
		self.settings.setServerStat(ctx.guild, "Killed", True)
		self.settings.setServerStat(ctx.guild, "KilledBy", author.id)
		await ctx.send('I am kill...\n\n*{}* did it...'.format(DisplayName.name(ctx.author)))
		
	@commands.command(pass_context=True)
	async def resurrect(self, ctx):
		"""Restore life to the bot.  What magic is this?"""
		# Check for role requirements
		requiredRole = self.settings.getServerStat(ctx.guild, "RequiredKillRole")
		if requiredRole == "":
			#admin only
			if not await Utils.is_admin_reply(ctx): return
		else:
			#role requirement
			if not any(x for x in ctx.author.roles if str(x.id) == str(requiredRole)) and not Utils.is_admin(ctx):
				return await ctx.send("You do not have sufficient privileges to access this command.")

		iskill = self.settings.getServerStat(ctx.guild, "Killed")
		if not iskill:
			return await ctx.send('Trying to bring back the *already-alive* - well aren\'t you special!')
		
		self.settings.setServerStat(ctx.guild, "Killed", False)
		self.settings.setServerStat(ctx.guild, "Hunger", "0")
		killedBy = self.settings.getServerStat(ctx.guild, "KilledBy")
		killedBy = DisplayName.memberForID(killedBy, ctx.guild)
		await ctx.send('Guess who\'s back??\n\n*{}* may have tried to keep me down - but I *just keep coming back!*'.format(DisplayName.name(killedBy)))
		
	@commands.command(pass_context=True)
	async def iskill(self, ctx):
		"""Check the ded of the bot."""
		isKill = self.settings.getServerStat(ctx.guild, "Killed")
		killedBy = self.settings.getServerStat(ctx.guild, "KilledBy")
		killedBy = DisplayName.memberForID(killedBy, ctx.guild)
		msg = 'I have no idea what you\'re talking about... Should I be worried?'
		if isKill:
			msg = '*Whispers from beyond the grave*\nI am kill...\n\n*{}* did it...'.format(DisplayName.name(killedBy))
		else:
			msg = 'Wait - are you asking if I\'m *dead*?  Why would you wanna know *that?*'
		await ctx.send(msg)

	@commands.command(pass_context=True)
	async def setkillrole(self, ctx, *, role : discord.Role = None):
		"""Sets the required role ID to add/remove hacks (admin only)."""
		if not await Utils.is_admin_reply(ctx): return
		if role == None:
			self.settings.setServerStat(ctx.guild, "RequiredKillRole", "")
			msg = 'Kill/resurrect now *admin-only*.'
			return await ctx.send(msg)
		if type(role) is str:
			try:
				role = discord.utils.get(ctx.server.roles, name=role)
			except:
				print("That role does not exist")
				return
		# If we made it this far - then we can add it
		self.settings.setServerStat(ctx.guild, "RequiredKillRole", role.id)
		msg = 'Role required for kill/resurrect set to **{}**.'.format(role.name)
		await ctx.send(Utils.suppressed(ctx,msg))

	@setkillrole.error
	async def killrole_error(self, ctx, error):
		# do stuff
		msg = 'setkillrole Error: {}'.format(error)
		await ctx.send(msg)

	@commands.command(pass_context=True)
	async def killrole(self, ctx):
		"""Lists the required role to kill/resurrect the bot."""
		role = self.settings.getServerStat(ctx.guild, "RequiredKillRole")
		if role == None or role == "":
			msg = '**Only Admins** can kill/ressurect the bot.'
			return await ctx.send(msg)
		# Role is set - let's get its name
		arole = next((x for x in ctx.guild.roles if str(x.id) == str(role)),None)
		if not arole:
			msg = 'There is no role that matches id: `{}` - consider updating this setting.'.format(role)
		msg = 'You need to be a/an **{}** to kill/ressurect the bot.'.format(arole.name)
		await ctx.send(Utils.suppressed(ctx,msg))
