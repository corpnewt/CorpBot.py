import asyncio, discord, time, parsedatetime, sys
from   datetime import datetime
from   operator import itemgetter
from   discord.ext import commands
from   Cogs import Utils, ReadableTime, DisplayName, Nullify

def setup(bot):
	# Add the bot
	bot.add_cog(TempRole(bot))

class TempRole(commands.Cog):

	# Init with the bot reference, and a reference to the settings var
	def __init__(self, bot):
		self.bot = bot
		self.settings = self.bot.get_cog("Settings")
		self.is_current = False # Used for stopping loops
		self.loop_list = []
		global Utils, DisplayName
		Utils = self.bot.get_cog("Utils")
		DisplayName = self.bot.get_cog("DisplayName")

	def _is_submodule(self, parent, child):
		return parent == child or child.startswith(parent + ".")

	@commands.Cog.listener()
	async def on_unloaded_extension(self, ext):
		# Called to shut things down
		if not self._is_submodule(ext.__name__, self.__module__):
			return
		self.is_current = False
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
		user_roles = self.settings.getUserStat(member, server, "TempRoles", [])
		# Check and see if we're overriding a current time
		temp_role = {}
		# Add it anew
		temp_role["ID"] = role.id
		temp_role["Cooldown"] = role_t*60 + int(time.time())
		user_roles.append(temp_role)
		self.settings.setUserStat(member, server, "TempRoles", user_roles)
		self.settings.role.add_roles(member, [role])
		self.bot.loop.create_task(self.check_temp_roles(member, temp_role))

	@commands.Cog.listener()
	async def on_loaded_extension(self, ext):
		# See if we were loaded
		if not self._is_submodule(ext.__name__, self.__module__):
			return
		self.is_current = True
		self.bot.loop.create_task(self.start_loading())

	async def start_loading(self):
		await self.bot.wait_until_ready()
		await self.bot.loop.run_in_executor(None, self.check_temp)
		
	def check_temp(self):
		# Check if we need to set any role removal timers
		t = time.time()
		print("Verifying Temp Roles...")
		for server in self.bot.guilds:
			for member in server.members:
				if not self.is_current:
					# Bail if we're not the current instance
					return
				temp_roles = self.settings.getUserStat(member, server, "TempRoles", [])
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
						self.bot.loop.create_task(self.check_temp_roles(member, temp_role))
					# Remove any useless roles now
					if len(remove_temps):
						for temp in remove_temps:
							temp_roles.remove(temp)
		print("Temp Roles Done - took {} seconds.".format(time.time() - t))

	def _log(self, message, *, value = None, member = None):
		print(" ")
		if not member == None:
			print(member)
		print(message)
		if not value == None:
			print(value)
		print(" ")

	async def check_temp_roles(self, member, temp_role):
		if not self.is_current: return # Bail if we're not current
		
		# Get a handle on the current temp role
		temp_roles = self.settings.getUserStat(member, member.guild, "TempRoles",[])
		found_role = next((x for x in temp_roles if x["ID"] == temp_role["ID"]),None)
		if not found_role: return # Didn't find it - bail
		if found_role["Cooldown"] == None: # We have it forever - remove from the list
			return self.settings.setUserStat(member, member.guild, "TempRoles", [x for x in temp_roles if not x["ID"] == found_role["ID"]])

		# Get the cooldown and server id
		c    = int(found_role["Cooldown"])
		r_id = int(found_role["ID"])

		# Wait until we're ready to remove
		timeleft = c-int(time.time())

		if timeleft > 0: # We need to wait - and then we'll re-run this function
			await asyncio.sleep(timeleft)
			try: return await self.check_temp_roles(member,found_role)
			except RecursionError:
				print("MAX RECURSION ({}) hit for temp role. Removing!\n   - Guild: {} - Member: {} - Role: {} - TimeLeft: {}".format(
					sys.getrecursionlimit(),
					member.guild,
					member,
					found_role,
					timeleft)
				)
			
		# Resolve the role
		role = member.guild.get_role(r_id)		
		if role and role in member.roles:
			self.settings.role.rem_roles(member, [role])
			# Check if we pm
			if self.settings.getServerStat(member.guild, "TempRolePM") and "AddedBy" in found_role:
				try: await member.send("**{}** was removed from your roles in *{}*.".format(role.name, member.guild.name))
				except: pass

		# Remove it from our TempRoles setting
		self.settings.setUserStat(member, member.guild, "TempRoles", [x for x in temp_roles if not x["ID"] == found_role["ID"]])
			
	@commands.command(pass_context=True)
	async def temppm(self, ctx, *, yes_no = None):
		"""Sets whether to inform users that they've been given a temp role."""

		if not await Utils.is_bot_admin_reply(ctx): return

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
		if not await Utils.is_admin_reply(ctx): return

		if role == None:
			self.settings.setServerStat(ctx.guild, "TempRole", None)
			await ctx.send("Default temp role *removed*.")
			return

		roleName = role
		role = DisplayName.roleForName(roleName, ctx.guild)
		if not role:
			msg = 'I couldn\'t find *{}*...'.format(Nullify.escape_all(roleName))
			await ctx.send(msg)
			return

		self.settings.setServerStat(ctx.guild, "TempRole", role.id)
		role_time = self.settings.getServerStat(ctx.guild, "TempRoleTime")

		msg = "**{}** is now the default temp role - will be active for *{}*.".format(Nullify.escape_all(role.name), ReadableTime.getReadableTimeBetween(0, role_time * 60))
		await ctx.send(msg)

	@commands.command(pass_context=True)
	async def getautotemp(self, ctx):
		"""Gets the temp role applied to each new user that joins."""
		if not await Utils.is_admin_reply(ctx): return

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
		msg = "**{}** is the default temp role - will be active for *{}*.".format(Nullify.escape_all(temp_role.name), ReadableTime.getReadableTimeBetween(0, role_time * 60))
		await ctx.send(msg)

	@commands.command(pass_context=True)
	async def temptime(self, ctx, *, minutes = None):
		"""Sets the number of minutes for the temp role - must be greater than 0 (admin-only)."""
		if not await Utils.is_admin_reply(ctx): return

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
	async def hastemp(self, ctx, *, member = None):
		"""Displays any temp roles the passed user has, and the remaining time."""
		# Check for admin status
		if not await Utils.is_bot_admin_reply(ctx): return
		# Get the array
		try:
			promoArray = self.settings.getServerStat(server, "TempRoleList", [])
		except Exception:
			promoArray = []
		if member == None:
			member = ctx.author
		else:
			member_name = member
			member = DisplayName.memberForName(member, ctx.guild)
			if not member:
				msg = 'I couldn\'t find *{}*...'.format(Nullify.escape_all(member_name))
				await ctx.send(msg)
				return
		# Got the member - let's check for roles
		temp_roles = self.settings.getUserStat(member, ctx.guild, "TempRoles", [])
		if not len(temp_roles):
			await ctx.send("*{}* has no logged temp roles!".format(DisplayName.name(member)))
			return
		roleText = "**__Current Temp Roles For {}:__**\n\n".format(DisplayName.name(member))
		c = time.time()
		for arole in temp_roles:
			# Get current role name based on id
			foundRole = False
			timeleft = arole["Cooldown"]-int(time.time())
			for role in ctx.guild.roles:
				if str(role.id) == str(arole['ID']):
					# We found it
					foundRole = True
					if not "AddedBy" in arole:
						added = "automatically"
					else:
						add_user = DisplayName.name(DisplayName.memberForID(arole["AddedBy"], ctx.guild))
						if not add_user:
							add_user = str(arole["AddedBy"])
						added = "by {}".format(add_user)
					roleText = '{}**{}** - added {} - *{}* remain\n'.format(roleText, Nullify.escape_all(role.name), added, ReadableTime.getReadableTimeBetween(0, timeleft))
			if not foundRole:
				roleText = '{}**{}** (removed from server)\n'.format(roleText, arole['Name'])
		await ctx.send(roleText)

	@commands.command(pass_context=True)
	async def addtemprole(self, ctx, *, role : str = None):
		"""Adds a new role to the temp role list (admin only)."""
		usage = 'Usage: `{}addtemprole [role]`'.format(ctx.prefix)
		if not await Utils.is_admin_reply(ctx): return

		if role == None:
			await ctx.message.channel.send(usage)
			return

		roleName = role
		role = DisplayName.roleForName(roleName, ctx.guild)
		if not role:
			msg = 'I couldn\'t find *{}*...'.format(Nullify.escape_all(roleName))
			await ctx.send(msg)
			return

		# Now we see if we already have that role in our list
		promoArray = self.settings.getServerStat(ctx.guild, "TempRoleList", [])

		if role.id in [int(x["ID"]) for x in promoArray]:
			# We found it - throw an error message and return
			msg = '**{}** is already in the list.'.format(Nullify.escape_all(role.name))
			await ctx.send(msg)
			return

		# If we made it this far - then we can add it
		promoArray.append({ 'ID' : role.id, 'Name' : role.name })
		self.settings.setServerStat(ctx.guild, "TempRoleList", promoArray)

		msg = '**{}** added to list.'.format(Nullify.escape_all(role.name))
		await ctx.message.channel.send(msg)
		return

	@commands.command(pass_context=True)
	async def removetemprole(self, ctx, *, role : str = None):
		"""Removes a role from the temp role list (admin only)."""
		usage = 'Usage: `{}removetemprole [role]`'.format(ctx.prefix)
		if not await Utils.is_admin_reply(ctx): return

		if role == None:
			await ctx.message.channel.send(usage)
			return

		roleName = role
		role = DisplayName.roleForName(roleName, ctx.guild)
		if not role:
			msg = 'I couldn\'t find *{}*...'.format(Nullify.escape_all(roleName))
			await ctx.send(msg)
			return

		# Now we see if we already have that role in our list
		promoArray = self.settings.getServerStat(ctx.guild, "TempRoleList", [])

		if role.id in [int(x["ID"]) for x in promoArray]:
			# We found it - throw an error message and return
			msg = '**{}** removed successfully.'.format(Nullify.escape_all(role.name))
			self.settings.setServerStat(ctx.guild, "TempRoleList", [x for x in promoArray if role.id != int(x["ID"])])
			await ctx.send(msg)
			return

		msg = '**{}** not found in list.'.format(Nullify.escape_all(role.name))
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
			promoArray = self.settings.getServerStat(server, "TempRoleList", [])
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
					roleText = '{}**{}**\n'.format(roleText, Nullify.escape_all(role.name))
			if not foundRole:
				roleText = '{}**{}** (removed from server)\n'.format(roleText, Nullify.escape_all(arole['Name']))

		await channel.send(roleText)

	@commands.command(pass_context=True)
	async def untemp(self, ctx, member = None, role = None):
		"""Removes the passed temp role from the passed user (bot-admin only)."""
		if not await Utils.is_bot_admin_reply(ctx): return

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
			msg = 'I couldn\'t find *{}*...'.format(Nullify.escape_all(member))
			await ctx.send(msg)
			return

		if not role_from_name:
			msg = 'I couldn\'t find *{}*...'.format(Nullify.escape_all(role))
			await ctx.send(msg)
			return

		# Make sure our role is in the list
		promoArray = self.settings.getServerStat(ctx.guild, "TempRoleList", [])
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
		
		user_roles = self.settings.getUserStat(member_from_name, ctx.guild, "TempRoles", [])
		for r in user_roles:
			if int(r["ID"]) == role_from_name.id:
				user_roles.remove(r)
				self.settings.setUserStat(member_from_name, ctx.guild, "TempRoles", user_roles)
				break
		
		msg = "*{}* was removed from **{}**.".format(
			DisplayName.name(member_from_name),
			Nullify.escape_all(role_from_name.name)
		)
		await message.edit(content=msg)
		# Check if we pm
		if self.settings.getServerStat(ctx.guild, "TempRolePM"):
			try:
				await member_from_name.send("**{}** was removed from your roles in *{}*.".format(Nullify.escape_all(role_from_name.name), Nullify.escape_all(ctx.guild.name)))
			except:
				pass


	@commands.command(pass_context=True)
	async def temp(self, ctx, member = None, role = None, *, cooldown = None):
		"""Gives the passed member the temporary role for the passed amount of time - needs quotes around member and role (bot-admin only)."""
		if not await Utils.is_bot_admin_reply(ctx): return

		if member == None or role == None:
			msg = 'Usage: `{}temp "[member]" "[role]" [cooldown]`'.format(ctx.prefix)
			return await ctx.send(msg)

		# Get member and role
		member_from_name = DisplayName.memberForName(member, ctx.guild)
		role_from_name   = DisplayName.roleForName(role, ctx.guild)

		if not member_from_name and not role_from_name:
			msg = "I couldn't find either the role or member..."
			return await ctx.send(msg)

		if not member_from_name:
			msg = 'I couldn\'t find *{}*...'.format(member)
			return await ctx.send(Utils.suppressed(ctx,msg))

		# Don't allow us to temp admins or bot admins
		if Utils.is_bot_admin(ctx,member_from_name): return await ctx.send("You can't apply temp roles to other admins or bot-admins.")

		if not role_from_name:
			msg = 'I couldn\'t find *{}*...'.format(role)
			return await ctx.send(Utils.suppressed(ctx,msg))

		# Make sure our role is in the list
		promoArray = self.settings.getServerStat(ctx.guild, "TempRoleList", [])
		if not role_from_name.id in [int(x["ID"]) for x in promoArray]:
			# No dice
			return await ctx.send("That role is not in the temp role list!")

		if cooldown == None:
			return await ctx.send("You must specify a time greater than 0 seconds.")

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
				return await ctx.send("That time value is invalid.")
			# Set the cooldown
			cooldown = end_time

		if cooldown < 1:
			return await ctx.send("You must specify a time greater than 0 seconds.")

		message = await ctx.send("Applying...")

		# Here we have a member, role, and end time - apply them!
		user_roles = self.settings.getUserStat(member_from_name, ctx.guild, "TempRoles", [])
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
				Nullify.escape_all(role_from_name.name),
				ReadableTime.getReadableTimeBetween(0, cooldown)
			)
			pm = "You have been given **{}** in *{}* for *{}*".format(
				Nullify.escape_all(role_from_name.name),
				Nullify.escape_all(ctx.guild.name),
				ReadableTime.getReadableTimeBetween(0, cooldown)
			)
			self.bot.loop.create_task(self.check_temp_roles(member_from_name, temp_role))
		else:
			msg = "*{}* has been given **{}** *until further notice*.".format(
				DisplayName.name(member_from_name),
				Nullify.escape_all(role_from_name.name)
			)
			pm = "You have been given **{}** in *{} until further notice*.".format(
				Nullify.escape_all(role_from_name.name),
				ctx.guild.name
			)
		# Announce it
		await message.edit(content=msg)
		# Check if we pm
		if self.settings.getServerStat(ctx.guild, "TempRolePM"):
			try: await member_from_name.send(pm)
			except: pass
