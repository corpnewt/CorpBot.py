import asyncio
import discord
from   urllib.parse import quote
from   discord.ext import commands
from   Cogs import Settings
from   Cogs import DisplayName

class Google:

	# Init with the bot reference
	def __init__(self, bot):
		self.bot = bot

	@commands.command(pass_context=True)
	async def google(self, ctx, *, query = None):
		"""Get some searching done."""

		if query == None:
			msg = 'You need a topic for me to Google.'
			await self.bot.send_message(ctx.message.channel, msg)
			return

		#query = query.replace(" ", "+")
		lmgtfy = "http://lmgtfy.com/?q={}".format(quote(query))
		msg = '*{}*, you can find your answers here:\n{}'.format(DisplayName.name(ctx.message.author), lmgtfy)
		# Say message
		await self.bot.send_message(ctx.message.channel, msg)