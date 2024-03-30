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
		if not message.guild:
			return
		# Valid message
		if not len(message.mentions):
			return
		name_list = [x.mention for x in message.mentions if x.status is discord.Status.offline]
		if not len(name_list):
			# No one was offline
			return
		ctx = await self.bot.get_context(message)
		if ctx.command:
			# Don't check if we're running a command
			return
		# We got a message in a server, and at least one user was mentioned
		if not self.settings.getServerStat(message.guild, "RemindOffline"):
			return
		if len(name_list) == 1:
			msg = "It looks like {} is offline - dm them if urgent.".format(name_list[0])
		else:
			msg = "It looks like the following users are offline - dm them if urgent:\n\n{}".format("\n".join(name_list))
		await ctx.send(msg,reference=message)

	@commands.command(pass_context=True)
	async def remindoffline(self, ctx, *, yes_no = None):
		"""Sets whether to inform users that pinged members are offline or not."""
		if not await Utils.is_bot_admin_reply(ctx): return
		await ctx.send(Utils.yes_no_setting(ctx,"Offline user reminder","RemindOffline",yes_no))
