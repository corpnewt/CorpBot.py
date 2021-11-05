import asyncio, discord, re
from   discord.ext import commands

def setup(bot):
	# Add the bot
	bot.add_cog(ThatsTrue(bot))

class ThatsTrue(commands.Cog):

	# Init with the bot reference, and a reference to the settings var
	def __init__(self, bot):
		self.bot = bot
		self.regex = re.compile(r"(?i)\b(bodymind|body mind|body-mind|earthdating|earth dating|earth-dating|impostor sus)\b")

	async def message(self, message):
		# Check the message - and if it contains "body-mind" or "earth dating"
		# respond with "That's true"
		ctx = await self.bot.get_context(message)
		if ctx.command:
			return {}
		if re.search(self.regex,ctx.message.content):
			return {"Respond":"That's true."}
