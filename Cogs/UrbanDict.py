import string, random, json, re
from   urllib.parse import quote
from   discord.ext import commands
from   Cogs import Settings, PickList, Nullify, DL

def setup(bot):
	# Add the bot and deps
	settings = bot.get_cog("Settings")
	bot.add_cog(UrbanDict(bot, settings))

# This module grabs Urban Dictionary definitions

class UrbanDict(commands.Cog):

	# Init with the bot reference, and a reference to the settings var and xp var
	def __init__(self, bot, settings):
		self.bot = bot
		self.settings = settings
		self.ua = 'CorpNewt DeepThoughtBot'
		self.regex = re.compile(r"\[[^\[\]]+\]")

	async def _get_json_list(self, url):
		try: json_data = await DL.async_json(url, headers = {'User-agent': self.ua})
		except: json_data = {}
		return json_data.get("list",[])

	def _format_definition(self, entry):
		value = entry.get("definition","Unknown definition")
		if entry.get("example"):
			lines = ["*{}*".format(x.strip()) if len(x.strip()) else "" for x in entry["example"].replace("*","").split("\n")]
			value += "\n\n__Example(s):__\n\n{}".format("\n".join(lines))
		for match in re.finditer(self.regex, value):
			match_url = "https://www.urbandictionary.com/define.php?term={}".format(quote(match.group(0)[1:-1]))
			value = value.replace(match.group(0),"__{}({})__".format(match.group(0),match_url))
		return value

	@commands.command(pass_context=True)
	async def define(self, ctx, *, word : str = None):
		"""Gives the definition of the word passed."""

		if not word: return await ctx.send('Usage: `{}define [word]`'.format(ctx.prefix))
		theJSON = await self._get_json_list("http://api.urbandictionary.com/v0/define?term={}".format(quote(word)))
		if not theJSON: return await ctx.send("I couldn't find a definition for \"{}\"...".format(Nullify.escape_all(word)))
		# Got it - let's build our response
		words = []
		for x in theJSON:
			words.append({
				"name":"{} - by {} ({} 👍 / {} 👎)".format(string.capwords(x["word"]),x["author"],x["thumbs_up"],x["thumbs_down"]),
				"value":self._format_definition(x),
				"sort": float(x["thumbs_up"])/(float(x["thumbs_up"])+float(x["thumbs_down"]))
			})
		# Sort the words by their "sort" value t_u / (t_u + t_d)
		words.sort(key=lambda x:x["sort"],reverse=True)
		return await PickList.PagePicker(title="Results For: {}".format(string.capwords(word)),list=words,ctx=ctx,max=1,url=theJSON[0]["permalink"]).pick()

	@commands.command(pass_context=True)
	async def randefine(self, ctx):
		"""Gives a random word and its definition."""

		theJSON = await self._get_json_list("http://api.urbandictionary.com/v0/random")
		if not theJSON: return await ctx.send("I couldn't find any definitions...")
		# Got it - let's build our response
		x = random.choice(theJSON)
		words = [{
			"name":"{} - by {} ({} 👍 / {} 👎)".format(string.capwords(x["word"]),x["author"],x["thumbs_up"],x["thumbs_down"]),
			"value":self._format_definition(x)
		}]
		return await PickList.PagePicker(title="Results For: {}".format(string.capwords(x["word"])),list=words,ctx=ctx,max=1,url=x["permalink"]).pick()
