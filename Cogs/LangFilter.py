import asyncio, discord, random, os
import regex as re
from   datetime import datetime
from   discord.ext import commands
from   Cogs import Utils, DisplayName, Message, Nullify, PickList

def setup(bot):
	# Add the bot and deps
	settings = bot.get_cog("Settings")
	bot.add_cog(LangFilter(bot, settings))

class ProfanitiesFilter(object):
	def __init__(self, filterlist, ignore_case=True, replacements="$@%-?!", 
				complete=True, inside_words=False):
		"""
		Inits the profanity filter.

		filterlist -- a list of regular expressions that
		matches words that are forbidden
		ignore_case -- ignore capitalization
		replacements -- string with characters to replace the forbidden word
		complete -- completely remove the word or keep the first and last char?
		inside_words -- search inside other words?
		
		Code from here https://stackoverflow.com/a/3533322
		
		Credit to leoluk

		"""

		self.badwords = filterlist
		self.ignore_case = ignore_case
		self.replacements = replacements
		self.complete = complete
		self.inside_words = inside_words

	def _make_clean_word(self, length):
		"""
		Generates a random replacement string of a given length
		using the chars in self.replacements.

		"""
		return ''.join([random.choice(self.replacements) for i in
				range(length)])

	def __replacer(self, match):
		value = match.group()
		if self.complete:
			return self._make_clean_word(len(value))
		else:
			return value[0]+self._make_clean_word(len(value)-2)+value[-1]

	def clean(self, text):
		"""Cleans a string from profanity."""

		regexp_insidewords = {
			True: r'(%s)',
			False: r'\b(%s)\b',
			}

		regexp = (regexp_insidewords[self.inside_words] % 
				'|'.join(self.badwords))

		try:
			r = re.compile(regexp, re.IGNORECASE if self.ignore_case else 0)
		except:
			return text

		return r.sub(self.__replacer, text, timeout=0.025)


'''if __name__ == '__main__':

	f = ProfanitiesFilter(['bad', 'un\\w+'], replacements="-")    
	example = "I am doing bad ungood badlike things."

	print f.clean(example)
	# Returns "I am doing --- ------ badlike things."

	f.inside_words = True    
	print f.clean(example)
	# Returns "I am doing --- ------ ---like things."

	f.complete = False    
	print f.clean(example)
	# Returns "I am doing b-d u----d b-dlike things."'''
	
