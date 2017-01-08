import asyncio
import discord
from   urllib.parse import quote
from   discord.ext import commands
from   Cogs import Settings
from   Cogs import DisplayName
from   Cogs import TinyURL

class ARTII:

	# Init with the bot reference
	def __init__(self, bot):
		self.bot = bot

	@commands.command(pass_context=True)
	async def ascii(self, ctx, *, query = None):
		"""Get some searching done."""

		if query == None:
			msg = 'You need word for me to make ASCII art.'
			await self.bot.send_message(ctx.message.channel, msg)
			return

		asciiv = "http://artii.herokuapp.com/make?text={}".format(quote(query))
		asciiT = TinyURL.tiny_url(asciiv)
		msg = '*{}*, you can find your answers here:\n\n{}'.format(DisplayName.name(ctx.message.author), asciiT)
		# Say message
		await self.bot.send_message(ctx.message.channel, msg)
