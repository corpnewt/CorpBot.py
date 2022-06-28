import asyncio, discord, random, re
from   datetime    import datetime
from   discord.ext import commands
from   Cogs        import Utils

async def setup(bot):
	settings = bot.get_cog("Settings")
	bot.add_cog(Spooktober(bot, settings))

class Spooktober(commands.Cog):
	
	def __init__(self, bot, settings):
		self.bot = bot
		self.settings = settings
		self.spoop_re = re.compile(r"sp[o0]{2,}(k|p)")

	async def message(self, message):
		if datetime.today().month == 10 and datetime.today().day == 31:
			if not self.settings.getGlobalStat("Spooking", False):
				# We have this turned off - bail
				return
			# it is the day of ultimate sp00p, sp00p all the messages
			if self.spoop_re.search(message.content.lower()):
				await message.add_reaction("🎃")
	
	@commands.command(pass_context=True)
	async def spooking(self, ctx, *, yes_no = None):
		"""Enables/Disables reacting 🎃 to every sp00py message on Halloween (owner only)."""
		if not await Utils.is_owner_reply(ctx): return
		await ctx.send(Utils.yes_no_setting(ctx,"Spooking","Spooking",yes_no,is_global=True))
