import asyncio
import discord
import time
import parsedatetime
from   datetime import datetime
from   operator import itemgetter
from   discord.ext import commands
from   Cogs import Settings
from   Cogs import ReadableTime
from   Cogs import DisplayName

# This is the admin module.  It holds the admin-only commands
# Everything here *requires* that you're an admin

class Admin:

	# Init with the bot reference, and a reference to the settings var
	def __init__(self, bot, settings):
		self.bot = bot
		self.settings = settings
		
	async def message(self, message):
		# Check the message and see if we should allow it - always yes.
		# This module doesn't need to cancel messages.
		ignore = False
		delete = False
		res    = None
		# Check if user is muted
		isMute = self.settings.getUserStat(message.author, message.server, "Muted")

		# Check for admin status
		isAdmin = message.author.permissions_in(message.channel).administrator
		if not isAdmin:
			checkAdmin = self.settings.getServerStat(message.server, "AdminArray")
			for role in message.author.roles:
				for aRole in checkAdmin:
					# Get the role that corresponds to the id
					if aRole['ID'] == role.id:
						isAdmin = True

		if isMute.lower() == "yes":
			ignore = True
			delete = True
			checkTime = self.settings.getUserStat(message.author, message.server, "Cooldown")
			if checkTime:
				checkTime = int(checkTime)
			currentTime = int(time.time())
			
			# Build our PM
			if checkTime:
				# We have a cooldown
				checkRead = ReadableTime.getReadableTimeBetween(currentTime, checkTime)
				res = 'You are currently **Muted**.  You need to wait *{}* before sending messages in *{}*.'.format(checkRead, message.server.name)
			else:
				# No cooldown - muted indefinitely
				res = 'You are still **Muted** in *{}* and cannot send messages until you are **Unmuted**.'.format(message.server.name)

			if checkTime and currentTime >= checkTime:
				# We have passed the check time
				ignore = False
				delete = False
				res    = None
				self.settings.setUserStat(message.author, message.server, "Cooldown", None)
				self.settings.setUserStat(message.author, message.server, "Muted", "No")
			
		
		ignoreList = self.settings.getServerStat(message.server, "IgnoredUsers")
		if ignoreList:
			for user in ignoreList:
				if not isAdmin and message.author.id == user["ID"]:
					# Found our user - ignored
					ignore = True

		adminLock = self.settings.getServerStat(message.server, "AdminLock")
		if not isAdmin and adminLock.lower() == "yes":
			ignore = True

		if isAdmin:
			ignore = False
			delete = False

		# Get Owner and OwnerLock
		try:
			ownerLock = self.settings.serverDict['OwnerLock']
		except KeyError:
			ownerLock = "No"
		try:
			owner = self.settings.serverDict['Owner']
		except KeyError:
			owner = None
		# Check if owner exists - and we're in OwnerLock
		if owner and ownerLock.lower() == "yes":
			# Check if the message author is the owner or not
			if not message.author.id == owner:
				# Not the owner - ignore
				ignore = True
				
		if not isAdmin and res:
			# We have a response - PM it
			await self.bot.send_message(message.author, res)
		
		return { 'Ignore' : ignore, 'Delete' : delete}


	@commands.command(pass_context=True)
	async def setmadlibschannel(self, ctx, *, channel : discord.Channel = None):
		"""Sets the required role ID to stop the music player (admin only)."""
		
		isAdmin = ctx.message.author.permissions_in(ctx.message.channel).administrator
		# Only allow admins to change server stats
		if not isAdmin:
			await self.bot.send_message(ctx.message.channel, 'You do not have sufficient privileges to access this command.')
			return

		if channel == None:
			self.settings.setServerStat(ctx.message.server, "MadLibsChannel", "")
			msg = 'MadLibs works in *any channel* now.'
			await self.bot.send_message(ctx.message.channel, msg)
			return

		if type(channel) is str:
			try:
				role = discord.utils.get(message.server.channels, name=role)
			except:
				print("That channel does not exist")
				return

		# If we made it this far - then we can add it
		self.settings.setServerStat(ctx.message.server, "MadLibsChannel", channel.id)

		msg = 'MadLibs channel set to **{}**.'.format(channel.name)
		await self.bot.send_message(ctx.message.channel, msg)
		
	
	@setmadlibschannel.error
	async def setmadlibschannel_error(self, ctx, error):
		# do stuff
		msg = 'setmadlibschannel Error: {}'.format(ctx)
		await self.bot.say(msg)

	@commands.command(pass_context=True)
	async def setxpreserve(self, ctx, *, member = None, xpAmount : int = None):
		"""Set's an absolute value for the member's xp reserve (admin only)."""
		
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
		if xpAmount == None:
			# Still no xp
			msg = 'Usage: `$setxpreserve [member] [amount]`'
			await self.bot.send_message(channel, msg)
			return

		self.settings.setUserStat(member, server, "XPReserve", xpAmount)
		msg = '*{}\'s* XPReserve was set to *{}*!'.format(DisplayName.name(member), xpAmount)
		await self.bot.send_message(channel, msg)


	@setxpreserve.error
	async def setxpreserve_error(self, ctx, error):
		# do stuff
		msg = 'setxp Error: {}'.format(ctx)
		await self.bot.say(msg)
	
	@commands.command(pass_context=True)
	async def setdefaultrole(self, ctx, *, role : discord.Role = None):
		"""Sets the default role or position for auto-role assignment."""
		author  = ctx.message.author
		server  = ctx.message.server
		channel = ctx.message.channel

		isAdmin = author.permissions_in(channel).administrator
		# Only allow admins to change server stats
		if not isAdmin:
			await self.bot.send_message(channel, 'You do not have sufficient privileges to access this command.')
			return

		if role is None:
			# Disable auto-role and set default to none
			self.settings.setServerStat(server, "DefaultRole", "")
			msg = 'Auto-role management now **disabled**.'
			await self.bot.send_message(channel, msg)
			return

		if type(role) is int:
			# Likely a position listed
			self.settings.setServerStat(server, "DefaultRole", role)
			try:
				rolename = discord.utils.get(server.roles, position=role)
				await self.bot.send_message(channel, 'Default role set to **{}**!'.format(rolename.name))
			except:
				print("That role does not exist")
				return

		if type(role) is str:
			try:
				role = discord.utils.get(server.roles, name=role)
			except:
				print("That role does not exist")
				return

		self.settings.setServerStat(server, "DefaultRole", role.id)
		await self.bot.send_message(channel, 'Default role set to **{}**!'.format(role.name))


	@setdefaultrole.error
	async def setdefaultrole_error(self, ctx, error):
		# do stuff
		msg = 'setdefaultrole Error: {}'.format(ctx)
		await self.bot.say(msg)


	@commands.command(pass_context=True)
	async def addxprole(self, ctx, *, role = None, xp : int = None):
		"""Adds a new role to the xp promotion/demotion system (admin only)."""
		
		author  = ctx.message.author
		server  = ctx.message.server
		channel = ctx.message.channel
		
		isAdmin = author.permissions_in(channel).administrator
		# Only allow admins to change server stats
		if not isAdmin:
			await self.bot.send_message(channel, 'You do not have sufficient privileges to access this command.')
			return
		if xp == None:
			# Either xp wasn't set - or it's the last section
			if type(role) is str:
				# It' a string - the hope continues
				roleCheck = DisplayName.checkRoleForInt(role, server)
				if not roleCheck:
					msg = 'Usage: `$addxprole [role] [required xp]`'
					await self.bot.send_message(ctx.message.channel, msg)
					return
				if not roleCheck["Role"]:
					msg = 'I couldn\'t find *{}* on the server.'.format(role)
					await self.bot.send_message(ctx.message.channel, msg)
					return
				role = roleCheck["Role"]
				xp   = roleCheck["Int"]

		if xp == None:
			msg = 'Usage: `$addxprole [role] [required xp]`'
			await self.bot.send_message(channel, msg)
			return
		if not type(xp) is int:
			msg = 'Usage: `$addxprole [role] [required xp]`'
			await self.bot.send_message(channel, msg)
			return

		# Now we see if we already have that role in our list
		promoArray = self.settings.getServerStat(server, "PromotionArray")
		for aRole in promoArray:
			# Get the role that corresponds to the id
			if aRole['ID'] == role.id:
				# We found it - throw an error message and return
				msg = '**{}** is already in the list.  Required xp: *{}*'.format(role.name, aRole['XP'])
				await self.bot.send_message(channel, msg)
				return

		# If we made it this far - then we can add it
		promoArray.append({ 'ID' : role.id, 'Name' : role.name, 'XP' : xp })
		self.settings.setServerStat(server, "PromotionArray", promoArray)

		msg = '**{}** added to list.  Required xp: *{}*'.format(role.name, xp)
		await self.bot.send_message(channel, msg)
		return

	@addxprole.error
	async def addxprole_error(self, ctx, error):
		# do stuff
		msg = 'addxprole Error: {}'.format(ctx)
		await self.bot.say(msg)
		
		
	@commands.command(pass_context=True)
	async def removexprole(self, ctx, *, role = None):
		"""Removes a role from the xp promotion/demotion system (admin only)."""
		
		author  = ctx.message.author
		server  = ctx.message.server
		channel = ctx.message.channel
		
		isAdmin = author.permissions_in(channel).administrator
		# Only allow admins to change server stats
		if not isAdmin:
			await self.bot.send_message(channel, 'You do not have sufficient privileges to access this command.')
			return

		if role == None:
			msg = 'Usage: `$removexprole [role]`'
			await self.bot.send_message(channel, msg)
			return

		if type(role) is str:
			# It' a string - the hope continues
			# Let's clear out by name first - then by role id
			promoArray = self.settings.getServerStat(server, "PromotionArray")

			for aRole in promoArray:
				# Get the role that corresponds to the name
				if aRole['Name'].lower() == role.lower():
					# We found it - let's remove it
					promoArray.remove(aRole)
					self.settings.setServerStat(server, "PromotionArray", promoArray)
					msg = '**{}** removed successfully.'.format(aRole['Name'])
					await self.bot.send_message(channel, msg)
					return
			# At this point - no name
			# Let's see if it's a role that's had a name change


			roleCheck = DisplayName.roleForName(role, server)
			if roleCheck:
				# We got a role
				# If we're here - then the role is an actual role
				promoArray = self.settings.getServerStat(server, "PromotionArray")

				for aRole in promoArray:
					# Get the role that corresponds to the id
					if aRole['ID'] == roleCheck.id:
						# We found it - let's remove it
						promoArray.remove(aRole)
						self.settings.setServerStat(server, "PromotionArray", promoArray)
						msg = '**{}** removed successfully.'.format(aRole['Name'])
						await self.bot.send_message(channel, msg)
						return
				
			# If we made it this far - then we didn't find it
			msg = '{} not found in list.'.format(roleCheck.name)
			await self.bot.send_message(channel, msg)
			return

		# If we're here - then the role is an actual role - I think?
		promoArray = self.settings.getServerStat(server, "PromotionArray")

		for aRole in promoArray:
			# Get the role that corresponds to the id
			if aRole['ID'] == role.id:
				# We found it - let's remove it
				promoArray.remove(aRole)
				self.settings.setServerStat(server, "PromotionArray", promoArray)
				msg = '**{}** removed successfully.'.format(aRole['Name'])
				await self.bot.send_message(channel, msg)
				return

		# If we made it this far - then we didn't find it
		msg = '{} not found in list.'.format(role.name)
		await self.bot.send_message(channel, msg)

	@removexprole.error
	async def removexprole_error(self, ctx, error):
		# do stuff
		msg = 'removexprole Error: {}'.format(ctx)
		await self.bot.say(msg)

	@commands.command(pass_context=True)
	async def prunexproles(self, ctx):
		"""Removes any roles from the xp promotion/demotion system that are no longer on the server (admin only)."""

		author  = ctx.message.author
		server  = ctx.message.server
		channel = ctx.message.channel

		isAdmin = author.permissions_in(channel).administrator
		# Only allow admins to change server stats
		if not isAdmin:
			await self.bot.send_message(channel, 'You do not have sufficient privileges to access this command.')
			return

		# Get the array
		promoArray = self.settings.getServerStat(server, "PromotionArray")
		# promoSorted = sorted(promoArray, key=itemgetter('XP', 'Name'))
		promoSorted = sorted(promoArray, key=lambda x:int(x['XP']))
		
		removed = 0
		for arole in promoSorted:
			# Get current role name based on id
			foundRole = False
			for role in server.roles:
				if role.id == arole['ID']:
					# We found it
					foundRole = True
			if not foundRole:
				promoArray.remove(arole)
				removed += 1

		msg = 'Removed *{}* orphaned roles.'.format(removed)
		await self.bot.send_message(ctx.message.channel, msg)
		

	@commands.command(pass_context=True)
	async def setxprole(self, ctx, *, role : discord.Role = None):
		"""Sets the required role ID to give xp, gamble, or feed the bot (admin only)."""
		
		isAdmin = ctx.message.author.permissions_in(ctx.message.channel).administrator
		# Only allow admins to change server stats
		if not isAdmin:
			await self.bot.send_message(ctx.message.channel, 'You do not have sufficient privileges to access this command.')
			return

		if role == None:
			self.settings.setServerStat(ctx.message.server, "RequiredXPRole", "")
			msg = 'Giving xp, gambling, and feeding the bot now available to *everyone*.'
			await self.bot.send_message(ctx.message.channel, msg)
			return

		if type(role) is str:
			try:
				role = discord.utils.get(message.server.roles, name=role)
			except:
				print("That role does not exist")
				return

		# If we made it this far - then we can add it
		self.settings.setServerStat(ctx.message.server, "RequiredXPRole", role.id)

		msg = 'Role required to give xp, gamble, or feed the bot set to **{}**.'.format(role.name)
		await self.bot.send_message(ctx.message.channel, msg)
		
	
	@setxprole.error
	async def xprole_error(self, ctx, error):
		# do stuff
		msg = 'setxprole Error: {}'.format(ctx)
		await self.bot.say(msg)

	@commands.command(pass_context=True)
	async def xprole(self, ctx):
		"""Lists the required role to give xp, gamble, or feed the bot."""
		role = self.settings.getServerStat(ctx.message.server, "RequiredXPRole")
		if role == None or role == "":
			msg = '**Everyone** can give xp, gamble, and feed the bot.'
			await self.bot.say(msg)
		else:
			# Role is set - let's get its name
			found = False
			for arole in ctx.message.server.roles:
				if arole.id == role:
					found = True
					msg = 'You need to be a/an **{}** to give xp, gamble, or feed the bot.'.format(arole.name)
			if not found:
				msg = 'There is no role that matches id: `{}` - consider updating this setting.'.format(role)
			await self.bot.send_message(ctx.message.channel, msg)
		
	@commands.command(pass_context=True)
	async def setstoprole(self, ctx, *, role : discord.Role = None):
		"""Sets the required role ID to stop the music player (admin only)."""
		
		isAdmin = ctx.message.author.permissions_in(ctx.message.channel).administrator
		# Only allow admins to change server stats
		if not isAdmin:
			await self.bot.send_message(ctx.message.channel, 'You do not have sufficient privileges to access this command.')
			return

		if role == None:
			self.settings.setServerStat(ctx.message.server, "RequiredStopRole", "")
			msg = 'Stopping the music now *admin-only*.'
			await self.bot.send_message(ctx.message.channel, msg)
			return

		if type(role) is str:
			try:
				role = discord.utils.get(message.server.roles, name=role)
			except:
				print("That role does not exist")
				return

		# If we made it this far - then we can add it
		self.settings.setServerStat(ctx.message.server, "RequiredStopRole", role.id)

		msg = 'Role required to stop the music player set to **{}**.'.format(role.name)
		await self.bot.send_message(ctx.message.channel, msg)
		
	
	@setstoprole.error
	async def stoprole_error(self, ctx, error):
		# do stuff
		msg = 'setstoprole Error: {}'.format(ctx)
		await self.bot.say(msg)

	@commands.command(pass_context=True)
	async def stoprole(self, ctx):
		"""Lists the required role to stop the bot from playing music."""
		role = self.settings.getServerStat(ctx.message.server, "RequiredStopRole")
		if role == None or role == "":
			msg = '**Only Admins** can use stop.'
			await self.bot.say(msg)
		else:
			# Role is set - let's get its name
			found = False
			for arole in ctx.message.server.roles:
				if arole.id == role:
					found = True
					msg = 'You need to be a/an **{}** to use stop.'.format(arole.name)
			if not found:
				msg = 'There is no role that matches id: `{}` - consider updating this setting.'.format(role)
			await self.bot.send_message(ctx.message.channel, msg)

		
	@commands.command(pass_context=True)
	async def setlinkrole(self, ctx, *, role : discord.Role = None):
		"""Sets the required role ID to add/remove links (admin only)."""
		
		isAdmin = ctx.message.author.permissions_in(ctx.message.channel).administrator
		# Only allow admins to change server stats
		if not isAdmin:
			await self.bot.send_message(ctx.message.channel, 'You do not have sufficient privileges to access this command.')
			return

		if role == None:
			self.settings.setServerStat(ctx.message.server, "RequiredLinkRole", "")
			msg = 'Add/remove links now *admin-only*.'
			await self.bot.send_message(ctx.message.channel, msg)
			return

		if type(role) is str:
			try:
				role = discord.utils.get(message.server.roles, name=role)
			except:
				print("That role does not exist")
				return

		# If we made it this far - then we can add it
		self.settings.setServerStat(ctx.message.server, "RequiredLinkRole", role.id)

		msg = 'Role required for add/remove links set to **{}**.'.format(role.name)
		await self.bot.send_message(ctx.message.channel, msg)
		
	
	@setlinkrole.error
	async def linkrole_error(self, ctx, error):
		# do stuff
		msg = 'setlinkrole Error: {}'.format(ctx)
		await self.bot.say(msg)
		
		
	@commands.command(pass_context=True)
	async def sethackrole(self, ctx, *, role : discord.Role = None):
		"""Sets the required role ID to add/remove hacks (admin only)."""
		
		isAdmin = ctx.message.author.permissions_in(ctx.message.channel).administrator
		# Only allow admins to change server stats
		if not isAdmin:
			await self.bot.send_message(ctx.message.channel, 'You do not have sufficient privileges to access this command.')
			return

		if role == None:
			self.settings.setServerStat(ctx.message.server, "RequiredHackRole", "")
			msg = 'Add/remove hacks now *admin-only*.'
			await self.bot.send_message(ctx.message.channel, msg)
			return

		if type(role) is str:
			try:
				role = discord.utils.get(message.server.roles, name=role)
			except:
				print("That role does not exist")
				return

		# If we made it this far - then we can add it
		self.settings.setServerStat(ctx.message.server, "RequiredHackRole", role.id)

		msg = 'Role required for add/remove hacks set to **{}**.'.format(role.name)
		await self.bot.send_message(ctx.message.channel, msg)


	@sethackrole.error
	async def hackrole_error(self, ctx, error):
		# do stuff
		msg = 'sethackrole Error: {}'.format(ctx)
		await self.bot.say(msg)
		
		
	@commands.command(pass_context=True)
	async def setrules(self, ctx, *, rules : str = None):
		"""Set the server's rules (admin only)."""
		
		isAdmin = ctx.message.author.permissions_in(ctx.message.channel).administrator
		# Only allow admins to change server stats
		if not isAdmin:
			await self.bot.send_message(ctx.message.channel, 'You do not have sufficient privileges to access this command.')
			return
		
		if rules == None:
			rules = ""
			
		self.settings.setServerStat(ctx.message.server, "Rules", rules)
		msg = 'Rules now set to:\n{}'.format(rules)
		
		await self.bot.send_message(ctx.message.channel, msg)
		
		
	@commands.command(pass_context=True)
	async def lock(self, ctx):
		"""Toggles whether the bot only responds to admins (admin only)."""
		
		isAdmin = ctx.message.author.permissions_in(ctx.message.channel).administrator
		
		# Only allow admins to change server stats
		if not isAdmin:
			await self.bot.send_message(ctx.message.channel, 'You do not have sufficient privileges to access this command.')
			return
		
		isLocked = self.settings.getServerStat(ctx.message.server, "AdminLock")
		if isLocked.lower() == "yes":
			msg = 'Admin lock now *Off*.'
			self.settings.setServerStat(ctx.message.server, "AdminLock", "No")
		else:
			msg = 'Admin lock now *On*.'
			self.settings.setServerStat(ctx.message.server, "AdminLock", "Yes")
		await self.bot.send_message(ctx.message.channel, msg)
		
		
	@commands.command(pass_context=True)
	async def addadmin(self, ctx, *, role : discord.Role = None):
		"""Adds a new role to the xp promotion/demotion system (admin only)."""
		isAdmin = ctx.message.author.permissions_in(ctx.message.channel).administrator
		# Only allow admins to change server stats
		if not isAdmin:
			await self.bot.send_message(ctx.message.channel, 'You do not have sufficient privileges to access this command.')
			return

		if role == None:
			msg = 'Usage: `$addadmin [role]`'
			await self.bot.send_message(ctx.message.channel, msg)
			return

		if type(role) is str:
			try:
				role = discord.utils.get(message.server.roles, name=role)
			except:
				print("That role does not exist")
				return

		# Now we see if we already have that role in our list
		promoArray = self.settings.getServerStat(ctx.message.server, "AdminArray")

		for aRole in promoArray:
			# Get the role that corresponds to the id
			if aRole['ID'] == role.id:
				# We found it - throw an error message and return
				msg = '**{}** is already in the list.'.format(role.name)
				await self.bot.send_message(ctx.message.channel, msg)
				return

		# If we made it this far - then we can add it
		promoArray.append({ 'ID' : role.id, 'Name' : role.name })
		self.settings.setServerStat(ctx.message.server, "AdminArray", promoArray)

		msg = '**{}** added to list.'.format(role.name)
		await self.bot.send_message(ctx.message.channel, msg)
		return

	@addadmin.error
	async def addadmin_error(self, ctx, error):
		# do stuff
		msg = 'addadmin Error: {}'.format(ctx)
		await self.bot.say(msg)
		
		
	@commands.command(pass_context=True)
	async def removeadmin(self, ctx, *, role : discord.Role = None):
		"""Removes a role from the admin list (admin only)."""
		isAdmin = ctx.message.author.permissions_in(ctx.message.channel).administrator
		# Only allow admins to change server stats
		if not isAdmin:
			await self.bot.send_message(ctx.message.channel, 'You do not have sufficient privileges to access this command.')
			return

		if role == None:
			msg = 'Usage: `$removeadmin [role]`'
			await self.bot.send_message(ctx.message.channel, msg)
			return

		if type(role) is str:
			try:
				role = discord.utils.get(message.server.roles, name=role)
			except:
				print("That role does not exist")
				return

		# If we're here - then the role is a real one
		promoArray = self.settings.getServerStat(ctx.message.server, "AdminArray")

		for aRole in promoArray:
			# Get the role that corresponds to the id
			if aRole['ID'] == role.id:
				# We found it - let's remove it
				promoArray.remove(aRole)
				self.settings.setServerStat(ctx.message.server, "AdminArray", promoArray)
				msg = '**{}** removed successfully.'.format(role.name)
				await self.bot.send_message(ctx.message.channel, msg)
				return

		# If we made it this far - then we didn't find it
		msg = '**{}** not found in list.'.format(aRole['Name'])
		await self.bot.send_message(ctx.message.channel, msg)

	@removeadmin.error
	async def removeadmin_error(self, ctx, error):
		# do stuff
		msg = 'removeadmin Error: {}'.format(ctx)
		await self.bot.say(msg)
		
		
	@commands.command(pass_context=True)
	async def removemotd(self, ctx, *, chan : discord.Channel = None):
		"""Removes the message of the day from the selected channel."""
		
		channel = ctx.message.channel
		author  = ctx.message.author
		server  = ctx.message.server
		
		isAdmin = author.permissions_in(channel).administrator
		# Only allow admins to change server stats
		if not isAdmin:
			await self.bot.send_message(channel, 'You do not have sufficient privileges to access this command.')
			return
		if chan == None:
			chan = channel
		if type(chan) is str:
			try:
				chan = discord.utils.get(server.channels, name=chan)
			except:
				print("That channel does not exist")
				return
		# At this point - we should have the necessary stuff
		motdArray = self.settings.getServerStat(server, "ChannelMOTD")
		for a in motdArray:
			# Get the channel that corresponds to the id
			if a['ID'] == chan.id:
				# We found it - throw an error message and return
				motdArray.remove(a)
				self.settings.setServerStat(server, "ChannelMOTD", motdArray)
				
				msg = 'MOTD for *{}* removed.'.format(channel.name)
				await self.bot.send_message(channel, msg)
				await self.bot.edit_channel(channel, topic=None)
				await self.updateMOTD()
				return		
		msg = 'MOTD for *{}* not found.'.format(chan.name)
		await self.bot.send_message(channel, msg)	
		
	@removemotd.error
	async def removemotd_error(self, ctx, error):
		# do stuff
		msg = 'removemotd Error: {}'.format(ctx)
		await self.bot.say(msg)	
				

	@commands.command(pass_context=True)
	async def broadcast(self, ctx, *, message : str = None):
		"""Broadcasts a message to all connected servers.  Can only be done by the owner."""

		channel = ctx.message.channel
		author  = ctx.message.author

		if message == None:
			msg = 'Usage: `$broadcast [message]`'
			await self.bot.send_message(channel, msg)
			return

		serverDict = self.settings.serverDict

		try:
			owner = serverDict['Owner']
		except KeyError:
			owner = None

		if owner == None:
			# No owner set
			msg = 'I have not been claimed, *yet*.'
			await self.bot.send_message(channel, msg)
			return
		else:
			if not author.id == owner:
				msg = 'You are not the *true* owner of me.  Only the rightful owner can broadcast.'
				await self.bot.send_message(channel, msg)
				return
		
		for server in self.bot.servers:
			await self.bot.send_message(server, message)

		
	@commands.command(pass_context=True)
	async def setmotd(self, ctx, message : str = None, users : str = "No", chan : discord.Channel = None):
		"""Adds a message of the day to the selected channel."""
		
		channel = ctx.message.channel
		author  = ctx.message.author
		server  = ctx.message.server
		
		isAdmin = author.permissions_in(channel).administrator
		# Only allow admins to change server stats
		if not isAdmin:
			await self.bot.send_message(channel, 'You do not have sufficient privileges to access this command.')
			return
		if not message:
			msg = 'Usage: `$setmotd "[message]" [usercount Yes/No (default is No)] [channel] `'
			await self.bot.send_message(channel, msg)
			return	
		if not chan:
			chan = channel
		if type(chan) is str:
			try:
				chan = discord.utils.get(server.channels, name=chan)
			except:
				print("That channel does not exist")
				return
		
		# At this point - we should have the necessary stuff
		motdArray = self.settings.getServerStat(server, "ChannelMOTD")
		for a in motdArray:
			# Get the channel that corresponds to the id
			if a['ID'] == chan.id:
				# We found it - throw an error message and return
				a['MOTD'] = message
				a['ListOnline'] = users
				self.settings.setServerStat(server, "ChannelMOTD", motdArray)
				
				msg = 'MOTD for *{}* changed.'.format(chan.name)
				await self.bot.send_message(channel, msg)
				await self.updateMOTD()
				return

		# If we made it this far - then we can add it
		motdArray.append({ 'ID' : chan.id, 'MOTD' : message, 'ListOnline' : users })
		self.settings.setServerStat(server, "ChannelMOTD", motdArray)

		msg = 'MOTD for *{}* added.'.format(chan.name)
		await self.bot.send_message(channel, msg)
		await self.updateMOTD()

		
	@setmotd.error
	async def setmotd_error(self, ctx, error):
		# do stuff
		msg = 'setmotd Error: {}'.format(ctx)
		await self.bot.say(msg)
		
		
	async def updateMOTD(self):
		for server in self.bot.servers:
			try:
				channelMOTDList = self.settings.getServerStat(server, "ChannelMOTD")
			except KeyError:
				channelMOTDList = []
			
			if len(channelMOTDList) > 0:
				members = 0
				membersOnline = 0
				for member in server.members:
					members += 1
					if str(member.status).lower() == "online":
						membersOnline += 1
				
			for id in channelMOTDList:
				channel = self.bot.get_channel(id['ID'])
				if channel:
					# Got our channel - let's update
					motd = id['MOTD'] # A markdown message of the day
					listOnline = id['ListOnline'] # Yes/No - do we list all online members or not?
						
					if listOnline.lower() == "yes":
						msg = '{} - ({}/{} users online)'.format(motd, int(membersOnline), int(members))
					else:
						msg = motd
							
					# print(msg)
							
					await self.bot.edit_channel(channel, topic=msg)
