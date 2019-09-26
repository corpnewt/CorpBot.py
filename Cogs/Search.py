import asyncio, discord, json, os
from   urllib.parse import quote
from   discord.ext import commands
from   Cogs import Settings, DisplayName, TinyURL, Message, DL

def setup(bot):
	# Add the bot and deps
	auth = "corpSiteAuth.txt"
	bot.add_cog(Search(bot, auth))

class Search(commands.Cog):

	# Init with the bot reference
	def __init__(self, bot, auth_file: str = None):
		self.bot = bot
		self.site_auth = None
		if os.path.isfile(auth_file):
		        with open(auth_file, 'r') as f:
		                self.site_auth = f.read()
		self.key = "3a337666060f628a0a91"

	def quote(self, query):
		# Strips all spaces, tabs, returns and replaces with + signs, then urllib quotes
		return quote(query.replace("+","%2B").replace("\t","+").replace("\r","+").replace("\n","+").replace(" ","+"))

	async def get_search(self, ctx, query, service=""):
		# Searches in the passed service
		service = "s={}&".format(service) if service else ""
		lmgtfy = "http://lmgtfy.com/?{}q={}".format(service, self.quote(query))
		try:
			lmgtfyT = await TinyURL.tiny_url(lmgtfy)
		except:
			msg = "It looks like I couldn't search for that... :("
		else:
			msg = '*{}*, you can find your answers here:\n\n<{}>'.format(DisplayName.name(ctx.message.author), lmgtfyT)
		return msg

	@commands.command(pass_context=True)
	async def google(self, ctx, *, query = None):
		"""Get some searching done."""

		if query == None:
			msg = 'You need a topic for me to Google.'
			await ctx.channel.send(msg)
			return

		msg = await self.get_search(ctx, query)
		# Say message
		await ctx.channel.send(msg)

	@commands.command(pass_context=True)
	async def bing(self, ctx, *, query = None):
		"""Get some uh... more searching done."""

		if query == None:
			msg = 'You need a topic for me to Bing.'
			await ctx.channel.send(msg)
			return

		msg = await self.get_search(ctx, query,"b")
		# Say message
		await ctx.channel.send(msg)

	@commands.command(pass_context=True)
	async def duck(self, ctx, *, query = None):
		"""Duck Duck... GOOSE."""

		if query == None:
			msg = 'You need a topic for me to DuckDuckGo.'
			await ctx.channel.send(msg)
			return

		msg = await self.get_search(ctx, query,"d")
		# Say message
		await ctx.channel.send(msg)

	@commands.command(pass_context=True)
	async def yahoo(self, ctx, *, query = None):
		"""Let Yahoo! answer your questions."""

		if query == None:
			msg = 'You need a topic for me to Yahoo.'
			await ctx.channel.send(msg)
			return

		msg = await self.get_search(ctx, query,"y")
		# Say message
		await ctx.channel.send(msg)

	@commands.command(pass_context=True)
	async def aol(self, ctx, *, query = None):
		"""The OG search engine."""

		if query == None:
			msg = 'You need a topic for me to AOL.'
			await ctx.channel.send(msg)
			return

		msg = await self.get_search(ctx, query,"a")
		# Say message
		await ctx.channel.send(msg)

	@commands.command(pass_context=True)
	async def ask(self, ctx, *, query = None):
		"""Jeeves, please answer these questions."""

		if query == None:
			msg = 'You need a topic for me to Ask Jeeves.'
			await ctx.channel.send(msg)
			return

		msg = await self.get_search(ctx, query,"k")
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
	async def convert(self, ctx, *, amount = None, frm = None, to = None):
		"""Convert currencies.  If run with no values, the script will print a list of available currencies."""
		
		# Get the list of currencies
		try: r = await DL.async_json("https://free.currconv.com/api/v7/currencies?apiKey="+self.key)
		except: return await ctx.send("Something went wrong!  The API I use may be down :(")
		
		if amount == None:
			# Gather our currency list
			curr_list = []
			for l in r.get("results",{}):
				# l is the key - let's format a list
				curr_list.append("{} - {}".format(r["results"][l]["id"], r["results"][l]["currencyName"]))
			if len(curr_list):
				curr_list = sorted(curr_list)
				return await Message.EmbedText(
					title="Currency List",
					description="\n".join(curr_list),
					desc_head="```\n",
					desc_foot="```",
					pm_after=0,
					color=ctx.author
				).send(ctx)
		
		# Split up our args
		vals = amount.split()
		try:
			# Walk the values and bail if formatted wrong
			vals = [x for x in vals if not x.lower() in ["to","from"]]
			amount = float(vals[0])
			frm    = vals[1]
			to     = vals[2]
		except:
			# Something went wrong! Print the usage.
			return await ctx.send("Usage: `{}convert [amount] [from_currency] [to_currency]` - or just `{}convert` for a list of currencies.".format(ctx.prefix,ctx.prefix))
		if amount <= 0:
			return await ctx.send("Anything times 0 is 0, silly.")

		# Verify we have a proper from/to type
		if not frm.upper() in r.get("results",{}):
			return await ctx.send("Invalid from currency!")
		if not to.upper() in r.get("results",{}):
			return await ctx.send("Invalid to currency!")

		# At this point, we should be able to convert
		# o = await DL.async_json("http://free.currencyconverterapi.com/api/v6/convert?q={}_{}&compact=ultra&apiKey={}".format(frm.upper(), to.upper(), self.key))
		try: o = await DL.async_json("http://free.currconv.com/api/v7/convert?q={}_{}&compact=ultra&apiKey={}".format(frm.upper(), to.upper(), self.key))
		except: return await ctx.send("Something went wrong getting that conversion.  The API I use may be down :(")

		if not o:
			return await ctx.send("Whoops!  I couldn't get that :(")
		
		# Format the numbers
		val = float(o[list(o)[0]])
		# Calculate the results
		inamnt  = "{:,f}".format(amount).rstrip("0").rstrip(".")
		output = "{:,f}".format(amount*val).rstrip("0").rstrip(".")
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

