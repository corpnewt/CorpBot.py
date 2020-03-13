import asyncio
import discord
from   discord.ext import commands

def setup(bot):
	# Add the bot
	bot.add_cog(ThatsTrue(bot))

class ThatsTrue(commands.Cog):

	# Init with the bot reference, and a reference to the settings var
	def __init__(self, bot):
		self.bot = bot

	async def message(self, message):
		# Check the message - and if it contains "body-mind" or "earth dating"
		# respond with "That's true"
		ctx = await self.bot.get_context(message)
		if ctx.command:
			return {}
		if any([x for x in ["bodymind","body-mind","body mind","earth dating","earth-dating","earthdating"] if x in ctx.message.content.lower()]):
			return {"Respond":"That's true."}