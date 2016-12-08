import asyncio
import discord
import re
import os
import random
import string
from   discord.ext import commands
from   Cogs import Settings
from   Cogs import DisplayName

class MadLibs:

	# Init with the bot reference, and a reference to the settings var
	def __init__(self, bot, settings):
		self.bot = bot
		self.settings = settings
		# Setup/compile our regex
		self.regex = re.compile(r"\[\[[^\[\]]+\]\]")
		self.botPrefix = "$"
		self.prefix = "$ml"
		self.leavePrefix = "$mleave"


	@commands.command(pass_context=True)
	async def madlibs(self, ctx):
		"""Let's play MadLibs!"""

		channel = ctx.message.channel
		author  = ctx.message.author
		server  = ctx.message.server

		# Check if we have a MadLibs channel - and if so, restrict to that
		channelID = self.settings.getServerStat(server, "MadLibsChannel")
		if not (not channelID or channelID == ""):
			# We need the channel id
			if not channelID == channel.id:
				msg = 'This isn\'t the channel for that...'
				for chan in server.channels:
					if chan.id == channelID:
						msg = 'This isn\'t the channel for that.  Take the MadLibs to the **{}** channel.'.format(chan.name)
				await self.bot.send_message(channel, msg)
				return

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
		
		# Check if we're already in a game
		if self.settings.getServerStat(server, "PlayingMadLibs"):
			msg = 'I\'m already playing MadLibs - use `{} [your word]` to submit answers.'.format(self.prefix)
			await self.bot.send_message(channel, msg)
			return
		
		self.settings.setServerStat(server, "PlayingMadLibs", "Yes")

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
			msg = "I need a/an **{}** (word *{}/{}*).  `{} [your word]`".format(words[i][2:-2], str(i+1), str(len(words)), self.prefix)
			await self.bot.send_message(channel, msg)

			# Setup the check
			def check(msg):	
				return msg.content.startswith(self.prefix)

			# Wait for a response
			talk = await self.bot.wait_for_message(channel=channel, check=check, timeout=60)

			if not talk:
				# We timed out - leave the loop
				msg = "*{}*, I'm done waiting... we'll play another time.".format(DisplayName.name(author))
				await self.bot.send_message(channel, msg)
				self.settings.setServerStat(server, "PlayingMadLibs", None)
				return

			# Check if the message is to leave
			if talk.content.startswith(self.leavePrefix):
				if talk.author is author:
					msg = "Alright, *{}*.  We'll play another time.".format(DisplayName.name(author))
					await self.bot.send_message(channel, msg)
					self.settings.setServerStat(server, "PlayingMadLibs", None)
					return
				else:
					# Not the originator
					msg = "Only the originator (*{}*) can leave the MadLibs.".format(DisplayName.name(author))
					await self.bot.send_message(channel, msg)
					continue

			# We got a relevant message
			word = talk.content
			# Let's remove the $ml prefix (with or without space)
			if word.startswith('{} '.format(self.prefix)):
				word = word[4:]
			if word.startswith(self.prefix):
				word = word[3:]
			
			# Check capitalization
			if words[i][:3].isupper():
				# Capitalized
				word = string.capwords(word)

			# Add to our list
			subs.append(word)
			# Increment our index
			i += 1

		# Let's replace
		for asub in subs:
			# Only replace the first occurence
			data = re.sub(self.regex, "**{}**".format(asub), data, 1)

		self.settings.setServerStat(server, "PlayingMadLibs", None)
		
		# Message the output
		await self.bot.send_message(channel, data)

	@madlibs.error
	async def madlibs_error(self, ctx, error):
		# Reset playing status and display error
		self.settings.setServerStat(server, "PlayingMadLibs", None)
		msg = 'madlibs Error: {}'.format(ctx)
		await self.bot.say(msg)
