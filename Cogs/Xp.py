import asyncio
import discord
import datetime
import random
from   discord.ext import commands
from   operator import itemgetter
from   Cogs import Settings

# This is the xp module.  It's likely to be retarded.

class Xp:

	# Init with the bot reference, and a reference to the settings var
	def __init__(self, bot, settings):
		self.bot = bot
		self.settings = settings
		self.bot.loop.create_task(self.addXP())
		
	def message(self, message):
		# Check the message and see if we should allow it - always yes.
		# This module doesn't need to cancel messages.
		return { 'Ignore' : False, 'Delete' : False}
		
	async def addXP(self):
		while not self.bot.is_closed:
			await asyncio.sleep(3600) # runs only every 1 hour (3600 seconds)
			print("Adding XP: {}".format(datetime.datetime.now().time().isoformat()))
			for server in self.bot.servers:
				# Iterate through the servers and add them
				xpAmount   = self.settings.getServerStat(server, "HourlyXP")
				onlyOnline = self.settings.getServerStat(server, "RequireOnline")
				for user in server.members:
					bumpXP = False
					if onlyOnline.lower() == "no":
						bumpXP = True
					else:
						if str(user.status).lower() == "online":
							bumpXP = True
							
					if bumpXP:
						boost          = int(self.settings.getServerStat(server, "IncreasePerRank"))
						promoteBy      = self.settings.getServerStat(server,     "PromoteBy")
						if promoteBy.lower() == "position":
							maxPos     = int(self.settings.getServerStat(server, "MaxPosition"))
						else:
							promoArray = self.settings.getServerStat(server, "PromotionArray")
							maxPos     = len(promoArray)-1
						biggest        = 0
						xpPayload      = 0
						for role in user.roles:
							if role.position <= maxPos and role.position > biggest:
								biggest = role.position

						xpPayload = int(xpAmount)
						self.settings.incrementStat(user, server, "XPReserve", xpPayload)
	
	@commands.command(pass_context=True)
	async def xp(self, ctx, member : discord.Member = None, xpAmount : int = None):
		"""Gift xp to other members."""
		
		author  = ctx.message.author
		server  = ctx.message.server
		channel = ctx.message.channel
		
		# Check for formatting issues
		if xpAmount == None or member == None:
			msg = 'Usage: `$xp [member] [amount]`'
			await self.bot.send_message(channel, msg)
			return
		if not type(xpAmount) is int:
			msg = 'Usage: `$xp [member] [amount]`'
			await self.bot.send_message(channel, msg)
			return
		if type(member) is str:
			try:
				member = discord.utils.get(server.members, name=member)
			except:
				print("That member does not exist")
				return
		# Get our user/server stats
		isAdmin    = author.permissions_in(channel).administrator
		adminUnlim = self.settings.getServerStat(server, "AdminUnlimited")
		reserveXP  = self.settings.getUserStat(author, server, "XPReserve")
		minRole    = self.settings.getServerStat(server, "MinimumXPRole")

		approve = True
		decrement = True

		# MinimumXPRole
		if author.top_role.position < int(minRole):
			approve = False
			msg = 'You don\'t have the permissions to give xp.'

		if xpAmount > int(reserveXP):
			approve = False
			msg = 'You can\'t give *{} xp*, you only have *{}!*'.format(xpAmount, reserveXP)

		if author == member:
			approve = False
			msg = 'You can\'t give yourself xp!  *Nice try...*'

		if xpAmount < 0:
			msg = 'Only admins can take away xp!'
			approve = False

		# Check admin last - so it overrides anything else
		if isAdmin and adminUnlim.lower() == "yes":
			# No limit - approve
			approve = True
			decrement = False

		userRole = member.top_role.position

		if approve:
			# XP was approved!  Let's say it - and check decrement from gifter's xp reserve
			msg = '*{}* was given *{} xp!*'.format(member.name, xpAmount)
			await self.bot.send_message(channel, msg)
			newXP = self.settings.incrementStat(member, server, "XP", xpAmount)
			if decrement:
				self.settings.incrementStat(author, server, "XPReserve", (-1*xpAmount))
			# Now we check for promotions
			await self.checkroles(member, channel)
		else:
			await self.bot.send_message(channel, msg)
			
	@xp.error
	async def xp_error(self, ctx, error):
		msg = 'xp Error: {}'.format(ctx)
		await self.bot.say(msg)
		
	@commands.command(pass_context=True)
	async def gamble(self, ctx, bet : int = None):
		"""Gamble your xp reserves for a chance at winning xp!"""
		
		author  = ctx.message.author
		server  = ctx.message.server
		channel = ctx.message.channel
		
		# bet must be a multiple of 10, member must have enough xpreserve to bet
		msg = 'Usage: `gamble [xp reserve bet] (must be multiple of 10)`'
		
		if not (bet or type(bet) == int):
			await self.bot.send_message(channel, msg)
			return
			
		if not type(bet) == int:
			await self.bot.send_message(channel, msg)
			return

		isAdmin    = author.permissions_in(channel).administrator
		adminUnlim = self.settings.getServerStat(server, "AdminUnlimited")
		reserveXP  = self.settings.getUserStat(author, server, "XPReserve")
		minRole    = self.settings.getServerStat(server, "MinimumXPRole")

		approve = True
		decrement = True

		# Check Bet
			
		if not bet % 10 == 0:
			approve = False
			msg = 'Bets must be in multiples of *10!*'
			
		if bet > int(reserveXP):
			approve = False
			msg = 'You can\'t bet *{}*, you only have *{}* xp reserve!'.format(bet, reserveXP)
			
		if bet < 0:
			msg = 'You can\'t bet negative amounts!'
			approve = False
			
		if bet == 0:
			msg = 'You can\'t bet *nothing!*'
			approve = False
			
		if author.top_role.position < int(minRole):
			approve = False
			msg = 'You don\'t have the permissions to bet.'
			
		# Check admin last - so it overrides anything else
		if isAdmin and adminUnlim.lower() == "yes":
			# No limit - approve
			approve = True
			decrement = False
			
		if approve:
			# Bet was approved - let's take the XPReserve right away
			if decrement:
				takeReserve = -1*bet
				self.settings.incrementStat(author, server, "XPReserve", takeReserve)
			
			# Bet more, less chance of winning, but more winnings!
			if bet < 100:
				betChance = 5
				payout = int(bet/10)
			elif bet < 500:
				betChance = 15
				payout = int(bet/4)
			else:
				betChance = 25
				payout = int(bet/2)
			
			# 1/betChance that user will win - and payout is 1/10th of the bet
			randnum = random.randint(1, betChance)
			# print('{} : {}'.format(randnum, betChance))
			if randnum == 1:
				# YOU WON!!
				self.settings.incrementStat(author, server, "XP", int(payout))
				msg = '{} bet {} and ***WON*** *{} xp!*'.format(author.name, bet, int(payout))
			else:
				msg = '*{}* bet *{}* and.... *didn\'t* win.  Better luck next time!'.format(author.name, bet)
			
		await self.bot.send_message(ctx.message.channel, msg)
			
			
	async def checkroles(self, user, channel):
		# This method checks whether we need to promote, demote, or whatever
		# then performs the said action, and outputs.
		
		server = channel.server
		
		# Get our preliminary vars
		msg         = None
		xpPromote   = self.settings.getServerStat(server,     "XPPromote")
		xpDemote    = self.settings.getServerStat(server,     "XPDemote")
		promoteBy   = self.settings.getServerStat(server,     "PromoteBy")
		requiredXP  = int(self.settings.getServerStat(server, "RequiredXP"))
		maxPosition = self.settings.getServerStat(server,     "MaxPosition")
		padXP       = self.settings.getServerStat(server,     "PadXPRoles")
		difficulty  = int(self.settings.getServerStat(server, "DifficultyMultiplier"))
		userXP      = self.settings.getUserStat(user, server, "XP")
		# Apply the pad
		userXP      = int(userXP)+(int(requiredXP)*int(padXP))
		
		if xpPromote.lower() == "yes":
			# We use XP to promote - let's check our levels
			if promoteBy.lower() == "position":
				# We use the position to promote
				# For now, this should be unused - it's unreliable
				gotLevels = 0
				for x in range(0, int(maxPosition)+1):
					# Get required xp per level
					required = (requiredXP*x) + (requiredXP*difficulty)
					if userXP >= required:
						gotLevels = x
				if gotLevels > int(maxPosition):
					# If we got too high - let's even out
					gotLevels = int(maxPosition)
				# Add 1 for our range, since it goes from 0 -> (gotLevels-1)
				gotLevels+=1
				for x in range(0, gotLevels):
					# fill in all the roles between
					for role in server.roles:
						if role.position < gotLevels:
							if not role in user.roles:
								# Only add if we need to
								await self.bot.add_roles(user, role)
								msg = '*{}* was promoted to **{}**!'.format(user.name, discord.utils.get(server.roles, position=gotLevels).name)
			elif promoteBy.lower() == "array":
				# This is, by far, the more functional way
				promoArray = self.settings.getServerStat(server, "PromotionArray")
				for role in promoArray:
					# Iterate through the roles, and add which we have xp for
					if int(role['XP']) <= userXP:
						# We *can* have this role, let's see if we already do
						currentRole = None
						for aRole in server.roles:
							# Get the role that corresponds to the id
							if aRole.id == role['ID']:
								# We found it
								currentRole = aRole
						# Now see if we have it, and add it if we don't
						if not currentRole in user.roles:
							await self.bot.add_roles(user, currentRole)
							msg = '*{}* was promoted to **{}**!'.format(user.name, currentRole.name)
					else:
						if xpDemote.lower() == "yes":
							# Let's see if we have this role, and remove it.  Demote time!
							currentRole = None
							for aRole in server.roles:
								# Get the role that corresponds to the id
								if aRole.id == role['ID']:
									# We found it
									currentRole = aRole
							# Now see if we have it, and take it away!
							if currentRole in user.roles:
								await self.bot.remove_roles(user, currentRole)
								msg = '*{}* was demoted from **{}**!'.format(user.name, currentRole.name)
		# Check if we have a message to display - and display it
		if msg:
			await self.bot.send_message(channel, msg)


	@commands.command(pass_context=True)
	async def listroles(self, ctx):
		"""Lists all roles, id's, and xp requirements for the xp promotion/demotion system."""
		
		server  = ctx.message.server
		channel = ctx.message.channel
		
		# Get the array
		promoArray = self.settings.getServerStat(server, "PromotionArray")

		# Sort by XP first, then by name
		promoSorted = sorted(promoArray, key=itemgetter('XP', 'Name'))
		
		roleText = "Current Roles:\n"
		for arole in promoSorted:
			roleText = '{}**{}** : *{} XP*\n'.format(roleText, arole['Name'], arole['XP'], arole['ID'])

		await self.bot.send_message(channel, roleText)
		
		
	@commands.command(pass_context=True)
	async def rank(self, ctx, member: discord.Member = None):
		"""Say the highest rank of a listed member."""
		
		if member is None:
			member = ctx.message.author
			
		if type(member) is str:
			try:
				member = discord.utils.get(server.members, name=member)
			except:
				print("That member does not exist")
				return
			
		promoArray = self.settings.getServerStat(ctx.message.server, "PromotionArray")
		promoSorted = sorted(promoArray, key=itemgetter('XP', 'Name'))
		
		highestRole = ""
		
		for role in promoSorted:
			# We *can* have this role, let's see if we already do
			currentRole = None
			for aRole in member.roles:
				# Get the role that corresponds to the id
				if aRole.id == role['ID']:
					# We found it
					highestRole = aRole.name

		if highestRole == "":
			msg = '*{}* has not acquired a rank yet.'.format(member.name)
		else:
			msg = '*{}* is a **{}**!'.format(member.name, highestRole)
			
		await self.bot.send_message(ctx.message.channel, msg)
		
	@rank.error
	async def rank_error(self, ctx, error):
		msg = 'rank Error: {}'.format(ctx)
		await self.bot.say(msg)
		
		
	# List the xp and xp reserve of a user
	@commands.command(pass_context=True)
	async def stats(self, ctx, member: discord.Member = None):
		"""List the xp and xp reserve of a listed member."""
		if member is None:
			member = ctx.message.author
		
		if type(member) is str:
			try:
				member = discord.utils.get(server.members, name=member)
			except:
				print("That member does not exist")
				return

		# Get user's xp
		newStat = self.settings.getUserStat(member, ctx.message.server, "XP")
		newState = self.settings.getUserStat(member, ctx.message.server, "XPReserve")

		msg = '*{}* has *{} xp*, and can gift up to *{} xp!*'.format(member.name, newStat, newState)
		await self.bot.send_message(ctx.message.channel, msg)
		
	@stats.error
	async def stats_error(self, ctx, error):
		msg = 'stats Error: {}'.format(ctx)
		await self.bot.say(msg)