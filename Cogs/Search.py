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
		global Utils, DisplayName
		Utils = self.bot.get_cog("Utils")
		DisplayName = self.bot.get_cog("DisplayName")

	def _is_submodule(self, parent, child):
		return parent == child or child.startswith(parent + ".")

	@commands.Cog.listener()
	async def on_loaded_extension(self, ext):
		if not self._is_submodule(ext.__name__, self.__module__):
			return
		# Maybe we'll warn about this in the future?  Redundancy is nice,
		# but not sure if the warning is needed.
		'''if not self.bot.settings_dict.get("currency"):
			if not self.bot.settings_dict.get("suppress_disabled_warnings"):
				print("* Fallback Currency Converter API key is missing")
				print("   ('currency' in settings_dict.json)")
				print("* You can get a free currency converter API key by signing up at:")
				print("   https://free.currencyconverterapi.com/free-api-key\n")'''

	def quote(self, query):
		# Strips all spaces, tabs, returns and replaces with + signs, then urllib quotes
		return quote(query.replace("+","%2B").replace("\t","+").replace("\r","+").replace("\n","+").replace(" ","+"),safe="+")

	async def get_search(self, ctx, query, service=""):
		# Searches in the passed service
		service = "s={}&".format(service) if service else ""
		lmgtfy = "https://lmgtfy2.com/?{}q={}".format(service, self.quote(query))
		try:
			lmgtfyT = await TinyURL.tiny_url(lmgtfy, self.bot)
		except Exception as e:
			print(e)
			msg = "It looks like I couldn't search for that... :("
		else:
			msg = '*{}*, you can find your answers here:\n<{}>'.format(DisplayName.name(ctx.message.author), lmgtfyT)
		return msg

	@commands.command()
	async def google(self, ctx, *, query = None):
		"""Get some searching done."""

		if query is None:
			return await ctx.send("You need a topic for me to Google.")
		await ctx.send(await self.get_search(ctx,query))

	@commands.command()
	async def bing(self, ctx, *, query = None):
		"""Get some uh... more searching done."""

		if query is None:
			return await ctx.send("You need a topic for me to Bing.")
		await ctx.send(await self.get_search(ctx,query,"b"))

	@commands.command()
	async def duck(self, ctx, *, query = None):
		"""Duck Duck... GOOSE."""

		if query is None:
			return await ctx.send("You need a topic for me to DuckDuckGo.")
		await ctx.send(await self.get_search(ctx,query,"d"))

	@commands.command()
	async def yahoo(self, ctx, *, query = None):
		"""Let Yahoo! answer your questions."""

		if query is None:
			return await ctx.send("You need a topic for me to Yahoo.")
		await ctx.send(await self.get_search(ctx,query,"y"))

	@commands.command()
	async def aol(self, ctx, *, query = None):
		"""The OG search engine."""

		if query is None:
			return await ctx.send("You need a topic for me to AOL.")
		await ctx.send(await self.get_search(ctx,query,"a"))

	@commands.command()
	async def ask(self, ctx, *, query = None):
		"""Jeeves, please answer these questions."""

		if query is None:
			return await ctx.send("You need a topic for me to Ask Jeeves.")
		await ctx.send(await self.get_search(ctx,query,"k"))

	async def _get_currency_list_fcc(self):
		# Get the list of currencies
		r = None
		try:
			r = await DL.async_json("https://free.currconv.com/api/v7/currencies?apiKey={}".format(
				self.bot.settings_dict.get("currency")
			))
		except: pass
		return r

	async def _get_currency_list_ea(self):
		# Get the list of currencies - https://github.com/fawazahmed0/exchange-api
		r = None
		try:
			r = await DL.async_json("https://cdn.jsdelivr.net/npm/@fawazahmed0/currency-api@latest/v1/currencies.min.json")
			assert r
		except:
			# Fallback URL
			try: r = await DL.async_json("https://latest.currency-api.pages.dev/v1/currencies.min.json")
			except: pass
		return r

	async def _get_currency_list(self):
		name_to_id = {}
		id_to_name = {}
		r = await self._get_currency_list_ea()
		if r:
			# Got the exchange-api
			for i in r:
				c_id = i.upper()
				id_to_name[c_id] = r[i]
				name_to_id[r[i]] = c_id
		elif self.bot.settings_dict.get("currency"):
			r = await self._get_currency_list_fcc()
			if r:
				# Got the freecurrencyconverter api
				for l in r.get("results",{}):
					if not all((x in r["results"][l] for x in ("id","currencyName"))):
						continue # Incomplete
					name = string.capwords(r["results"][l]["currencyName"])
					c_id = r["results"][l]["id"].upper()
					name_to_id[name] = c_id
					id_to_name[c_id] = name
		return (name_to_id,id_to_name)

	async def _convert(self, frm, to):
		r = val = None
		try:
			r = await DL.async_json("https://cdn.jsdelivr.net/npm/@fawazahmed0/currency-api@latest/v1/currencies/{}.min.json".format(
				frm.lower()
			))
			assert r
		except:
			# Fallback URL
			try: r = await DL.async_json("https://latest.currency-api.pages.dev/v1/currencies/{}.min.json".format(frm.lower()))
			except: pass
		if r:
			# Got it via the exchange-api
			val = r.get(frm.lower(),{}).get(to.lower())
		elif self.bot.settings_dict.get("currency"):
			# Try the freecurrencyconverter api
			try:
				r = await DL.async_json("http://free.currconv.com/api/v7/convert?q={}_{}&compact=ultra&apiKey={}".format(
					frm.upper(),
					to.upper(),
					self.bot.settings_dict["currency"]
				))
				val = float(r[list(r)[0]])
			except: pass
		return val

	@commands.command(aliases=["listcurr","lcurr","currl"])
	async def currlist(self, ctx, *, search = None):
		"""List currencies for the convert command."""
		# Get our list of currencies first
		name_to_id,id_to_name = await self._get_currency_list()
		if not name_to_id:
			return await ctx.send("Something went wrong getting the currency list :(")
		# Get the longest currency abbreviation for padding purposes
		pad_to = len(max(id_to_name,key=len))
		# Check if we're searching
		if search:
			# Get our fuzzy matched results
			id_search   = FuzzySearch.search(search.lower(), id_to_name)
			name_search = FuzzySearch.search(search.lower(), name_to_id)
			full_match  = next((x["Item"] for x in id_search+name_search if x.get("Ratio") == 1),None)
			if full_match: # Got an exact match - build an embed
				if full_match in id_to_name:
					name,code,t = id_to_name[full_match],full_match,"Currency Code"
				else:
					name,code,t = full_match,name_to_id[full_match],"Currency Name"
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
					name_to_id[x["Item"]].rjust(pad_to),
					x["Item"]
				) for x in name_search])
				fields.append({"name":"Close Currency Name Matches:","value":curr_mess})
			if len(id_search):
				curr_mess = "\n".join(["└─ `{}` - {}".format(
					x["Item"].rjust(pad_to),
					id_to_name[x["Item"]]
				) for x in id_search])
				fields.append({"name":"Close Currency Code Matches:","value":curr_mess})
			return await Message.Embed(title="Search Results For \"{}\"".format(search),description=desc,fields=fields).send(ctx)
		# We're not searching - list them all
		curr_list = ["`{}` - {}".format(i.rjust(pad_to),string.capwords(id_to_name[i])) for i in sorted(id_to_name)]
		return await PickList.PagePicker(
			title="Currency List",
			description="\n".join(curr_list),
			color=ctx.author,
			ctx=ctx
		).pick()

	@commands.command(aliases=["con","conv","currency","curr"])
	async def convert(self, ctx, *, amount = None, frm = None, to = None):
		"""Convert currencies.  If run with no values, the script will print a list of available currencies."""
		
		if amount is None: # Invoke our currency list
			return await ctx.invoke(self.currlist,search=amount)
		
		# Get the list of currencies
		name_to_id,id_to_name = await self._get_currency_list()
		if not name_to_id:
			return await ctx.send("Something went wrong getting the currency list :(")

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
			elif val.upper() in id_to_name:
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
		if not frm.upper() in id_to_name:
			return await ctx.send("Invalid `[from_currency]`!")
		if not to.upper() in id_to_name:
			return await ctx.send("Invalid `[to_currency]`!")

		# At this point, we should be able to convert
		val = await self._convert(frm,to)
		if val is None:
			return await ctx.send("Whoops!  I couldn't get that conversion :(")
		
		# Calculate the results
		inamnt = "{:,f}".format(num).rstrip("0").rstrip(".")
		output = "{:,f}".format(num*val).rstrip("0").rstrip(".")
		await ctx.send("{} {} is {} {}".format(inamnt,frm.upper(), output, to.upper()))
