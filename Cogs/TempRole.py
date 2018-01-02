import asyncio
import discord
import time
import parsedatetime
from   datetime import datetime
from   operator import itemgetter
from   discord.ext import commands
from   Cogs import ReadableTime
from   Cogs import DisplayName
from   Cogs import Nullify

def setup(bot):
	# Add the bot
	bot.add_cog(TempRole(bot))

class TempRole:

	# Init with the bot reference, and a reference to the settings var
	def __init__(self, bot):
		self.bot = bot
		self.settings = self.bot.get_cog("Settings")
		self.loop_list = []

	def _is_submodule(self, parent, child):
		return parent == child or child.startswith(parent + ".")

	@asyncio.coroutine
	async def on_unloaded_extension(self, ext):
		# Called to shut things down
		if not self._is_submodule(ext.__name__, self.__module__):
			return
		for task in self.loop_list:
			task.cancel()

	async def onjoin(self, member, server):
		# Let the api settle
		# Add 2 second delay to hopefully prevent the api from hating us :(
		# await asyncio.sleep(2)
		# Pls no hate

		role   = self.settings.getServerStat(server, "TempRole")
		role_t = self.settings.getServerStat(server, "TempRoleTime")

		if role == None:
			# No temp role
			return
		if role_t < 1:
			# No time
			return
		role = DisplayName.roleForName(role, server)
		if not role:
			# Doesn't exist
			return
		
		# Here we have a member, role, and end time - apply them!
		user_roles = self.settings.getUserStat(member, server, "TempRoles")
		# Check and see if we're overriding a current time
		temp_role = {}
		# Add it anew
		temp_role["ID"] = role.id
		temp_role["Cooldown"] = role_t*60 + int(time.time())
		user_roles.append(temp_role)
		self.settings.setUserStat(member, server, "TempRoles", user_roles)
		self.settings.role.add_roles(member, [role])
		self.loop_list.append(self.bot.loop.create_task(self.check_temp_roles(member, temp_role)))

	@asyncio.coroutine
	async def on_loaded_extension(self, ext):
		# See if we were loaded
		if not self._is_submodule(ext.__name__, self.__module__):
			return
		# Check if we need to set any role removal timers
		for server in self.bot.guilds:
			for member in server.members:
				temp_roles = self.settings.getUserStat(member, server, "TempRoles")
				if len(temp_roles):
					# We have a list
					remove_temps = []
					for temp_role in temp_roles:
						if temp_role["Cooldown"] == None:
							# Permanent temp role
							# Let's see if the role still exists
							found = False
							for role in member.roles:
								if role.id == int(temp_role["ID"]):
									found = True
									break
							if not found:
								remove_temps.append(temp_role)
							continue
						self.loop_list.append(self.bot.loop.create_task(self.check_temp_roles(member, temp_role)))
					# Remove any useless roles now
					if len(remove_temps):
						for temp in remove_temps:
							temp_roles.remove(temp)
							
	def _remove_task(self, task):
		if task in self.loop_list:
			self.loop_list.remove(task)

	def _log(self, message, *, value = None, member = None):
		print(" ")
		if not member == None:
			print(member)
		print(message)
		if not value == None:
			print(value)
		print(" ")

	async def check_temp_roles(self, member, temp_role):
		# Get the current task
		task = asyncio.Task.current_task()
		
		#self._log("Temp Role Object:", value=temp_role, member=member)

		# Get the cooldown and server id
		c = int(temp_role["Cooldown"])
		r_id = int(temp_role["ID"])

		# Wait until we're ready to remove
		timeleft = c-int(time.time())
		
		#self._log("Time left check 1 - do we have time left?", value=timeleft, member=member)
		
		if timeleft > 0:
			await asyncio.sleep(timeleft)
		# Resolve the role
		role = DisplayName.roleForID(r_id, member.guild)

		#self._log("Role check - is role?", value=role, member=member)
		
		if not role:
			# Doesn't exist - remove it
			temp_roles = self.settings.getUserStat(member, member.guild, "TempRoles")
			temp_roles.remove(temp_role)
			self._remove_task(task)
			return
		# We have a role - let's see if we still need to keep it
		c = temp_role["Cooldown"]

		#self._log("Cooldown check - do we have a cooldown?", value=c, member=member)

		if c == None:
			# We now have this role forever
			# One last check to make sure it all makes sense
			found = False
			temp_roles = self.settings.getUserStat(member, member.guild, "TempRoles")
			if not role in member.roles:
				temp_roles.remove(temp_role)
				self.settings.setUserStat(member, member.guild, "TempRoles", temp_roles)
			self._remove_task(task)
			return
		# We still have a cooldown
		timeleft = c-int(time.time())

		#self._log("Time left:", value=timeleft, member=member)

		if timeleft > 0:
			# Recalibrate
			self.loop_list.append(self.bot.loop.create_task(self.check_temp_roles(member, temp_role)))
			self._remove_task(task)
			return
		# Here - we're either past our cooldown, or who knows what else

		#self._log("Past the cooldown - no time left - do we have the role?", value=(role in member.roles), member=member)

		if role in member.roles:
			#self._log("Removing the role now - on time (supposedly)", member=member, value=role)
			# We have the role still - remove it
			self.settings.role.rem_roles(member, [role])

		# Remove the entry from our user settings
		temp_roles = self.settings.getUserStat(member, member.guild, "TempRoles")
		if not temp_roles:
			temp_roles = []
		if temp_role in temp_roles:
			#self._log("Temp Role was in user settings - removing", member=member)
			temp_roles.remove(temp_role)
			self.settings.setUserStat(member, member.guild, "TempRoles", temp_roles)

		# Check if we pm
		if self.settings.getServerStat(member.guild, "TempRolePM") and "AddedBy" in temp_role:
			try:
				await member.send("**{}** was removed from your roles in *{}*.".format(role.name, member.guild.name))
			except:
				pass
		self._remove_task(task)
			
	@commands.command(pass_context=True)
	async def temppm(self, ctx, *, yes_no = None):
		"""Sets whether to inform users that they've been given a temp role."""

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

		setting_name = "Temp role pm"
		setting_val  = "TempRolePM"

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
	async def autotemp(self, ctx, *, role = None):
		"""Sets the temp role to apply to each new user that joins."""
		usage = 'Usage: `{}addtemprole [role]`'.format(ctx.prefix)
		# Check if we're suppressing @here and @everyone mentions
		if self.settings.getServerStat(ctx.message.guild, "SuppressMentions"):
			suppress = True
		else:
			suppress = False

		isAdmin = ctx.message.author.permissions_in(ctx.message.channel).administrator
		# Only allow admins to change server stats
		if not isAdmin:
			await ctx.message.channel.send('You do not have sufficient privileges to access this command.')
			return

		if role == None:
			self.settings.setServerStat(ctx.guild, "TempRole", None)
			await ctx.send("Default temp role *removed*.")
			return

		roleName = role
		role = DisplayName.roleForName(roleName, ctx.guild)
		if not role:
			msg = 'I couldn\'t find *{}*...'.format(roleName)
			# Check for suppress
			if suppress:
				msg = Nullify.clean(msg)
			await ctx.send(msg)
			return

		self.settings.setServerStat(ctx.guild, "TempRole", role.id)
		role_time = self.settings.getServerStat(ctx.guild, "TempRoleTime")

		msg = "**{}** is now the default temp role - will be active for *{}*.".format(role.name, ReadableTime.getReadableTimeBetween(0, role_time * 60))
		if suppress:
			msg = Nullify.clean(msg)
		await ctx.send(msg)

	@commands.command(pass_context=True)
	async def getautotemp(self, ctx):
		"""Gets the temp role applied to each new user that joins."""
		# Check if we're suppressing @here and @everyone mentions
		if self.settings.getServerStat(ctx.message.guild, "SuppressMentions"):
			suppress = True
		else:
			suppress = False

		isAdmin = ctx.message.author.permissions_in(ctx.message.channel).administrator
		# Only allow admins to change server stats
		if not isAdmin:
			await ctx.message.channel.send('You do not have sufficient privileges to access this command.')
			return

		temp_id = self.settings.getServerStat(ctx.guild, "TempRole")
		if temp_id == None:
			# No temp setup
			await ctx.send("There is no default temp role.")
			return

		temp_role = DisplayName.roleForName(temp_id, ctx.guild)
		if temp_role == None:
			# Not a role anymore
			await ctx.send("The default temp role ({}) no longer exists.".format(temp_id))
			return
		role_time = self.settings.getServerStat(ctx.guild, "TempRoleTime")
		msg = "**{}** is the default temp role - will be active for *{}*.".format(temp_role.name, ReadableTime.getReadableTimeBetween(0, role_time * 60))
		if suppress:
			msg = Nullify.clean(msg)
		await ctx.send(msg)

	@commands.command(pass_context=True)
	async def temptime(self, ctx, *, minutes = None):
		"""Sets the number of minutes for the temp role - must be greater than 0 (admin-only)."""
		# Check if we're suppressing @here and @everyone mentions
		if self.settings.getServerStat(ctx.message.guild, "SuppressMentions"):
			suppress = True
		else:
			suppress = False

		isAdmin = ctx.message.author.permissions_in(ctx.message.channel).administrator
		# Only allow admins to change server stats
		if not isAdmin:
			await ctx.message.channel.send('You do not have sufficient privileges to access this command.')
			return

		try:
			minutes = int(minutes)
		except:
			await ctx.send("That's not a valid integer!")
			return

		if minutes < 1:
			await ctx.send("Time must be greater than 0!")
			return

		self.settings.setServerStat(ctx.guild, "TempRoleTime", minutes)

		msg = "Temp role will last *{}*.".format(ReadableTime.getReadableTimeBetween(0, minutes*60))
		await ctx.send(msg)

	@commands.command(pass_context=True)
	async def addtemprole(self, ctx, *, role : str = None):
		"""Adds a new role to the temp role list (admin only)."""
		usage = 'Usage: `{}addtemprole [role]`'.format(ctx.prefix)
		# Check if we're suppressing @here and @everyone mentions
		if self.settings.getServerStat(ctx.message.guild, "SuppressMentions"):
			suppress = True
		else:
			suppress = False

		isAdmin = ctx.message.author.permissions_in(ctx.message.channel).administrator
		# Only allow admins to change server stats
		if not isAdmin:
			await ctx.message.channel.send('You do not have sufficient privileges to access this command.')
			return

		if role == None:
			await ctx.message.channel.send(usage)
			return

		roleName = role
		role = DisplayName.roleForName(roleName, ctx.guild)
		if not role:
			msg = 'I couldn\'t find *{}*...'.format(roleName)
			# Check for suppress
			if suppress:
				msg = Nullify.clean(msg)
			await ctx.send(msg)
			return

		# Now we see if we already have that role in our list
		promoArray = self.settings.getServerStat(ctx.guild, "TempRoleList")

		if role.id in [int(x["ID"]) for x in promoArray]:
			# We found it - throw an error message and return
			msg = '**{}** is already in the list.'.format(role.name)
			# Check for suppress
			if suppress:
				msg = Nullify.clean(msg)
			await ctx.send(msg)
			return

		# If we made it this far - then we can add it
		promoArray.append({ 'ID' : role.id, 'Name' : role.name })
		self.settings.setServerStat(ctx.guild, "TempRoleList", promoArray)

		msg = '**{}** added to list.'.format(role.name)
		# Check for suppress
		if suppress:
			msg = Nullify.clean(msg)
		await ctx.message.channel.send(msg)
		return

	@commands.command(pass_context=True)
	async def removetemprole(self, ctx, *, role : str = None):
		"""Removes a role from the temp role list (admin only)."""
		usage = 'Usage: `{}removetemprole [role]`'.format(ctx.prefix)
		# Check if we're suppressing @here and @everyone mentions
		if self.settings.getServerStat(ctx.message.guild, "SuppressMentions"):
			suppress = True
		else:
			suppress = False

		isAdmin = ctx.message.author.permissions_in(ctx.message.channel).administrator
		# Only allow admins to change server stats
		if not isAdmin:
			await ctx.message.channel.send('You do not have sufficient privileges to access this command.')
			return

		if role == None:
			await ctx.message.channel.send(usage)
			return

		roleName = role
		role = DisplayName.roleForName(roleName, ctx.guild)
		if not role:
			msg = 'I couldn\'t find *{}*...'.format(roleName)
			# Check for suppress
			if suppress:
				msg = Nullify.clean(msg)
			await ctx.send(msg)
			return

		# Now we see if we already have that role in our list
		promoArray = self.settings.getServerStat(ctx.guild, "TempRoleList")

		if role.id in [int(x["ID"]) for x in promoArray]:
			# We found it - throw an error message and return
			msg = '**{}** removed successfully.'.format(role.name)
			self.settings.setServerStat(ctx.guild, "TempRoleList", [x for x in promoArray if role.id != int(x["ID"])])
			# Check for suppress
			if suppress:
				msg = Nullify.clean(msg)
			await ctx.send(msg)
			return

		msg = '**{}** not found in list.'.format(role.name)
		# Check for suppress
		if suppress:
			msg = Nullify.clean(msg)
		await ctx.send(msg)
		return

	@commands.command(pass_context=True)
	async def listtemproles(self, ctx):
		"""Lists all roles for the temp role system."""
		
		server  = ctx.message.guild
		channel = ctx.message.channel

		# Check if we're suppressing @here and @everyone mentions
		if self.settings.getServerStat(server, "SuppressMentions"):
			suppress = True
		else:
			suppress = False
		
		# Get the array
		try:
			promoArray = self.settings.getServerStat(server, "TempRoleList")
		except Exception:
			promoArray = []
		if promoArray == None:
			promoArray = []


		if not len(promoArray):
			msg = "There aren't any roles in the user role list yet.  Add some with the `{}addtemprole` command!".format(ctx.prefix)
			await ctx.channel.send(msg)
			return

		# Sort by XP first, then by name
		# promoSorted = sorted(promoArray, key=itemgetter('XP', 'Name'))
		promoSorted = sorted(promoArray, key=lambda x:x['Name'])
		
		roleText = "**__Current Temp Roles:__**\n\n"
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
	async def untemp(self, ctx, member = None, role = None):
		"""Removes the passed temp role from the passed user (bot-admin only)."""
		# Check if we're suppressing @here and @everyone mentions
		if self.settings.getServerStat(ctx.message.guild, "SuppressMentions"):
			suppress = True
		else:
			suppress = False
		
		isAdmin = ctx.message.author.permissions_in(ctx.message.channel).administrator
		if not isAdmin:
			checkAdmin = self.settings.getServerStat(ctx.message.guild, "AdminArray")
			for arole in ctx.message.author.roles:
				for aRole in checkAdmin:
					# Get the role that corresponds to the id
					if str(aRole['ID']) == str(arole.id):
						isAdmin = True
		# Only allow admins to change server stats
		if not isAdmin:
			await ctx.channel.send('You do not have sufficient privileges to access this command.')
			return

		if member == None or role == None:
			msg = 'Usage: `{}untemp "[member]" "[role]"`'.format(ctx.prefix)
			await ctx.channel.send(msg)
			return

		# Get member and role
		member_from_name = DisplayName.memberForName(member, ctx.guild)
		role_from_name   = DisplayName.roleForName(role, ctx.guild)

		if not member_from_name and not role_from_name:
			msg = "I couldn't find either the role or member..."
			await ctx.send(msg)
			return

		if not member_from_name:
			msg = 'I couldn\'t find *{}*...'.format(member)
			# Check for suppress
			if suppress:
				msg = Nullify.clean(msg)
			await ctx.send(msg)
			return

		if not role_from_name:
			msg = 'I couldn\'t find *{}*...'.format(role)
			# Check for suppress
			if suppress:
				msg = Nullify.clean(msg)
			await ctx.send(msg)
			return

		# Make sure our role is in the list
		promoArray = self.settings.getServerStat(ctx.guild, "TempRoleList")
		if not role_from_name.id in [int(x["ID"]) for x in promoArray]:
			# No dice
			await ctx.send("That role is not in the temp role list!")
			return

		# Check if the user has that role - and remove it
		if not role_from_name in member_from_name.roles:
			# Don't have it
			await ctx.send("That user doesn't have that role!")
			return

		message = await ctx.send("Applying...")
		# We should be able to remove it now
		self.settings.role.rem_roles(member_from_name, [role_from_name])
		
		user_roles = self.settings.getUserStat(member_from_name, ctx.guild, "TempRoles")
		for r in user_roles:
			if int(r["ID"]) == role_from_name.id:
				user_roles.remove(r)
				self.settings.setUserStat(member_from_name, ctx.guild, "TempRoles", user_roles)
				break
		
		msg = "*{}* was removed from **{}**.".format(
			DisplayName.name(member_from_name),
			role_from_name.name
		)
		# Announce it
		if suppress:
			msg = Nullify.clean(msg)
		await message.edit(content=msg)
		# Check if we pm
		if self.settings.getServerStat(ctx.guild, "TempRolePM"):
			try:
				await member_from_name.send("**{}** was removed from your roles in *{}*.".format(role_from_name.name, ctx.guild.name))
			except:
				pass


	@commands.command(pass_context=True)
	async def temp(self, ctx, member = None, role = None, *, cooldown = None):
		"""Gives the passed member the temporary role for the passed amount of time - needs quotes around member and role (bot-admin only)."""
		# Check if we're suppressing @here and @everyone mentions
		if self.settings.getServerStat(ctx.message.guild, "SuppressMentions"):
			suppress = True
		else:
			suppress = False
		
		isAdmin = ctx.message.author.permissions_in(ctx.message.channel).administrator
		if not isAdmin:
			checkAdmin = self.settings.getServerStat(ctx.message.guild, "AdminArray")
			for arole in ctx.message.author.roles:
				for aRole in checkAdmin:
					# Get the role that corresponds to the id
					if str(aRole['ID']) == str(arole.id):
						isAdmin = True
		# Only allow admins to change server stats
		if not isAdmin:
			await ctx.channel.send('You do not have sufficient privileges to access this command.')
			return

		if member == None or role == None:
			msg = 'Usage: `{}temp "[member]" "[role]" [cooldown]`'.format(ctx.prefix)
			await ctx.channel.send(msg)
			return

		# Get member and role
		member_from_name = DisplayName.memberForName(member, ctx.guild)
		role_from_name   = DisplayName.roleForName(role, ctx.guild)

		if not member_from_name and not role_from_name:
			msg = "I couldn't find either the role or member..."
			await ctx.send(msg)
			return

		if not member_from_name:
			msg = 'I couldn\'t find *{}*...'.format(member)
			# Check for suppress
			if suppress:
				msg = Nullify.clean(msg)
			await ctx.send(msg)
			return

		# Don't allow us to temp admins or bot admins
		isAdmin = member_from_name.permissions_in(ctx.channel).administrator
		if not isAdmin:
			checkAdmin = self.settings.getServerStat(ctx.guild, "AdminArray")
			for arole in member_from_name.roles:
				for aRole in checkAdmin:
					# Get the role that corresponds to the id
					if str(aRole['ID']) == str(arole.id):
						isAdmin = True
		# Only allow admins to change server stats
		if isAdmin:
			await ctx.channel.send("You can't apply temp roles to other admins or bot-admins.")
			return

		if not role_from_name:
			msg = 'I couldn\'t find *{}*...'.format(role)
			# Check for suppress
			if suppress:
				msg = Nullify.clean(msg)
			await ctx.send(msg)
			return

		# Make sure our role is in the list
		promoArray = self.settings.getServerStat(ctx.guild, "TempRoleList")
		if not role_from_name.id in [int(x["ID"]) for x in promoArray]:
			# No dice
			await ctx.send("That role is not in the temp role list!")
			return

		if cooldown == None:
			await ctx.send("You must specify a time greater than 0 seconds.")
			return

		if not cooldown == None:
			# Get the end time
			end_time = None
			try:
				# Get current time - and end time
				currentTime = int(time.time())
				cal         = parsedatetime.Calendar()
				time_struct, parse_status = cal.parse(cooldown)
				start       = datetime(*time_struct[:6])
				end         = time.mktime(start.timetuple())
				# Get the time from now to end time
				end_time = end-currentTime
			except:
				pass
			if end_time == None:
				# We didn't get a time
				await ctx.send("That time value is invalid.")
				return
			# Set the cooldown
			cooldown = end_time

		if cooldown < 1:
			await ctx.send("You must specify a time greater than 0 seconds.")
			return

		message = await ctx.send("Applying...")

		# Here we have a member, role, and end time - apply them!
		user_roles = self.settings.getUserStat(member_from_name, ctx.guild, "TempRoles")
		# Check and see if we're overriding a current time
		found = False
		temp_role = {}
		for r in user_roles:
			if int(r["ID"]) == role_from_name.id:
				# Already have it - update the cooldown
				r["Cooldown"] = cooldown + int(time.time()) if cooldown != None else cooldown
				r["AddedBy"] = ctx.author.id
				temp_role = r
				found = True
				break
		if not found:
			# Add it anew
			temp_role["ID"] = role_from_name.id
			temp_role["Cooldown"] = cooldown + int(time.time()) if cooldown != None else cooldown
			temp_role["AddedBy"] = ctx.author.id
			user_roles.append(temp_role)
			self.settings.setUserStat(member_from_name, ctx.guild, "TempRoles", user_roles)
		if not role_from_name in member_from_name.roles:
			self.settings.role.add_roles(member_from_name, [role_from_name])
		if not cooldown == None:
			# We have a cooldown
			msg = "*{}* has been given **{}** for *{}*.".format(
				DisplayName.name(member_from_name),
				role_from_name.name,
				ReadableTime.getReadableTimeBetween(0, cooldown)
			)
			pm = "You have been given **{}** in *{}* for *{}*".format(
				role_from_name.name,
				ctx.guild.name,
				ReadableTime.getReadableTimeBetween(0, cooldown)
			)
			self.loop_list.append(self.bot.loop.create_task(self.check_temp_roles(member_from_name, temp_role)))
		else:
			msg = "*{}* has been given **{}** *until further notice*.".format(
				DisplayName.name(member_from_name),
				role_from_name.name
			)
			pm = "You have been given **{}** in *{} until further notice*.".format(
				role_from_name.name,
				ctx.guild.name
			)
		# Announce it
		if suppress:
			msg = Nullify.clean(msg)
		await message.edit(content=msg)
		# Check if we pm
		if self.settings.getServerStat(ctx.guild, "TempRolePM"):
			try:
				await member_from_name.send(pm)
			except:
				pass
