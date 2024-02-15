import string, json, re
from   urllib.parse import quote
from   discord.ext import commands
from   Cogs import Settings, PickList, DL

def setup(bot):
	# Add the bot and deps
	settings = bot.get_cog("Settings")
	bot.add_cog(Dictionary(bot, settings))

# This module grabs Dictionary definitions

class Dictionary(commands.Cog):

	# Init with the bot reference, and a reference to the settings var and xp var
	def __init__(self, bot, settings):
		self.bot = bot
		self.settings = settings

	@commands.command(aliases=["dict"])
	async def dictionary(self, ctx, *, word : str = None):
		"""Queries dictionaryapi.dev for the definition of the word passed."""

		if not word: return await ctx.send('Usage: `{}dictionary [word]`'.format(ctx.prefix))
		# Try to query the api
		try:
			response = await DL.async_json("https://api.dictionaryapi.dev/api/v2/entries/en/{}".format(quote(word)))
			if response and isinstance(response,list):
				response = response[0] # Get the first
			assert isinstance(response,dict)
		except:
			response = []
		# Make sure we got at least something
		if not "word" in response:
			return await ctx.send("I couldn't find anything for that query :(")
		fields = []
		# Walk the phonetics - retain all different entries, and
		# link audio where applicable
		if response.get("phonetics"):
			phonetics = {}
			for p in response["phonetics"]:
				if not "text" in p: continue
				# Let's prioritize phonetics with audio - and prioritize US audio if
				# present.
				if not p["text"] in phonetics:
					phonetics[p["text"]] = current = ""
				else:
					current = phonetics[p["text"]]
				if p.get("audio"):
					if not current or p["audio"].split(".")[-2].lower().endswith("-us"):
						phonetics[p["text"]] = p["audio"]
			if phonetics:
				# Format based on our dict
				p_text = ""
				for p,v in phonetics.items():
					if not v: continue # Only include those with audio
					p_text += "[{}]({})\n".format(p,v)
				if p_text:
					fields.append({
						"name":"Phonetics",
						"value":p_text.strip()
					})
		# Walk the meanings and store them by part of speech
		if response.get("meanings"):
			for m in response["meanings"]:
				if not all((x in m for x in ("partOfSpeech","definitions"))):
					continue
				n = string.capwords(m["partOfSpeech"])
				d_text = ""
				for i,d in enumerate(m["definitions"],start=1):
					d_text += "{}. {}\n".format(i,d["definition"].strip())
				if d_text:
					fields.append({
						"name":n,
						"value":d_text.strip()
					})
		# Display our embed
		await PickList.PagePicker(
			title="Definition for \"{}\"".format(string.capwords(response["word"])),
			list=fields,
			ctx=ctx,
			url=response.get("sourceUrls",[None])[0],
			footer="Powered by https://dictionaryapi.dev"
		).pick()
