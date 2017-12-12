import asyncio
import discord
import datetime
import random
from   discord.ext import commands
from   operator import itemgetter
from   Cogs import Settings
from   Cogs import DisplayName
from   Cogs import Nullify
from   Cogs import CheckRoles
from   Cogs import UserTime

def setup(bot):
	# Add the bot and deps
	settings = bot.get_cog("Settings")
	bot.add_cog(Xp(bot, settings))

# This is the xp module.  It's likely to be retarded.

class Xp:

	# Init with the bot reference, and a reference to the settings var
	def __init__(self, bot, settings):
		self.bot = bot
		self.settings = settings
		self.loop_list = []

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

	# Proof of concept stuff for reloading cog/extension
	def _is_submodule(self, parent, child):
		return parent == child or child.startswith(parent + ".")

	@asyncio.coroutine
	async def on_unloaded_extension(self, ext):
		# Called to shut things down
		if not self._is_submodule(ext.__name__, self.__module__):
			return
		for task in self.loop_list:
			task.cancel()

	@asyncio.coroutine
	async def on_loaded_extension(self, ext):
		# See if we were loaded
		if not self._is_submodule(ext.__name__, self.__module__):
			return
		self.loop_list.append(self.bot.loop.create_task(self.addXP()))

	def suppressed(self, guild, msg):
		# Check if we're suppressing @here and @everyone mentions
		if self.settings.getServerStat(guild, "SuppressMentions"):
			return Nullify.clean(msg)
		else:
			return msg
		
	async def addXP(self):
		await self.bot.wait_until_ready()
		while not self.bot.is_closed():
			await asyncio.sleep(600) # runs only every 10 minutes (600 seconds)
			print("Adding XP: {}".format(datetime.datetime.now().time().isoformat()))
			for server in self.bot.guilds:
				# Iterate through the servers and add them
				xpAmount   = int(self.settings.getServerStat(server, "HourlyXP"))
				xpAmount   = float(xpAmount/6)
				xpRAmount  = int(self.settings.getServerStat(server, "HourlyXPReal"))
				xpRAmount  = float(xpRAmount/6)

				xpLimit    = self.settings.getServerStat(server, "XPLimit")
				xprLimit   = self.settings.getServerStat(server, "XPReserveLimit")
				
				onlyOnline = self.settings.getServerStat(server, "RequireOnline")
				requiredXP = self.settings.getServerStat(server, "RequiredXPRole")
				
				for user in server.members:
					
					if not self._can_xp(user, server):
						continue

					bumpXP = False
					if onlyOnline == False:
						bumpXP = True
					else:
						if user.status == discord.Status.online:
							bumpXP = True

					# Check if we're blocked
					xpblock = self.settings.getServerStat(server, "XpBlockArray")
					if user.id in xpblock:
						# No xp for you
						continue

					for role in user.roles:
						if role.id in xpblock:
							bumpXP = False
							break
							
					if bumpXP:
						if xpAmount > 0:
							# User is online add hourly xp reserve
							
							# First we check if we'll hit our limit
							skip = False
							if not xprLimit == None:
								# Get the current values
								newxp = self.settings.getUserStat(user, server, "XPReserve")
								# Make sure it's this xpr boost that's pushing us over
								# This would only push us up to the max, but not remove
								# any we've already gotten
								if newxp + xpAmount > xprLimit:
									skip = True
									if newxp < xprLimit:
										self.settings.setUserStat(user, server, "XPReserve", xprLimit)
							if not skip:
								xpLeftover = self.settings.getUserStat(user, server, "XPLeftover")

								if xpLeftover == None:
									xpLeftover = 0
								else:
									xpLeftover = float(xpLeftover)
								gainedXp = xpLeftover+xpAmount
								gainedXpInt = int(gainedXp) # Strips the decimal point off
								xpLeftover = float(gainedXp-gainedXpInt) # Gets the < 1 value
								self.settings.setUserStat(user, server, "XPLeftover", xpLeftover)
								self.settings.incrementStat(user, server, "XPReserve", gainedXpInt)
						
						if xpRAmount > 0:
							# User is online add hourly xp

							# First we check if we'll hit our limit
							skip = False
							if not xpLimit == None:
								# Get the current values
								newxp = self.settings.getUserStat(user, server, "XP")
								# Make sure it's this xpr boost that's pushing us over
								# This would only push us up to the max, but not remove
								# any we've already gotten
								if newxp + xpRAmount > xpLimit:
									skip = True
									if newxp < xpLimit:
										self.settings.setUserStat(user, server, "XP", xpLimit)
							if not skip:
								xpRLeftover = self.settings.getUserStat(user, server, "XPRealLeftover")
								if xpRLeftover == None:
									xpRLeftover = 0
								else:
									xpRLeftover = float(xpRLeftover)
								gainedXpR = xpRLeftover+xpRAmount
								gainedXpRInt = int(gainedXpR) # Strips the decimal point off
								xpRLeftover = float(gainedXpR-gainedXpRInt) # Gets the < 1 value
								self.settings.setUserStat(user, server, "XPRealLeftover", xpRLeftover)
								self.settings.incrementStat(user, server, "XP", gainedXpRInt)

							# Check our default channels
							targetChan = server.get_channel(server.id)
							targetChanID = self.settings.getServerStat(server, "DefaultChannel")
							if len(str(targetChanID)):
								# We *should* have a channel
								tChan = self.bot.get_channel(int(targetChanID))
								if tChan:
									# We *do* have one
									targetChan = tChan
						
							# Check for promotion/demotion
							try:
								if targetChan:
									await CheckRoles.checkroles(user, targetChan, self.settings, self.bot)
								else:
									# No channel - just pass the server, and we'll do without messages
									await CheckRoles.checkroles(user, server, self.settings, self.bot)
							except Exception:
								continue

	@commands.command(pass_context=True)
	async def xp(self, ctx, *, member = None, xpAmount : int = None):
		"""Gift xp to other members."""

		author  = ctx.message.author
		server  = ctx.message.guild
		channel = ctx.message.channel

		# Check if we're suppressing @here and @everyone mentions
		if self.settings.getServerStat(server, "SuppressMentions"):
			suppress = True
		else:
			suppress = False

		usage = 'Usage: `{}xp [role/member] [amount]`'.format(ctx.prefix)

		isRole = False

		if member == None:
			await ctx.message.channel.send(usage)
			return

		# Check for formatting issues
		if xpAmount == None:
			# Either xp wasn't set - or it's the last section
			if type(member) is str:
				# It' a string - the hope continues
				roleCheck = DisplayName.checkRoleForInt(member, server)
				if not roleCheck:
					# Returned nothing - means there isn't even an int
					msg = 'I couldn\'t find *{}* on the server.'.format(member)
					# Check for suppress
					if suppress:
						msg = Nullify.clean(msg)
					await ctx.message.channel.send(msg)
					return
				if roleCheck["Role"]:
					isRole = True
					member   = roleCheck["Role"]
					xpAmount = roleCheck["Int"]
				else:
					# Role is invalid - check for member instead
					nameCheck = DisplayName.checkNameForInt(member, server)
					if not nameCheck:
						await ctx.message.channel.send(usage)
						return
					if not nameCheck["Member"]:
						msg = 'I couldn\'t find *{}* on the server.'.format(member)
						# Check for suppress
						if suppress:
							msg = Nullify.clean(msg)
						await ctx.message.channel.send(msg)
						return
					member   = nameCheck["Member"]
					xpAmount = nameCheck["Int"]

		if xpAmount == None:
			# Still no xp - let's run stats instead
			if isRole:
				await ctx.message.channel.send(usage)
			else:
				await ctx.invoke(self.stats, member=member)
			return
		if not type(xpAmount) is int:
			await ctx.message.channel.send(usage)
			return

		# Get our user/server stats
		isAdmin         = author.permissions_in(channel).administrator
		checkAdmin = self.settings.getServerStat(ctx.message.guild, "AdminArray")
		# Check for bot admin
		isBotAdmin      = False
		for role in ctx.message.author.roles:
			for aRole in checkAdmin:
				# Get the role that corresponds to the id
				if str(aRole['ID']) == str(role.id):
					isBotAdmin = True
					break

		botAdminAsAdmin = self.settings.getServerStat(server, "BotAdminAsAdmin")
		adminUnlim      = self.settings.getServerStat(server, "AdminUnlimited")
		reserveXP       = self.settings.getUserStat(author, server, "XPReserve")
		requiredXP      = self.settings.getServerStat(server, "RequiredXPRole")
		xpblock         = self.settings.getServerStat(server, "XpBlockArray")

		approve = True
		decrement = True
		admin_override = False

		# RequiredXPRole
		if not self._can_xp(author, server):
			approve = False
			msg = 'You don\'t have the permissions to give xp.'

		if xpAmount > int(reserveXP):
			approve = False
			msg = 'You can\'t give *{:,} xp*, you only have *{:,}!*'.format(xpAmount, reserveXP)

		if author == member:
			approve = False
			msg = 'You can\'t give yourself xp!  *Nice try...*'

		if xpAmount < 0:
			msg = 'Only admins can take away xp!'
			approve = False
			# Avoid admins gaining xp
			decrement = False

		if xpAmount == 0:
			msg = 'Wow, very generous of you...'
			approve = False

		# Check bot admin
		if isBotAdmin and botAdminAsAdmin:
			# Approve as admin
			approve = True
			admin_override = True
			if adminUnlim:
				# No limit
				decrement = False
			else:
				if xpAmount < 0:
					# Don't decrement if negative
					decrement = False
				if xpAmount > int(reserveXP):
					# Don't approve if we don't have enough
					msg = 'You can\'t give *{:,} xp*, you only have *{:,}!*'.format(xpAmount, reserveXP)
					approve = False
			
		# Check admin last - so it overrides anything else
		if isAdmin:
			# No limit - approve
			approve = True
			admin_override = True
			if adminUnlim:
				# No limit
				decrement = False
			else:
				if xpAmount < 0:
					# Don't decrement if negative
					decrement = False
				if xpAmount > int(reserveXP):
					# Don't approve if we don't have enough
					msg = 'You can\'t give *{:,} xp*, you only have *{:,}!*'.format(xpAmount, reserveXP)
					approve = False

		# Check author and target for blocks
		# overrides admin because admins set this.
		if type(member) is discord.Role:
			if member.id in xpblock:
				msg = "That role cannot receive xp!"
				approve = False
		else:
			# User
			if member.id in xpblock:
				msg = "That member cannot receive xp!"
				approve = False
			else:
				for role in member.roles:
					if role.id in xpblock:
						msg = "That member's role cannot receive xp!"
						approve = False
		
		if ctx.author.id in xpblock:
			msg = "You can't give xp!"
			approve = False
		else:
			for role in ctx.author.roles:
				if role.id in xpblock:
					msg = "Your role cannot give xp!"
					approve = False

		if approve:

			self.bot.dispatch("xp", member, ctx.author, xpAmount)

			if isRole:
				# XP was approved - let's iterate through the users of that role,
				# starting with the lowest xp
				#
				# Work through our members
				memberList = []
				sMemberList = self.settings.getServerStat(server, "Members")
				for amem in server.members:
					if amem == author:
						continue
					if amem.id in xpblock:
						# Blocked - only if not admin sending it
						continue
					roles = amem.roles
					if member in roles:
						# This member has our role
						# Add to our list
						for smem in sMemberList:
							# Find our server entry
							if str(smem) == str(amem.id):
								# Add it.
								sMemberList[smem]["ID"] = smem
								memberList.append(sMemberList[smem])
				memSorted = sorted(memberList, key=lambda x:int(x['XP']))
				if len(memSorted):
					# There actually ARE members in said role
					totalXP = xpAmount
					if xpAmount > len(memSorted):
						# More xp than members
						leftover = xpAmount % len(memSorted)
						eachXP = (xpAmount-leftover)/len(memSorted)
						for i in range(0, len(memSorted)):
							cMember = DisplayName.memberForID(memSorted[i]['ID'], server)
							if leftover>0:
								self.settings.incrementStat(cMember, server, "XP", eachXP+1)
								leftover -= 1
							else:
								self.settings.incrementStat(cMember, server, "XP", eachXP)
							await CheckRoles.checkroles(cMember, channel, self.settings, self.bot)
					else:
						for i in range(0, xpAmount):
							cMember = DisplayName.memberForID(memSorted[i]['ID'], server)
							self.settings.incrementStat(cMember, server, "XP", 1)
							await CheckRoles.checkroles(cMember, channel, self.settings, self.bot)

					# Decrement if needed
					if decrement:
						self.settings.incrementStat(author, server, "XPReserve", (-1*xpAmount))
					msg = '*{:,} collective xp* was given to *{}!*'.format(totalXP, member.name)
					# Check for suppress
					if suppress:
						msg = Nullify.clean(msg)
					await channel.send(msg)
				else:
					msg = 'There are no eligible members in *{}!*'.format(member.name)
					await channel.send(msg)

			else:
				# Decrement if needed
				if decrement:
					self.settings.incrementStat(author, server, "XPReserve", (-1*xpAmount))
				# XP was approved!  Let's say it - and check decrement from gifter's xp reserve
				msg = '*{}* was given *{:,} xp!*'.format(DisplayName.name(member), xpAmount)
				# Check for suppress
				if suppress:
					msg = Nullify.clean(msg)
				await channel.send(msg)
				self.settings.incrementStat(member, server, "XP", xpAmount)
				# Now we check for promotions
				await CheckRoles.checkroles(member, channel, self.settings, self.bot)
		else:
			await channel.send(msg)
			
	'''@xp.error
	async def xp_error(self, ctx, error):
		msg = 'xp Error: {}'.format(error)
		await ctx.channel.send(msg)'''

	@commands.command(pass_context=True)
	async def defaultrole(self, ctx):
		"""Lists the default role that new users are assigned."""

		# Check if we're suppressing @here and @everyone mentions
		if self.settings.getServerStat(ctx.message.guild, "SuppressMentions"):
			suppress = True
		else:
			suppress = False

		role = self.settings.getServerStat(ctx.message.guild, "DefaultRole")
		if role == None or role == "":
			msg = 'New users are not assigned a role on joining this server.'
			await ctx.channel.send(msg)
		else:
			# Role is set - let's get its name
			found = False
			for arole in ctx.message.guild.roles:
				if str(arole.id) == str(role):
					found = True
					msg = 'New users will be assigned to **{}**.'.format(arole.name)
					# Check for suppress
					if suppress:
						msg = Nullify.clean(msg)
			if not found:
				msg = 'There is no role that matches id: `{}` - consider updating this setting.'.format(role)
			await ctx.message.channel.send(msg)
		
	@commands.command(pass_context=True)
	async def gamble(self, ctx, bet : int = None):
		"""Gamble your xp reserves for a chance at winning xp!"""
		
		author  = ctx.message.author
		server  = ctx.message.guild
		channel = ctx.message.channel
		
		# bet must be a multiple of 10, member must have enough xpreserve to bet
		msg = 'Usage: `{}gamble [xp reserve bet] (must be multiple of 10)`'.format(ctx.prefix)
		
		if not (bet or type(bet) == int):
			await channel.send(msg)
			return
			
		if not type(bet) == int:
			await channel.send(msg)
			return

		isAdmin    = author.permissions_in(channel).administrator
		checkAdmin = self.settings.getServerStat(ctx.message.guild, "AdminArray")
		# Check for bot admin
		isBotAdmin      = False
		for role in ctx.message.author.roles:
			for aRole in checkAdmin:
				# Get the role that corresponds to the id
				if str(aRole['ID']) == str(role.id):
					isBotAdmin = True
					break
		botAdminAsAdmin = self.settings.getServerStat(server, "BotAdminAsAdmin")
		adminUnlim = self.settings.getServerStat(server, "AdminUnlimited")
		reserveXP  = self.settings.getUserStat(author, server, "XPReserve")
		minRole    = self.settings.getServerStat(server, "MinimumXPRole")
		requiredXP = self.settings.getServerStat(server, "RequiredXPRole")
		xpblock    = self.settings.getServerStat(server, "XpBlockArray")

		approve = True
		decrement = True

		# Check Bet
			
		if not bet % 10 == 0:
			approve = False
			msg = 'Bets must be in multiples of *10!*'
			
		if bet > int(reserveXP):
			approve = False
			msg = 'You can\'t bet *{:,}*, you only have *{:,}* xp reserve!'.format(bet, reserveXP)
			
		if bet < 0:
			msg = 'You can\'t bet negative amounts!'
			approve = False
			
		if bet == 0:
			msg = 'You can\'t bet *nothing!*'
			approve = False

		# RequiredXPRole
		if not self._can_xp(author, server):
			approve = False
			msg = 'You don\'t have the permissions to gamble.'
				
		# Check bot admin
		if isBotAdmin and botAdminAsAdmin:
			# Approve as admin
			approve = True
			if adminUnlim:
				# No limit
				decrement = False
			else:
				if bet < 0:
					# Don't decrement if negative
					decrement = False
				if bet > int(reserveXP):
					# Don't approve if we don't have enough
					msg = 'You can\'t bet *{:,}*, you only have *{:,}* xp reserve!'.format(bet, reserveXP)
					approve = False
			
		# Check admin last - so it overrides anything else
		if isAdmin:
			# No limit - approve
			approve = True
			if adminUnlim:
				# No limit
				decrement = False
			else:
				if bet < 0:
					# Don't decrement if negative
					decrement = False
				if bet > int(reserveXP):
					# Don't approve if we don't have enough
					msg = 'You can\'t bet *{:,}*, you only have *{:,}* xp reserve!'.format(bet, reserveXP)
					approve = False

		# Check if we're blocked
		if ctx.author.id in xpblock:
			msg = "You can't gamble for xp!"
			approve = False
		else:
			for role in ctx.author.roles:
				if role.id in xpblock:
					msg = "Your role cannot gamble for xp!"
					approve = False
			
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
				msg = '*{}* bet *{:,}* and ***WON*** *{:,} xp!*'.format(DisplayName.name(author), bet, int(payout))
				# Now we check for promotions
				await CheckRoles.checkroles(author, channel, self.settings, self.bot)
			else:
				msg = '*{}* bet *{:,}* and.... *didn\'t* win.  Better luck next time!'.format(DisplayName.name(author), bet)
			
		await ctx.message.channel.send(msg)
			
	@commands.command(pass_context=True)
	async def recheckroles(self, ctx):
		"""Re-iterate through all members and assign the proper roles based on their xp (admin only)."""

		author  = ctx.message.author
		server  = ctx.message.guild
		channel = ctx.message.channel

		isAdmin = author.permissions_in(channel).administrator

		# Only allow admins to change server stats
		if not isAdmin:
			await channel.send('You do not have sufficient privileges to access this command.')
			return
		
		message = await ctx.channel.send('Checking roles...')

		changeCount = 0
		for member in server.members:
			# Now we check for promotions
			if await CheckRoles.checkroles(member, channel, self.settings, self.bot, True):
				changeCount += 1
		
		if changeCount == 1:
			await message.edit(content='Done checking roles.\n\n*1 user* updated.')
			#await channel.send('Done checking roles.\n\n*1 user* updated.')
		else:
			await message.edit(content='Done checking roles.\n\n*{:,} users* updated.'.format(changeCount))
			#await channel.send('Done checking roles.\n\n*{} users* updated.'.format(changeCount))

	@commands.command(pass_context=True)
	async def recheckrole(self, ctx, *, user : discord.Member = None):
		"""Re-iterate through all members and assign the proper roles based on their xp (admin only)."""

		author  = ctx.message.author
		server  = ctx.message.guild
		channel = ctx.message.channel

		isAdmin = author.permissions_in(channel).administrator

		# Only allow admins to change server stats
		if not isAdmin:
			await channel.send('You do not have sufficient privileges to access this command.')
			return

		if not user:
			user = author

		# Now we check for promotions
		if await CheckRoles.checkroles(user, channel, self.settings, self.bot):
			await channel.send('Done checking roles.\n\n*{}* was updated.'.format(DisplayName.name(user)))
		else:
			await channel.send('Done checking roles.\n\n*{}* was not updated.'.format(DisplayName.name(user)))



	@commands.command(pass_context=True)
	async def listxproles(self, ctx):
		"""Lists all roles, id's, and xp requirements for the xp promotion/demotion system."""
		
		server  = ctx.message.guild
		channel = ctx.message.channel

		# Check if we're suppressing @here and @everyone mentions
		if self.settings.getServerStat(server, "SuppressMentions"):
			suppress = True
		else:
			suppress = False
		
		# Get the array
		promoArray = self.settings.getServerStat(server, "PromotionArray")

		# Sort by XP first, then by name
		# promoSorted = sorted(promoArray, key=itemgetter('XP', 'Name'))
		promoSorted = sorted(promoArray, key=lambda x:int(x['XP']))
		
		if not len(promoSorted):
			roleText = "There are no roles in the xp role list.  You can add some with the `{}addxprole [role] [xpamount]` command!\n".format(ctx.prefix)
		else:
			roleText = "**__Current Roles:__**\n\n"
			for arole in promoSorted:
				# Get current role name based on id
				foundRole = False
				for role in server.roles:
					if str(role.id) == str(arole['ID']):
						# We found it
						foundRole = True
						roleText = '{}**{}** : *{:,} XP*\n'.format(roleText, role.name, arole['XP'])
				if not foundRole:
					roleText = '{}**{}** : *{:,} XP* (removed from server)\n'.format(roleText, arole['Name'], arole['XP'])

		# Get the required role for using the xp system
		role = self.settings.getServerStat(ctx.message.guild, "RequiredXPRole")
		if role == None or role == "":
			roleText = '{}\n**Everyone** can give xp, gamble, and feed the bot.'.format(roleText)
		else:
			# Role is set - let's get its name
			found = False
			for arole in ctx.message.guild.roles:
				if str(arole.id) == str(role):
					found = True
					vowels = "aeiou"
					if arole.name[:1].lower() in vowels:
						roleText = '{}\nYou need to be an **{}** to *give xp*, *gamble*, or *feed* the bot.'.format(roleText, arole.name)
					else:
						roleText = '{}\nYou need to be a **{}** to *give xp*, *gamble*, or *feed* the bot.'.format(roleText, arole.name)
					# roleText = '{}\nYou need to be a/an **{}** to give xp, gamble, or feed the bot.'.format(roleText, arole.name)
			if not found:
				roleText = '{}\nThere is no role that matches id: `{}` for using the xp system - consider updating that setting.'.format(roleText, role)

		# Check for suppress
		if suppress:
			roleText = Nullify.clean(roleText)

		await channel.send(roleText)
		
		
	@commands.command(pass_context=True)
	async def rank(self, ctx, *, member = None):
		"""Say the highest rank of a listed member."""
		
		# Check if we're suppressing @here and @everyone mentions
		if self.settings.getServerStat(ctx.message.guild, "SuppressMentions"):
			suppress = True
		else:
			suppress = False

		if member is None:
			member = ctx.message.author
			
		if type(member) is str:
			memberName = member
			member = DisplayName.memberForName(memberName, ctx.message.guild)
			if not member:
				msg = 'I couldn\'t find *{}*...'.format(memberName)
				# Check for suppress
				if suppress:
					msg = Nullify.clean(msg)
				await ctx.message.channel.send(msg)
				return
			
		# Create blank embed
		stat_embed = discord.Embed(color=member.color)
			
		promoArray = self.settings.getServerStat(ctx.message.guild, "PromotionArray")
		# promoSorted = sorted(promoArray, key=itemgetter('XP', 'Name'))
		promoSorted = sorted(promoArray, key=lambda x:int(x['XP']))
		
		
		memName = member.name
		# Get member's avatar url
		avURL = member.avatar_url
		if not len(avURL):
			avURL = member.default_avatar_url
		if member.nick:
			# We have a nickname
			# Add to embed
			stat_embed.set_author(name='{}, who currently goes by {}'.format(member.name, member.nick), icon_url=avURL)
		else:
			# Add to embed
			stat_embed.set_author(name='{}'.format(member.name), icon_url=avURL)
			
		
		highestRole = ""
		
		for role in promoSorted:
			# We *can* have this role, let's see if we already do
			currentRole = None
			for aRole in member.roles:
				# Get the role that corresponds to the id
				if str(aRole.id) == str(role['ID']):
					# We found it
					highestRole = aRole.name

		if highestRole == "":
			msg = '*{}* has not acquired a rank yet.'.format(DisplayName.name(member))
			# Add Rank
			stat_embed.add_field(name="Current Rank", value='None acquired yet', inline=True)
		else:
			msg = '*{}* is a **{}**!'.format(DisplayName.name(member), highestRole)
			# Add Rank
			stat_embed.add_field(name="Current Rank", value=highestRole, inline=True)
			
		# await ctx.message.channel.send(msg)
		await ctx.message.channel.send(embed=stat_embed)
		
	@rank.error
	async def rank_error(self, error, ctx):
		msg = 'rank Error: {}'.format(error)
		await ctx.channel.send(msg)


	# List the top 10 xp-holders
	@commands.command(pass_context=True)
	async def leaderboard(self, ctx, total : int = 10):
		"""List the top xp-holders (max of 50)."""
		promoArray = self.settings.getServerStat(ctx.message.guild, "Members")
		promoSorted = sorted(promoArray, key=lambda x:int(promoArray[x]['XP']))

		startIndex = 0
		if total > 50:
			total = 50
		if total < 1:
			total = 1
		msg = ""

		if len(promoSorted) < total:
			total = len(promoSorted)
		
		if len(promoSorted):
			# makes sure we have at least 1 user - shouldn't be necessary though
			startIndex = len(promoSorted)-1
			msg = "**Top** ***{}*** **XP-Holders in** ***{}***:\n".format(total, self.suppressed(ctx.guild, ctx.guild.name))

		for i in range(0, total):
			# Loop through from startIndex to startIndex+total-1
			index = startIndex-i
			# cMemName = "{}#{}".format(promoSorted[index]['Name'], promoSorted[index]['Discriminator'])
			cMember = DisplayName.memberForID(promoSorted[index], ctx.message.guild)
			#if ctx.message.guild.get_member_named(cMemName):
				# Member exists
				#cMember = ctx.message.guild.get_member_named(cMemName)
			#else:
				#cMember = None
			if cMember:
				cMemberDisplay = DisplayName.name(cMember)
			else:
				cMemberDisplay = promoSorted[index]

			msg = '{}\n{}. *{}* - *{:,} xp*'.format(msg, i+1, cMemberDisplay, promoArray[promoSorted[index]]['XP'])

		await ctx.message.channel.send(msg)

		
	# List the top 10 xp-holders
	@commands.command(pass_context=True)
	async def bottomxp(self, ctx, total : int = 10):
		"""List the bottom xp-holders (max of 50)."""
		promoArray = self.settings.getServerStat(ctx.message.guild, "Members")
		# promoSorted = sorted(promoArray, key=itemgetter('XP'))
		promoSorted = sorted(promoArray, key=lambda x:int(promoArray[x]['XP']))

		startIndex = 0
		if total > 50:
			total = 50
		if total < 1:
			total = 1
		msg = ""

		if len(promoSorted) < total:
			total = len(promoSorted)
		
		if len(promoSorted):
			# makes sure we have at least 1 user - shouldn't be necessary though
			msg = "**Bottom** ***{}*** **XP-Holders in** ***{}***:\n".format(total, self.suppressed(ctx.guild, ctx.guild.name))

		for i in range(0, total):
			# Loop through from startIndex to startIndex+total-1
			index = startIndex+i
			# cMemName = "{}#{}".format(promoSorted[index]['Name'], promoSorted[index]['Discriminator'])
			cMember = DisplayName.memberForID(promoSorted[index], ctx.message.guild)
			#if ctx.message.guild.get_member_named(cMemName):
				# Member exists
				#cMember = ctx.message.guild.get_member_named(cMemName)
			#else:
				#cMember = None
			if cMember:
					cMemberDisplay = DisplayName.name(cMember)
			else:
				cMemberDisplay = promoSorted[index]
			msg = '{}\n{}. *{}* - *{:,} xp*'.format(msg, i+1, cMemberDisplay, promoArray[promoSorted[index]]['XP'])

		await ctx.message.channel.send(msg)
		
		
	# List the xp and xp reserve of a user
	@commands.command(pass_context=True)
	async def stats(self, ctx, *, member= None):
		"""List the xp and xp reserve of a listed member."""
		
		# Check if we're suppressing @here and @everyone mentions
		if self.settings.getServerStat(ctx.message.guild, "SuppressMentions"):
			suppress = True
		else:
			suppress = False
		
		if member is None:
			member = ctx.message.author
			
		if type(member) is str:
			memberName = member
			member = DisplayName.memberForName(memberName, ctx.message.guild)
			if not member:
				msg = 'I couldn\'t find *{}*...'.format(memberName)
				# Check for suppress
				if suppress:
					msg = Nullify.clean(msg)
				await ctx.message.channel.send(msg)
				return

		url = member.avatar_url
		if not len(url):
			url = member.default_avatar_url
		url = url.split("?size=")[0]

		# Create blank embed
		stat_embed = discord.Embed(color=member.color)
						
		stat_embed.set_thumbnail(url=url)

		# Get user's xp
		newStat = int(self.settings.getUserStat(member, ctx.message.guild, "XP"))
		newState = int(self.settings.getUserStat(member, ctx.message.guild, "XPReserve"))
		
		# Add XP and XP Reserve
		stat_embed.add_field(name="XP", value="{:,}".format(newStat), inline=True)
		stat_embed.add_field(name="XP Reserve", value="{:,}".format(newState), inline=True)
		
		memName = member.name
		# Get member's avatar url
		avURL = member.avatar_url
		if not len(avURL):
			avURL = member.default_avatar_url
		if member.nick:
			# We have a nickname
			msg = "__***{},*** **who currently goes by** ***{}:***__\n\n".format(member.name, member.nick)
			
			# Add to embed
			stat_embed.set_author(name='{}, who currently goes by {}'.format(member.name, member.nick))
		else:
			msg = "__***{}:***__\n\n".format(member.name)
			# Add to embed
			stat_embed.set_author(name='{}'.format(member.name))
		# Get localized user time
		local_time = UserTime.getUserTime(ctx.author, self.settings, member.joined_at)
		j_time_str = "{} {}".format(local_time['time'], local_time['zone'])
		
		msg = "{}**Joined:** *{}*\n".format(msg, j_time_str) # I think this will work
		msg = "{}**XP:** *{:,}*\n".format(msg, newStat)
		msg = "{}**XP Reserve:** *{:,}*\n".format(msg, newState)
		
		# Add Joined
		stat_embed.add_field(name="Joined", value=j_time_str, inline=True)

		# msg = '*{}* has *{} xp*, and can gift up to *{} xp!*'.format(DisplayName.name(member), newStat, newState)

		# Get user's current role
		promoArray = self.settings.getServerStat(ctx.message.guild, "PromotionArray")
		# promoSorted = sorted(promoArray, key=itemgetter('XP', 'Name'))
		promoSorted = sorted(promoArray, key=lambda x:int(x['XP']))
		
		highestRole = None
		if len(promoSorted):
			nextRole = promoSorted[0]
		else:
			nextRole = None

		for role in promoSorted:
			if int(nextRole['XP']) < newStat:
				nextRole = role
			# We *can* have this role, let's see if we already do
			currentRole = None
			for aRole in member.roles:
				# Get the role that corresponds to the id
				if str(aRole.id) == str(role['ID']):
					# We found it
					highestRole = aRole.name
					if len(promoSorted) > (promoSorted.index(role)+1):
						# There's more roles above this
						nRoleIndex = promoSorted.index(role)+1
						nextRole = promoSorted[nRoleIndex]


		if highestRole:
			msg = '{}**Current Rank:** *{}*\n'.format(msg, highestRole)
			# Add Rank
			stat_embed.add_field(name="Current Rank", value=highestRole, inline=True)
		else:
			if len(promoSorted):
				# Need to have ranks to acquire one
				msg = '{}They have not acquired a rank yet.\n'.format(msg)
				# Add Rank
				stat_embed.add_field(name="Current Rank", value='None acquired yet', inline=True)
		
		if nextRole and (newStat < int(nextRole['XP'])):
			# Get role
			next_role = DisplayName.roleForID(int(nextRole["ID"]), ctx.guild)
			if not next_role:
				next_role_text = "Role ID: {} (Removed from server)".format(nextRole["ID"])
			else:
				next_role_text = next_role.name
			msg = '{}\n*{:,}* more *xp* required to advance to **{}**'.format(msg, int(nextRole['XP']) - newStat, next_role_text)
			# Add Next Rank
			stat_embed.add_field(name="Next Rank", value='{} ({:,} more xp required)'.format(next_role_text, int(nextRole['XP'])-newStat), inline=True)
			
		# Add status
		status_text = ":green_heart:"
		if member.status == discord.Status.offline:
			status_text = ":black_heart:"
		elif member.status == discord.Status.dnd:
			status_text = ":heart:"
		elif member.status == discord.Status.idle:
			status_text = ":yellow_heart:"
		stat_embed.add_field(name="Status", value=status_text, inline=True)

		stat_embed.add_field(name="ID", value=str(member.id), inline=True)
		stat_embed.add_field(name="User Name", value="{}#{}".format(member.name, member.discriminator), inline=True)
		
		if member.game and member.game.name:
			# Playing a game!
			play_list = [ "Playing", "Streaming", "Listening to", "Watching" ]
			try:
				play_string = play_list[member.game.type]
			except:
				play_string = "Playing"
			stat_embed.add_field(name=play_string, value=str(member.game.name), inline=True)
			if member.game.type == 1:
				# Add the URL too
				stat_embed.add_field(name="Stream URL", value="[Watch Now]({})".format(member.game.url), inline=True)
		# Add joinpos
		joinedList = []
		for mem in ctx.message.guild.members:
			joinedList.append({ 'ID' : mem.id, 'Joined' : mem.joined_at })
		
		# sort the users by join date
		joinedList = sorted(joinedList, key=lambda x:x['Joined'])
		check_item = { "ID" : member.id, "Joined" : member.joined_at }
		total = len(joinedList)
		position = joinedList.index(check_item) + 1
		
		stat_embed.add_field(name="Join Position", value="{:,} of {:,}".format(position, total), inline=True)
		
		# Get localized user time
		local_time = UserTime.getUserTime(ctx.author, self.settings, member.created_at, clock=False)
		c_time_str = "{} {}".format(local_time['time'], local_time['zone'])
		# add created_at footer
		created = "Created at " + c_time_str
		stat_embed.set_footer(text=created)

		#await ctx.message.channel.send(msg)
		await ctx.send(embed=stat_embed)
		
	@stats.error
	async def stats_error(self, ctx, error):
		msg = 'stats Error: {}'.format(error)
		await ctx.channel.send(msg)


	# List the xp and xp reserve of a user
	@commands.command(pass_context=True)
	async def xpinfo(self, ctx):
		"""Gives a quick rundown of the xp system."""

		server  = ctx.message.guild
		channel = ctx.message.channel

		# Check if we're suppressing @here and @everyone mentions
		if self.settings.getServerStat(server, "SuppressMentions"):
			suppress = True
		else:
			suppress = False

		serverName = self.suppressed(server, server.name)
		hourlyXP = int(self.settings.getServerStat(server, "HourlyXP"))
		hourlyXPReal = int(self.settings.getServerStat(server, "HourlyXPReal"))
		xpPerMessage = int(self.settings.getServerStat(server, "XPPerMessage"))
		xpRPerMessage = int(self.settings.getServerStat(server, "XPRPerMessage"))
		if not xpPerMessage:
			xpPerMessage = 0
		if not xpRPerMessage:
			xpRPerMessage = 0
		if not hourlyXPReal:
			hourlyXPReal = 0
		if not hourlyXP:
			hourlyXP = 0
		onlyOnline = self.settings.getServerStat(server, "RequireOnline")
		xpProm = self.settings.getServerStat(server, "XPPromote")
		xpDem = self.settings.getServerStat(server, "XPDemote")
		xpStr = None

		if xpProm and xpDem:
			# Bot promote and demote
			xpStr = "This is what I check to handle promotions and demotions.\n"
		else:
			if xpProm:
				xpStr = "This is what I check to handle promotions.\n"
			elif xpDem:
				xpStr = "This is what I check to handle demotions.\n"

		msg = "__***{}'s*** **XP System**__\n\n__What's What:__\n\n".format(serverName)
		msg = "{}**XP:** This is the xp you have *earned.*\nIt comes from other users gifting you xp, or if you're lucky enough to `{}gamble` and win.\n".format(msg, ctx.prefix)
		
		if xpStr:
			msg = "{}{}".format(msg, xpStr)
		
		hourStr = None
		if hourlyXPReal > 0:
			hourStr = "Currently, you receive *{} xp* each hour".format(hourlyXPReal)
			if onlyOnline:
				hourStr = "{} (but *only* if your status is *Online*).".format(hourStr)
			else:
				hourStr = "{}.".format(hourStr)
		if hourStr:
			msg = "{}{}\n".format(msg, hourStr)
			
		if xpPerMessage > 0:
			msg = "{}Currently, you receive *{} xp* per message.\n".format(msg, xpPerMessage)
			
		msg = "{}This can only be taken away by an *admin*.\n\n".format(msg)
		msg = "{}**XP Reserve:** This is the xp you can *gift*, *gamble*, or use to *feed* me.\n".format(msg)

		hourStr = None
		if hourlyXP > 0:
			hourStr = "Currently, you receive *{} xp reserve* each hour".format(hourlyXP)
			if onlyOnline:
				hourStr = "{} (but *only* if your status is *Online*).".format(hourStr)
			else:
				hourStr = "{}.".format(hourStr)
		
		if hourStr:
			msg = "{}{}\n".format(msg, hourStr)
		
		if xpRPerMessage > 0:
			msg = "{}Currently, you receive *{} xp reserve* per message.\n".format(msg, xpRPerMessage)

		msg = "{}\n__How Do I Use It?:__\n\nYou can gift other users xp by using the `{}xp [user] [amount]` command.\n".format(msg, ctx.prefix)
		msg = "{}This pulls from your *xp reserve*, and adds to their *xp*.\n".format(msg)
		msg = "{}It does not change the *xp* you have *earned*.\n\n".format(msg)

		msg = "{}You can gamble your *xp reserve* to have a chance to win a percentage back as *xp* for yourself.\n".format(msg)
		msg = "{}You do so by using the `{}gamble [amount in multiple of 10]` command.\n".format(msg, ctx.prefix)
		msg = "{}This pulls from your *xp reserve* - and if you win, adds to your *xp*.\n\n".format(msg)

		msg = "{}You can also *feed* me.\n".format(msg)
		msg = "{}This is done with the `{}feed [amount]` command.\n".format(msg, ctx.prefix)
		msg = "{}This pulls from your *xp reserve* - and doesn't affect your *xp*.\n\n".format(msg)
		
		msg = "{}You can check your *xp*, *xp reserve*, current role, and next role using the `{}stats` command.\n".format(msg, ctx.prefix)
		msg = "{}You can check another user's stats with the `{}stats [user]` command.\n\n".format(msg, ctx.prefix)

		# Get the required role for using the xp system
		role = self.settings.getServerStat(server, "RequiredXPRole")
		if role == None or role == "":
			msg = '{}Currently, **Everyone** can *give xp*, *gamble*, and *feed* the bot.\n\n'.format(msg)
		else:
			# Role is set - let's get its name
			found = False
			for arole in server.roles:
				if str(arole.id) == str(role):
					found = True
					vowels = "aeiou"
					if arole.name[:1].lower() in vowels:
						msg = '{}Currently, you need to be an **{}** to *give xp*, *gamble*, or *feed* the bot.\n\n'.format(msg, arole.name)
					else:
						msg = '{}Currently, you need to be a **{}** to *give xp*, *gamble*, or *feed* the bot.\n\n'.format(msg, arole.name)
			if not found:
				msg = '{}There is no role that matches id: `{}` for using the xp system - consider updating that setting.\n\n'.format(msg, role)

		msg = "{}Hopefully that clears things up!".format(msg)

		# Check for suppress
		if suppress:
			msg = Nullify.clean(msg)

		await ctx.message.channel.send(msg)
