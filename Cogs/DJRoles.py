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
			
	@commands.command(pass_context=True)
	async def ytlist(self, ctx, yes_no = None):
		"""Gets or sets whether or not the server will show a list of options when searching with the play command - or if it'll just pick the first (admin only)."""
		if not await Utils.is_admin_reply(ctx): return
		await ctx.send(Utils.yes_no_setting(ctx,"Youtube search list","YTMultiple",yes_no))

	@commands.command(pass_context=True)
	async def adddj(self, ctx, *, role : str = None):
		"""Adds a new role to the dj list (bot-admin only)."""
		usage = 'Usage: `{}adddj [role]`'.format(ctx.prefix)
		if not await Utils.is_bot_admin_reply(ctx): return

		if role == None:
			return await ctx.send(usage)

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
		promoArray = self.settings.getServerStat(ctx.guild, "DJArray")
		if next((x for x in promoArray if str(x["ID"])==str(role.id)),False):
			msg = '**{}** is already in the list.'.format(role.name)
			return await ctx.send(Utils.suppressed(ctx,msg))

		# If we made it this far - then we can add it
		promoArray.append({ 'ID' : role.id, 'Name' : role.name })
		self.settings.setServerStat(ctx.guild, "DJArray", promoArray)

		msg = '**{}** added to list.'.format(role.name)
		await ctx.send(Utils.suppressed(ctx,msg))
		
		
	@commands.command(pass_context=True)
	async def removedj(self, ctx, *, role : str = None):
		"""Removes a role from the dj list (bot-admin only)."""
		usage = 'Usage: `{}removedj [role]`'.format(ctx.prefix)
		if not await Utils.is_bot_admin_reply(ctx): return
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
		promoArray = self.settings.getServerStat(ctx.guild, "DJArray")
		# Check by id first, then by name
		found_role = next((x for x in promoArray if str(x["ID"])==str(role.id)),False)
		if not found_role:
			found_role = next((x for x in promoArray if x["Name"].lower()==role.name.lower()),False)
		if found_role:
			promoArray.remove(found_role)
			self.settings.setServerStat(ctx.guild, "DJArray", promoArray)
			msg = '**{}** removed successfully.'.format(found_role['Name'])
			return await ctx.send(Utils.suppressed(ctx,msg))
		# If we made it this far - then we didn't find it
		msg = '**{}** not found in list.'.format(role)
		await ctx.send(Utils.suppressed(ctx,msg))


	@commands.command(pass_context=True)
	async def listdj(self, ctx):
		"""Lists dj roles and id's."""
		promoArray = self.settings.getServerStat(ctx.guild, "DJArray")
		promoSorted = sorted(promoArray, key=itemgetter('Name'))
		if not len(promoSorted):
			roleText = "There are no dj roles set yet.  Use `{}adddj [role]` to add some.".format(ctx.prefix)
			return await ctx.channel.send(roleText)
		roleText = "__**Current DJ Roles:**__\n\n"
		for arole in promoSorted:
			role = ctx.guild.get_role(int(arole["ID"]))
			roleText += "**{}** (removed from server)\n".format(arole["Name"]) if role is None else "**{}** (ID : `{}`)\n".format(role.name, arole["ID"])
		await ctx.send(Utils.suppressed(ctx,roleText))