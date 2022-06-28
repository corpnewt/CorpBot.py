import asyncio, discord
from   discord.ext import commands
from   Cogs import Utils, DisplayName

async def setup(bot):
	# Add the bot
	await bot.add_cog(OfflineUser(bot))

# This is the OfflineUser module

class OfflineUser(commands.Cog):

	# Init with the bot reference, and a reference to the settings var
	def __init__(self, bot):
		self.bot = bot
		self.settings = bot.get_cog("Settings")
		global Utils, DisplayName
		Utils = self.bot.get_cog("Utils")
		DisplayName = self.bot.get_cog("DisplayName")
		
	async def _send_message(self, ctx, msg, pm = False):
		# Helper method to send messages to their proper location
		if pm == True and not ctx.channel == ctx.author.dm_channel:
			# Try to dm
			try:
				await ctx.author.send(msg)
				return await ctx.message.add_reaction("📬")
			except discord.Forbidden:
				pass
		await ctx.send(msg,allowed_mentions=discord.AllowedMentions.all())

	@commands.Cog.listener()
	async def on_message(self, message):
		if not message.guild:
			return
		if not self.settings.getServerStat(message.guild, "RemindOffline"):
			return
		# Valid message
		ctx = await self.bot.get_context(message)
		if ctx.command:
			# Don't check if we're running a command
			return
		if not len(message.mentions):
			return
		name_list = [DisplayName.name(x) for x in message.mentions if x.status is discord.Status.offline]
		if not len(name_list):
			# No one was offline
			return
		if len(name_list) == 1:
			msg = "{}, it looks like {} is offline - pm them if urgent.".format(ctx.author.mention, name_list[0])
		else:
			msg = "{}, it looks like the following users are offline - pm them if urgent:\n\n{}".format(ctx.author.mention, ", ".join(name_list))
		await self._send_message(ctx, msg, True)

	@commands.command()
	async def remindoffline(self, ctx, *, yes_no = None):
		"""Sets whether to inform users that pinged members are offline or not."""
		if not await Utils.is_bot_admin_reply(ctx): return
		await ctx.send(Utils.yes_no_setting(ctx,"Offline user reminder","RemindOffline",yes_no))