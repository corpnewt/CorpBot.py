import asyncio
import discord
import wikipedia
import textwrap
from   discord.ext import commands
from   Cogs import Settings


# This is the Face module. It sends faces.

class Wiki:

	# Init with the bot reference, and a reference to the settings var
	def __init__(self, bot):
		self.bot = bot

	@commands.command(pass_context=True)
	async def wiki(self, ctx, *, search : str = None):
		"""Search Wikipedia!"""
		if search == None:
			await ctx.channel.send("Usage: `{}wiki [search terms]`".format(ctx.prefix))
			return
		
		results = wikipedia.search(search)

		if not len(results):
			await ctx.channel.send("No results :(")
			return

		# Assume the first result
		newSearch = results[0]
		# Try to get a hit
		try:
			wik = wikipedia.page(newSearch)
		except wikipedia.DisambiguationError:
			await ctx.channel.send("That search wasn't specific enough - try again with more detail.")
			return

		# Create our embed
		wiki_embed = discord.Embed(color=ctx.author.color)
		wiki_embed.title = wik.title
		wiki_embed.url = wik.url
		textList = textwrap.wrap(wik.content, 500, break_long_words=True, replace_whitespace=False)
		wiki_embed.add_field(name="Wikipedia Results", value=textList[0]+"...")

		await ctx.channel.send(embed=wiki_embed)