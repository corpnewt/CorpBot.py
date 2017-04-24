import asyncio
import discord
import random
import datetime
from   discord.ext import commands
from   Cogs import Settings
from   Cogs import Xp
from   Cogs import DisplayName
from   Cogs import Nullify

# This is the feed module.  It allows the bot to be fed,
# get hungry, die, be resurrected, etc.

class Feed:

	# Init with the bot reference, and a reference to the settings var and xp var
	def __init__(self, bot, settings, xp, prefix):
		self.bot = bot
		self.settings = settings
		self.xp = xp
		self.bot.loop.create_task(self.getHungry())
		self.prefix = prefix
		
	async def message(self, message):
		# Check the message and see if we should allow it.
		ignore = False
		delete = False
		hunger = int(self.settings.getServerStat(message.guild, "Hunger"))
		hungerLock = self.settings.getServerStat(message.guild, "HungerLock")
		isKill = self.settings.getServerStat(message.guild, "Killed")
		if isKill.lower() == "yes":
			ignore = True
			if message.content.startswith('{}iskill'.format(self.prefix)) or message.content.startswith('{}resurrect'.format(self.prefix)) or message.content.startswith('{}hunger'.format(self.prefix)) or message.content.startswith('{}feed'.format(self.prefix)):
				ignore = False
				
		if hunger >= 100 and hungerLock.lower() == "yes":
			ignore = True
			if message.content.startswith('{}iskill'.format(self.prefix)) or message.content.startswith('{}resurrect'.format(self.prefix)) or message.content.startswith('{}hunger'.format(self.prefix)) or message.content.startswith('{}feed'.format(self.prefix)):
				ignore = False
				
		# Check if admin and override
		isAdmin = message.author.permissions_in(message.channel).administrator
		if not isAdmin:
			checkAdmin = self.settings.getServerStat(message.guild, "AdminArray")
			for role in message.author.roles:
				for aRole in checkAdmin:
					# Get the role that corresponds to the id
					if str(aRole['ID']) == str(role.id):
						isAdmin = True
		if isAdmin:
			ignore = False
			delete = False
		
		return { 'Ignore' : ignore, 'Delete' : delete}
		
	async def getHungry(self):
		await self.bot.wait_until_ready()
		while not self.bot.is_closed():
			# Add The Hunger
			await asyncio.sleep(900) # runs every 15 minutes
			for server in self.bot.guilds:
				# Iterate through the servers and add them
				isKill = self.settings.getServerStat(server, "Killed")
				
				if isKill.lower() == "no":
					hunger = int(self.settings.getServerStat(server, "Hunger"))
					# Check if hunger is 100% and increase by 1 if not
					hunger += 1
				
					if hunger > 100:
						hunger = 100
					
					self.settings.setServerStat(server, "Hunger", hunger)
		
	@commands.command(pass_context=True)
	async def hunger(self, ctx):
		"""How hungry is the bot?"""
		
		channel = ctx.message.channel
		author  = ctx.message.author
		server  = ctx.message.guild
		
		hunger = int(self.settings.getServerStat(server, "Hunger"))
		isKill = self.settings.getServerStat(server, "Killed")
		overweight = hunger * -1
		if hunger < 0:
			
			if hunger <= -1:
				msg = 'I\'m stuffed ({}% overweight)... maybe I should take a break from eating...'.format(overweight)
			if hunger <= -10:
				msg = 'I\'m pudgy ({}% overweight)... I may get fat if I keeps going.'.format(overweight)
			if hunger <= -25:
				msg = 'I am, well fat ({}% overweight)... Diet time?'.format(overweight)
			if hunger <= -50:
				msg = 'I\'m obese ({}% overweight)... Eating is my enemy right now.'.format(overweight)
			if hunger <= -75:
				msg = 'I look fat to an extremely unhealthy degree ({}% overweight)... maybe you should think about *my* health?'.format(overweight)
			if hunger <= -100:
				msg = 'I am essentially dead from over-eating ({}% overweight).  I hope you\'re happy.'.format(overweight)
			if hunger <= -150:
				msg = 'I *AM* dead from over-eating ({}% overweight).  You will have to `{}resurrect` me to get me back.'.format(overweight, ctx.prefix)
				
		elif hunger == 0:
			msg = 'I\'m full ({}%).  You are safe.  *For now.*'.format(hunger)
		elif hunger <= 15:
			msg = 'I feel mostly full ({}%).  I am appeased.'.format(hunger)
		elif hunger <= 25:
			msg = 'I feel a bit peckish ({}%).  A snack is in order.'.format(hunger)
		elif hunger <= 50:
			msg = 'I\'m hungry ({}%).  Present your offerings.'.format(hunger)
		elif hunger <= 75:
			msg = 'I\'m *starving* ({}%)!  Do you want me to starve to death?'.format(hunger)
		else:
			msg = 'I\'m ***hangry*** ({}%)!  Feed me or feel my *wrath!*'.format(hunger)
			
		if isKill.lower() == "yes" and hunger > -150:
			msg = 'I *AM* dead.  Likely from *lack* of care.  You will have to `{}resurrect` me to get me back.'.format(overweight, self.prefix)
			
		await channel.send(msg)
		
	@commands.command(pass_context=True)
	async def feed(self, ctx, food : int = None):
		"""Feed the bot some xp!"""
		# feed the bot, and maybe you'll get something in return!
		msg = 'Usage: `{}feed [xp reserve feeding]`'.format(ctx.prefix)
		
		channel = ctx.message.channel
		author  = ctx.message.author
		server  = ctx.message.guild
		
		if food == None:
			await channel.send(msg)
			return
			
		if not type(food) == int:
			await channel.send(msg)
			return

		isAdmin    = author.permissions_in(channel).administrator
		adminUnlim = self.settings.getServerStat(server, "AdminUnlimited")
		reserveXP  = self.settings.getUserStat(author, server, "XPReserve")
		minRole    = self.settings.getServerStat(server, "MinimumXPRole")
		requiredXP = self.settings.getServerStat(server, "RequiredXPRole")
		isKill = self.settings.getServerStat(server, "Killed")
		hunger = int(self.settings.getServerStat(server, "Hunger"))

		approve = True
		decrement = True

		# Check Food

		if food > int(reserveXP):
			approve = False
			msg = 'You can\'t feed me *{}*, you only have *{}* xp reserve!'.format(food, reserveXP)
			
		if food < 0:
			msg = 'You can\'t feed me less than nothing! You think this is funny?!'
			approve = False
			
		if food == 0:
			msg = 'You can\'t feed me *nothing!*'
			approve = False
			
		#if author.top_role.position < int(minRole):
			#approve = False
			#msg = 'You don\'t have the permissions to feed me.'
		
		# RequiredXPRole
		if requiredXP:
			foundRole = False
			for checkRole in author.roles:
				if str(checkRole.id) == str(requiredXP):
					foundRole = True
			if not foundRole:
				approve = False
				msg = 'You don\'t have the permissions to feed me.'

		# Check admin last - so it overrides anything else
		if isAdmin and adminUnlim.lower() == "yes":
			# No limit - approve
			approve = True
			decrement = False
			
		if approve:
			# Feed was approved - let's take the XPReserve right away
			# Apply food - then check health
			hunger -= food
			
			self.settings.setServerStat(server, "Hunger", hunger)
			takeReserve = -1*food
			if decrement:
				self.settings.incrementStat(author, server, "XPReserve", takeReserve)

			if isKill.lower() == "yes":
				# Bot's dead...
				msg = '*{}* carelessly shoves *{} xp* into the carcass of *{}*... maybe resurrect them first next time?'.format(DisplayName.name(author), food, DisplayName.serverNick(self.bot.user, server))
				await channel.send(msg)
				return
			
			# Bet more, less chance of winning, but more winnings!
			chanceToWin = 50
			payout = int(food*2)
			
			# 1/chanceToWin that user will win - and payout is double the food
			randnum = random.randint(1, chanceToWin)
			if randnum == 1:
				# YOU WON!!
				self.settings.incrementStat(author, server, "XP", int(payout))
				msg = '*{}\'s* offering of *{}* has made me feel *exceptionally* generous.  Please accept this *magical* package with *{} xp!*'.format(DisplayName.name(author), food, int(payout))
				
				# Got XP - let's see if we need to promote
				await self.xp.checkroles(author, channel)
			else:
				msg = '*{}* fed me *{} xp!* Thank you, kind soul! Perhaps I\'ll spare you...'.format(DisplayName.name(author), food)
		
			if hunger <= -150:
				# Kill the bot here
				self.settings.setServerStat(server, "Killed", "Yes")
				self.settings.setServerStat(server, "KilledBy", author.id)
				msg = '{}\n\nI am kill...\n\n*{}* did it...'.format(msg, DisplayName.name(author))			
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
		
		await channel.send(msg)
		
	@commands.command(pass_context=True)
	async def kill(self, ctx):
		"""Kill the bot... you heartless soul."""
		
		channel = ctx.message.channel
		author  = ctx.message.author
		server  = ctx.message.guild
		
		# Check for role requirements
		requiredRole = self.settings.getServerStat(server, "RequiredKillRole")
		if requiredRole == "":
			#admin only
			isAdmin = author.permissions_in(channel).administrator
			if not isAdmin:
				await channel.send('You do not have sufficient privileges to access this command.')
				return
		else:
			#role requirement
			hasPerms = False
			for role in author.roles:
				if str(role.id) == str(requiredRole):
					hasPerms = True
			if not hasPerms:
				await channel.send('You do not have sufficient privileges to access this command.')
				return

		iskill = self.settings.getServerStat(server, "Killed")
		if iskill.lower() == 'yes':
			killedby = self.settings.getServerStat(server, "KilledBy")
			killedby = DisplayName.memberForID(killedby, server)
			await channel.send('I am *already* kill...\n\n*{}* did it...'.format(DisplayName.name(killedby)))
			return
		
		self.settings.setServerStat(server, "Killed", "Yes")
		self.settings.setServerStat(server, "KilledBy", author.id)
		await channel.send('I am kill...\n\n*{}* did it...'.format(DisplayName.name(author)))
		
	@commands.command(pass_context=True)
	async def resurrect(self, ctx):
		"""Restore life to the bot.  What magic is this?"""
		
		channel = ctx.message.channel
		author  = ctx.message.author
		server  = ctx.message.guild
		
		# Check for role requirements
		requiredRole = self.settings.getServerStat(server, "RequiredKillRole")
		if requiredRole == "":
			#admin only
			isAdmin = author.permissions_in(channel).administrator
			if not isAdmin:
				await channel.send('You do not have sufficient privileges to access this command.')
				return
		else:
			#role requirement
			hasPerms = False
			for role in author.roles:
				if str(role.id) == str(requiredRole):
					hasPerms = True
			if not hasPerms:
				await channel.send('You do not have sufficient privileges to access this command.')
				return

		iskill = self.settings.getServerStat(server, "Killed")
		if iskill.lower() == 'no':
			await channel.send('Trying to bring back the *already-alive* - well aren\'t you special!')
			return
		
		self.settings.setServerStat(server, "Killed", "No")
		self.settings.setServerStat(server, "Hunger", "0")
		killedBy = self.settings.getServerStat(server, "KilledBy")
		killedBy = DisplayName.memberForID(killedBy, server)
		await channel.send('Guess who\'s back??\n\n*{}* may have tried to keep me down - but I *just keep coming back!*'.format(DisplayName.name(killedBy)))
		
	@commands.command(pass_context=True)
	async def iskill(self, ctx):
		"""Check the ded of the bot."""
		
		channel = ctx.message.channel
		author  = ctx.message.author
		server  = ctx.message.guild
		
		isKill = self.settings.getServerStat(server, "Killed")
		killedBy = self.settings.getServerStat(server, "KilledBy")
		killedBy = DisplayName.memberForID(killedBy, server)
		msg = 'I have no idea what you\'re talking about... Should I be worried?'
		if isKill.lower() == "yes":
			msg = '*Whispers from beyond the grave*\nI am kill...\n\n*{}* did it...'.format(DisplayName.name(killedBy))
		else:
			msg = 'Wait - are you asking if I\'m *dead*?  Why would you wanna know *that?*'
			
		await channel.send(msg)
		

	@commands.command(pass_context=True)
	async def setkillrole(self, ctx, role : discord.Role = None):
		"""Sets the required role ID to add/remove hacks (admin only)."""
		
		channel = ctx.message.channel
		author  = ctx.message.author
		server  = ctx.message.guild

		# Check if we're suppressing @here and @everyone mentions
		if self.settings.getServerStat(ctx.message.guild, "SuppressMentions").lower() == "yes":
			suppress = True
		else:
			suppress = False
		
		isAdmin = author.permissions_in(channel).administrator
		# Only allow admins to change server stats
		if not isAdmin:
			await channel.send('You do not have sufficient privileges to access this command.')
			return

		if role == None:
			self.settings.setServerStat(server, "RequiredKillRole", "")
			msg = 'Kill/resurrect now *admin-only*.'
			await channel.send(msg)
			return

		if type(role) is str:
			try:
				role = discord.utils.get(server.roles, name=role)
			except:
				print("That role does not exist")
				return

		# If we made it this far - then we can add it
		self.settings.setServerStat(server, "RequiredKillRole", role.id)

		msg = 'Role required for kill/resurrect set to **{}**.'.format(role.name)
		# Check for suppress
		if suppress:
			msg = Nullify.clean(msg)
		await channel.send(msg)

	@setkillrole.error
	async def killrole_error(self, ctx, error):
		# do stuff
		msg = 'setkillrole Error: {}'.format(ctx)
		await error.channel.send(msg)

	@commands.command(pass_context=True)
	async def killrole(self, ctx):
		"""Lists the required role to kill/resurrect the bot."""

		# Check if we're suppressing @here and @everyone mentions
		if self.settings.getServerStat(ctx.message.guild, "SuppressMentions").lower() == "yes":
			suppress = True
		else:
			suppress = False

		role = self.settings.getServerStat(ctx.message.guild, "RequiredKillRole")
		if role == None or role == "":
			msg = '**Only Admins** can kill/ressurect the bot.'.format(ctx)
			await ctx.channel.send(msg)
		else:
			# Role is set - let's get its name
			found = False
			for arole in ctx.message.guild.roles:
				if str(arole.id) == str(role):
					found = True
					msg = 'You need to be a/an **{}** to kill/ressurect the bot.'.format(arole.name)
			if not found:
				msg = 'There is no role that matches id: `{}` - consider updating this setting.'.format(role)
			# Check for suppress
			if suppress:
				msg = Nullify.clean(msg)
			await ctx.channel.send(msg)
