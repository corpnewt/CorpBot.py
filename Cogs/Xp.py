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
	async def setxp(self, ctx, *, member = None, xpAmount : int = None):
		"""Sets an absolute value for the member's xp (admin only)."""
		
		author  = ctx.message.author
		server  = ctx.message.server
		channel = ctx.message.channel
		
		isAdmin = author.permissions_in(channel).administrator
		# Only allow admins to change server stats
		if not isAdmin:
			await self.bot.send_message(channel, 'You do not have sufficient privileges to access this command.')
			return
		if xpAmount == None:
			# Check if we have trailing xp
			nameCheck = DisplayName.checkNameForInt(member, server)
			if not nameCheck:
				await self.bot.send_message(ctx.message.channel, usage)
				return
			if not nameCheck["Member"]:
				msg = 'I couldn\'t find *{}* on the server.'.format(member)
				await self.bot.send_message(ctx.message.channel, msg)
				return
			member   = nameCheck["Member"]
			xpAmount = nameCheck["Int"]
			
		# Check for formatting issues
		if not xpAmount:
			# Still no xp...
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
	async def xp(self, ctx, *, member = None, xpAmount : int = None):
		"""Gift xp to other members."""
		
		author  = ctx.message.author
		server  = ctx.message.server
		channel = ctx.message.channel

		usage = 'Usage: `$xp [role/member] [amount]`'

		isRole = False

		if member == None:
			await self.bot.send_message(ctx.message.channel, usage)
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
					await self.bot.send_message(ctx.message.channel, msg)
					return
				if roleCheck["Role"]:
					isRole = True
					member   = roleCheck["Role"]
					xpAmount = roleCheck["Int"]
				else:
					# Role is invalid - check for member instead
					nameCheck = DisplayName.checkNameForInt(member, server)
					if not nameCheck:
						await self.bot.send_message(ctx.message.channel, usage)
						return
					if not nameCheck["Member"]:
						msg = 'I couldn\'t find *{}* on the server.'.format(member)
						await self.bot.send_message(ctx.message.channel, msg)
						return
					member   = nameCheck["Member"]
					xpAmount = nameCheck["Int"]

		if xpAmount == None:
			# Still no xp
			await self.bot.send_message(ctx.message.channel, usage)
			return
		if not type(xpAmount) is int:
			await self.bot.send_message(ctx.message.channel, usage)
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
					roles = amem.roles
					if member in roles:
						# This member has our role
						# Add to our list
						for smem in sMemberList:
							# Find our server entry
							if smem["ID"] == amem.id:
								# Add it.
								memberList.append(smem)
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
							await self.checkroles(cMember, channel)
					else:
						for i in range(0, xpAmount):
							cMember = DisplayName.memberForID(memSorted[i]['ID'], server)
							self.settings.incrementStat(cMember, server, "XP", 1)
							await self.checkroles(cMember, channel)

					# Decrement if needed
					if decrement:
						self.settings.incrementStat(author, server, "XPReserve", (-1*xpAmount))
					msg = '*{} collective xp* was given to *{}!*'.format(totalXP, member.name)
					await self.bot.send_message(channel, msg)
				else:
					msg = 'There are no eligible members in *{}!*'.format(member.name)
					await self.bot.send_message(channel, msg)

			else:
				# Decrement if needed
				if decrement:
					self.settings.incrementStat(author, server, "XPReserve", (-1*xpAmount))
				# XP was approved!  Let's say it - and check decrement from gifter's xp reserve
				msg = '*{}* was given *{} xp!*'.format(DisplayName.name(member), xpAmount)
				await self.bot.send_message(channel, msg)
				self.settings.incrementStat(member, server, "XP", xpAmount)
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
				# Now we check for promotions
				await self.checkroles(author, channel)
			else:
				msg = '*{}* bet *{}* and.... *didn\'t* win.  Better luck next time!'.format(DisplayName.name(author), bet)
			
		await self.bot.send_message(ctx.message.channel, msg)
			
	@commands.command(pass_context=True)
	async def recheckroles(self, ctx):
		"""Re-iterate through all members and assign the proper roles based on their xp (admin only)."""

		author  = ctx.message.author
		server  = ctx.message.server
		channel = ctx.message.channel

		isAdmin = author.permissions_in(channel).administrator

		# Only allow admins to change server stats
		if not isAdmin:
			await self.bot.send_message(channel, 'You do not have sufficient privileges to access this command.')
			return

		changeCount = 0
		for member in server.members:
			# Now we check for promotions
			if await self.checkroles(member, channel, True):
				changeCount += 1
		
		if changeCount == 1:
			await self.bot.send_message(channel, 'Done checking roles.\n\n*1 user* updated.')
		else:
			await self.bot.send_message(channel, 'Done checking roles.\n\n*{} users* updated.'.format(changeCount))

	@commands.command(pass_context=True)
	async def recheckrole(self, ctx, *, user : discord.Member = None):
		"""Re-iterate through all members and assign the proper roles based on their xp (admin only)."""

		author  = ctx.message.author
		server  = ctx.message.server
		channel = ctx.message.channel

		isAdmin = author.permissions_in(channel).administrator

		# Only allow admins to change server stats
		if not isAdmin:
			await self.bot.send_message(channel, 'You do not have sufficient privileges to access this command.')
			return

		if not user:
			user = author

		# Now we check for promotions
		if await self.checkroles(user, channel):
			await self.bot.send_message(channel, 'Done checking roles.\n\n*{}* was updated.'.format(DisplayName.name(user)))
		else:
			await self.bot.send_message(channel, 'Done checking roles.\n\n*{}* was not updated.'.format(DisplayName.name(user)))


			
	async def checkroles(self, user, channel, suppress : bool = False):
		# This method checks whether we need to promote, demote, or whatever
		# then performs the said action, and outputs.
		
		server = channel.server
		
		# Get our preliminary vars
		msg         = None
		xpPromote   = self.settings.getServerStat(server,     "XPPromote")
		xpDemote    = self.settings.getServerStat(server,     "XPDemote")
		userXP      = int(self.settings.getUserStat(user, server, "XP"))

		changed = False
		
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
						changed = True
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
							changed = True
		# Check if we have a message to display - and display it
		if msg and (not suppress):
			await self.bot.send_message(channel, msg)
		return changed


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
			# Get current role name based on id
			foundRole = False
			for role in server.roles:
				if role.id == arole['ID']:
					# We found it
					foundRole = True
					roleText = '{}**{}** : *{} XP*\n'.format(roleText, role.name, arole['XP'])
			if not foundRole:
				roleText = '{}**{}** : *{} XP* (removed from server)\n'.format(roleText, arole['Name'], arole['XP'])

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
	async def rank(self, ctx, *, member: discord.Member = None):
		"""Say the highest rank of a listed member."""
		
		if member is None:
			member = ctx.message.author
			
		if type(member) is str:
			try:
				member = discord.utils.get(server.members, name=member)
			except:
				print("That member does not exist")
				return
			
		# Create blank embed
		stat_embed = discord.Embed(color=member.color)
			
		promoArray = self.settings.getServerStat(ctx.message.server, "PromotionArray")
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
				if aRole.id == role['ID']:
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
			
		# await self.bot.send_message(ctx.message.channel, msg)
		
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

		if len(promoSorted) < 10:
			total = len(promoSorted)
		
		if len(promoSorted):
			# makes sure we have at least 1 user - shouldn't be necessary though
			startIndex = len(promoSorted)-1
			msg = "**Top** ***{}*** **XP-Holders in** ***{}***:\n".format(total, ctx.message.server.name)

		for i in range(0, total):
			# Loop through from startIndex to startIndex+total-1
			index = startIndex-i
			# cMemName = "{}#{}".format(promoSorted[index]['Name'], promoSorted[index]['Discriminator'])
			cMember = DisplayName.memberForID(promoSorted[index]['ID'], ctx.message.server)
			#if ctx.message.server.get_member_named(cMemName):
				# Member exists
				#cMember = ctx.message.server.get_member_named(cMemName)
			#else:
				#cMember = None
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

		if len(promoSorted) < 10:
			total = len(promoSorted)
		
		if len(promoSorted):
			# makes sure we have at least 1 user - shouldn't be necessary though
			msg = "**Bottom** ***{}*** **XP-Holders in** ***{}***:\n".format(total, ctx.message.server.name)

		for i in range(0, total):
			# Loop through from startIndex to startIndex+total-1
			index = startIndex+i
			# cMemName = "{}#{}".format(promoSorted[index]['Name'], promoSorted[index]['Discriminator'])
			cMember = DisplayName.memberForID(promoSorted[index]['ID'], ctx.message.server)
			#if ctx.message.server.get_member_named(cMemName):
				# Member exists
				#cMember = ctx.message.server.get_member_named(cMemName)
			#else:
				#cMember = None
			if cMember:
					cMemberDisplay = DisplayName.name(cMember)
			else:
				cMemberDisplay = promoSorted[index]['Name']
			msg = '{}\n{}. *{}* - *{} xp*'.format(msg, i+1, cMemberDisplay, promoSorted[index]['XP'])

		await self.bot.send_message(ctx.message.channel, msg)
		
		
	# List the xp and xp reserve of a user
	@commands.command(pass_context=True)
	async def stats(self, ctx, *, member: discord.Member = None):
		"""List the xp and xp reserve of a listed member."""
		if member is None:
			member = ctx.message.author
		
		if type(member) is str:
			try:
				member = discord.utils.get(server.members, name=member)
			except:
				print("That member does not exist")
				return

		# Create blank embed
		stat_embed = discord.Embed(color=member.color)
					    
		# Get user's xp
		newStat = int(self.settings.getUserStat(member, ctx.message.server, "XP"))
		newState = int(self.settings.getUserStat(member, ctx.message.server, "XPReserve"))
		
		# Add XP and XP Reserve
		stat_embed.add_field(name="XP", value=newStat, inline=True)
		stat_embed.add_field(name="XP Reserve", value=newState, inline=True)
		
		memName = member.name
		# Get member's avatar url
		avURL = member.avatar_url
		if not len(avURL):
			avURL = member.default_avatar_url
		if member.nick:
			# We have a nickname
			msg = "__***{},*** **who currently goes by** ***{}:***__\n\n".format(member.name, member.nick)
			
			# Add to embed
			stat_embed.set_author(name='{}, who currently goes by {}'.format(member.name, member.nick), icon_url=avURL)
		else:
			msg = "__***{}:***__\n\n".format(member.name)
			# Add to embed
			stat_embed.set_author(name='{}'.format(member.name), icon_url=avURL)
			
		msg = "{}**Joined:** *{}*\n".format(msg, member.joined_at.strftime("%Y-%m-%d %H:%M")) # I think this will work
		msg = "{}**XP:** *{}*\n".format(msg, newStat)
		msg = "{}**XP Reserve:** *{}*\n".format(msg, newState)
		
		# Add Joined
		stat_embed.add_field(name="Joined", value=member.joined_at.strftime("%Y-%m-%d %H:%M"), inline=True)

		# msg = '*{}* has *{} xp*, and can gift up to *{} xp!*'.format(DisplayName.name(member), newStat, newState)

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
			if int(nextRole['XP']) < newStat:
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
			msg = '{}\n*{}* more *xp* required to advance to **{}**'.format(msg, int(nextRole['XP']) - newStat, nextRole['Name'])
			# Add Next Rank
			stat_embed.add_field(name="Next Rank", value='{} ({} more xp required)'.format(nextRole['Name'], int(nextRole['XP'])-newStat), inline=True)
			
		#await self.bot.send_message(ctx.message.channel, msg)
		await self.bot.send_message(ctx.message.channel, embed=stat_embed)
		
	@stats.error
	async def stats_error(self, ctx, error):
		msg = 'stats Error: {}'.format(ctx)
		await self.bot.say(msg)


	# List the xp and xp reserve of a user
	@commands.command(pass_context=True)
	async def xpinfo(self, ctx):
		"""Gives a quick rundown of the xp system."""

		server  = ctx.message.server
		channel = ctx.message.channel

		serverName = server.name
		hourlyXP = int(self.settings.getServerStat(server, "HourlyXP"))
		if not hourlyXP:
			hourlyXP = 0
		onlyOnline = self.settings.getServerStat(server, "RequireOnline")
		xpProm = self.settings.getServerStat(server, "XPPromote")
		xpDem = self.settings.getServerStat(server, "XPDemote")
		xpStr = None

		if (xpProm.lower() == "yes") and (xpDem.lower() == "yes"):
			# Bot promote and demote
			xpStr = "This is what I check to handle promotions and demotions.\n"
		else:
			if xpProm.lower() == "yes":
				xpStr = "This is what I check to handle promotions.\n"
			elif xpDem.lower() == "yes":
				xpStr = "This is what I check to handle demotions.\n"

		msg = "__***{}'s*** **XP System**__\n\n__What's What:__\n\n".format(serverName)
		msg = "{}**XP:** This is the xp you have *earned.*\nIt comes from other users gifting you xp, or if you're lucky enough to `$gamble` and win.\n".format(msg)
		if xpStr:
			msg = "{}{}".format(msg, xpStr)
		msg = "{}This can only be taken away by an *admin*.\n\n".format(msg)
		msg = "{}**XP Reserve:** This is the xp you can *gift*, *gamble*, or use to *feed* me.\n".format(msg)

		hourStr = None
		if hourlyXP > 0:
			hourStr = "Currently, you receive *{} xp reserve* each hour".format(hourlyXP)
			if onlyOnline.lower() == "yes":
				hourStr = "{} (but *only* if your status is *Online*).".format(hourStr)
			else:
				hourStr = "{}.".format(hourStr)
		
		if hourStr:
			msg = "{}{}".format(msg, hourStr)

		msg = "{}\n\n__How Do I Use It?:__\n\nYou can gift other users xp by using the `$xp [user] [amount]` command.\n".format(msg)
		msg = "{}This pulls from your *xp reserve*, and adds to their *xp*.\n".format(msg)
		msg = "{}It does not change the *xp* you have *earned*.\n\n".format(msg)

		msg = "{}You can gamble your *xp reserve* to have a chance to win a percentage back as *xp* for yourself.\n".format(msg)
		msg = "{}You do so by using the `$gamble [amount in multiple of 10]` command.\n".format(msg)
		msg = "{}This pulls from your *xp reserve* - and if you win, adds to your *xp*.\n\n".format(msg)

		msg = "{}You can also *feed* me.\n".format(msg)
		msg = "{}This is done with the `$feed [amount]` command.\n".format(msg)
		msg = "{}This pulls from your *xp reserve* - and doesn't affect your *xp*.\n\n".format(msg)
		
		msg = "{}You can check your *xp*, *xp reserve*, current role, and next role using the `$stats` command.\n".format(msg)
		msg = "{}You can check another user's stats with the `$stat [user]` command.\n\n".format(msg)

		# Get the required role for using the xp system
		role = self.settings.getServerStat(server, "RequiredXPRole")
		if role == None or role == "":
			msg = '{}Currently, **Everyone** can *give xp*, *gamble*, and *feed* the bot.\n\n'.format(msg)
		else:
			# Role is set - let's get its name
			found = False
			for arole in server.roles:
				if arole.id == role:
					found = True
					msg = '{}Currently, you need to be a/an **{}** to *give xp*, *gamble*, or *feed* the bot.\n\n'.format(msg, arole.name)
			if not found:
				msg = '{}There is no role that matches id: `{}` for using the xp system - consider updating that settings.\n\n'.format(msg, role)

		msg = "{}Hopefully that clears things up!".format(msg)

		await self.bot.send_message(ctx.message.channel, msg)
