import asyncio, discord, json, os
from   urllib.parse import quote
from   discord.ext import commands
from   Cogs import Settings, DisplayName, Message, DL

async def setup(bot):
	# Add the bot and deps
	bot.add_cog(Discogs(bot))

class Discogs(commands.Cog):

	# Init with the bot reference
	def __init__(self, bot, auth_file: str = None):
		self.bot = bot
		self.key = bot.settings_dict.get("discogs","")
		global Utils, DisplayName
		Utils = self.bot.get_cog("Utils")
		DisplayName = self.bot.get_cog("DisplayName")

	def quote(self, query):
		# Strips all spaces, tabs, returns and replaces with + signs, then urllib quotes
		return quote(query.replace("+","%2B").replace("\t","+").replace("\r","+").replace("\n","+").replace(" ","+"),safe="+")

	async def discog(self, url, ctx):
		# Get the search results - per_page maxes at 100
		try: r = await DL.async_json(url)
		except: return await ctx.send("Something went wrong!  The API I use may be down, or maybe too many requests happened too quickly :(")
		if not r.get("results",None):
			return await ctx.send("I couldn't find anything from that search.")
		# Let's give an embed with the first result
		result = r["results"][0]
		# Gather fields
		fields = []
		for x in ("genre","style","year","type","label"):
			if not x in result:
				continue
			fields.append({"name":x.capitalize(),"value":", ".join(result[x]) if isinstance(result[x],list) else str(result[x]).capitalize(),"inline":True})
		if not len(fields):
			return await ctx.send("I didn't get enough info from that search.")
		await Message.Embed(
			color=ctx.author,
			title=result["title"],
			fields=fields,
			url="https://www.discogs.com"+result["uri"],
			image=result["cover_image"],
			footer="Powered by discogs.com"
		).send(ctx)

	@commands.command(pass_context=True)
	async def discogs(self, ctx, *, search = None):
		"""Perform a general discogs.com search. Could return albums, artits, etc.
		By default, all searches are interpreted as song title searches, but you can refine them with the following:
		
		track=Song name
		album=Album title
		artist=Artist to search for
		type=Type to search, can be one of: all, artist, release, or master
		
		For example, if you want to search for Weak and Powerless by A Perfect Circle, you could use the following format:
		
		$discogs weak and powerless album=thirteenth step artist=a perfect circle
		
		If you wanted to search only releases, you could use:
		
		$discogs track=weak and powerless album=thirteenth step artist=a perfect circle type=release"""
		
		if search == None:
			return await ctx.send("Usage: `{}discogs [search terms]`".format(ctx.prefix))
		# Split the search query by whitespace, then walk each and split by = only getting the prefix as needed
		search_dict = {
			"type":[],
			"artist":[],
			"album":[],
			"track":[]
		}
		current_key = "track"
		search_list = search.split()
		while len(search_list):
			x=search_list.pop(0)
			got_type = ""
			for a in ("type","artist","album","track"):
				if x.lower().startswith(a+"="):
					current_key = got_type = a
			if got_type:
				search_list.insert(0,x[len(got_type)+1:])
				continue
			search_dict[current_key].append(x)
		# Let's build the search url
		search_text = ""
		for x in search_dict:
			s = " ".join(search_dict[x])
			x = "title" if x == "album" else x
			if s:
				search_text += "&{}={}".format(x,self.quote(s))
		# Get the search results - per_page maxes at 100
		url = "https://api.discogs.com/database/search?{}&per_page=10&token={}".format(search_text,self.key)
		await self.discog(url,ctx)
