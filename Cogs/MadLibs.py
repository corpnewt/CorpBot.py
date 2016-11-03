import asyncio
import discord
import re
import os
import random
from   discord.ext import commands
from   Cogs import Settings

class MadLibs:

	# Init with the bot reference, and a reference to the settings var
	def __init__(self, bot, settings):
		self.bot = bot
		self.settings = settings
		# Setup/compile our regex
		self.regex = re.compile(r"\[\[[^\[\]]+\]\]")
		

	def message(self, message):
		# Check the message and see if we should allow it - always yes.
		# This module doesn't need to cancel messages.
		return { 'Ignore' : False, 'Delete' : False}


	@commands.command(pass_context=True)
	async def madlibs(self, ctx):
		"""Let's play MadLibs!"""

		channel = ctx.message.channel
		author  = ctx.message.author
		server  = ctx.message.server

		# Check if our folder exists
		if not os.path.isdir("./Cogs/MadLibs"):
			msg = 'I\'m not configured for MadLibs yet...'
			await self.bot.send_message(channel, msg)
			return

		# Folder exists - let's see if it has any files
		choices = [] # Empty array
		for file in os.listdir("./Cogs/MadLibs"):
			if file.endswith(".txt"):
				choices.append(file)
		
		if len(choices) == 0:
			# No madlibs...
			msg = 'I\'m not configured for MadLibs yet...'
			await self.bot.send_message(channel, msg)
			return

		# Get a random madlib from those available
		randnum = random.randint(0, (len(choices)-1))
		randLib = choices[randnum]

		# Let's load our text and get to work
		with open("./Cogs/MadLibs/{}".format(randLib), 'r') as myfile:
			data = myfile.read()

		# Set up an empty arry
		words = []

		# Match
		matches = re.finditer(self.regex, data)

		# Iterate matches
		for match in matches:
			words.append(match.group(0))

		# Create empty substitution array
		subs = []

		# Iterate words and ask for input
		i = 0
		while i < len(words):
			# Ask for the next word
			msg = "I need a/an **{}** (type `$ml [your word]` to respond).".format(words[i][2:-2])
			await self.bot.send_message(channel, msg)

			# Setup the check
			def check(msg):
				return msg.content.startswith('$ml')

			# Wait for a response
			talk = await self.bot.wait_for_message(channel=channel, check=check, timeout=25)

			if not talk:
				# We timed out - leave the loop
				msg = "*{}*, I'm done waiting... we'll play another time.".format(author.name)
				await self.bot.send_message(channel, msg)
				return

			# We got a relevant message
			word = talk.content
			# Let's remove the $ml prefix (with or without space)
			if word.startswith('$ml '):
				word = word[4:]
			if word.startswith('$ml'):
				word = word[3:]

			# Add to our list
			subs.append(word)
			# Increment our index
			i += 1

		# Let's replace
		for asub in subs:
			# Only replace the first occurence
			data = re.sub(self.regex, "**{}**".format(asub), data, 1)

		# Message the output
		await self.bot.send_message(channel, data)