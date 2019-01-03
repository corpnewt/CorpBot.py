import asyncio
import discord
import json
import os
from   urllib.parse import quote
from   discord.ext import commands
from   Cogs import Settings
from   Cogs import DisplayName
from   Cogs import TinyURL
from   Cogs import Message
from   Cogs import DL
from   pyquery import PyQuery as pq

def setup(bot):
	# Add the bot and deps
	auth = "corpSiteAuth.txt"
	bot.add_cog(Search(bot, auth))

class Search:

	# Init with the bot reference
	def __init__(self, bot, auth_file: str = None):
		self.bot = bot
		self.site_auth = None
		if os.path.isfile(auth_file):
		        with open(auth_file, 'r') as f:
		                self.site_auth = f.read()

	@commands.command(pass_context=True)
	async def google(self, ctx, *, query = None):
		"""Get some searching done."""

		if query == None:
			msg = 'You need a topic for me to Google.'
			await ctx.channel.send(msg)
			return

		lmgtfy = "http://lmgtfy.com/?q={}".format(quote(query))
		lmgtfyT = TinyURL.tiny_url(lmgtfy)
		msg = '*{}*, you can find your answers here:\n\n<{}>'.format(DisplayName.name(ctx.message.author), lmgtfyT)
		# Say message
		await ctx.channel.send(msg)

	@commands.command(pass_context=True)
	async def bing(self, ctx, *, query = None):
		"""Get some uh... more searching done."""

		if query == None:
			msg = 'You need a topic for me to Bing.'
			await ctx.channel.send(msg)
			return

		lmgtfy = "http://letmebingthatforyou.com/?q={}".format(quote(query))
		lmgtfyT = TinyURL.tiny_url(lmgtfy)
		msg = '*{}*, you can find your answers here:\n\n<{}>'.format(DisplayName.name(ctx.message.author), lmgtfyT)
		# Say message
		await ctx.channel.send(msg)

	@commands.command(pass_context=True)
	async def duck(self, ctx, *, query = None):
		"""Duck Duck... GOOSE."""

		if query == None:
			msg = 'You need a topic for me to DuckDuckGo.'
			await ctx.channel.send(msg)
			return

		lmgtfy = "https://lmddgtfy.net/?q={}".format(quote(query))
		lmgtfyT = TinyURL.tiny_url(lmgtfy)
		msg = '*{}*, you can find your answers here:\n\n<{}>'.format(DisplayName.name(ctx.message.author), lmgtfyT)
		# Say message
		await ctx.channel.send(msg)


	@commands.command(pass_context=True)
	async def searchsite(self, ctx, category_name = None, *, query = None):
		"""Search corpnewt.com forums."""

		auth = self.site_auth

		if auth == None:
			await ctx.channel.send("Sorry this feature is not supported!")
			return

		if query == None or category_name == None:
			msg = "Usage: `{}searchsite [category] [search term]`\n\n Categories can be found at:\n\nhttps://corpnewt.com/".format(ctx.prefix)
			await ctx.channel.send(msg)
			return

		categories_url = "https://corpnewt.com/api/categories"
		categories_json = await DL.async_json(categories_url, headers={'Authorization': auth})
		categories = categories_json["categories"]

		category = await self.find_category(categories, category_name)

		if category == None:
			await ctx.channel.send("Usage: `{}searchsite [category] [search term]`\n\n Categories can be found at:\n\nhttps://corpnewt.com/".format(ctx.prefix))
			return

		search_url = "https://corpnewt.com/api/search?term={}&in=titlesposts&categories[]={}&searchChildren=true&showAs=posts".format(query, category["cid"])
		search_json = await DL.async_json(search_url, headers={'Authorization': auth})
		posts = search_json["posts"]
		resultString = 'Results'
		if len(posts) == 1 :
			resultString = 'Result'
		result_string = '**Found {} {} for:** ***{}***\n\n'.format(len(posts), resultString, query)
		limit = 5
		ctr = 0
		for post in posts:
			if ctr < limit:
				ctr = ctr + 1
				result_string += '__{}__\n<https://corpnewt.com/topic/{}>\n\n'.format(post["topic"]["title"], post["topic"]["slug"])
			
		await ctx.channel.send(result_string)


	@commands.command(pass_context=True)
	async def convert(self, ctx, amount = None , frm = None, *, to = None):
		"""convert currencies"""

		hasError = False

		try:
			amount = float(amount.replace(",",""))
		except:
			hasError = True

		if frm == None or to == None or amount <= 0:
			hasError = True

		# Get the list of currencies
		r = await DL.async_json("https://free.currencyconverterapi.com/api/v6/currencies")

		if hasError:
			# Gather our currency list
			curr_list = []
			for l in r.get("results",{}):
				# l is the key - let's format a list
				curr_list.append("{} - {}".format(r["results"][l]["id"], r["results"][l]["currencyName"]))
			if len(curr_list):
				curr_list = sorted(curr_list)
				await Message.EmbedText(
					title="Currency List",
					description="\n".join(curr_list),
					desc_head="```\n",
					desc_foot="```",
					pm_after=0,
					color=ctx.author
				).send(ctx)
				return

		# Verify we have a proper from/to type
		if not frm.upper() in r.get("results",{}):
			await ctx.send("Invalid from currency!")
			return
		if not to.upper() in r.get("results",{}):
			await ctx.send("Invalid to currency!")
			return

		# At this point, we should be able to convert
		o = await DL.async_json("http://free.currencyconverterapi.com/api/v5/convert?q={}_{}&compact=y".format(frm.upper(), to.upper()))

		if not o:
			await ctx.send("Whoops!  I couldn't get that :(")
			return
		
		# Format the numbers
		val = o[list(o)[0]]["val"]
		# Strip any commas
		val    = val.replace(",","")
		# Calculate the results
		amount = "{:,}".format(int(amount)) if int(amount) == float(amount) else "{:,f}".format(amount).rstrip("0")
		output = float(amount)*float(val)
		output = "{:,}".format(int(output)) if int(output) == float(output) else "{:,f}".format(output).rstrip("0")
		await ctx.channel.send("{} {} is {} {}".format(amount,str(frm).upper(), output, str(to).upper()))

	async def find_category(self, categories, category_to_search):
		"""recurse through the categories and sub categories to find the correct category"""
		result_category = None
		
		for category in categories:
			if str(category["name"].lower()).strip() == str(category_to_search.lower()).strip():
					return category

			if len(category["children"]) > 0:
					result_category = await self.find_category(category["children"], category_to_search)
					if result_category != None:
							return result_category
		
		return result_category

