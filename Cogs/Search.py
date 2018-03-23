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
			amount = float(amount)
		except:
			hasError = True

		if frm == None or to == None or amount <= 0:
			hasError = True
		
		if hasError == True:
			r = await DL.async_text("http://www.xe.com/currency/")
			curr_list = []
			try:
				lst = r.split("search-text'>")
				for l in lst:
					curr_list.append(l.split("<")[0])
				if not "XBT - Bitcoin" in curr_list:
					curr_list.append("XBT - Bitcoin")
				curr_list = sorted(curr_list)
			except:
				curr_list = []
			await ctx.send("Usage: `{}convert [amount] [from_currency] [to_currency]`".format(ctx.prefix))
			if len(curr_list):
				await Message.EmbedText(
					title="Currency List",
					description="\n".join(curr_list),
					desc_head="```\n",
					desc_foot="```",
					pm_after=0,
					color=ctx.author
				).send(ctx)
			return

		if"to" in to:
			to = to.replace("to","")
			to = to.strip()

		# convert_url = "https://finance.google.com/finance/converter?a={}&from={}&to={}".format(amount,frm,to)
		convert_url = "http://www.xe.com/currencyconverter/convert/?Amount={}&From={}&To={}".format(amount,frm,to)
		r = await DL.async_text(convert_url)

		try:
			amt = r.split("uccResultAmount'>")[1].split("<")[0]
			to  = r.split("uccToCurrencyCode'>")[1].split("<")[0]
			results = [amt, to]
		except:
			await ctx.send("Error getting currency conversion results :(")
			return
		
		'''doc = pq(r)
		result = str(doc('#uccResultAmount span').text())
		results = result.split(" ")'''
		
		if len(results):
			amount = "{:,}".format(int(amount)) if int(amount) == float(amount) else "{:,f}".format(amount).rstrip("0")
			results[0] = float(results[0].replace(",", ""))
			results[0] = "{:,}".format(int(results[0])) if int(results[0]) == float(results[0]) else "{:,f}".format(results[0]).rstrip("0")
			await ctx.channel.send("{} {} is {} {}".format(amount,str(frm).upper(),results[0], results[1]))
		else:
			await ctx.channel.send("Whoops!  I couldn't make that conversion.")

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

