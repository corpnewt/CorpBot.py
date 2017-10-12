import random
import re

import asyncio
import discord
import os
from   datetime import datetime
from   discord.ext import commands
from   Cogs import DisplayName
from   Cogs import Nullify
from   Cogs import Message

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

		r = re.compile(regexp, re.IGNORECASE if self.ignore_case else 0)

		return r.sub(self.__replacer, text)


'''if __name__ == '__main__':

	f = ProfanitiesFilter(['bad', 'un\w+'], replacements="-")    
	example = "I am doing bad ungood badlike things."

	print f.clean(example)
	# Returns "I am doing --- ------ badlike things."

	f.inside_words = True    
	print f.clean(example)
	# Returns "I am doing --- ------ ---like things."

	f.complete = False    
	print f.clean(example)
	# Returns "I am doing b-d u----d b-dlike things."'''
	
class LangFilter:

	# Init with the bot reference, and a reference to the settings var
	def __init__(self, bot, settings, replacements = "@#$%&"):
		self.bot = bot
		self.settings = settings
		self.replacements = replacements
		
		
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
		isAdmin = message.author.permissions_in(message.channel).administrator
		if not isAdmin:
			checkAdmin = self.settings.getServerStat(message.guild, "AdminArray")
			for role in message.author.roles:
				for aRole in checkAdmin:
					# Get the role that corresponds to the id
					if str(aRole['ID']) == str(role.id):
						isAdmin = True
		if isAdmin:
			return { "Ignore" : False, "Delete" : False }
		
		f = ProfanitiesFilter(word_list, replacements=self.replacements)
		f.ignore_case = True
		f.inside_words = True
		
		new_msg = f.clean(message.content)
		if not new_msg == message.content:
			# Something changed
			new_msg = "Hey *{}*, based on my calculations, here's a cleaner version of that messsage:\n\n".format(DisplayName.name(message.author)) + new_msg
			await message.channel.send(new_msg)
			return { "Ignore" : False, "Delete" : True }
		return { "Ignore" : False, "Delete" : False }
		
	
	@commands.command(pass_context=True)
	async def addfilter(self, ctx, *, words = None):
		"""Adds comma delimited words to the word list (bot-admin only)."""
		
		isAdmin = ctx.author.permissions_in(ctx.channel).administrator
		if not isAdmin:
			checkAdmin = self.settings.getServerStat(ctx.guild, "AdminArray")
			for role in ctx.author.roles:
				for aRole in checkAdmin:
					# Get the role that corresponds to the id
					if str(aRole['ID']) == str(role.id):
						isAdmin = True
		# Only allow admins to change server stats
		if not isAdmin:
			await ctx.send('You do not have sufficient privileges to access this command.')
			return
			
		if words == None:
			msg = 'Usage: `{}addfilter word1, word2, word3...`'.format(ctx.prefix)
			await ctx.send(msg)
			return
			
		serverOptions = self.settings.getServerStat(ctx.guild, "FilteredWords")
		words = "".join(words.split())
		optionList = words.split(',')
		addedOptions = []
		for option in optionList:
			option = option.replace("(", "\(").replace(")", "\)")
			if not option.lower() in serverOptions:
				# Only add if not already added
				addedOptions.append(option.lower())
		if not len(addedOptions):
			await ctx.send('No new words were passed.')
			return
		
		for option in addedOptions:
			serverOptions.append(option)
			
		if len(addedOptions) == 1:
			await ctx.send('*1* word added to language filter.')
		else:
			await ctx.send('*{}* words added to language filter.'.format(len(addedOptions)))
			
			
	@commands.command(pass_context=True)
	async def remfilter(self, ctx, *, words = None):
		"""Removes comma delimited words from the word list (bot-admin only)."""
		
		isAdmin = ctx.author.permissions_in(ctx.channel).administrator
		if not isAdmin:
			checkAdmin = self.settings.getServerStat(ctx.guild, "AdminArray")
			for role in ctx.author.roles:
				for aRole in checkAdmin:
					# Get the role that corresponds to the id
					if str(aRole['ID']) == str(role.id):
						isAdmin = True
		# Only allow admins to change server stats
		if not isAdmin:
			await ctx.send('You do not have sufficient privileges to access this command.')
			return
			
		if words == None:
			msg = 'Usage: `{}remfilter word1, word2, word3...`'.format(ctx.prefix)
			await ctx.send(msg)
			return
			
		serverOptions = self.settings.getServerStat(ctx.guild, "FilteredWords")
		words = "".join(words.split())
		optionList = words.split(',')
		addedOptions = []
		for option in optionList:
			# Clear any instances of \( to (
			# Reset them to \(
			# This should allow either \( or ( to work correctly -
			# While still allowing \\( or whatever as well
			option = option.replace("\(", "(").replace("\)", ")")
			option = option.replace("(", "\(").replace(")", "\)")
			if option.lower() in serverOptions:
				# Only add if not already added
				addedOptions.append(option.lower())
		if not len(addedOptions):
			await ctx.send('No new words were passed.')
			return
		
		for option in addedOptions:
			serverOptions.remove(option)
			
		if len(addedOptions) == 1:
			await ctx.send('*1* word removed from language filter.')
		else:
			await ctx.send('*{}* words removed from language filter.'.format(len(addedOptions)))
		
		
	@commands.command(pass_context=True)
	async def listfilter(self, ctx):
		"""Prints out the list of words that will be filtered (bot-admin only)."""
		
		isAdmin = ctx.author.permissions_in(ctx.channel).administrator
		if not isAdmin:
			checkAdmin = self.settings.getServerStat(ctx.guild, "AdminArray")
			for role in ctx.author.roles:
				for aRole in checkAdmin:
					# Get the role that corresponds to the id
					if str(aRole['ID']) == str(role.id):
						isAdmin = True
		# Only allow admins to change server stats
		if not isAdmin:
			await ctx.send('You do not have sufficient privileges to access this command.')
			return
			
		serverOptions = self.settings.getServerStat(ctx.guild, "FilteredWords")
		
		if not len(serverOptions):
			await ctx.send("The filtered words list is empty!")
			return
		
		string_list = ", ".join(serverOptions)
		
		msg = "__**Filtered Words:**__\n\n" + string_list
		
		await Message.Message(message=msg).send(ctx)
		
	@commands.command(pass_context=True)
	async def clearfilter(self, ctx):
		"""Empties the list of words that will be filtered (bot-admin only)."""
		
		isAdmin = ctx.author.permissions_in(ctx.channel).administrator
		if not isAdmin:
			checkAdmin = self.settings.getServerStat(ctx.guild, "AdminArray")
			for role in ctx.author.roles:
				for aRole in checkAdmin:
					# Get the role that corresponds to the id
					if str(aRole['ID']) == str(role.id):
						isAdmin = True
		# Only allow admins to change server stats
		if not isAdmin:
			await ctx.send('You do not have sufficient privileges to access this command.')
			return
			
		serverOptions = self.settings.getServerStat(ctx.guild, "FilteredWords")
		self.settings.setServerStat(ctx.guild, "FilteredWords", [])
		
		if len(serverOptions) == 1:
			await ctx.send('*1* word removed from language filter.')
		else:
			await ctx.send('*{}* words removed from language filter.'.format(len(serverOptions)))
			
	@commands.command(pass_context=True)
	async def dumpfilter(self, ctx):
		"""Saves the filtered word list to a text file and uploads it to the requestor (bot-admin only)."""
		
		isAdmin = ctx.author.permissions_in(ctx.channel).administrator
		if not isAdmin:
			checkAdmin = self.settings.getServerStat(ctx.guild, "AdminArray")
			for role in ctx.author.roles:
				for aRole in checkAdmin:
					# Get the role that corresponds to the id
					if str(aRole['ID']) == str(role.id):
						isAdmin = True
		# Only allow admins to change server stats
		if not isAdmin:
			await ctx.send('You do not have sufficient privileges to access this command.')
			return
		
		serverOptions = self.settings.getServerStat(ctx.guild, "FilteredWords")
		
		if not len(serverOptions):
			await ctx.author.send("The filtered words list is empty!")
			return
			
		timeStamp = datetime.today().strftime("%Y-%m-%d %H.%M")
		filename = "{}-WordList-{}.txt".format(ctx.guild.id, timeStamp)
		msg = "\n".join(serverOptions)
		
		msg = msg.encode('utf-8')
		with open(filename, "wb") as myfile:
			myfile.write(msg)
			
		await ctx.author.send(file=discord.File(filename))
		os.remove(filename)
		
	
	'''@commands.command(pass_context=True)
	async def setfilter(self, ctx, url = None):
		"""Sets the word list to a passed text file url, or attachment contents (bot-admin only)."""
		
		isAdmin = ctx.author.permissions_in(ctx.channel).administrator
		if not isAdmin:
			checkAdmin = self.settings.getServerStat(ctx.guild, "AdminArray")
			for role in ctx.author.roles:
				for aRole in checkAdmin:
					# Get the role that corresponds to the id
					if str(aRole['ID']) == str(role.id):
						isAdmin = True
		# Only allow admins to change server stats
		if not isAdmin:
			await ctx.send('You do not have sufficient privileges to access this command.')
			return
			
		if url == None and len(ctx.message.attachments) == 0:
			await ctx.send("Usage: `{}setfilter [url or attachment]`".format(ctx.prefix))
			return
		
		if url == None:
			url = ctx.message.attachments[0].url
			
		'''