class LangFilter(commands.Cog):

	# Init with the bot reference, and a reference to the settings var
	def __init__(self, bot, settings, replacements = "@#$%&"):
		self.bot = bot
		self.settings = settings
		self.replacements = replacements
		global Utils, DisplayName
		Utils = self.bot.get_cog("Utils")
		DisplayName = self.bot.get_cog("DisplayName")
		
		
	async def test_message(self, message):
		# Implemented to bypass having message called twice
		return { "Ignore" : False, "Delete" : False }


	async def message_edit(self, before, message):
		return await self.message(message)


	async def message(self, message):
		# Check the message and see if we should allow it - always yes.
		word_list = self.settings.getServerStat(message.guild, "FilteredWords")
		if not len(word_list):
			# No filter
			return { "Ignore" : False, "Delete" : False }
	
		# Check for admin/bot-admin
		ctx = await self.bot.get_context(message)
		if Utils.is_bot_admin(ctx):
			return { "Ignore" : False, "Delete" : False }
		
		f = ProfanitiesFilter(word_list, replacements=self.replacements)
		f.ignore_case = True
		f.inside_words = True
		
		new_msg = f.clean(message.content)
		if not new_msg == message.content:
			# Something changed
			new_msg = "Hey *{}*, based on my calculations, here's a cleaner version of that messsage:\n\n".format(DisplayName.name(message.author)) + Nullify.resolve_mentions(new_msg,ctx=ctx)
			await message.channel.send(new_msg)
			return { "Ignore" : False, "Delete" : True }
		return { "Ignore" : False, "Delete" : False }
		
	
	@commands.command(pass_context=True)
	async def addfilter(self, ctx, *, regex_filter = None):
		"""Adds the passed regex pattern to the language filter (bot-admin only)."""
		if not await Utils.is_bot_admin_reply(ctx): return
			
		if regex_filter is None:
			msg = 'Usage: `{}addfilter regex_filter`'.format(ctx.prefix)
			return await ctx.send(msg)

		try:
			re.compile(regex_filter)
		except Exception as e:
			return await ctx.send(Nullify.escape_all(str(e)))
			
		serverOptions = self.settings.getServerStat(ctx.guild, "FilteredWords", [])
		if regex_filter in serverOptions:
			return await ctx.send("That regex pattern already exists in language filter!")
		
		serverOptions.append(regex_filter)

		self.settings.setServerStat(ctx.guild, "FilteredWords", serverOptions)
			
		return await ctx.send("Regex pattern added to language filter!")
			
			
	@commands.command(pass_context=True)
	async def remfilter(self, ctx, *, regex_filter_number = None):
		"""Removes the regex filter at the passed number from the language filter (bot-admin only)."""
		if not await Utils.is_bot_admin_reply(ctx): return

		try: regex_filter = int(regex_filter_number)
		except: regex_filter = None
		
		if regex_filter is None:
			return await ctx.send("Usage: `{}remfilter regex_filter_number`".format(ctx.prefix))
			
		serverOptions = self.settings.getServerStat(ctx.guild, "FilteredWords", [])

		if not 0 < regex_filter <= len(serverOptions):
			return await ctx.send("Usage: `{}remfilter regex_filter_number`".format(ctx.prefix))
		
		serverOptions.pop(regex_filter-1)
		self.settings.setServerStat(ctx.guild, "FilteredWords", serverOptions)
			
		return await ctx.send("Regex pattern removed from language filter!")
		
		
	@commands.command(pass_context=True)
	async def listfilter(self, ctx):
		"""Lists the regex patterns in the language filter (bot-admin only)."""
		if not await Utils.is_bot_admin_reply(ctx): return
			
		serverOptions = self.settings.getServerStat(ctx.guild, "FilteredWords")
		
		if not len(serverOptions):
			return await ctx.send("The filtered words list is empty!")

		entries = ["{}. {}".format(i,Nullify.escape_all(x)) for i,x in enumerate(serverOptions,start=1)]
		return await PickList.PagePicker(
			title="Language Filter ({:,} total)".format(len(entries)),
			description="\n".join(entries),
			ctx=ctx
		).pick()

		
	@commands.command(pass_context=True)
	async def clearfilter(self, ctx):
		"""Empties the language filter (bot-admin only)."""
		if not await Utils.is_bot_admin_reply(ctx): return
			
		serverOptions = self.settings.getServerStat(ctx.guild, "FilteredWords")
		self.settings.setServerStat(ctx.guild, "FilteredWords", [])
		
		await ctx.send('*{:,}* regex pattern{} removed from language filter.'.format(
			len(serverOptions),
			"" if len(serverOptions)==1 else "s"
		))

	
	@commands.command(pass_context=True)
	async def dumpfilter(self, ctx):
		"""Saves the filtered word list to a text file and uploads it to the requestor (bot-admin only)."""
		if not await Utils.is_bot_admin_reply(ctx): return
		
		serverOptions = self.settings.getServerStat(ctx.guild, "FilteredWords")
		
		if not len(serverOptions):
			return await ctx.send("The filter list is empty!")
			
		timeStamp = datetime.today().strftime("%Y-%m-%d %H.%M")
		filename = "{}-Filter-{}.txt".format(ctx.guild.id, timeStamp)
		msg = "\n".join(serverOptions)
		
		msg = msg.encode('utf-8')
		with open(filename, "wb") as myfile:
			myfile.write(msg)
			
		await ctx.send(file=discord.File(filename))
		os.remove(filename)
