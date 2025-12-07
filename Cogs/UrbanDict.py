import string, random, json, re, math
from   urllib.parse import quote, unquote
from   html import unescape
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
		self.href_regex = re.compile(r"<a (class=\"(?P<class>[^\"]+)\" )?href=\"(?P<url>[^\s]+)\">(?P<text>[^<]+)<\/a>")

	def wilson_lower_bound(self, p, n, z=1.96):
		if n == 0:
			return 0
		phat = p / n
		denominator = 1 + z**2 / n
		center = phat + z**2 / (2 * n)
		radical = math.sqrt(phat * (1 - phat) * z**2 / n + z**4 / (4 * n**2))
		return (center - radical) / denominator

	def _italicize(self, text):
		lines = []
		for l in text.replace("*","").split("\n"):
			l = l.strip()
			if len(l):
				try:
					vals = l.split(". ")
					if len(vals) > 1 and int(vals[0]):
						# Got a numbered element
						l = "{}. *{}*".format(
							vals[0],
							". ".join(vals[1:])
						)
				except:
					l = "*{}*".format(l)
			lines.append(l)
		return "\n".join(lines)

	def _process_html(self, html, prefix="https://www.urbandictionary.com"):
		# Locate and replace all <a (class=) href=></a> matches
		html = html.replace("\r","").replace("\n","")
		matches = self.href_regex.finditer(html)
		for m in matches:
			try:
				url = m.group("url")
				text = m.group("text")
				repl = "[{}]({})".format(
					text,
					# Quote them an extra level to ensure they don't get unquoted
					quote(prefix+url)
				)
				html = html.replace(m.group(0),repl)
			except:
				continue
		html = html.replace("<br>","\n") # Strip line break HTML tags
		# Return the resulting HTML, unquoted (we quoted our URL info above,
		# so that should remain sane)
		return unescape(unquote(html))

	async def _get_page_data(self, url):
		formatted = {}
		try:
			page_html = await DL.async_text(url, headers = {"User-Agent": self.ua})
			assert page_html
		except:
			return formatted
		# If we have html - let's scrape for info and build our data
		try:
			signature = page_html.split('data-vote-signature="')[1].split('"')[0]
		except:
			signature = None
		try:
			def_ids   = [str(x) for x in json.loads(page_html.split('data-vote-defids="')[1].split('"')[0])]
		except:
			def_ids   = []
		
		entries = page_html.split('<div class="definition ')[1:]
		for entry in entries:
			try:
				word        = entry.split('data-word="')[1].split('"')[0]
				definition  = self._process_html(entry.split('<div class="break-words meaning mb-4">')[1].split("</div>")[0].strip())
				example     = self._italicize(self._process_html(entry.split('<div class="break-words example italic mb-4">')[1].split("</div>")[0].strip()))
				cont_date   = self._process_html(entry.split('<div class="contributor font-bold">by ')[1].split("</div>")[0].strip())
				contributor = "[".join("]".join(cont_date.split("]")[:-1]).split("[")[1:])
				date        = cont_date.split(")")[-1]
				data_id     = entry.split('data-defid="')[1].split('"')[0]
				url         = entry.split('data-share-url="')[1].split('"')[0]
				formatted[data_id] = {
					"word":        word,
					"definition":  definition,
					"example":     example,
					"author":      contributor,
					"date":        date,
					"thumbs_up":   0,
					"thumbs_down": 0,
					"url":         url
				}
			except:
				continue
		if formatted and signature:
			# Try to load the votes via the api
			api_url = "https://www.urbandictionary.com/api/vote?defids={}&signature={}".format(
				",".join(def_ids) if def_ids else ",".join(list(formatted)),
				signature
			)
			try:
				json_data = await DL.async_json(api_url, headers={"User-Agent":self.ua})
				votes = json_data["votes"]
				for data_id in votes:
					if not data_id in formatted:
						continue
					try:
						formatted[data_id]["thumbs_up"]   = votes[data_id]["up"]
						formatted[data_id]["thumbs_down"] = votes[data_id]["down"]
					except:
						continue
			except:
				pass
		return formatted

	@commands.command(pass_context=True)
	async def define(self, ctx, *, word : str = None):
		"""Gives the definition of the word passed."""

		if not word: return await ctx.send('Usage: `{}define [word]`'.format(ctx.prefix))
		search_url = "https://www.urbandictionary.com/define.php?term={}".format(quote(word))
		data = await self._get_page_data(search_url)
		if not data:
			return await ctx.send("I couldn't find a definition for \"{}\"...".format(Nullify.escape_all(word)))
		# Got it - let's build our response
		words = []
		for x in data.values():
			words.append({
				"name":"{} - by {} ({:,} 👍 / {:,} 👎)".format(string.capwords(x["word"]),x["author"],x["thumbs_up"],x["thumbs_down"]),
				"value":"{}{}".format(
					x["definition"],
					"\n\n__Example(s):__\n\n{}".format(x["example"]) if x["example"] else ""
				),
				"sort": self.wilson_lower_bound(
					x["thumbs_up"],
					x["thumbs_up"]+x["thumbs_down"]
				)
			})
		# Sort the words by their "sort" value t_u / (t_u + t_d)
		# words.sort(key=lambda x:x["sort"],reverse=True)
		return await PickList.PagePicker(
			title="Results For: {}".format(string.capwords(word)),
			list=words,
			ctx=ctx,
			max=1,
			url=search_url
		).pick()

	@commands.command(pass_context=True)
	async def randefine(self, ctx):
		"""Gives a random word and its definition."""

		search_url = "https://www.urbandictionary.com/random.php"
		data = await self._get_page_data(search_url)
		if not data:
			return await ctx.send("I couldn't find any definitions...")
		x = random.choice(list(data.values()))
		words = [{
			"name":"{} - by {} ({:,} 👍 / {:,} 👎)".format(string.capwords(x["word"]),x["author"],x["thumbs_up"],x["thumbs_down"]),
			"value":"{}{}".format(
				x["definition"],
				"\n\n__Example(s):__\n\n{}".format(x["example"]) if x["example"] else ""
			),
		}]
		return await PickList.PagePicker(title="Results For: {}".format(string.capwords(x["word"])),list=words,ctx=ctx,max=1,url=x["url"]).pick()
