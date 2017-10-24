import asyncio
import discord
import random
from   discord.ext import commands
from   Cogs import Settings
from   Cogs import DisplayName
from   Cogs import Nullify
from   Cogs import DL
import urllib

def setup(bot):
	# Add the bot
	bot.add_cog(Ascii(bot))
	
class Ascii:
    
	def __init__(self, bot):
		self.bot = bot

	@commands.command(pass_context=True, no_pm=True)
	async def ascii(self, ctx, *, text : str = None):
		"""Beautify some text (font list at http://artii.herokuapp.com/fonts_list)."""

		if text == None:
			await ctx.channel.send('Usage: `{}ascii [font (optional)] [text]`\n(font list at http://artii.herokuapp.com/fonts_list)'.format(ctx.prefix))
			return

		# Get list of fonts
		fonturl = "http://artii.herokuapp.com/fonts_list"
		response = await DL.async_text(fonturl)
		fonts = response.split()

		font = None
		# Split text by space - and see if the first word is a font
		parts = text.split()
		if len(parts) > 1:
			# We have enough entries for a font
			if parts[0] in fonts:
				# We got a font!
				font = parts[0]
				text = ' '.join(parts[1:])
	
		url = "http://artii.herokuapp.com/make?{}".format(urllib.parse.urlencode({'text':text}))
		if font:
			url += '&font={}'.format(font)
		response = await DL.async_text(url)
		await ctx.channel.send("```Markup\n{}```".format(response))
