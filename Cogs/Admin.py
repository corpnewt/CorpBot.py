import discord
from   discord.ext import commands
from   Cogs import Utils, Settings, CheckRoles, DisplayName, Utils

# This is the admin module.  It holds the admin-only commands
# Everything here *requires* that you're an admin

def setup(bot):
	# Add the bot and deps
	settings = bot.get_cog("Settings")
	bot.add_cog(Admin(bot, settings))

class Admin(commands.Cog):

	# Init with the bot reference, and a reference to the settings var
	def __init__(self, bot, settings):
		self.bot = bot
		self.settings = settings
		global Utils, DisplayName
		Utils = self.bot.get_cog("Utils")
		DisplayName = self.bot.get_cog("DisplayName")

	
	@commands.command(pass_context=True)
	async def defaultchannel(self, ctx):
		"""Lists the server's default channel, whether custom or not."""
		# Returns the default channel for the server
		default = None
		targetChan = ctx.guild.get_channel(ctx.guild.id)
		default = targetChan

		targetChanID = self.settings.getServerStat(ctx.guild, "DefaultChannel")
		if len(str(targetChanID)):
			# We *should* have a channel
			tChan = self.bot.get_channel(int(targetChanID))
			if tChan:
				# We *do* have one
				targetChan = tChan
		if targetChan == None:
			# We don't have a default
			if default == None:
				msg = "There is currently no default channel set."
			else:
				msg = "The default channel is the server's original default: {}".format(default.mention)
		else:
			# We have a custom channel
			msg = "The default channel is set to **{}**.".format(targetChan.mention)
		await ctx.channel.send(msg)
		
	
	@commands.command(pass_context=True)
	async def setdefaultchannel(self, ctx, *, channel: discord.TextChannel = None):
		"""Sets a replacement default channel for bot messages (admin only)."""
		
		if not await Utils.is_admin_reply(ctx): return

		default = ctx.guild.get_channel(ctx.guild.id)

		if channel == None:
			self.settings.setServerStat(ctx.message.guild, "DefaultChannel", "")
			if default == None:
				msg = 'Default channel has been *removed completely*.'
			else:
				msg = 'Default channel has been returned to the server\'s original:  **{}**.'.format(default.mention)
			await ctx.message.channel.send(msg)
			return

		# If we made it this far - then we can add it
		self.settings.setServerStat(ctx.message.guild, "DefaultChannel", channel.id)

		msg = 'Default channel set to **{}**.'.format(channel.mention)
		await ctx.message.channel.send(msg)
		
	
	@setdefaultchannel.error
	async def setdefaultchannel_error(self, error, ctx):
		# do stuff
		msg = 'setdefaultchannel Error: {}'.format(error)
		await ctx.channel.send(msg)
	

	@commands.command(pass_context=True)
	async def setmadlibschannel(self, ctx, *, channel: discord.TextChannel = None):
		"""Sets the channel for MadLibs (admin only)."""
		
		if not await Utils.is_admin_reply(ctx): return

		if channel == None:
			self.settings.setServerStat(ctx.message.guild, "MadLibsChannel", "")
			msg = 'MadLibs works in *any channel* now.'
			await ctx.message.channel.send(msg)
			return

		if type(channel) is str:
			try:
				role = discord.utils.get(message.guild.channels, name=role)
			except:
				print("That channel does not exist")
				return

		# If we made it this far - then we can add it
		self.settings.setServerStat(ctx.message.guild, "MadLibsChannel", channel.id)

		msg = 'MadLibs channel set to **{}**.'.format(channel.name)
		await ctx.message.channel.send(msg)
		
	
	@setmadlibschannel.error
	async def setmadlibschannel_error(self, error, ctx):
		# do stuff
		msg = 'setmadlibschannel Error: {}'.format(error)
		await ctx.channel.send(msg)


	@commands.command(pass_context=True)
	async def xpreservelimit(self, ctx, *, limit = None):
		"""Gets and sets a limit to the maximum xp reserve a member can get.  Pass a negative value for unlimited."""

		if not await Utils.is_admin_reply(ctx): return
			
		if limit == None:
			# print the current limit
			server_lim = self.settings.getServerStat(ctx.guild, "XPReserveLimit")
			if server_lim == None:
				await ctx.send("There is no xp reserve limit.")
				return
			else:
				await ctx.send("The current xp reserve limit is *{:,}*.".format(server_lim))

		try:
			limit = int(limit)
		except Exception:
			return await ctx.send("Limit must be an integer.")

		if limit < 0:
			self.settings.setServerStat(ctx.guild, "XPReserveLimit", None)
			await ctx.send("Xp reserve limit removed!")
		else:
			self.settings.setServerStat(ctx.guild, "XPReserveLimit", limit)
			await ctx.send("Xp reserve limit set to *{:,}*.".format(limit))

	@commands.command(pass_context=True)
	async def onexprole(self, ctx, *, yes_no = None):
		"""Gets and sets whether or not to remove all but the current xp role a user has acquired."""
		if not await Utils.is_admin_reply(ctx): return
		await ctx.send(Utils.yes_no_setting(ctx,"One xp role at a time","OnlyOneRole",yes_no))


	@commands.command(pass_context=True)
	async def xplimit(self, ctx, *, limit = None):
		"""Gets and sets a limit to the maximum xp a member can get.  Pass a negative value for unlimited."""

		if not await Utils.is_admin_reply(ctx): return
			
		if limit == None:
			# print the current limit
			server_lim = self.settings.getServerStat(ctx.guild, "XPLimit")
			if server_lim == None:
				await ctx.send("There is no xp limit.")
				return
			else:
				await ctx.send("The current xp limit is *{:,}*.".format(server_lim))

		try:
			limit = int(limit)
		except Exception:
			return await ctx.send("Limit must be an integer.")

		if limit < 0:
			self.settings.setServerStat(ctx.guild, "XPLimit", None)
			await ctx.send("Xp limit removed!")
		else:
			self.settings.setServerStat(ctx.guild, "XPLimit", limit)
			await ctx.send("Xp limit set to *{:,}*.".format(limit))
			

	@commands.command(pass_context=True)
	async def setxp(self, ctx, *, member = None, xpAmount : int = None):
		"""Sets an absolute value for the member's xp (admin only)."""
		
		author  = ctx.message.author
		server  = ctx.message.guild
		channel = ctx.message.channel

		usage = 'Usage: `{}setxp [member] [amount]`'.format(ctx.prefix)
		if not await Utils.is_admin_reply(ctx): return

		if member == None:
			await ctx.message.channel.send(usage)
			return

		if xpAmount == None:
			# Check if we have trailing xp
			nameCheck = DisplayName.checkNameForInt(member, server)
			if not nameCheck or nameCheck['Member'] is None:
				nameCheck = DisplayName.checkRoleForInt(member, server)
				if not nameCheck:
					await ctx.message.channel.send(usage)
					return
			if "Role" in nameCheck:
				mem = nameCheck["Role"]
			else:
				mem = nameCheck["Member"]
			exp = nameCheck["Int"]
			if not mem:
				msg = 'I couldn\'t find *{}* on the server.'.format(member)
				msg = Utils.suppressed(ctx,msg)
				await ctx.message.channel.send(msg)
				return
			member   = mem
			xpAmount = exp
			
		# Check for formatting issues
		if xpAmount == None:
			# Still no xp...
			await channel.send(usage)
			return

		if type(member) is discord.Member:
			self.settings.setUserStat(member, server, "XP", xpAmount)
		else:
			for m in ctx.guild.members:
				if member in m.roles:
					self.settings.setUserStat(m, server, "XP", xpAmount)
		msg = '*{}\'s* xp was set to *{:,}!*'.format(DisplayName.name(member), xpAmount)
		msg = Utils.suppressed(ctx,msg)
		await channel.send(msg)
		await CheckRoles.checkroles(member, channel, self.settings, self.bot)


	@commands.command(pass_context=True)
	async def setxpreserve(self, ctx, *, member = None, xpAmount : int = None):
		"""Set's an absolute value for the member's xp reserve (admin only)."""
		
		author  = ctx.message.author
		server  = ctx.message.guild
		channel = ctx.message.channel

		usage = 'Usage: `{}setxpreserve [member] [amount]`'.format(ctx.prefix)
		if not await Utils.is_admin_reply(ctx): return

		if member == None:
			await ctx.message.channel.send(usage)
			return
		
		if xpAmount == None:
			# Check if we have trailing xp
			nameCheck = DisplayName.checkNameForInt(member, server)
			if not nameCheck or nameCheck['Member'] is None:
				nameCheck = DisplayName.checkRoleForInt(member, server)
				if not nameCheck:
					await ctx.message.channel.send(usage)
					return
			if "Role" in nameCheck:
				mem = nameCheck["Role"]
			else:
				mem = nameCheck["Member"]
			exp = nameCheck["Int"]
			if not mem:
				msg = 'I couldn\'t find *{}* on the server.'.format(member)
				msg = Utils.suppressed(ctx,msg)
				await ctx.message.channel.send(msg)
				return
			member   = mem
			xpAmount = exp
			
		# Check for formatting issues
		if xpAmount == None:
			# Still no xp...
			await channel.send(usage)
			return

		if type(member) is discord.Member:
			self.settings.setUserStat(member, server, "XPReserve", xpAmount)
		else:
			for m in ctx.guild.members:
				if member in m.roles:
					self.settings.setUserStat(m, server, "XPReserve", xpAmount)
		msg = '*{}\'s* XPReserve was set to *{:,}!*'.format(DisplayName.name(member), xpAmount)
		await channel.send(msg)

	
	@commands.command(pass_context=True)
	async def setdefaultrole(self, ctx, *, role : str = None):
		"""Sets the default role or position for auto-role assignment."""
		author  = ctx.message.author
		server  = ctx.message.guild
		channel = ctx.message.channel
		if not await Utils.is_admin_reply(ctx): return

		if role is None:
			# Disable auto-role and set default to none
			self.settings.setServerStat(server, "DefaultRole", "")
			msg = 'Auto-role management now **disabled**.'
			await channel.send(msg)
			return

		if type(role) is str:
			if role == "everyone":
				role = "@everyone"
			roleName = role
			role = DisplayName.roleForName(roleName, server)
			if not role:
				msg = 'I couldn\'t find *{}*...'.format(roleName)
				msg = Utils.suppressed(ctx,msg)
				await ctx.message.channel.send(msg)
				return

		self.settings.setServerStat(server, "DefaultRole", role.id)
		rolename = role.name
		msg = Utils.suppressed(ctx,rolename)
		await channel.send('Default role set to **{}**!'.format(rolename))


	@setdefaultrole.error
	async def setdefaultrole_error(self, error, ctx):
		# do stuff
		msg = 'setdefaultrole Error: {}'.format(error)
		await ctx.channel.send(msg)


	@commands.command(pass_context=True)
	async def addxprole(self, ctx, *, role = None, xp : int = None):
		"""Adds a new role to the xp promotion/demotion system (admin only)."""
		
		author  = ctx.message.author
		server  = ctx.message.guild
		channel = ctx.message.channel

		usage = 'Usage: `{}addxprole [role] [required xp]`'.format(ctx.prefix)
		if not await Utils.is_admin_reply(ctx): return
		if xp == None:
			# Either xp wasn't set - or it's the last section
			if type(role) is str:
				if role == "everyone":
					role = "@everyone"
				# It' a string - the hope continues
				roleCheck = DisplayName.checkRoleForInt(role, server)
				if not roleCheck:
					await ctx.message.channel.send(usage)
					return
				if not roleCheck["Role"]:
					msg = 'I couldn\'t find *{}* on the server.'.format(role)
					msg = Utils.suppressed(ctx,msg)
					await ctx.message.channel.send(msg)
					return
				role = roleCheck["Role"]
				xp   = roleCheck["Int"]

		if xp == None:
			await channel.send(usage)
			return
		if not type(xp) is int:
			await channel.send(usage)
			return

		# Now we see if we already have that role in our list
		promoArray = self.settings.getServerStat(server, "PromotionArray")
		for aRole in promoArray:
			# Get the role that corresponds to the id
			if str(aRole['ID']) == str(role.id):
				# We found it - throw an error message and return
				aRole['XP'] = xp
				msg = '**{}** updated!  Required xp:  *{:,}*'.format(role.name, xp)
				msg = Utils.suppressed(ctx,msg)
				await channel.send(msg)
				return

		# If we made it this far - then we can add it
		promoArray.append({ 'ID' : role.id, 'Name' : role.name, 'XP' : xp })
		self.settings.setServerStat(server, "PromotionArray", promoArray)

		msg = '**{}** added to list.  Required xp: *{:,}*'.format(role.name, xp)
		msg = Utils.suppressed(ctx,msg)
		await channel.send(msg)
		return
		
	@commands.command(pass_context=True)
	async def removexprole(self, ctx, *, role = None):
		"""Removes a role from the xp promotion/demotion system (admin only)."""
		
		author  = ctx.message.author
		server  = ctx.message.guild
		channel = ctx.message.channel

		usage = 'Usage: `{}removexprole [role]`'.format(ctx.prefix)
		if not await Utils.is_admin_reply(ctx): return

		if role == None:
			await channel.send(usage)
			return

		if type(role) is str:
			if role == "everyone":
				role = "@everyone"
			# It' a string - the hope continues
			# Let's clear out by name first - then by role id
			promoArray = self.settings.getServerStat(server, "PromotionArray")

			for aRole in promoArray:
				# Get the role that corresponds to the name
				if aRole['Name'].lower() == role.lower() or str(aRole["ID"]) == str(role):
					# We found it - let's remove it
					promoArray.remove(aRole)
					self.settings.setServerStat(server, "PromotionArray", promoArray)
					msg = '**{}** removed successfully.'.format(aRole['Name'])
					msg = Utils.suppressed(ctx,msg)
					await channel.send(msg)
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
					if str(aRole['ID']) == str(roleCheck.id):
						# We found it - let's remove it
						promoArray.remove(aRole)
						self.settings.setServerStat(server, "PromotionArray", promoArray)
						msg = '**{}** removed successfully.'.format(aRole['Name'])
						msg = Utils.suppressed(ctx,msg)
						await channel.send(msg)
						return
				
			# If we made it this far - then we didn't find it
			msg = '{} not found in list.'.format(role)
			msg = Utils.suppressed(ctx,msg)
			await channel.send(msg)
			return

		# If we're here - then the role is an actual role - I think?
		promoArray = self.settings.getServerStat(server, "PromotionArray")

		for aRole in promoArray:
			# Get the role that corresponds to the id
			if str(aRole['ID']) == str(role.id):
				# We found it - let's remove it
				promoArray.remove(aRole)
				self.settings.setServerStat(server, "PromotionArray", promoArray)
				msg = '**{}** removed successfully.'.format(aRole['Name'])
				msg = Utils.suppressed(ctx,msg)
				await channel.send(msg)
				return

		# If we made it this far - then we didn't find it
		msg = '{} not found in list.'.format(role.name)
		msg = Utils.suppressed(ctx,msg)
		await channel.send(msg)

	@commands.command(pass_context=True)
	async def prunexproles(self, ctx):
		"""Removes any roles from the xp promotion/demotion system that are no longer on the server (admin only)."""

		author  = ctx.message.author
		server  = ctx.message.guild
		channel = ctx.message.channel

		if not await Utils.is_admin_reply(ctx): return

		# Get the array
		promoArray = self.settings.getServerStat(server, "PromotionArray")
		# promoSorted = sorted(promoArray, key=itemgetter('XP', 'Name'))
		promoSorted = sorted(promoArray, key=lambda x:int(x['XP']))
		
		removed = 0
		for arole in promoSorted:
			# Get current role name based on id
			foundRole = False
			for role in server.roles:
				if str(role.id) == str(arole['ID']):
					# We found it
					foundRole = True
			if not foundRole:
				promoArray.remove(arole)
				removed += 1

		msg = 'Removed *{}* orphaned roles.'.format(removed)
		await ctx.message.channel.send(msg)
		

	@commands.command(pass_context=True)
	async def setxprole(self, ctx, *, role : str = None):
		"""Sets the required role ID to give xp, gamble, or feed the bot (admin only)."""
		if not await Utils.is_admin_reply(ctx): return
		if role == None:
			self.settings.setServerStat(ctx.message.guild, "RequiredXPRole", "")
			msg = 'Giving xp, gambling, and feeding the bot now available to *everyone*.'
			await ctx.message.channel.send(msg)
			return

		if type(role) is str:
			if role == "everyone":
				role = "@everyone"
			roleName = role
			role = DisplayName.roleForName(roleName, ctx.message.guild)
			if not role:
				msg = 'I couldn\'t find *{}*...'.format(roleName)
				msg = Utils.suppressed(ctx,msg)
				await ctx.message.channel.send(msg)
				return

		# If we made it this far - then we can add it
		self.settings.setServerStat(ctx.message.guild, "RequiredXPRole", role.id)

		msg = 'Role required to give xp, gamble, or feed the bot set to **{}**.'.format(role.name)
		msg = Utils.suppressed(ctx,msg)
		await ctx.message.channel.send(msg)
		
	
	@setxprole.error
	async def xprole_error(self, error, ctx):
		# do stuff
		msg = 'xprole Error: {}'.format(error)
		await ctx.channel.send(msg)

	@commands.command(pass_context=True)
	async def xprole(self, ctx):
		"""Lists the required role to give xp, gamble, or feed the bot."""
		role = self.settings.getServerStat(ctx.message.guild, "RequiredXPRole")
		if role == None or role == "":
			msg = '**Everyone** can give xp, gamble, and feed the bot.'
			await ctx.message.channel.send(msg)
		else:
			# Role is set - let's get its name
			found = False
			for arole in ctx.message.guild.roles:
				if str(arole.id) == str(role):
					found = True
					vowels = "aeiou"
					if arole.name[:1].lower() in vowels:
						msg = 'You need to be an **{}** to *give xp*, *gamble*, or *feed* the bot.'.format(arole.name)
					else:
						msg = 'You need to be a **{}** to *give xp*, *gamble*, or *feed* the bot.'.format(arole.name)
			if not found:
				msg = 'There is no role that matches id: `{}` - consider updating this setting.'.format(role)
			msg = Utils.suppressed(ctx,msg)
			await ctx.message.channel.send(msg)
		
	@commands.command(pass_context=True)
	async def setstoprole(self, ctx, *, role : str = None):
		"""Sets the required role ID to stop the music player (admin only)."""
		if not await Utils.is_admin_reply(ctx): return
		if role == None:
			self.settings.setServerStat(ctx.message.guild, "RequiredStopRole", "")
			msg = 'Stopping the music now *admin-only*.'
			await ctx.message.channel.send(msg)
			return

		if type(role) is str:
			if role == "everyone":
				role = "@everyone"
			roleName = role
			role = DisplayName.roleForName(roleName, ctx.message.guild)
			if not role:
				msg = 'I couldn\'t find *{}*...'.format(roleName)
				msg = Utils.suppressed(ctx,msg)
				await ctx.message.channel.send(msg)
				return

		# If we made it this far - then we can add it
		self.settings.setServerStat(ctx.message.guild, "RequiredStopRole", role.id)

		msg = 'Role required to stop the music player set to **{}**.'.format(role.name)
		msg = Utils.suppressed(ctx,msg)
		await ctx.message.channel.send(msg)
		
	
	@setstoprole.error
	async def stoprole_error(self, error, ctx):
		# do stuff
		msg = 'setstoprole Error: {}'.format(error)
		await ctx.channel.send(msg)

	@commands.command(pass_context=True)
	async def stoprole(self, ctx):
		"""Lists the required role to stop the bot from playing music."""
		role = self.settings.getServerStat(ctx.message.guild, "RequiredStopRole")
		if role == None or role == "":
			msg = '**Only Admins** can use stop.'
			await ctx.message.channel.send(msg)
		else:
			# Role is set - let's get its name
			found = False
			for arole in ctx.message.guild.roles:
				if str(arole.id) == str(role):
					found = True
					vowels = "aeiou"
					if arole.name[:1].lower() in vowels:
						msg = 'You need to be an **{}** to use `$stop`.'.format(arole.name)
					else:
						msg = 'You need to be a **{}** to use `$stop`.'.format(arole.name)
					
			if not found:
				msg = 'There is no role that matches id: `{}` - consider updating this setting.'.format(role)
			msg = Utils.suppressed(ctx,msg)
			await ctx.message.channel.send(msg)

		
	@commands.command(pass_context=True)
	async def setlinkrole(self, ctx, *, role : str = None):
		"""Sets the required role ID to add/remove links (admin only)."""
		if not await Utils.is_admin_reply(ctx): return
		if role == None:
			self.settings.setServerStat(ctx.message.guild, "RequiredLinkRole", "")
			msg = 'Add/remove links now *admin-only*.'
			await ctx.message.channel.send(msg)
			return

		if type(role) is str:
			if role == "everyone":
				role = "@everyone"
			roleName = role
			role = DisplayName.roleForName(roleName, ctx.message.guild)
			if not role:
				msg = 'I couldn\'t find *{}*...'.format(roleName)
				msg = Utils.suppressed(ctx,msg)
				await ctx.message.channel.send(msg)
				return

		# If we made it this far - then we can add it
		self.settings.setServerStat(ctx.message.guild, "RequiredLinkRole", role.id)

		msg = 'Role required for add/remove links set to **{}**.'.format(role.name)
		msg = Utils.suppressed(ctx,msg)
		await ctx.message.channel.send(msg)
		
	
	@setlinkrole.error
	async def setlinkrole_error(self, error, ctx):
		# do stuff
		msg = 'setlinkrole Error: {}'.format(error)
		await ctx.channel.send(msg)
		
		
	@commands.command(pass_context=True)
	async def sethackrole(self, ctx, *, role : str = None):
		"""Sets the required role ID to add/remove hacks (admin only)."""
		if not await Utils.is_admin_reply(ctx): return
		if role == None:
			self.settings.setServerStat(ctx.message.guild, "RequiredHackRole", "")
			msg = 'Add/remove hacks now *admin-only*.'
			await ctx.message.channel.send(msg)
			return

		if type(role) is str:
			if role == "everyone":
				role = "@everyone"
			roleName = role
			role = DisplayName.roleForName(roleName, ctx.message.guild)
			if not role:
				msg = 'I couldn\'t find *{}*...'.format(roleName)
				msg = Utils.suppressed(ctx,msg)
				await ctx.message.channel.send(msg)
				return

		# If we made it this far - then we can add it
		self.settings.setServerStat(ctx.message.guild, "RequiredHackRole", role.id)

		msg = 'Role required for add/remove hacks set to **{}**.'.format(role.name)
		msg = Utils.suppressed(ctx,msg)
		await ctx.message.channel.send(msg)


	@sethackrole.error
	async def hackrole_error(self, error, ctx):
		# do stuff
		msg = 'sethackrole Error: {}'.format(error)
		await ctx.channel.send(msg)


	@commands.command(pass_context=True)
	async def settagrole(self, ctx, *, role : str = None):
		"""Sets the required role ID to add/remove tags (admin only)."""
		if not await Utils.is_admin_reply(ctx): return
		if role == None:
			self.settings.setServerStat(ctx.message.guild, "RequiredTagRole", "")
			msg = 'Add/remove tags now *admin-only*.'
			await ctx.message.channel.send(msg)
			return

		if type(role) is str:
			if role == "everyone":
				role = "@everyone"
			roleName = role
			role = DisplayName.roleForName(roleName, ctx.message.guild)
			if not role:
				msg = 'I couldn\'t find *{}*...'.format(roleName)
				msg = Utils.suppressed(ctx,msg)
				await ctx.message.channel.send(msg)
				return

		# If we made it this far - then we can add it
		self.settings.setServerStat(ctx.message.guild, "RequiredTagRole", role.id)

		msg = 'Role required for add/remove tags set to **{}**.'.format(role.name)
		msg = Utils.suppressed(ctx,msg)
		await ctx.message.channel.send(msg)


	@settagrole.error
	async def tagrole_error(self, error, ctx):
		# do stuff
		msg = 'settagrole Error: {}'.format(error)
		await ctx.channel.send(msg)
		
		
	@commands.command(pass_context=True)
	async def setrules(self, ctx, *, rules : str = None):
		"""Set the server's rules (bot-admin only)."""
		
		if not await Utils.is_bot_admin_reply(ctx): return
		
		if rules == None:
			rules = ""
			
		self.settings.setServerStat(ctx.message.guild, "Rules", rules)
		msg = 'Rules now set to:\n{}'.format(rules)
		
		await ctx.message.channel.send(Utils.suppressed(ctx,msg))
		
		
	@commands.command(pass_context=True)
	async def rawrules(self, ctx):
		"""Display the markdown for the server's rules (bot-admin only)."""
		if not await Utils.is_bot_admin_reply(ctx): return
		rules = self.settings.getServerStat(ctx.message.guild, "Rules")
		rules = rules.replace('\\', '\\\\').replace('*', '\\*').replace('`', '\\`').replace('_', '\\_')
		msg = "*{}* Rules (Raw Markdown):\n{}".format(Utils.suppressed(ctx, ctx.guild.name), rules)
		await ctx.channel.send(msg)
		
		
	@commands.command(pass_context=True)
	async def lock(self, ctx):
		"""Toggles whether the bot only responds to admins (admin only)."""
		
		if not await Utils.is_admin_reply(ctx): return
		
		isLocked = self.settings.getServerStat(ctx.message.guild, "AdminLock")
		if isLocked:
			msg = 'Admin lock now *Off*.'
			self.settings.setServerStat(ctx.message.guild, "AdminLock", False)
		else:
			msg = 'Admin lock now *On*.'
			self.settings.setServerStat(ctx.message.guild, "AdminLock", True)
		await ctx.message.channel.send(msg)
		
		
	@commands.command(pass_context=True)
	async def addadmin(self, ctx, *, role : str = None):
		"""Adds a new role to the admin list (admin only)."""

		usage = 'Usage: `{}addadmin [role]`'.format(ctx.prefix)
		if not await Utils.is_admin_reply(ctx): return
		if role == None:
			await ctx.send(usage)
			return

		roleName = role
		if type(role) is str:
			if role.lower() == "everyone" or role.lower() == "@everyone":
				role = ctx.guild.default_role
			else:
				role = DisplayName.roleForName(roleName, ctx.guild)
			if not role:
				msg = 'I couldn\'t find *{}*...'.format(roleName)
				msg = Utils.suppressed(ctx,msg)
				await ctx.message.channel.send(msg)
				return

		# Now we see if we already have that role in our list
		promoArray = self.settings.getServerStat(ctx.message.guild, "AdminArray")

		for aRole in promoArray:
			# Get the role that corresponds to the id
			if str(aRole['ID']) == str(role.id):
				# We found it - throw an error message and return
				msg = '**{}** is already in the list.'.format(role.name)
				msg = Utils.suppressed(ctx,msg)
				await ctx.message.channel.send(msg)
				return

		# If we made it this far - then we can add it
		promoArray.append({ 'ID' : role.id, 'Name' : role.name })
		self.settings.setServerStat(ctx.message.guild, "AdminArray", promoArray)

		msg = '**{}** added to list.'.format(role.name)
		msg = Utils.suppressed(ctx,msg)
		await ctx.message.channel.send(msg)
		return

	@addadmin.error
	async def addadmin_error(self, error, ctx):
		# do stuff
		msg = 'addadmin Error: {}'.format(error)
		await ctx.channel.send(msg)
		
		
	@commands.command(pass_context=True)
	async def removeadmin(self, ctx, *, role : str = None):
		"""Removes a role from the admin list (admin only)."""

		usage = 'Usage: `{}removeadmin [role]`'.format(ctx.prefix)
		if not await Utils.is_admin_reply(ctx): return
		if role == None:
			return await ctx.send(usage)

		# Name placeholder
		roleName = role
		if type(role) is str:
			if role.lower() == "everyone" or role.lower() == "@everyone":
				role = ctx.guild.default_role
			else:
				role = DisplayName.roleForName(role, ctx.guild)

		# If we're here - then the role is a real one
		promoArray = self.settings.getServerStat(ctx.message.guild, "AdminArray")

		for aRole in promoArray:
			# Check for Name
			if aRole['Name'].lower() == roleName.lower():
				# We found it - let's remove it
				promoArray.remove(aRole)
				self.settings.setServerStat(ctx.message.guild, "AdminArray", promoArray)
				msg = '**{}** removed successfully.'.format(aRole['Name'])
				msg = Utils.suppressed(ctx,msg)
				await ctx.message.channel.send(msg)
				return

			# Get the role that corresponds to the id
			if role and (str(aRole['ID']) == str(role.id)):
				# We found it - let's remove it
				promoArray.remove(aRole)
				self.settings.setServerStat(ctx.message.guild, "AdminArray", promoArray)
				msg = '**{}** removed successfully.'.format(role.name)
				msg = Utils.suppressed(ctx,msg)
				await ctx.message.channel.send(msg)
				return

		# If we made it this far - then we didn't find it
		msg = '**{}** not found in list.'.format(role.name)
		msg = Utils.suppressed(ctx,msg)
		await ctx.message.channel.send(msg)

	@removeadmin.error
	async def removeadmin_error(self, error, ctx):
		# do stuff
		msg = 'removeadmin Error: {}'.format(error)
		await ctx.channel.send(msg)
		
		
	@commands.command(pass_context=True)
	async def removemotd(self, ctx, *, chan = None):
		"""Removes the message of the day from the selected channel."""
		
		channel = ctx.message.channel
		server  = ctx.message.guild
		
		if not await Utils.is_admin_reply(ctx): return
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
			if str(a['ID']) == str(chan.id):
				# We found it - throw an error message and return
				motdArray.remove(a)
				self.settings.setServerStat(server, "ChannelMOTD", motdArray)
				
				msg = 'MOTD for *{}* removed.'.format(channel.name)
				await channel.send(msg)
				await channel.edit(topic=None)
				await self.updateMOTD()
				return		
		msg = 'MOTD for *{}* not found.'.format(chan.name)
		msg = Utils.suppressed(ctx,msg)
		await channel.send(msg)	
		
	@removemotd.error
	async def removemotd_error(self, error, ctx):
		# do stuff
		msg = 'removemotd Error: {}'.format(error)
		await ctx.channel.send(msg)
				

	@commands.command(pass_context=True)
	async def broadcast(self, ctx, *, message : str = None):
		"""Broadcasts a message to all connected servers.  Can only be done by the owner."""
		if message == None:
			return await ctx.send("Usage: `{}broadcast [message]`".format(ctx.prefix))
		# Only allow owner
		isOwner = self.settings.isOwner(ctx.author)
		if isOwner == None:
			msg = 'I have not been claimed, *yet*.'
			await ctx.send(msg)
			return
		elif isOwner == False:
			msg = 'You are not the *true* owner of me.  Only the rightful owner can use this command.'
			await ctx.send(msg)
			return
		for server in self.bot.guilds:
			# Get the default channel
			targetChan = server.get_channel(server.id)
			targetChanID = self.settings.getServerStat(server, "DefaultChannel")
			if len(str(targetChanID)):
				# We *should* have a channel
				tChan = self.bot.get_channel(int(targetChanID))
				if tChan:
					# We *do* have one
					targetChan = tChan
			try:
				await targetChan.send(message)
			except Exception:
				pass

		
	@commands.command(pass_context=True)
	async def settopic(self, ctx, channel = None, *, message = ""):
		"""Sets the channel topic of the passed channel (bot-admin only)."""
		usage = 'Usage: `{}settopic [channel] [message]`'.format(ctx.prefix)
		if not await Utils.is_bot_admin_reply(ctx): return
		if not channel and not message: return await ctx.send(usage)
		resolved_channel = DisplayName.channelForName(channel,ctx.guild,"text")
		if not resolved_channel:
			# Not a channel - assume it's part of the message
			message = channel + message
			resolved_channel = ctx.channel
		try: await resolved_channel.edit(topic=message if message else None)
		except: return await ctx.send("Something went wrong when changing the channel topic :(")
		return await ctx.send("Topic for {} {}!".format(resolved_channel.mention,"set" if message else "removed"))

	@commands.command()
	async def slowmode(self, ctx, channel = None, seconds = None):
		"""Sets the number of seconds for slow mode for the passed channel - use any number 0 or lower to disable (bot-admin only)."""
		usage = 'Usage: `{}slowmode [channel] [seconds]`'.format(ctx.prefix)
		if not await Utils.is_bot_admin_reply(ctx): return
		if channel == seconds == None: return await ctx.send(usage)
		resolved_channel = DisplayName.channelForName(channel,ctx.guild,"text")
		if not resolved_channel:
			# Not a channel - assume it's part of the message
			seconds = channel
			resolved_channel = ctx.channel
		if seconds == None: # Print the slow mode
			sm = ctx.channel.slowmode_delay
			return await ctx.send("Slow mode is {} in {}!".format(
				"enabled with a delay of {:,} second{}".format(sm,"" if sm == 1 else "s") if sm > 0 else "" if sm > 0 else "disabled",
				resolved_channel.mention,
			))
		try: seconds = int(seconds)
		except: return await ctx.send("Invalid seconds value passed!")
		try: await resolved_channel.edit(slowmode_delay=0 if seconds <= 0 else seconds)
		except: return await ctx.send("Something went wrong when updating slow mode :(")
		return await ctx.send("Slow mode is {} in {}!".format(
			"enabled with a delay of {:,} second{}".format(seconds, "" if seconds == 1 else "s") if seconds > 0 else "disabled",
			resolved_channel.mention
		))
