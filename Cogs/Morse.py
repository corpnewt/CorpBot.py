import asyncio
import discord
from   discord.ext import commands
from   operator import itemgetter
import base64
import binascii
import re
from   Cogs import Nullify

def setup(bot):
	# Add the bot and deps
	settings = bot.get_cog("Settings")
	bot.add_cog(Morse(bot, settings))

class Morse:

	# Init with the bot reference
	def __init__(self, bot, settings):
		self.bot = bot
		self.settings = settings
		self.to_morse = { 
			"a" : ".-",
			"b" : "-...",
			"c" : "-.-.",
			"d" : "-..",
			"e" : ".",
			"f" : "..-.",
			"g" : "--.",
			"h" : "....",
			"i" : "..",
			"j" : ".---",
			"k" : "-.-",
			"l" : ".-..",
			"m" : "--",
			"n" : "-.",
			"o" : "---",
			"p" : ".--.",
			"q" : "--.-",
			"r" : ".-.",
			"s" : "...",
			"t" : "-",
			"u" : "..-",
			"v" : "...-",
			"w" : ".--",
			"x" : "-..-",
			"y" : "-.--",
			"z" : "--..",
			"1" : ".----",
			"2" : "..---",
			"3" : "...--",
			"4" : "....-",
			"5" : ".....",
			"6" : "-....",
			"7" : "--...",
			"8" : "---..",
			"9" : "----.",
			"0" : "-----"
			}


	def suppressed(self, guild, msg):
		# Check if we're suppressing @here and @everyone mentions
		if self.settings.getServerStat(guild, "SuppressMentions"):
			return Nullify.clean(msg)
		else:
			return msg
		
		
	@commands.command(pass_context=True)
	async def morsetable(self, ctx, num_per_row = None):
		"""Prints out the morse code lookup table."""
		try:
			num_per_row = int(num_per_row)
		except Exception:
			num_per_row = 5
		
		msg = "__**Morse Code Lookup Table:**__\n```\n"
		max_length = 0
		current_row = 0
		row_list = [[]]
		cur_list = []
		sorted_list = sorted(self.to_morse)
		print(sorted_list)
		for key in sorted_list:
			print(key)
			entry = "{} : {}".format(key.upper(), self.to_morse[key])
			if len(entry) > max_length:
				max_length = len(entry)
			row_list[len(row_list)-1].append(entry)
			if len(row_list[len(row_list)-1]) >= num_per_row:
				row_list.append([])
				current_row += 1
		
		for row in row_list:
			for entry in row:
				entry = entry.ljust(max_length)
				msg += entry + "  "
			msg += "\n"
		
		msg += "```"
		await ctx.send(self.suppressed(ctx.guild, msg))


	@commands.command(pass_context=True)
	async def morse(self, ctx, *, content = None):
		"""Converts ascii to morse code.  Accepts a-z and 0-9.  Each letter is comprised of "-" or "." and separated by 1 space.  Each word is separated by 4 spaces."""

		if content == None:
			await ctx.send("Usage `{}morse [content]`".format(ctx.prefix))
			return

		# Only accept alpha numeric stuff and spaces
		word_list = content.split()
		morse_list = []
		for word in word_list:
			# Iterate through words
			letter_list = []
			for letter in word:
				# Iterate through each letter of each word
				if letter.lower() in self.to_morse:
					# It's in our list - add the morse equivalent
					letter_list.append(self.to_morse[letter.lower()])
			if len(letter_list):
				# We have letters - join them into morse words
				# each separated by a space
				morse_list.append(" ".join(letter_list))
			
		if not len(morse_list):
			# We didn't get any valid words
			await ctx.send("There were no valid a-z/0-9 chars in the passed content.")
			return

		# We got *something*
		msg = "    ".join(morse_list)
		msg = "```\n" + msg + "```"
		await ctx.send(self.suppressed(ctx.guild, msg))


	@commands.command(pass_context=True)
	async def unmorse(self, ctx, *, content = None):
		"""Converts morse code to ascii.  Each letter is comprised of "-" or "." and separated by 1 space.  Each word is separated by 4 spaces."""

		if content == None:
			await ctx.send("Usage `{}unmorse [content]`".format(ctx.prefix))
			return

		# Only accept alpha numeric stuff and spaces
		word_list = content.split("    ")
		ascii_list = []
		for word in word_list:
			# Split by space for letters
			letter_list = word.split()
			letter_ascii = []
			# Iterate through letters
			for letter in letter_list:
				for key in self.to_morse:
					if self.to_morse[key] == letter:
						# Found one
						letter_ascii.append(key.upper())
			if len(letter_ascii):
				# We have letters - join them into ascii words
				ascii_list.append("".join(letter_ascii))
			
		if not len(ascii_list):
			# We didn't get any valid words
			await ctx.send("There were no valid morse chars in the passed content.")
			return

		# We got *something* - join separated by a space
		msg = " ".join(ascii_list)
		msg = "```\n" + msg + "```"
		await ctx.send(self.suppressed(ctx.guild, msg))

	
