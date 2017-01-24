import asyncio
import discord
import urllib
import requests
import json
import os
from   urllib.parse import quote
from   discord.ext import commands
from   Cogs import Settings
from   Cogs import DisplayName
from   Cogs import TinyURL
from   pyquery import PyQuery as pq

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
			await self.bot.send_message(ctx.message.channel, msg)
			return

		lmgtfy = "http://lmgtfy.com/?q={}".format(quote(query))
		lmgtfyT = TinyURL.tiny_url(lmgtfy)
		msg = '*{}*, you can find your answers here:\n\n{}'.format(DisplayName.name(ctx.message.author), lmgtfyT)
		# Say message
		await self.bot.send_message(ctx.message.channel, msg)

	@commands.command(pass_context=True)
	async def bing(self, ctx, *, query = None):
		"""Get some uh... more searching done."""

		if query == None:
			msg = 'You need a topic for me to Bing.'
			await self.bot.send_message(ctx.message.channel, msg)
			return

		lmgtfy = "http://letmebingthatforyou.com/?q={}".format(quote(query))
		lmgtfyT = TinyURL.tiny_url(lmgtfy)
		msg = '*{}*, you can find your answers here:\n\n{}'.format(DisplayName.name(ctx.message.author), lmgtfyT)
		# Say message
		await self.bot.send_message(ctx.message.channel, msg)

	@commands.command(pass_context=True)
	async def duck(self, ctx, *, query = None):
		"""Duck Duck... GOOSE."""

		if query == None:
			msg = 'You need a topic for me to DuckDuckGo.'
			await self.bot.send_message(ctx.message.channel, msg)
			return

		lmgtfy = "https://lmddgtfy.net/?q={}".format(quote(query))
		lmgtfyT = TinyURL.tiny_url(lmgtfy)
		msg = '*{}*, you can find your answers here:\n\n{}'.format(DisplayName.name(ctx.message.author), lmgtfyT)
		# Say message
		await self.bot.send_message(ctx.message.channel, msg)


	@commands.command(pass_context=True)
	async def searchsite(self, ctx, category_name = None, *, query = None):
		"""Search corpnewt.com forums."""

		auth = self.site_auth

		if auth == None:
			await self.bot.say("Sorry this feature is not supported!")
			return

		if query == None or category_name == None:
			msg = "Usage: `{}searchsite [category] [search term]`\n\n Categories can be found at:\n\nhttps://corpnewt.com/".format(ctx.prefix)
			await self.bot.send_message(ctx.message.channel, msg)
			return

		categories_url = "https://corpnewt.com/api/categories"
		r = requests.get(categories_url, headers={'Authorization': auth})
		categories_json = json.loads(r.text)
		categories = categories_json["categories"]

		category = await self.find_category(categories, category_name)

		if category == None:
			await self.bot.say("Usage: `{}searchsite [category] [search term]`\n\n Categories can be found at:\n\nhttps://corpnewt.com/".format(ctx.prefix))
			return

		search_url = "https://corpnewt.com/api/search?term={}&in=titlesposts&categories[]={}&searchChildren=true&showAs=posts".format(query, category["cid"])
		r = requests.get(search_url, headers={'Authorization': auth})
		search_json = json.loads(r.text)
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
				result_string += '__{}__\nhttps://corpnewt.com/topic/{}\n\n'.format(post["topic"]["title"], post["topic"]["slug"])
			
		await self.bot.say(result_string)


	@commands.command(pass_context=True)
	async def convert(self, ctx, amount : int, frm = None, to = None):
		"""convert currencies"""
		convert_url = "https://www.google.com/finance/converter?a={}&from={}&to={}".format(amount,frm,to)
		r = requests.get(convert_url)
		doc = pq(r.text)
		await self.bot.say("{} {} is {}".format(amount,str(frm).upper(),str(doc('#currency_converter_result span').text())))

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

