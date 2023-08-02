import asyncio, discord, json, os, string
from   urllib.parse import quote
from   discord.ext import commands
from   Cogs import Settings, DisplayName, TinyURL, Message, DL, PickList, FuzzySearch

def setup(bot):
	# Add the bot and deps
	bot.add_cog(Search(bot))

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

	@commands.command()
	async def google(self, ctx, *, query = None):
		"""Get some searching done."""

		if query is None:
			return await ctx.send("You need a topic for me to Google.")
		lmgtfy  = "https://letmegooglethat.com/?q={}".format(self.quote(query))
		try:
			msg = "*{}*, you can find your answers here:\n<{}>".format(
				DisplayName.name(ctx.author),
				await TinyURL.tiny_url(lmgtfy,self.bot)
			)
		except:
			msg = "It looks like I couldn't search for that... :("
		await ctx.send(msg)

	@commands.command()
	async def bing(self, ctx, *, query = None):
		"""Get some uh... more searching done."""

		if query is None:
			return await ctx.send("You need a topic for me to Bing.")
		lmgtfy  = "https://letmebingthatforyou.com/BingThis/{}".format(quote(query))
		try:
			msg = "*{}*, you can find your answers here:\n<{}>".format(
				DisplayName.name(ctx.author),
				await TinyURL.tiny_url(lmgtfy,self.bot)
			)
		except:
			msg = "It looks like I couldn't search for that... :("
		await ctx.send(msg)

	@commands.command()
	async def duck(self, ctx, *, query = None):
		"""Duck Duck... GOOSE."""

		if query is None:
			return await ctx.send("You need a topic for me to DuckDuckGo.")
		lmgtfy  = "https://lmddgtfy.net/?q={}".format(quote(query))
		try:
			msg = "*{}*, you can find your answers here:\n<{}>".format(
				DisplayName.name(ctx.author),
				await TinyURL.tiny_url(lmgtfy,self.bot)
			)
		except:
			msg = "It looks like I couldn't search for that... :("
		await ctx.send(msg)

	'''async def get_search(self, ctx, query, service=""):
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
	async def yahoo(self, ctx, *, query = None):
		"""Let Yahoo! answer your questions."""

		if query is None:
			msg = 'You need a topic for me to Yahoo.'
			return await ctx.send(msg)

		msg = await self.get_search(ctx, query,"y")
		# Say message
		await ctx.send(msg)

	@commands.command()
	async def aol(self, ctx, *, query = None):
		"""The OG search engine."""

		if query is None:
			msg = 'You need a topic for me to AOL.'
			return await ctx.send(msg)

		msg = await self.get_search(ctx, query,"a")
		# Say message
		await ctx.send(msg)

	@commands.command()
	async def ask(self, ctx, *, query = None):
		"""Jeeves, please answer these questions."""

		if query is None:
			msg = 'You need a topic for me to Ask Jeeves.'
			return await ctx.send(msg)

		msg = await self.get_search(ctx, query,"k")
		# Say message
		await ctx.send(msg)


	@commands.command()
	async def searchsite(self, ctx, category_name = None, *, query = None):
		"""Search corpnewt.com forums."""

		auth = self.site_auth

		if auth is None:
			return await ctx.send("Sorry this feature is not supported!")

		if query is None or category_name is None:
			msg = "Usage: `{}searchsite [category] [search term]`\n\n Categories can be found at:\n\nhttps://corpnewt.com/".format(ctx.prefix)
			return await ctx.send(msg)

		categories_url = "https://corpnewt.com/api/categories"
		categories_json = await DL.async_json(categories_url, headers={'Authorization': auth})
		categories = categories_json["categories"]

		category = await self.find_category(categories, category_name)

		if category is None:
			return await ctx.send("Usage: `{}searchsite [category] [search term]`\n\n Categories can be found at:\n\nhttps://corpnewt.com/".format(ctx.prefix))

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
			
		await ctx.send(result_string)


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
		
		return result_category'''


	async def _get_api_status(self):
		try:
			api_status_html = await DL.async_text("https://www.currencyconverterapi.com/server-status")
			api_status = api_status_html.split("<td>Free API</td>")[-1].split(">")[1].split("<")[0]
		except:
			api_status = "UNKNOWN"
		return api_status

	async def _get_currency_list(self):
		# Get the list of currencies
		api_status = "UNKNOWN"
		r = None
		try: r = await DL.async_json("https://free.currconv.com/api/v7/currencies?apiKey="+self.key)
		except:
			api_status = await self._get_api_status()
		return (r,api_status)

	@commands.command(aliases=["listcurr","lcurr","currl"])
	async def currlist(self, ctx, *, search = None):
		"""List currencies for the convert command."""
		# Get the list of currencies
		r,api_status = await self._get_currency_list()
		if not r: return await ctx.send("Something went wrong getting the currency list :(\nThe current status of the API I use is: `{}`".format(api_status))
		# Gather our currency list
		name_to_id = {}
		id_to_name = {}
		for l in r.get("results",{}):
			if not all((x in r["results"][l] for x in ("id","currencyName"))): continue # Incomplete
			name_to_id[r["results"][l]["currencyName"]] = r["results"][l]["id"]
			id_to_name[r["results"][l]["id"]] = r["results"][l]["currencyName"]
		if not name_to_id:return await ctx.send("Something went wrong getting the currency list :(")
		# Check if we're searching
		if search:
			# Get our fuzzy matched results
			id_search   = FuzzySearch.search(search.lower(), id_to_name)
			name_search = FuzzySearch.search(search.lower(), name_to_id)
			full_match  = next((x["Item"] for x in id_search+name_search if x.get("Ratio") == 1),None)
			if full_match: # Got an exact match - build an embed
				if full_match in id_to_name:
					name,code,t = string.capwords(id_to_name[full_match]),full_match,"Currency Code"
				else:
					name,code,t = string.capwords(full_match),name_to_id[full_match],"Currency Name"
				return await Message.Embed(
					title="Search Results For \"{}\"".format(search),
					description="Exact {} Match:\n\n`{}` - {}".format(t,code,name),
					color=ctx.author,
					).send(ctx)
			# Got close matches
			desc = "No exact currency matches for \"{}\"".format(search)
			fields = []
			if len(name_search):
				curr_mess = "\n".join(["└─ `{}` - {}".format(
					name_to_id[x["Item"]],
					string.capwords(x["Item"])
				) for x in name_search])
				fields.append({"name":"Close Currency Name Matches:","value":curr_mess})
			if len(id_search):
				curr_mess = "\n".join(["└─ `{}` - {}".format(
					x["Item"],
					string.capwords(id_to_name[x["Item"]])
				) for x in id_search])
				fields.append({"name":"Close Currency Code Matches:","value":curr_mess})
			return await Message.Embed(title="Search Results For \"{}\"".format(search),description=desc,fields=fields).send(ctx)
		# We're not searching - list them all
		curr_list = sorted(["`{}` - {}".format(i,string.capwords(id_to_name[i])) for i in id_to_name])
		return await PickList.PagePicker(
			title="Currency List",
			description="\n".join(curr_list),
			color=ctx.author,
			ctx=ctx
		).pick()

	@commands.command()
	async def convert(self, ctx, *, amount = None, frm = None, to = None):
		"""Convert currencies.  If run with no values, the script will print a list of available currencies."""
		
		if amount is None: # Invoke our currency list
			return await ctx.invoke(self.currlist,search=amount)

		# Get the list of currencies
		r,api_status = await self._get_currency_list()
		if not r: return await ctx.send("Something went wrong getting that conversion :(\nThe current status of the API I use is: `{}`".format(api_status))
		
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
