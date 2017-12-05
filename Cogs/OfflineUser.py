import asyncio
import discord
from   discord.ext import commands
from   Cogs import DisplayName

def setup(bot):
	# Add the bot
	bot.add_cog(OfflineUser(bot))

# This is the OfflineUser module

class OfflineUser:

	# Init with the bot reference, and a reference to the settings var
	def __init__(self, bot):
		self.bot = bot
		self.settings = bot.get_cog("Settings")
		
	async def _send_message(self, ctx, msg, pm = False):
		# Helper method to send messages to their proper location
		if pm == True and not ctx.channel == ctx.author.dm_channel:
			# Try to dm
			try:
				await ctx.author.send(msg)
				await ctx.message.add_reaction("📬")
			except discord.Forbidden:
				await ctx.send(msg)
			return
		await ctx.send(msg)

	@asyncio.coroutine
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
		name_list = []
		for mention in message.mentions:
			if mention.status == discord.Status.offline:
				name_list.append(DisplayName.name(mention))
		if not len(name_list):
			# No one was offline
			return
		if len(name_list) == 1:
			msg = "{}, it looks like {} is offline - pm them if urgent.".format(ctx.author.mention, name_list[0])
		else:
			msg = "{}, it looks like the following users are offline - pm them if urgent:\n\n{}".format(ctx.author.mention, ", ".join(name_list))
		await self._send_message(ctx, msg, True)

	@commands.command(pass_context=True)
	async def remindoffline(self, ctx, *, yes_no = None):
		"""Sets whether to inform users that pinged members are offline or not."""

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

		setting_name = "Offline user reminder"
		setting_val  = "RemindOffline"

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
