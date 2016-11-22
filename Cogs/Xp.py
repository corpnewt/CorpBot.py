import asyncio
import discord
import datetime
import random
from   discord.ext import commands
from   operator import itemgetter
from   Cogs import Settings
from   Cogs import DisplayName

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
						self.settings.incrementStat(user, server, "XPReserve", int(xpAmount))

	@commands.command(pass_context=True)
	async def setxp(self, ctx, member : discord.Member = None, xpAmount : int = None):
		"""Sets an absolute value for the member's xp (admin only)."""
		
		author  = ctx.message.author
		server  = ctx.message.server
		channel = ctx.message.channel
		
		isAdmin = author.permissions_in(channel).administrator
		# Only allow admins to change server stats
		if not isAdmin:
			await self.bot.send_message(channel, 'You do not have sufficient privileges to access this command.')
			return

		# Check for formatting issues
		if not (xpAmount or member):
			msg = 'Usage: `$setxp [member] [amount]`'
			await self.bot.send_message(channel, msg)
			return
		if not type(xpAmount) is int:
			msg = 'Usage: `$setxp [member] [amount]`'
			await self.bot.send_message(channel, msg)
			return
		if xpAmount < 0:
			msg = 'Usage: `$setxp [member] [amount]`'
			await self.bot.send_message(channel, msg)
			return
		if type(member) is str:
			try:
				member = discord.utils.get(server.members, name=member)
			except:
				print("That member does not exist")
				return

		self.settings.setUserStat(member, server, "XP", xpAmount)
		msg = '*{}\'s* xp was set to *{}!*'.format(DisplayName.name(member), xpAmount)
		await self.bot.send_message(channel, msg)
		await self.checkroles(member, channel)


	@setxp.error
	async def setxp_error(self, ctx, error):
		# do stuff
		msg = 'setxp Error: {}'.format(ctx)
		await self.bot.say(msg)
	
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
		requiredXP = self.settings.getServerStat(server, "RequiredXPRole")

		approve = True
		decrement = True

		# RequiredXPRole
		if requiredXP:
			foundRole = False
			for checkRole in author.roles:
				if checkRole.id == requiredXP:
					foundRole = True
			if not foundRole:
				approve = False
				msg = msg = 'You don\'t have the permissions to give xp.'

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

		if approve:
			# XP was approved!  Let's say it - and check decrement from gifter's xp reserve
			msg = '*{}* was given *{} xp!*'.format(DisplayName.name(member), xpAmount)
			await self.bot.send_message(channel, msg)
			self.settings.incrementStat(member, server, "XP", xpAmount)
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
	async def defaultrole(self, ctx):
		"""Lists the default role that new users are assigned."""
		role = self.settings.getServerStat(ctx.message.server, "DefaultRole")
		if role == None or role == "":
			msg = 'New users are not assigned a role on joining this server.'
			await self.bot.say(msg)
		else:
			# Role is set - let's get its name
			found = False
			for arole in ctx.message.server.roles:
				if arole.id == role:
					found = True
					msg = 'New users will be assigned to **{}**.'.format(arole.name)
			if not found:
				msg = 'There is no role that matches id: `{}` - consider updating this setting.'.format(role)
			await self.bot.send_message(ctx.message.channel, msg)
		
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
		requiredXP = self.settings.getServerStat(server, "RequiredXPRole")

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

		# RequiredXPRole
		if requiredXP:
			foundRole = False
			for checkRole in author.roles:
				if checkRole.id == requiredXP:
					foundRole = True
			if not foundRole:
				approve = False
				msg = msg = 'You don\'t have the permissions to gamble.'
			
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
				msg = '*{}* bet *{}* and ***WON*** *{} xp!*'.format(DisplayName.name(author), bet, int(payout))
			else:
				msg = '*{}* bet *{}* and.... *didn\'t* win.  Better luck next time!'.format(DisplayName.name(author), bet)
			
		await self.bot.send_message(ctx.message.channel, msg)
			
			
	async def checkroles(self, user, channel):
		# This method checks whether we need to promote, demote, or whatever
		# then performs the said action, and outputs.
		
		server = channel.server
		
		# Get our preliminary vars
		msg         = None
		xpPromote   = self.settings.getServerStat(server,     "XPPromote")
		xpDemote    = self.settings.getServerStat(server,     "XPDemote")
		userXP      = self.settings.getUserStat(user, server, "XP")
		
		if xpPromote.lower() == "yes":
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
						msg = '*{}* was promoted to **{}**!'.format(DisplayName.name(user), currentRole.name)
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
							msg = '*{}* was demoted from **{}**!'.format(DisplayName.name(user), currentRole.name)
		# Check if we have a message to display - and display it
		if msg:
			await self.bot.send_message(channel, msg)


	@commands.command(pass_context=True)
	async def listxproles(self, ctx):
		"""Lists all roles, id's, and xp requirements for the xp promotion/demotion system."""
		
		server  = ctx.message.server
		channel = ctx.message.channel
		
		# Get the array
		promoArray = self.settings.getServerStat(server, "PromotionArray")

		# Sort by XP first, then by name
		# promoSorted = sorted(promoArray, key=itemgetter('XP', 'Name'))
		promoSorted = sorted(promoArray, key=lambda x:int(x['XP']))
		
		roleText = "Current Roles:\n"
		for arole in promoSorted:
			roleText = '{}**{}** : *{} XP*\n'.format(roleText, arole['Name'], arole['XP'], arole['ID'])

		# Get the required role for using the xp system
		role = self.settings.getServerStat(ctx.message.server, "RequiredXPRole")
		if role == None or role == "":
			roleText = '{}\n**Everyone** can give xp, gamble, and feed the bot.'.format(roleText)
		else:
			# Role is set - let's get its name
			found = False
			for arole in ctx.message.server.roles:
				if arole.id == role:
					found = True
					roleText = '{}\nYou need to be a/an **{}** to give xp, gamble, or feed the bot.'.format(roleText, arole.name)
			if not found:
				roleText = '{}\nThere is no role that matches id: `{}` for using the xp system - consider updating that settings.'.format(roleText, role)

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
		# promoSorted = sorted(promoArray, key=itemgetter('XP', 'Name'))
		promoSorted = sorted(promoArray, key=lambda x:int(x['XP']))
		
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
			msg = '*{}* has not acquired a rank yet.'.format(DisplayName.name(member))
		else:
			msg = '*{}* is a **{}**!'.format(DisplayName.name(member), highestRole)
			
		await self.bot.send_message(ctx.message.channel, msg)
		
	@rank.error
	async def rank_error(self, ctx, error):
		msg = 'rank Error: {}'.format(ctx)
		await self.bot.say(msg)


	# List the top 10 xp-holders
	@commands.command(pass_context=True)
	async def topxp(self, ctx):
		"""List the top 10 xp-holders - or all members, if there are less than 10 total."""
		promoArray = self.settings.getServerStat(ctx.message.server, "Members")
		promoSorted = sorted(promoArray, key=lambda x:int(x['XP']))
		# promoSorted = sorted(promoArray, key=itemgetter('XP'))

		startIndex = 0
		total = 10
		msg = ""

		if len(promoSorted) < 9:
			total = len(promoSorted)
		
		if len(promoSorted):
			# makes sure we have at least 1 user - shouldn't be necessary though
			startIndex = len(promoSorted)-1
			msg = "**Top** ***{}*** **XP-Holders in** ***{}***:\n".format(total, ctx.message.server.name)

		for i in range(0, total):
			# Loop through from startIndex to startIndex+total-1
			index = startIndex-i
			cMemName = "{}#{}".format(promoSorted[index]['Name'], promoSorted[index]['Discriminator'])

			if ctx.message.server.get_member_named(cMemName):
				# Member exists
				cMember = ctx.message.server.get_member_named(cMemName)
			else:
				cMember = None
			if cMember:
				cMemberDisplay = DisplayName.name(cMember)
			else:
				cMemberDisplay = promoSorted[index]['Name']

			msg = '{}\n{}. *{}* - *{} xp*'.format(msg, i+1, cMemberDisplay, promoSorted[index]['XP'])

		await self.bot.send_message(ctx.message.channel, msg)

		
	# List the top 10 xp-holders
	@commands.command(pass_context=True)
	async def bottomxp(self, ctx):
		"""List the bottom 10 xp-holders - or all members, if there are less than 10 total."""
		promoArray = self.settings.getServerStat(ctx.message.server, "Members")
		# promoSorted = sorted(promoArray, key=itemgetter('XP'))
		promoSorted = sorted(promoArray, key=lambda x:int(x['XP']))

		startIndex = 0
		total = 10
		msg = ""

		if len(promoSorted) < 9:
			total = len(promoSorted)
		
		if len(promoSorted):
			# makes sure we have at least 1 user - shouldn't be necessary though
			msg = "**Bottom** ***{}*** **XP-Holders in** ***{}***:\n".format(total, ctx.message.server.name)

		for i in range(0, total):
			# Loop through from startIndex to startIndex+total-1
			index = startIndex+i
			cMemName = "{}#{}".format(promoSorted[index]['Name'], promoSorted[index]['Discriminator'])
			if ctx.message.server.get_member_named(cMemName):
				# Member exists
				cMember = ctx.message.server.get_member_named(cMemName)
			else:
				cMember = None
			if cMember:
					cMemberDisplay = DisplayName.name(cMember)
			else:
				cMemberDisplay = promoSorted[index]['Name']
			msg = '{}\n{}. *{}* - *{} xp*'.format(msg, i+1, cMemberDisplay, promoSorted[index]['XP'])

		await self.bot.send_message(ctx.message.channel, msg)
		
		
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

		msg = '*{}* has *{} xp*, and can gift up to *{} xp!*'.format(DisplayName.name(member), newStat, newState)

		# Get user's current role
		promoArray = self.settings.getServerStat(ctx.message.server, "PromotionArray")
		# promoSorted = sorted(promoArray, key=itemgetter('XP', 'Name'))
		promoSorted = sorted(promoArray, key=lambda x:int(x['XP']))
		
		highestRole = None
		if len(promoSorted):
			nextRole = promoSorted[0]
		else:
			nextRole = None

		for role in promoSorted:
			if nextRole['XP'] < newStat:
				nextRole = role
			# We *can* have this role, let's see if we already do
			currentRole = None
			for aRole in member.roles:
				# Get the role that corresponds to the id
				if aRole.id == role['ID']:
					# We found it
					highestRole = aRole.name
					if len(promoSorted) > (promoSorted.index(role)+1):
						# There's more roles above this
						nextRole = role


		if highestRole:
			msg = '{}\nThey are a **{}**!'.format(msg, highestRole)
		else:
			msg = '{}\nThey have not acquired a rank yet.'.format(msg)
		
		if nextRole and (newStat < nextRole['XP']):
			msg = '{}\nThey need *{}* more xp to advance to **{}**!'.format(msg, nextRole['XP'] - newStat, nextRole['Name'])

		await self.bot.send_message(ctx.message.channel, msg)
		
	@stats.error
	async def stats_error(self, ctx, error):
		msg = 'stats Error: {}'.format(ctx)
		await self.bot.say(msg)
