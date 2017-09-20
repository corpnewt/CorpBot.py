import asyncio
import discord
from   discord.ext import commands
from   Cogs import DisplayName

def setup(bot):
	# Add the bot
	bot.add_cog(Heart(bot))

class Heart:

	# Init with the bot reference, and a reference to the settings var
	def __init__(self, bot):
		self.bot = bot

	async def message(self, message):
		# Check the message - and append a heart if a ping exists, but no command
		context = await self.bot.get_context(message)
		if context.command:
			return {}
		# Check for a mention
		try:
			botMember = discord.utils.get(message.guild.members, id=self.bot.user.id)
		except Exception:
			# Couldn't get a member - just get the user
			botMember = self.bot.user
		if botMember.mention in message.content:
			# We got a mention!
			return { "Reaction" : "❤"}