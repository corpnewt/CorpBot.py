import asyncio, discord, json, os
from   urllib.parse import quote
from   discord.ext import commands
from   Cogs import Settings, DisplayName, TinyURL, Message, DL, PickList

async def setup(bot):
	# Add the bot and deps
	await bot.add_cog(Search(bot))

class Search(commands.Cog):

	# Init with the bot reference
	def __init__(self, bot, auth_file: str = None):
		self.bot       = bot
		self.site_auth = bot.settings_dict.get("corpsiteauth",None)
		self.key       = bot.settings_dict.get("currency","")
		global Utils, DisplayName
		Utils = self.bot.get_cog("Utils")
		DisplayName = self.bot.get_cog("DisplayName")

	def quote(self, query):
		# Strips all spaces, tabs, returns and replaces with + signs, then urllib quotes
		return quote(query.replace("+","%2B").replace("\t","+").replace("\r","+").replace("\n","+").replace(" ","+"),safe="+")

	async def get_search(self, ctx, query, service=""):
		# Searches in the passed service
		service = "s={}&".format(service) if service else ""
		lmgtfy = "http://lmgtfy.com/?{}q={}".format(service, self.quote(query))
		try:
			lmgtfyT = await TinyURL.tiny_url(lmgtfy, self.bot)
		except Exception as e:
			print(e)
			msg = "It looks like I couldn't search for that... :("
		else:
			msg = '*{}*, you can find your answers here:\n\n<{}>'.format(DisplayName.name(ctx.message.author), lmgtfyT)
		return msg

	@commands.command()
	async def google(self, ctx, *, query = None):
		"""Get some searching done."""

		if query == None:
			msg = 'You need a topic for me to Google.'
			await ctx.channel.send(msg)
			return

		msg = await self.get_search(ctx, query)
		# Say message
		await ctx.channel.send(msg)

	@commands.command()
	async def bing(self, ctx, *, query = None):
		"""Get some uh... more searching done."""

		if query == None:
			msg = 'You need a topic for me to Bing.'
			await ctx.channel.send(msg)
			return

		msg = await self.get_search(ctx, query,"b")
		# Say message
		await ctx.channel.send(msg)

	@commands.command()
	async def duck(self, ctx, *, query = None):
		"""Duck Duck... GOOSE."""

		if query == None:
			msg = 'You need a topic for me to DuckDuckGo.'
			await ctx.channel.send(msg)
			return

		msg = await self.get_search(ctx, query,"d")
		# Say message
		await ctx.channel.send(msg)

	@commands.command()
	async def yahoo(self, ctx, *, query = None):
		"""Let Yahoo! answer your questions."""

		if query == None:
			msg = 'You need a topic for me to Yahoo.'
			await ctx.channel.send(msg)
			return

		msg = await self.get_search(ctx, query,"y")
		# Say message
		await ctx.channel.send(msg)

	@commands.command()
	async def aol(self, ctx, *, query = None):
		"""The OG search engine."""

		if query == None:
			msg = 'You need a topic for me to AOL.'
			await ctx.channel.send(msg)
			return

		msg = await self.get_search(ctx, query,"a")
		# Say message
		await ctx.channel.send(msg)

	@commands.command()
	async def ask(self, ctx, *, query = None):
		"""Jeeves, please answer these questions."""

		if query == None:
			msg = 'You need a topic for me to Ask Jeeves.'
			await ctx.channel.send(msg)
			return

		msg = await self.get_search(ctx, query,"k")
		# Say message
		await ctx.channel.send(msg)


	@commands.command()
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


	async def _get_api_status(self):
		try:
			api_status_html = await DL.async_text("https://www.currencyconverterapi.com/server-status")
			api_status = api_status_html.split("<td>Free API</td>")[-1].split(">")[1].split("<")[0]
		except:
			api_status = "UNKNOWN"
		return api_status

	@commands.command()
	async def convert(self, ctx, *, amount = None, frm = None, to = None):
		"""Convert currencies.  If run with no values, the script will print a list of available currencies."""
		
		# Get the list of currencies
		try: r = await DL.async_json("https://free.currconv.com/api/v7/currencies?apiKey="+self.key)
		except:
			api_status = await self._get_api_status()
			return await ctx.send("Something went wrong getting that conversion :(\nThe current status of the API I use is: `{}`".format(api_status))
		
		if amount == None:
			# Gather our currency list
			curr_list = []
			for l in r.get("results",{}):
				# l is the key - let's format a list
				curr_list.append("{} - {}".format(r["results"][l]["id"], r["results"][l]["currencyName"]))
			if len(curr_list):
				curr_list = sorted(curr_list)
				return await PickList.PagePicker(
					title="Currency List",
					description="\n".join(curr_list),
					d_header="```\n",
					d_footer="```",
					color=ctx.author,
					ctx=ctx
				).pick()
		
		# Set up our args
		num = frm = to = None
		vals = amount.split()
		last = None
		conv = []
		for val in vals:
			if all(x in "+-0123456789." for x in val if not x == ",") and num is None:
				# Got a number
				try: num = float(val.replace(",",""))
				except: pass # Not a valid number
			elif val.lower() in ["from","to"]:
				last = True if val.lower() == "to" else False
			elif val.upper() in r.get("results",{}):
				# Should have a valid type - let's add it and the type to the list
				conv.append([last,val])
				last = None
			if len(conv) >= 2 and num != None: break # We have enough info - bail
		if num is None: num = 1
		if len(conv) < 2:
			return await ctx.send("Usage: `{}convert [amount] [from_currency] (to) [to_currency]` - Type `{}convert` for a list of valid currencies.".format(ctx.prefix,ctx.prefix))
		if num == 0:
			return await ctx.send("Anything times 0 is 0, silly.")
		# Normalize our to/from prioritizing the end arg
		conv[0][0] = False if conv[1][0] == True else True if conv[1][0] == False else conv[0][0] if conv[0][0] != None else False # wut
		conv[1][0] = conv[0][0]^True # Make sure it's reversed
		frm = conv[0][1] if conv[0][0] == False else conv[1][1]
		to  = conv[0][1] if conv[0][0] == True else conv[1][1]

		# Verify we have a proper from/to type
		if not frm.upper() in r.get("results",{}):
			return await ctx.send("Invalid from currency!")
		if not to.upper() in r.get("results",{}):
			return await ctx.send("Invalid to currency!")

		# At this point, we should be able to convert
		try: o = await DL.async_json("http://free.currconv.com/api/v7/convert?q={}_{}&compact=ultra&apiKey={}".format(frm.upper(), to.upper(), self.key))
		except:
			api_status = await self._get_api_status()
			return await ctx.send("Something went wrong getting that conversion :(\nThe current status of the API I use is: `{}`".format(api_status))

		if not o:
			return await ctx.send("Whoops!  I couldn't get that :(")
		
		# Format the numbers
		val = float(o[list(o)[0]])
		# Calculate the results
		inamnt  = "{:,f}".format(num).rstrip("0").rstrip(".")
		output = "{:,f}".format(num*val).rstrip("0").rstrip(".")
		await ctx.send("{} {} is {} {}".format(inamnt,frm.upper(), output, to.upper()))

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

