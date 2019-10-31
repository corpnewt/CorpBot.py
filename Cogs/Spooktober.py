import asyncio, discord, random
from   datetime    import datetime
from   discord.ext import commands
from   Cogs        import Utils

def setup(bot):
	settings = bot.get_cog("Settings")
	bot.add_cog(Spooktober(bot, settings))

class Spooktober(commands.Cog):
	
	def __init__(self, bot, settings):
		self.bot = bot
		self.settings = settings

	async def message(self, message):
		if datetime.today().month == 10 and datetime.today().day == 31:
			if not self.settings.getServerStat(message.guild, "Spooking", False):
				# We have this turned off - bail
				return
			# it is the day of ultimate sp00p, sp00p all the messages
			if any(x.lower() in message.content.lower() for x in ("spook","sp00p")):
				await message.add_reaction("🎃")
	
	@commands.command(pass_context=True)
	async def spooking(self, ctx, *, yes_no = None):
		"""Enables/Disables reacting 🎃 to every sp00py message on Halloween (bot-admin only)."""
		if not await Utils.is_admin_reply(ctx): return
		await ctx.send(Utils.yes_no_setting(ctx,"Spooking","Spooking",yes_no))
