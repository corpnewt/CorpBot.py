import asyncio
import discord
import wikipedia
import textwrap
from   discord.ext import commands
from   Cogs import Settings
from   Cogs import PickList

def setup(bot):
	# Add the bot
	bot.add_cog(Wiki(bot))

# This is the Face module. It sends faces.

class Wiki:

	# Init with the bot reference, and a reference to the settings var
	def __init__(self, bot):
		self.bot = bot

	@commands.command(pass_context=True)
	async def wiki(self, ctx, *, search : str = None):
		"""Search Wikipedia!"""
		if search == None:
			await ctx.send("Usage: `{}wiki [search terms]`".format(ctx.prefix))
			return
		
		results = wikipedia.search(search)

		if not len(results):
			await ctx.send("No results for `{}` :(".format(search.replace('`', '\\`')))
			return
		
		message = None
		# We got results - let's list if we have more than 1
		if len(results) > 1:
			# List
			if len(results) > 5:
				results = results[:5]
			index, message = await PickList.Picker(
				title="There were multiple results for `{}`, please pick from the following list:".format(search.replace('`', '\\`')),
				list=results,
				ctx=ctx
			).pick()
			# Check if we errored/cancelled
			if index < 0:
				await message.edit(content="Wiki results for `{}` canceled.".format(search.replace('`', '\\`')))
				return
			newSearch = results[index]
		else:
			# Only one result
			newSearch = results[0]
		
		# Try to get a hit
		try:
			wik = wikipedia.page(newSearch)
		except wikipedia.DisambiguationError:
			msg = "That search wasn't specific enough - try again with more detail."
			if message:
				await message.edit(content=msg)
			else:
				await ctx.send(msg)
			return

		# Create our embed
		wiki_embed = discord.Embed(color=ctx.author.color)
		wiki_embed.title = wik.title
		wiki_embed.url = wik.url
		textList = textwrap.wrap(wik.content, 500, break_long_words=True, replace_whitespace=False)
		wiki_embed.add_field(name="Wikipedia Results", value=textList[0]+"...")

		# Check if we sent a message earlier and edit - otherwise send new
		if message:
			await message.edit(content=" ", embed=wiki_embed)
		else:
			await ctx.send(embed=wiki_embed)
