import asyncio, discord
from   operator import itemgetter
from   discord.ext import commands
from   Cogs import Utils, DisplayName

def setup(bot):
	# Add the bot and deps
	settings = bot.get_cog("Settings")
	bot.add_cog(DJRoles(bot, settings))

class DJRoles(commands.Cog):

	# Init with the bot reference, and a reference to the settings var and xp var
	def __init__(self, bot, settings):
		self.bot = bot
		self.settings = settings
		global Utils, DisplayName
		Utils = self.bot.get_cog("Utils")
		DisplayName = self.bot.get_cog("DisplayName")

	async def _add_role(self, ctx, role = None, setting = "DJArray", command = "adddj"):
		if not await Utils.is_bot_admin_reply(ctx): return
		if role is None:
			return await ctx.send("Usage: `{}{} [role]`".format(ctx.prefix,command))
		roleName = role
		if type(role) is str:
			if role.lower() == "everyone" or role.lower() == "@everyone":
				role = ctx.guild.default_role
			else:
				role = DisplayName.roleForName(roleName, ctx.guild)
			if not role:
				msg = 'I couldn\'t find *{}*...'.format(roleName)
				return await ctx.send(Utils.suppressed(ctx,msg))
		# Now we see if we already have that role in our list
		djArray = self.settings.getServerStat(ctx.guild, setting, [])
		if next((x for x in djArray if str(x["ID"])==str(role.id)),False):
			msg = '**{}** is already in the list.'.format(role.name)
			return await ctx.send(Utils.suppressed(ctx,msg))
		# If we made it this far - then we can add it
		djArray.append({ 'ID' : role.id, 'Name' : role.name })
		self.settings.setServerStat(ctx.guild, setting, djArray)
		await ctx.send(Utils.suppressed(ctx,"**{}** added to list.".format(role.name)))

	async def _rem_role(self, ctx, role = None, setting = "DJArray", command = "removedj"):
		if not await Utils.is_bot_admin_reply(ctx): return
		if role == None:
			return await ctx.send("Usage: `{}{} [role]`".format(ctx.prefix,command))
		# Name placeholder
		roleName = role
		if type(role) is str:
			if role.lower() == "everyone" or role.lower() == "@everyone":
				role = ctx.guild.default_role
			else:
				role = DisplayName.roleForName(role, ctx.guild)
		# If we're here - then the role is a real one
		djArray = self.settings.getServerStat(ctx.guild, setting, [])
		# Check by id first, then by name
		found_role = next((x for x in djArray if str(x["ID"])==str(role.id)),False)
		if not found_role:
			found_role = next((x for x in djArray if x["Name"].lower()==role.name.lower()),False)
		if found_role:
			djArray.remove(found_role)
			self.settings.setServerStat(ctx.guild, setting, djArray)
			return await ctx.send(Utils.suppressed(ctx,"**{}** removed successfully.".format(found_role['Name'])))
		# If we made it this far - then we didn't find it
		await ctx.send(Utils.suppressed(ctx,"**{}** not found in list.".format(role)))

	async def _list_role(self, ctx, setting = "DJArray", command = "adddj"):
		djArray = sorted(self.settings.getServerStat(ctx.guild,setting,[]),key=itemgetter("Name"))
		if not len(djArray):
			roleText = "There are no roles set yet.  Use `{}{} [role]` to add some.".format(ctx.prefix,command)
			return await ctx.send(roleText)
		roleText = "__**Current {} Roles:**__\n\n".format(setting.replace("Array",""))
		for arole in djArray:
			role = ctx.guild.get_role(int(arole["ID"]))
			roleText += "**{}** (removed from server)\n".format(arole["Name"]) if role is None else "**{}** (ID : `{}`)\n".format(role.name, arole["ID"])
		await ctx.send(Utils.suppressed(ctx,roleText))

	@commands.command(aliases=["newdj"])
	async def adddj(self, ctx, *, role : str = None):
		"""Adds a new role to the dj list (bot-admin only)."""
		await self._add_role(ctx,role,setting="DJArray",command="adddj")
		
	@commands.command(aliases=["remdj","deletedj","deldj"])
	async def removedj(self, ctx, *, role : str = None):
		"""Removes a role from the dj list (bot-admin only)."""
		await self._rem_role(ctx,role,setting="DJArray",command="removedj")

	@commands.command(pass_context=True)
	async def listdj(self, ctx):
		"""Lists dj roles and id's."""
		await self._list_role(ctx,setting="DJArray",command="adddj")

	@commands.command(aliases=["newmc"])
	async def addmc(self, ctx, *, role : str = None):
		"""Adds a new role to the mc list (bot-admin only)."""
		await self._add_role(ctx,role,setting="MCArray",command="addmc")
		
	@commands.command(aliases=["remmc","deletemc","delmc"])
	async def removemc(self, ctx, *, role : str = None):
		"""Removes a role from the mc list (bot-admin only)."""
		await self._rem_role(ctx,role,setting="MCArray",command="removemc")

	@commands.command(pass_context=True)
	async def listmc(self, ctx):
		"""Lists mc roles and id's."""
		await self._list_role(ctx,setting="MCArray",command="addmc")