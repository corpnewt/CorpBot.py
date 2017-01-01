import asyncio
import discord
from   discord.ext import commands
from   Cogs import Settings
from   Cogs import DisplayName

# This is the Uptime module. It keeps track of how long the bot's been up

class Setup:

	# Init with the bot reference, and a reference to the settings var
	def __init__(self, bot, settings):
		self.bot = bot
		self.settings = settings

	@commands.command(pass_context=True)
	async def setup(self, ctx):
		"""Runs first-time setup (server owner only)."""

		channel = ctx.message.channel
		author  = ctx.message.author
		server  = ctx.message.server

		if channel.is_private:
			msg = 'You have to send this command in the main chat - otherwise I don\'t know what server we\'re setting up.'
			await self.bot.send_message(author, msg)
			return

		if not author is server.owner:
			msg = 'The server *owner* needs to set me up.'
			await self.bot.send_message(channel, msg)
			return

		# If we're here, begin the setup

		#############################
		# Role Management:
		#############################
		# 1. Auto role? Yes/no
		#  a. If yes - get role ID (let's move away from position)
		# 2. Use XP? Yes/no
		#  a. If yes:
		#    * how much reserve per hour
		#    * how much xp/reserve to start
		await self.startSetup(ctx)

	# Check for y, n, or skip
	def check(self, msg):
		if not msg.channel.is_private:
			return False
		if msg.content.startswith('y'):
			return True
		if msg.content.startswith('n'):
			return True
		if msg.content == 'skip':
			return True
		return False

	def checkRole(self, msg):
		if not msg.channel.is_private:
			return False
		return True

	async def startSetup(self, ctx):
		channel = ctx.message.channel
		author  = ctx.message.author
		server  = ctx.message.server

		msg = 'Hello! Let\'s start the setup!\nI\'ll ask you for some info - and you can either answer my questions,\nor choose `skip` to use my default (or a value already set if we\'ve gone through parts of the setup before).'
		await self.bot.send_message(author, msg)
		await self.autoRole(ctx)

	# Set up the auto-role system
	async def autoRole(self, ctx):
		channel = ctx.message.channel
		author  = ctx.message.author
		server  = ctx.message.server

		defRole = self.settings.getServerStat(server, "DefaultRole")
		verify = int(self.settings.getServerStat(server, "VerificationTime"))

		msg = '**__Auto-Role Management__**:\n\nWould you like me to auto-assign a role to new users when they join? (y/n/skip)'
		if defRole:
			auto = 'set to: **{}**.'.format(DisplayName.roleForID(defRole, server))
		else:
			auto = '*disabled*.'

		if verify == 0:
			verifyString = 'No delay before applying.'
		else:
			verifyString = '{} minute delay before applying.'.format(verify)

		msg = '{}\n\nCurrently {}\n{}'.format(msg, auto, verifyString)
		
		await self.bot.send_message(author, msg)
			

		gotIt = False
		while not gotIt:
			talk = await self.bot.wait_for_message(check=self.check, author=author, timeout=60)
			if not talk:
				msg = "*{}*, I'm out of time... type `$setup` in the main chat to start again.".format(DisplayName.name(author))
				await self.bot.send_message(author, msg)
				return
			else:
				# We got something
				if talk.content.startswith('y'):
					await self.autoRoleName(ctx)
				elif talk.content.startswith('n'):
					self.settings.setServerStat(server, "DefaultRole", None)
					await self.bot.send_message(author, 'Auto-role *disabled.*')
				else:
					# Skipping
					await self.bot.send_message(author, 'Auto-role shall remain {}'.format(auto))
					await self.xpSystem(ctx)
				gotIt = True

	# Get our default role
	async def autoRoleName(self, ctx):
		channel = ctx.message.channel
		author  = ctx.message.author
		server  = ctx.message.server

		msg = 'Please type the name of the role to auto-assign:'
		await self.bot.send_message(author, msg)
		gotIt = False
		while not gotIt:
			talk = await self.bot.wait_for_message(check=self.checkRole, author=author, timeout=60)
			if not talk:
				msg = "*{}*, I'm out of time... type `$setup` in the chat to start again.".format(DisplayName.name(author))
				await self.bot.send_message(author, msg)
				return
			else:
				# We got a response - check if it's a real role
				role = DisplayName.roleForName(talk.content, server)
				if not role:
					msg = "It doesn't look like **{}** is a role on your server - try again.".format(talk.content)
					await self.bot.send_message(author, msg)
					continue
				else:
					# Got a role!
					msg = "Auto-role now set to **{}**!".format(role.name)
					await self.bot.send_message(author, msg)
					self.settings.setServerStat(server, "DefaultRole", role.id)
					gotIt = True
		# Let's find out how long to wait for auto role to apply
		verify = int(self.settings.getServerStat(server, "VerificationTime"))
		msg = 'If you have a higher security server - or just want a delay before applying a default role, I can help with that.  What would you like this delay to be (in minutes)?\n\nCurrent is *{}*.'.format(verify)
		await self.bot.send_message(author, msg)
		gotIt = False
		while not gotIt:
			talk = await self.bot.wait_for_message(check=self.checkRole, author=author, timeout=60)
			if not talk:
				msg = "*{}*, I'm out of time... type `$setup` in the main chat to start again.".format(DisplayName.name(author))
				await self.bot.send_message(author, msg)
				return
			else:
				# We got something
				if talk.content == "skip":
					await self.bot.send_message(author, 'Auto-role delay time will remian *{} minutes*.'.format(threshold))
				else:
					try:
						talkInt = int(talk.content)
						await self.bot.send_message(author, 'Auto-role delay time is now *{} minutes!*'.format(talkInt))
						self.settings.setServerStat(server, "VerificationTime", talkInt)
					except ValueError:
						await self.bot.send_message(author, 'Auto-role delay time needs to be a whole number - try again.')
						continue
				gotIt = True
		# Onward
		await self.xpSystem(ctx)

	async def xpSystem(self, ctx):
		channel = ctx.message.channel
		author  = ctx.message.author
		server  = ctx.message.server

		defXP = self.settings.getServerStat(server, "DefaultXP")
		if not defXP:
			defXP = 0
		defXPR = self.settings.getServerStat(server, "DefaultXPReserve")
		if not defXPR:
			defXPR = 10
		hourXP = self.settings.getServerStat(server, "HourlyXP")
		reqOnline = self.settings.getServerStat(server, "RequireOnline")
		reqXP = self.settings.getServerStat(server, "RequiredXPRole")
		if not reqXP:
			reqXP = "Everyone"
		else:
			reqXP = DisplayName.roleForID(reqXP, server)
		adminUnlimited = self.settings.getServerStat(server, "AdminUnlimited")
		xpProm = self.settings.getServerStat(server, "XPPromote")
		xpDem = self.settings.getServerStat(server, "XPDemote")

		msg = '**__XP Management System__**\n\nI can help auto-manage roles by promoting/demoting based on xp.\n\nWould you like to go through that setup? (y/n)'
		msg = '{}\n\n__Current settings:__\n\nDefault xp on join: *{}*\nDefault xp reserve on join: *{}*\nHourly xp reserve: *{}*\nHourly xp requires users to be online: *{}*\nRequired Role to use the XP system: **{}**\nAdmins can spend unlimited xp: *{}*\nUsers can be promoted based on xp: *{}*\nUsers can be demoted based on xp: *{}*'.format(msg, defXP, defXPR, hourXP, reqOnline, reqXP, adminUnlimited, xpProm, xpDem)
		await self.bot.send_message(author, msg)

		gotIt = False
		while not gotIt:
			talk = await self.bot.wait_for_message(check=self.check, author=author, timeout=60)
			if not talk:
				msg = "*{}*, I'm out of time... type `$setup` in the main chat to start again.".format(DisplayName.name(author))
				await self.bot.send_message(author, msg)
				return
			else:
				# We got something
				if talk.content.startswith('y'):
					# await self.autoRoleName(ctx)
					await self.setupXP(ctx)
				elif talk.content.startswith('n'):
					await self.picThresh(ctx)
				else:
					# Skipping
					await self.picThresh(ctx)
				gotIt = True
		# Onward

	async def setupXP(self, ctx):
		channel = ctx.message.channel
		author  = ctx.message.author
		server  = ctx.message.server

		##########################################################################################################################
		# Default XP
		defXP = self.settings.getServerStat(server, "DefaultXP")
		if not defXP:
			defXP = 0
		msg = 'How much xp should each user get when they join?\n\nCurrent is *{}*.'.format(defXP)
		await self.bot.send_message(author, msg)
		gotIt = False
		while not gotIt:
			talk = await self.bot.wait_for_message(check=self.checkRole, author=author, timeout=60)
			if not talk:
				msg = "*{}*, I'm out of time... type `$setup` in the main chat to start again.".format(DisplayName.name(author))
				await self.bot.send_message(author, msg)
				return
			else:
				# We got something
				if talk.content == "skip":
					await self.bot.send_message(author, 'Default xp reserve will remian *{}*.'.format(defXP))
				else:
					try:
						talkInt = int(talk.content)
						await self.bot.send_message(author, 'Default xp reserve is now *{}!*'.format(talkInt))
						self.settings.setServerStat(server, "DefaultXP", talkInt)
					except ValueError:
						# await self.autoRoleName(ctx)
						await self.bot.send_message(author, 'Default xp reserve needs to be a whole number - try again.')
						continue
				gotIt = True
		
		##########################################################################################################################
		# Default XP Reserve
		defXPR = self.settings.getServerStat(server, "DefaultXPReserve")
		if not defXPR:
			defXPR = 10
		msg = 'How much xp reserve (xp they can gift, gamble, or feed to the bot) should each user get when they join?\n\nCurrent is *{}*.'.format(defXPR)
		await self.bot.send_message(author, msg)
		gotIt = False
		while not gotIt:
			talk = await self.bot.wait_for_message(check=self.checkRole, author=author, timeout=60)
			if not talk:
				msg = "*{}*, I'm out of time... type `$setup` in the main chat to start again.".format(DisplayName.name(author))
				await self.bot.send_message(author, msg)
				return
			else:
				# We got something
				if talk.content == "skip":
					await self.bot.send_message(author, 'Default xp reserve will remian *{}*.'.format(defXPR))
				else:
					try:
						talkInt = int(talk.content)
						await self.bot.send_message(author, 'Default xp reserve is now *{}!*'.format(talkInt))
						self.settings.setServerStat(server, "DefaultXPReserve", talkInt)
					except ValueError:
						# await self.autoRoleName(ctx)
						await self.bot.send_message(author, 'Default xp reserve needs to be a whole number - try again.')
						continue
				gotIt = True
		
		##########################################################################################################################
		# Hourly XP
		hourXP = self.settings.getServerStat(server, "HourlyXP")
		if not hourXP:
			hourXP = 3
		msg = 'How much xp reserve (xp they can gift, gamble, or feed to the bot) should each user get per hour?\n\nCurrent is *{}*.'.format(hourXP)
		await self.bot.send_message(author, msg)
		gotIt = False
		while not gotIt:
			talk = await self.bot.wait_for_message(check=self.checkRole, author=author, timeout=60)
			if not talk:
				msg = "*{}*, I'm out of time... type `$setup` in the main chat to start again.".format(DisplayName.name(author))
				await self.bot.send_message(author, msg)
				return
			else:
				# We got something
				if talk.content == "skip":
					await self.bot.send_message(author, 'Hourly xp reserve will remian *{}*.'.format(hourXP))
				else:
					try:
						talkInt = int(talk.content)
						await self.bot.send_message(author, 'Hourly xp reserve is now *{}!*'.format(talkInt))
						self.settings.setServerStat(server, "HourlyXP", talkInt)
					except ValueError:
						# await self.autoRoleName(ctx)
						await self.bot.send_message(author, 'Hourly xp reserve needs to be a whole number - try again.')
						continue
				gotIt = True

		##########################################################################################################################
		# Required Online
		reqOnline = self.settings.getServerStat(server, "RequireOnline")
		msg = 'Would you like the bot to require users to be *Online* in order to gain hourly xp? (y/n)\n\nCurrent is *{}*.'.format(reqOnline)
		await self.bot.send_message(author, msg)
		gotIt = False
		while not gotIt:
			talk = await self.bot.wait_for_message(check=self.check, author=author, timeout=60)
			if not talk:
				msg = "*{}*, I'm out of time... type `$setup` in the main chat to start again.".format(DisplayName.name(author))
				await self.bot.send_message(author, msg)
				return
			else:
				# We got something
				if talk.content.startswith('y'):
					self.settings.setServerStat(server, "RequireOnline", "Yes")
					await self.bot.send_message(author, 'Require Online set to *Yes.*')
				elif talk.content.startswith('n'):
					self.settings.setServerStat(server, "RequireOnline", "No")
					await self.bot.send_message(author, 'Require Online set to *No.*')
				else:
					# Skipping
					await self.bot.send_message(author, 'Require Online shall remain *{}*'.format(reqOnline))
				gotIt = True
		
		##########################################################################################################################
		# Required Role for XP
		reqXP = self.settings.getServerStat(server, "RequiredXPRole")
		if not reqXP:
			reqXP = "Everyone"
		else:
			reqXP = DisplayName.roleForID(reqXP, server)
		msg = 'What should the minimum role be to use the xp system? (type `everyone` to give all users access)\n\nCurrent is **{}**.'.format(reqXP)
		await self.bot.send_message(author, msg)
		gotIt = False
		while not gotIt:
			talk = await self.bot.wait_for_message(check=self.checkRole, author=author, timeout=60)
			if not talk:
				msg = "*{}*, I'm out of time... type `$setup` in the main chat to start again.".format(DisplayName.name(author))
				await self.bot.send_message(author, msg)
				return
			else:
				# We got something
				if talk.content == "skip":
					await self.bot.send_message(author, 'Minimum xp role will remian **{}**.'.format(reqXP))
				elif talk.content == "everyone":
					self.settings.setServerStat(server, "RequiredXPRole", None)
					await self.bot.send_message(author, 'Minimum xp role set to **Everyone**.')
				else:
					role = DisplayName.roleForName(talk.content, server)
					if not role:
						msg = "It doesn't look like **{}** is a role on your server - try again.".format(talk.content)
						await self.bot.send_message(author, msg)
						continue
					else:
						self.settings.setServerStat(server, "RequiredXPRole", role.id)
						await self.bot.send_message(author, 'Minimum xp role set to **{}**.'.format(role.name))
				gotIt = True

		##########################################################################################################################
		# Required Role for XP
		adminUnlimited = self.settings.getServerStat(server, "AdminUnlimited")
		msg = 'Would you like to give server admins unlimited xp reserve? (y/n)\n\nCurrent is *{}*.'.format(adminUnlimited)
		await self.bot.send_message(author, msg)
		gotIt = False
		while not gotIt:
			talk = await self.bot.wait_for_message(check=self.check, author=author, timeout=60)
			if not talk:
				msg = "*{}*, I'm out of time... type `$setup` in the main chat to start again.".format(DisplayName.name(author))
				await self.bot.send_message(author, msg)
				return
			else:
				# We got something
				if talk.content.startswith('y'):
					self.settings.setServerStat(server, "AdminUnlimited", "Yes")
					await self.bot.send_message(author, 'Unlimited xp reserve for admins set to *Yes.*')
				elif talk.content.startswith('n'):
					self.settings.setServerStat(server, "AdminUnlimited", "No")
					await self.bot.send_message(author, 'Unlimited xp reserve for admins set to *No.*')
				else:
					# Skipping
					await self.bot.send_message(author, 'Unlimited xp reserve for admins shall remain *{}*'.format(adminUnlimited))
				gotIt = True

		##########################################################################################################################
		# Required Role for XP
		xpProm = self.settings.getServerStat(server, "XPPromote")
		msg = 'Would you like me to auto-promote users based on xp? (y/n) - You\'ll be able to set which roles can be promoted to - and their xp requirements.\n\nCurrent is *{}*.'.format(xpProm)
		await self.bot.send_message(author, msg)
		gotIt = False
		while not gotIt:
			talk = await self.bot.wait_for_message(check=self.check, author=author, timeout=60)
			if not talk:
				msg = "*{}*, I'm out of time... type `$setup` in the main chat to start again.".format(DisplayName.name(author))
				await self.bot.send_message(author, msg)
				return
			else:
				# We got something
				if talk.content.startswith('y'):
					self.settings.setServerStat(server, "XPPromote", "Yes")
					await self.bot.send_message(author, 'XP promote set to *Yes.*')
				elif talk.content.startswith('n'):
					self.settings.setServerStat(server, "XPPromote", "No")
					await self.bot.send_message(author, 'XP promote set to *No.*')
				else:
					# Skipping
					await self.bot.send_message(author, 'XP promote shall remain *{}*'.format(xpProm))
				gotIt = True

		##########################################################################################################################
		# Required Role for XP
		xpDem = self.settings.getServerStat(server, "XPDemote")
		msg = 'Would you like me to auto-demote users based on xp? (y/n) - You\'ll be able to set which roles can be demoted to - and their xp requirements.\n\nCurrent is *{}*.'.format(xpDem)
		await self.bot.send_message(author, msg)
		gotIt = False
		while not gotIt:
			talk = await self.bot.wait_for_message(check=self.check, author=author, timeout=60)
			if not talk:
				msg = "*{}*, I'm out of time... type `$setup` in the main chat to start again.".format(DisplayName.name(author))
				await self.bot.send_message(author, msg)
				return
			else:
				# We got something
				if talk.content.startswith('y'):
					self.settings.setServerStat(server, "XPDemote", "Yes")
					await self.bot.send_message(author, 'XP demote set to *Yes.*')
				elif talk.content.startswith('n'):
					self.settings.setServerStat(server, "XPDemote", "No")
					await self.bot.send_message(author, 'XP demote set to *No.*')
				else:
					# Skipping
					await self.bot.send_message(author, 'XP demote shall remain *{}*'.format(xpDem))
				gotIt = True

		##########################################################################################################################
		# XP Roles
		# Recheck xpProm and xpDem
		xpProm = self.settings.getServerStat(server, "XPPromote")
		xpDem = self.settings.getServerStat(server, "XPDemote")
		if xpProm.lower() == "yes" or xpDem.lower() == "yes":
			msg = 'To set up your xp promotion/demotion roles - use the `$addxprole [role] [required xp]` and `$removexprole [role]` in the main chat.'
			await self.bot.send_message(author, msg)

		await self.picThresh(ctx)


	async def picThresh(self, ctx):
		channel = ctx.message.channel
		author  = ctx.message.author
		server  = ctx.message.server

		threshold = self.settings.getServerStat(server, "PictureThreshold")

		msg = 'As an anti-spam protection measure, I have a cooldown between each picture I can display.  What would you like this cooldown delay to be (in seconds)?\n\nCurrent is *{}*.'.format(threshold)
		await self.bot.send_message(author, msg)
		gotIt = False
		while not gotIt:
			talk = await self.bot.wait_for_message(check=self.checkRole, author=author, timeout=60)
			if not talk:
				msg = "*{}*, I'm out of time... type `$setup` in the main chat to start again.".format(DisplayName.name(author))
				await self.bot.send_message(author, msg)
				return
			else:
				# We got something
				if talk.content == "skip":
					await self.bot.send_message(author, 'Anti-spam picture cooldown will remian *{}*.'.format(threshold))
				else:
					try:
						talkInt = int(talk.content)
						await self.bot.send_message(author, 'Anti-spam picture cooldown is now *{}!*'.format(talkInt))
						self.settings.setServerStat(server, "PictureThreshold", talkInt)
					except ValueError:
						# await self.autoRoleName(ctx)
						await self.bot.send_message(author, 'Anti-spam picture cooldown needs to be a whole number - try again.')
						continue
				gotIt = True
		await self.hungerLock(ctx)

	async def hungerLock(self, ctx):
		channel = ctx.message.channel
		author  = ctx.message.author
		server  = ctx.message.server

		hLock = self.settings.getServerStat(server, "HungerLock")
		msg = 'Would you like me to ignore users when I get too hungry (I *always* listen to admins)? (y/n)\n\nCurrent is *{}*.'.format(hLock)
		await self.bot.send_message(author, msg)
		gotIt = False
		while not gotIt:
			talk = await self.bot.wait_for_message(check=self.check, author=author, timeout=60)
			if not talk:
				msg = "*{}*, I'm out of time... type `$setup` in the main chat to start again.".format(DisplayName.name(author))
				await self.bot.send_message(author, msg)
				return
			else:
				# We got something
				if talk.content.startswith('y'):
					self.settings.setServerStat(server, "HungerLock", "Yes")
					await self.bot.send_message(author, 'Hunger lock set to *Yes.*')
				elif talk.content.startswith('n'):
					self.settings.setServerStat(server, "HungerLock", "No")
					await self.bot.send_message(author, 'Hunger lock set to *No.*')
				else:
					# Skipping
					await self.bot.send_message(author, 'Hunger lock shall remain *{}*'.format(hLock))
				gotIt = True
		await self.defVolume(ctx)


	async def defVolume(self, ctx):
		channel = ctx.message.channel
		author  = ctx.message.author
		server  = ctx.message.server

		dVol = float(self.settings.getServerStat(server, "DefaultVolume"))
		if not dVol:
			dVol = 0.6
		msg = 'What would you like the default volume of the music player to be? (values can be 1-100)\n\nCurrent is *{}*.'.format(int(dVol*100))
		await self.bot.send_message(author, msg)
		gotIt = False
		while not gotIt:
			talk = await self.bot.wait_for_message(check=self.checkRole, author=author, timeout=60)
			if not talk:
				msg = "*{}*, I'm out of time... type `$setup` in the main chat to start again.".format(DisplayName.name(author))
				await self.bot.send_message(author, msg)
				return
			else:
				if talk.content == "skip":
					await self.bot.send_message(author, 'Default volume will remian *{}*.'.format(int(dVol*100)))
				else:
					try:
						talkInt = int(talk.content)
						if talkInt > 100:
							talkInt = 100
						if talkInt < 1:
							talkInt = 1
						await self.bot.send_message(author, 'Default volume is now *{}!*'.format(talkInt))
						self.settings.setServerStat(server, "DefaultVolume", (talkInt/100))
					except ValueError:
						# await self.autoRoleName(ctx)
						await self.bot.send_message(author, 'Default volume needs to be a whole number - try again.')
						continue
				gotIt = True

		await self.setupComplete(ctx)

	async def setupComplete(self, ctx):
		channel = ctx.message.channel
		author  = ctx.message.author
		server  = ctx.message.server

		await self.bot.send_message(author, '__Setup Status for *{}*:__\n\n**COMPLETE**\n\nThanks, *{}*, for hanging out with me and getting things setup.\nIf you want to explore my other options - feel free to check them all out with `$help`.\n\nAlso - I work best in an admin role and it needs to be listed *above* any roles you would like me to manage.\n\nThanks!'.format(server.name, DisplayName.name(author)))

# Calling a bot command:  await self.setup.callback(self, ctx)
