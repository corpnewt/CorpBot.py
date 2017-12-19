import asyncio
import discord
import random
from   discord.ext import commands
from   Cogs import Settings
from   Cogs import DisplayName
from   Cogs import Nullify

def setup(bot):
	# Add the bot and deps
	settings = bot.get_cog("Settings")
	bot.add_cog(UserRole(bot, settings))

class UserRole:
	
	def __init__(self, bot, settings):
		self.bot = bot
		self.settings = settings

	@commands.command(pass_context=True)
	async def adduserrole(self, ctx, *, role = None):
		"""Adds a new role to the user role system (admin only)."""
		
		author  = ctx.message.author
		server  = ctx.message.guild
		channel = ctx.message.channel

		usage = 'Usage: `{}adduserrole [role]`'.format(ctx.prefix)

		# Check if we're suppressing @here and @everyone mentions
		if self.settings.getServerStat(server, "SuppressMentions"):
			suppress = True
		else:
			suppress = False
		
		isAdmin = author.permissions_in(channel).administrator
		# Only allow admins to change server stats
		if not isAdmin:
			await channel.send('You do not have sufficient privileges to access this command.')
			return
		
		if role == None:
			await ctx.send(usage)
			return

		if type(role) is str:
			if role == "everyone":
				role = "@everyone"
			# It' a string - the hope continues
			roleCheck = DisplayName.roleForName(role, server)
			if not roleCheck:
				msg = "I couldn't find **{}**...".format(role)
				if suppress:
					msg = Nullify.clean(msg)
				await ctx.send(msg)
				return
			role = roleCheck

		# Now we see if we already have that role in our list
		try:
			promoArray = self.settings.getServerStat(server, "UserRoles")
		except Exception:
			promoArray = []
		if promoArray == None:
			promoArray = []

		for aRole in promoArray:
			# Get the role that corresponds to the id
			if str(aRole['ID']) == str(role.id):
				# We found it - throw an error message and return
				msg = '**{}** is already in the list.'.format(role.name)
				# Check for suppress
				if suppress:
					msg = Nullify.clean(msg)
				await channel.send(msg)
				return

		# If we made it this far - then we can add it
		promoArray.append({ 'ID' : role.id, 'Name' : role.name })
		self.settings.setServerStat(server, "UserRoles", promoArray)

		msg = '**{}** added to list.'.format(role.name)
		# Check for suppress
		if suppress:
			msg = Nullify.clean(msg)
		await channel.send(msg)
		return

	@adduserrole.error
	async def adduserrole_error(self, ctx, error):
		# do stuff
		msg = 'adduserrole Error: {}'.format(ctx)
		await error.channel.send(msg)

	@commands.command(pass_context=True)
	async def removeuserrole(self, ctx, *, role = None):
		"""Removes a role from the user role system (admin only)."""
		
		author  = ctx.message.author
		server  = ctx.message.guild
		channel = ctx.message.channel

		usage = 'Usage: `{}removeuserrole [role]`'.format(ctx.prefix)

		# Check if we're suppressing @here and @everyone mentions
		if self.settings.getServerStat(server, "SuppressMentions"):
			suppress = True
		else:
			suppress = False
		
		isAdmin = author.permissions_in(channel).administrator
		# Only allow admins to change server stats
		if not isAdmin:
			await channel.send('You do not have sufficient privileges to access this command.')
			return

		if role == None:
			await channel.send(usage)
			return

		if type(role) is str:
			if role == "everyone":
				role = "@everyone"
			# It' a string - the hope continues
			# Let's clear out by name first - then by role id
			try:
				promoArray = self.settings.getServerStat(server, "UserRoles")
			except Exception:
				promoArray = []
			if promoArray == None:
				promoArray = []

			for aRole in promoArray:
				# Get the role that corresponds to the name
				if aRole['Name'].lower() == role.lower():
					# We found it - let's remove it
					promoArray.remove(aRole)
					self.settings.setServerStat(server, "UserRoles", promoArray)
					msg = '**{}** removed successfully.'.format(aRole['Name'])
					# Check for suppress
					if suppress:
						msg = Nullify.clean(msg)
					await channel.send(msg)
					return
			# At this point - no name
			# Let's see if it's a role that's had a name change


			roleCheck = DisplayName.roleForName(role, server)
			if roleCheck:
				# We got a role
				# If we're here - then the role is an actual role
				try:
					promoArray = self.settings.getServerStat(server, "UserRoles")
				except Exception:
					promoArray = []
				if promoArray == None:
					promoArray = []

				for aRole in promoArray:
					# Get the role that corresponds to the id
					if str(aRole['ID']) == str(roleCheck.id):
						# We found it - let's remove it
						promoArray.remove(aRole)
						self.settings.setServerStat(server, "UserRoles", promoArray)
						msg = '**{}** removed successfully.'.format(aRole['Name'])
						# Check for suppress
						if suppress:
							msg = Nullify.clean(msg)
						await channel.send(msg)
						return
				
			# If we made it this far - then we didn't find it
			msg = '*{}* not found in list.'.format(roleCheck.name)
			# Check for suppress
			if suppress:
				msg = Nullify.clean(msg)
			await channel.send(msg)
			return

		# If we're here - then the role is an actual role - I think?
		try:
			promoArray = self.settings.getServerStat(server, "UserRoles")
		except Exception:
			promoArray = []
		if promoArray == None:
			promoArray = []

		for aRole in promoArray:
			# Get the role that corresponds to the id
			if str(arole['ID']) == str(role.id):
				# We found it - let's remove it
				promoArray.remove(aRole)
				self.settings.setServerStat(server, "UserRoles", promoArray)
				msg = '**{}** removed successfully.'.format(aRole['Name'])
				# Check for suppress
				if suppress:
					msg = Nullify.clean(msg)
				await channel.send(msg)
				return

		# If we made it this far - then we didn't find it
		msg = '*{}* not found in list.'.format(role.name)
		# Check for suppress
		if suppress:
			msg = Nullify.clean(msg)
		await channel.send(msg)

	@removeuserrole.error
	async def removeuserrole_error(self, ctx, error):
		# do stuff
		msg = 'removeuserrole Error: {}'.format(ctx)
		await error.channel.send(msg)

	@commands.command(pass_context=True)
	async def listuserroles(self, ctx):
		"""Lists all roles for the user role system."""
		
		server  = ctx.message.guild
		channel = ctx.message.channel

		# Check if we're suppressing @here and @everyone mentions
		if self.settings.getServerStat(server, "SuppressMentions"):
			suppress = True
		else:
			suppress = False
		
		# Get the array
		try:
			promoArray = self.settings.getServerStat(server, "UserRoles")
		except Exception:
			promoArray = []
		if promoArray == None:
			promoArray = []


		if not len(promoArray):
			msg = "There aren't any roles in the user role list yet.  Add some with the `{}adduserrole` command!".format(ctx.prefix)
			await ctx.channel.send(msg)
			return

		# Sort by XP first, then by name
		# promoSorted = sorted(promoArray, key=itemgetter('XP', 'Name'))
		promoSorted = sorted(promoArray, key=lambda x:x['Name'])
		
		roleText = "**__Current Roles:__**\n\n"
		for arole in promoSorted:
			# Get current role name based on id
			foundRole = False
			for role in server.roles:
				if str(role.id) == str(arole['ID']):
					# We found it
					foundRole = True
					roleText = '{}**{}**\n'.format(roleText, role.name)
			if not foundRole:
				roleText = '{}**{}** (removed from server)\n'.format(roleText, arole['Name'])

		# Check for suppress
		if suppress:
			roleText = Nullify.clean(roleText)

		await channel.send(roleText)

	@commands.command(pass_context=True)
	async def oneuserrole(self, ctx, *, yes_no = None):
		"""Turns on/off one user role at a time (bot-admin only; always on by default)."""

		# Check for admin status
		isAdmin = ctx.author.permissions_in(ctx.channel).administrator
		if not isAdmin:
			checkAdmin = self.settings.getServerStat(ctx.guild, "AdminArray")
			for role in ctx.author.roles:
				for aRole in checkAdmin:
					# Get the role that corresponds to the id
					if str(aRole['ID']) == str(role.id):
						isAdmin = True
		if not isAdmin:
			await ctx.send("You do not have permission to use this command.")
			return

		setting_name = "One user role at a time"
		setting_val  = "OnlyOneUserRole"

		current = self.settings.getServerStat(ctx.guild, setting_val)
		if yes_no == None:
			if current:
				msg = "{} currently *enabled.*".format(setting_name)
			else:
				msg = "{} currently *disabled.*".format(setting_name)
		elif yes_no.lower() in [ "yes", "on", "true", "enabled", "enable" ]:
			yes_no = True
			if current == True:
				msg = '{} remains *enabled*.'.format(setting_name)
			else:
				msg = '{} is now *enabled*.'.format(setting_name)
		elif yes_no.lower() in [ "no", "off", "false", "disabled", "disable" ]:
			yes_no = False
			if current == False:
				msg = '{} remains *disabled*.'.format(setting_name)
			else:
				msg = '{} is now *disabled*.'.format(setting_name)
		else:
			msg = "That's not a valid setting."
			yes_no = current
		if not yes_no == None and not yes_no == current:
			self.settings.setServerStat(ctx.guild, setting_val, yes_no)
		await ctx.send(msg)

	@commands.command(pass_context=True)
	async def clearroles(self, ctx):
		"""Removes all user roles from your roles."""
		# Get the array
		try:
			promoArray = self.settings.getServerStat(ctx.guild, "UserRoles")
		except Exception:
			promoArray = []
		if promoArray == None:
			promoArray = []
		
		remRole = []
		for arole in promoArray:
			roleTest = DisplayName.roleForID(arole['ID'], ctx.guild)
			if not roleTest:
				# Not a real role - skip
				continue
			if roleTest in ctx.author.roles:
				# We have it
				remRole.append(roleTest)

		if not len(remRole):
			await ctx.send("You have no roles from the user role list.")
			return		
		self.settings.role.rem_roles(ctx.author, remRole)
		if len(remRole) == 1:
			await ctx.send("1 user role removed from your roles.")
		else:
			await ctx.send("{} user roles removed from your roles.".format(len(remRole)))


	@commands.command(pass_context=True)
	async def remrole(self, ctx, *, role = None):
		"""Removes a role from the user role list from your roles."""

		if role == None:
			await ctx.send("Usage: `{}remrole [role name]`".format(ctx.prefix))
			return

		server  = ctx.message.guild
		channel = ctx.message.channel

		if self.settings.getServerStat(server, "OnlyOneUserRole"):
			await ctx.invoke(self.setrole, role=None)
			return

		# Check if we're suppressing @here and @everyone mentions
		if self.settings.getServerStat(server, "SuppressMentions"):
			suppress = True
		else:
			suppress = False
		
		# Get the array
		try:
			promoArray = self.settings.getServerStat(server, "UserRoles")
		except Exception:
			promoArray = []
		if promoArray == None:
			promoArray = []

		# Check if role is real
		roleCheck = DisplayName.roleForName(role, server)
		if not roleCheck:
			# No luck...
			msg = '*{}* not found in list.\n\nTo see a list of user roles - run `{}listuserroles`'.format(role, ctx.prefix)
			# Check for suppress
			if suppress:
				msg = Nullify.clean(msg)
			await channel.send(msg)
			return
		
		# Got a role - set it
		role = roleCheck

		remRole = []
		for arole in promoArray:
			roleTest = DisplayName.roleForID(arole['ID'], server)
			if not roleTest:
				# Not a real role - skip
				continue
			if str(arole['ID']) == str(role.id):
				# We found it!
				if roleTest in ctx.author.roles:
					# We have it
					remRole.append(roleTest)
				else:
					# We don't have it...
					await ctx.send("You don't currently have that role.")
					return
				break

		if not len(remRole):
			# We didn't find that role
			msg = '*{}* not found in list.\n\nTo see a list of user roles - run `{}listuserroles`'.format(role.name, ctx.prefix)
			# Check for suppress
			if suppress:
				msg = Nullify.clean(msg)
			await channel.send(msg)
			return

		if len(remRole):
			self.settings.role.rem_roles(ctx.author, remRole)

		msg = '*{}* has been removed from **{}!**'.format(DisplayName.name(ctx.message.author), role.name)
		if suppress:
			msg = Nullify.clean(msg)
		await channel.send(msg)
		

	@commands.command(pass_context=True)
	async def addrole(self, ctx, *, role = None):
		"""Adds a role from the user role list to your roles.  You can have multiples at a time."""

		if role == None:
			await ctx.send("Usage: `{}addrole [role name]`".format(ctx.prefix))
			return

		server  = ctx.message.guild
		channel = ctx.message.channel

		if self.settings.getServerStat(server, "OnlyOneUserRole"):
			await ctx.invoke(self.setrole, role=role)
			return

		# Check if we're suppressing @here and @everyone mentions
		if self.settings.getServerStat(server, "SuppressMentions"):
			suppress = True
		else:
			suppress = False
		
		# Get the array
		try:
			promoArray = self.settings.getServerStat(server, "UserRoles")
		except Exception:
			promoArray = []
		if promoArray == None:
			promoArray = []

		# Check if role is real
		roleCheck = DisplayName.roleForName(role, server)
		if not roleCheck:
			# No luck...
			msg = '*{}* not found in list.\n\nTo see a list of user roles - run `{}listuserroles`'.format(role, ctx.prefix)
			# Check for suppress
			if suppress:
				msg = Nullify.clean(msg)
			await channel.send(msg)
			return
		
		# Got a role - set it
		role = roleCheck

		addRole = []
		for arole in promoArray:
			roleTest = DisplayName.roleForID(arole['ID'], server)
			if not roleTest:
				# Not a real role - skip
				continue
			if str(arole['ID']) == str(role.id):
				# We found it!
				if roleTest in ctx.author.roles:
					# We already have it
					await ctx.send("You already have that role.")
					return
				addRole.append(roleTest)
				break

		if not len(addRole):
			# We didn't find that role
			msg = '*{}* not found in list.\n\nTo see a list of user roles - run `{}listuserroles`'.format(role.name, ctx.prefix)
			# Check for suppress
			if suppress:
				msg = Nullify.clean(msg)
			await channel.send(msg)
			return

		if len(addRole):
			self.settings.role.add_roles(ctx.author, addRole)

		msg = '*{}* has acquired **{}!**'.format(DisplayName.name(ctx.message.author), role.name)
		if suppress:
			msg = Nullify.clean(msg)
		await channel.send(msg)

	@commands.command(pass_context=True)
	async def setrole(self, ctx, *, role = None):
		"""Sets your role from the user role list.  You can only have one at a time."""

		server  = ctx.message.guild
		channel = ctx.message.channel

		if not self.settings.getServerStat(server, "OnlyOneUserRole"):
			await ctx.invoke(self.addrole, role=role)
			return

		# Check if we're suppressing @here and @everyone mentions
		if self.settings.getServerStat(server, "SuppressMentions"):
			suppress = True
		else:
			suppress = False
		
		# Get the array
		try:
			promoArray = self.settings.getServerStat(server, "UserRoles")
		except Exception:
			promoArray = []
		if promoArray == None:
			promoArray = []

		if role == None:
			# Remove us from all roles
			remRole = []
			for arole in promoArray:
				roleTest = DisplayName.roleForID(arole['ID'], server)
				if not roleTest:
					# Not a real role - skip
					continue
				if roleTest in ctx.message.author.roles:
					# We have this in our roles - remove it
					remRole.append(roleTest)
			if len(remRole):
				self.settings.role.rem_roles(ctx.author, remRole)
			# Give a quick status
			msg = '*{}* has been moved out of all roles in the list!'.format(DisplayName.name(ctx.message.author))
			if suppress:
				msg = Nullify.clean(msg)
			await channel.send(msg)
			return

		# Check if role is real
		roleCheck = DisplayName.roleForName(role, server)
		if not roleCheck:
			# No luck...
			msg = '*{}* not found in list.\n\nTo see a list of user roles - run `{}listuserroles`'.format(role, ctx.prefix)
			# Check for suppress
			if suppress:
				msg = Nullify.clean(msg)
			await channel.send(msg)
			return
		
		# Got a role - set it
		role = roleCheck

		addRole = []
		remRole = []
		for arole in promoArray:
			roleTest = DisplayName.roleForID(arole['ID'], server)
			if not roleTest:
				# Not a real role - skip
				continue
			if str(arole['ID']) == str(role.id):
				# We found it!
				addRole.append(roleTest)
			elif roleTest in ctx.message.author.roles:
				# Not our intended role and we have this in our roles - remove it
				remRole.append(roleTest)

		if not len(addRole):
			# We didn't find that role
			msg = '*{}* not found in list.\n\nTo see a list of user roles - run `{}listuserroles`'.format(role.name, ctx.prefix)
			# Check for suppress
			if suppress:
				msg = Nullify.clean(msg)
			await channel.send(msg)
			return

		if len(remRole) or len(addRole):
			self.settings.role.change_roles(ctx.author, add_roles=addRole, rem_roles=remRole)

		msg = '*{}* has been moved to **{}!**'.format(DisplayName.name(ctx.message.author), role.name)
		if suppress:
			msg = Nullify.clean(msg)
		await channel.send(msg)
