import asyncio, discord
from   discord.ext import commands
from   Cogs import Utils, DisplayName

def setup(bot):
	# Add the bot
	bot.add_cog(OfflineUser(bot))

# This is the OfflineUser module

class OfflineUser(commands.Cog):

	# Init with the bot reference, and a reference to the settings var
	def __init__(self, bot):
		self.bot = bot
		self.settings = bot.get_cog("Settings")
		global Utils, DisplayName
		Utils = self.bot.get_cog("Utils")
		DisplayName = self.bot.get_cog("DisplayName")

	@commands.Cog.listener()
	async def on_message(self, message):
		if message.author.bot:
			return
		if not message.guild:
			return
		# Valid message
		if not len(message.mentions):
			return
		name_list = [x for x in message.mentions if x != message.author and x.status is discord.Status.offline]
		if not len(name_list):
			# No one was offline
			return
		ctx = await self.bot.get_context(message)
		if ctx.command:
			# Don't check if we're running a command
			return
		# We got a message in a server, and at least one user was mentioned
		if not self.settings.getServerStat(message.guild, "RemindOffline"):
			# We're not mentioning server-wide, let's see if any of the offline users
			# have the setting set
			personal_list = [x for x in name_list if self.settings.getGlobalUserStat(x,"RemindOffline",False)]
			if not personal_list:
				return
			# Update the name_list
			name_list = personal_list
		if len(name_list) == 1:
			msg = "It looks like {} is offline - pm them if urgent.".format(name_list[0].mention)
		else:
			msg = "It looks like the following users are offline - pm them if urgent:\n\n{}".format("\n".join([x.mention for x in name_list]))
		await ctx.send(msg,reference=message,mention_author=True)

	@commands.command()
	async def afk(self, ctx, *, yes_no = None):
		"""Sets whether the bot should reply to pings stating you're offline regardless of the per-server $remindoffline settings."""
		display_name = "Personal offline reminder"
		current = self.settings.getGlobalUserStat(ctx.author,"RemindOffline",False)
		if yes_no is None:
			# Output what we have
			return await ctx.send("{} currently *{}*.".format(display_name,"enabled" if current else "disabled"))
		elif yes_no.lower() in ("1","yes","on","true","enabled","enable"):
			yes_no = True
			msg = "{} {} *enabled*.".format(display_name,"remains" if current else "is now")
		elif yes_no.lower() in ("0","no","off","false","disabled","disable"):
			yes_no = False
			msg = "{} {} *disabled*.".format(display_name,"is now" if current else "remains")
		else:
			msg = "That's not a valid setting."
			yes_no = current
		if yes_no != current:
			# We've updated it
			self.settings.setGlobalUserStat(ctx.author,"RemindOffline",yes_no)
		return await ctx.send(msg)

	@commands.command()
	async def remindoffline(self, ctx, *, yes_no = None):
		"""Sets whether to inform users that pinged members are offline or not."""
		if not await Utils.is_bot_admin_reply(ctx): return
		await ctx.send(Utils.yes_no_setting(ctx,"Offline user reminder","RemindOffline",yes_no))
