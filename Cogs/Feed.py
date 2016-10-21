import asyncio
import discord
import random
import datetime
from   discord.ext import commands
from   Cogs import Settings
from   Cogs import Xp

# This is the feed module.  It allows the bot to be fed,
# get hungry, die, be resurrected, etc.

class Feed:

	# Init with the bot reference, and a reference to the settings var and xp var
	def __init__(self, bot, settings, xp):
		self.bot = bot
		self.settings = settings
		self.xp = xp
		self.bot.loop.create_task(self.getHungry())
		
	def message(self, message):
		# Check the message and see if we should allow it.
		ignore = False
		delete = False
		hunger = int(self.settings.getServerStat(message.server, "Hunger"))
		hungerLock = self.settings.getServerStat(message.server, "HungerLock")
		isKill = self.settings.getServerStat(message.server, "Killed")
		if isKill.lower() == "yes":
			ignore = True
			if message.content.startswith('$iskill') or message.content.startswith('$resurrect') or message.content.startswith('$hunger') or message.content.startswith('$feed'):
				ignore = False
				
		if hunger >= 100 and hungerLock.lower() == "yes":
			ignore = True
		
		return { 'Ignore' : ignore, 'Delete' : delete}
		
	async def getHungry(self):
		while not self.bot.is_closed:
			# Add The Hunger
			await asyncio.sleep(900) # runs every 15 minutes
			for server in self.bot.servers:
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
		server  = ctx.message.server
		
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
				msg = 'I *AM* dead from over-eating ({}% overweight).  You will have to `$ressurect` me to get me back.'.format(overweight)
				
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
			msg = 'I\'m ***hangry*** ({}%)!  Feed me or feel me *wrath!*'.format(hunger)
			
		if isKill.lower() == "yes" and hunger > -150:
			msg = 'I *AM* dead.  Likely from *lack* of care.  You will have to `$ressurect` me to get me back.'.format(overweight)
			
		await self.bot.send_message(channel, msg)
		
	@commands.command(pass_context=True)
	async def feed(self, ctx, food : int = None):
		"""Feed the bot some xp!"""
		# feed the bot, and maybe you'll get something in return!
		msg = 'Usage: `feed [xp reserve feeding]`'
		
		channel = ctx.message.channel
		author  = ctx.message.author
		server  = ctx.message.server
		
		if food == None:
			await self.bot.send_message(channel, msg)
			return
			
		if not type(food) == int:
			await self.bot.send_message(channel, msg)
			return

		isAdmin    = author.permissions_in(channel).administrator
		adminUnlim = self.settings.getServerStat(server, "AdminUnlimited")
		reserveXP  = self.settings.getUserStat(author, server, "XPReserve")
		minRole    = self.settings.getServerStat(server, "MinimumXPRole")
		hunger     = int(self.settings.getServerStat(server, "Hunger"))
		isKill     = self.settings.getServerStat(server, "Killed")

		approve    = True
		decrement  = True

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
			
		if author.top_role.position < int(minRole):
			approve = False
			msg = 'You don\'t have the permissions to feed me.'
			
		# Check admin last - so it overrides anything else
		if isAdmin and adminUnlim.lower() == "yes":
			# No limit - approve
			approve = True
			decrement = False
			
		if isKill.lower() == "yes":
			# Bot's dead...
			msg = '*{}* carelessly shoves *{} xp* into the carcass of *{}*... maybe resurrect them first next time?'.format(author.name, food, self.bot.user.name)
			await self.bot.send_message(channel, msg)
			return
			
		if approve:
			# Feed was approved - let's take the XPReserve right away
			# Apply food - then check health
			hunger -= food
			
			self.settings.setServerStat(server, "Hunger", hunger)
			takeReserve = -1*food
			if decrement:
				self.settings.incrementStat(author, server, "XPReserve", takeReserve)
			
			# Bet more, less chance of winning, but more winnings!
			chanceToWin = 50
			payout = int(food*2)
			
			# 1/chanceToWin that user will win - and payout is double the food
			randnum = random.randint(1, chanceToWin)
			if randnum == 1:
				# YOU WON!!
				self.settings.incrementStat(author, server, "XP", int(payout))
				msg = '*{}\'s* offering of *{}* has made me feel *exceptionally* generous.  Please accept this *magical* package with *{} xp!*'.format(author.name, food, int(payout))
				
				# Got XP - let's see if we need to promote
				await self.xp.checkroles(author, channel)
			else:
				msg = '*{}* fed me *{} xp!* Thank you, kind soul! Perhaps I\'ll spare you...'.format(author.name, food)
		
			if hunger <= -150:
				# Kill the bot here
				self.settings.setServerStat(server, "Killed", "Yes")
				self.settings.setServerStat(server, "KilledBy", author.name)
				msg = '{}\nI am kill...\n\n{} did it...'.format(msg, author.name)			
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
				msg = '{}\n\nIf you keep over-feeding me, I *may* get fat...'.format(msg)
		
		await self.bot.send_message(channel, msg)
		
	@commands.command(pass_context=True)
	async def kill(self, ctx):
		"""Kill the bot... you heartless soul."""
		
		channel = ctx.message.channel
		author  = ctx.message.author
		server  = ctx.message.server
		
		# Check for role requirements
		requiredRole = self.settings.getServerStat(server, "RequiredKillRole")
		if requiredRole == "":
			#admin only
			isAdmin = author.permissions_in(channel).administrator
			if not isAdmin:
				await self.bot.send_message(channel, 'You do not have sufficient privileges to access this command.')
				return
		else:
			#role requirement
			hasPerms = False
			for role in author.roles:
				if role.id == requiredRole:
					hasPerms = True
			if not hasPerms:
				await self.bot.send_message(channel, 'You do not have sufficient privileges to access this command.')
				return
		
		self.settings.setServerStat(server, "Killed", "Yes")
		self.settings.setServerStat(server, "KilledBy", author.name)
		await self.bot.send_message(channel, 'I am kill...\n\n*{}* did it...'.format(author.name))
		
	@commands.command(pass_context=True)
	async def resurrect(self, ctx):
		"""Restore life to the bot.  What magic is this?"""
		
		channel = ctx.message.channel
		author  = ctx.message.author
		server  = ctx.message.server
		
		# Check for role requirements
		requiredRole = self.settings.getServerStat(server, "RequiredKillRole")
		if requiredRole == "":
			#admin only
			isAdmin = author.permissions_in(channel).administrator
			if not isAdmin:
				await self.bot.send_message(channel, 'You do not have sufficient privileges to access this command.')
				return
		else:
			#role requirement
			hasPerms = False
			for role in author.roles:
				if role.id == requiredRole:
					hasPerms = True
			if not hasPerms:
				await self.bot.send_message(channel, 'You do not have sufficient privileges to access this command.')
				return
		
		self.settings.setServerStat(server, "Killed", "No")
		self.settings.setServerStat(server, "Hunger", "0")
		killedBy = self.settings.getServerStat(server, "KilledBy")
		await self.bot.send_message(channel, 'Guess who\'s back??\n\n*{}* may have tried to keep me down - but I *just keep coming back!*'.format(killedBy))
		
	@commands.command(pass_context=True)
	async def iskill(self, ctx):
		"""Check the ded of the bot."""
		
		channel = ctx.message.channel
		author  = ctx.message.author
		server  = ctx.message.server
		
		isKill = self.settings.getServerStat(server, "Killed")
		killedBy = self.settings.getServerStat(server, "KilledBy")
		msg = 'I have no idea what you\'re talking about... Should I be worried?'
		if isKill.lower() == "yes":
			msg = '*Whispers from beyond the grave*\nI am kill...\n\n*{}* did it...'.format(killedBy)
		else:
			msg = 'Wait - are you asking if I\'m *dead*?  Why would you wanna know *that?*'
			
		await self.bot.send_message(channel, msg)
		

	@commands.command(pass_context=True)
	async def setkillrole(self, ctx, role : discord.Role = None):
		"""Sets the required role ID to add/remove hacks (admin only)."""
		
		channel = ctx.message.channel
		author  = ctx.message.author
		server  = ctx.message.server
		
		isAdmin = author.permissions_in(channel).administrator
		# Only allow admins to change server stats
		if not isAdmin:
			await self.bot.send_message(channel, 'You do not have sufficient privileges to access this command.')
			return

		if role == None:
			self.settings.setServerStat(server, "RequiredKillRole", "")
			msg = 'Kill/resurrect now *admin-only*.'
			await self.bot.send_message(channel, msg)
			return

		if type(role) is str:
			try:
				role = discord.utils.get(server.roles, name=role)
			except:
				print("That role does not exist")
				return

		# If we made it this far - then we can add it
		self.settings.setServerStat(server, "RequiredKillRole", role.id)

		msg = 'Role required for kill/resurrect set to *{}*.'.format(role.name)
		await self.bot.send_message(channel, msg)

	@setkillrole.error
	async def killrole_error(ctx, error):
		# do stuff
		msg = 'setkillrole Error: {}'.format(ctx)
		await self.bot.say(msg)