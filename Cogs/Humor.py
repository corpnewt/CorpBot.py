import asyncio
import discord
import random
import json
import time
import os
from   discord.ext import commands
from Cogs import Message
from Cogs import FuzzySearch
from Cogs import GetImage
from Cogs import Nullify
from Cogs import Message
from Cogs import DL

def setup(bot):
	# Add the bot and deps
	settings = bot.get_cog("Settings")
	bot.add_cog(Humor(bot, settings))

# This module is for random funny things I guess...

class Humor:

	def __init__(self, bot, settings, listName = "Adjectives.txt"):
		self.bot = bot
		self.settings = settings
		# Setup our adjective list
		self.adj = []
		marks = map(chr, range(768, 879))
		self.marks = list(marks)
		if os.path.exists(listName):
			with open(listName) as f:
				for line in f:
					self.adj.append(line)
					
					
	@commands.command(pass_context=True)
	async def zalgo(self, ctx, *, message = None):
		"""Ỉ s̰hͨo̹u̳lͪd͆ r͈͍e͓̬a͓͜lͨ̈l̘̇y̡͟ h͚͆a̵͢v͐͑eͦ̓ i͋̍̕n̵̰ͤs͖̟̟t͔ͤ̉ǎ͓͐ḻ̪ͨl̦͒̂ḙ͕͉d͏̖̏ ṡ̢ͬö̹͗m̬͔̌e̵̤͕ a̸̫͓͗n̹ͥ̓͋t̴͍͊̍i̝̿̾̕v̪̈̈͜i̷̞̋̄r̦̅́͡u͓̎̀̿s̖̜̉͌..."""
		if message == None:
			await ctx.send("Usage: `{}zalgo [message]`".format(ctx.prefix))
			return
		# Check if we're suppressing @here and @everyone mentions
		if self.settings.getServerStat(ctx.message.guild, "SuppressMentions"):
			suppress = True
		else:
			suppress = False
		
		words = message.split()
		try:
			iterations = int(words[len(words)-1])
			words = words[:-1]
		except Exception:
			iterations = 1
			
		if iterations > 100:
			iterations = 100
		if iterations < 1:
			iterations = 1
			
		zalgo = " ".join(words)
		for i in range(iterations):
			if len(zalgo) > 2000:
				break
			zalgo = self._zalgo(zalgo)
		
		zalgo = zalgo[:2000]

		# Check for suppress
		if suppress:
			zalgo = Nullify.clean(zalgo)
		await Message.Message(message=zalgo).send(ctx)
		#await ctx.send(zalgo)
		
	def _zalgo(self, text):
		words = text.split()
		zalgo = ' '.join(''.join(c + ''.join(random.choice(self.marks)
				for _ in range(i // 2 + 1)) * c.isalnum()
				for c in word)
				for i, word in enumerate(words))
		return zalgo

	@commands.command(pass_context=True)
	async def holy(self, ctx, *, subject : str = None):
		"""Time to backup the Batman!"""
		
		if subject == None:
			await ctx.channel.send("Usage: `{}holy [subject]`".format(ctx.prefix))
			return
		
		# Check if we're suppressing @here and @everyone mentions
		if self.settings.getServerStat(ctx.message.guild, "SuppressMentions"):
			suppress = True
		else:
			suppress = False
		
		matchList = []
		for a in self.adj:
			if a[:1].lower() == subject[:1].lower():
				matchList.append(a)
		
		if not len(matchList):
			# Nothing in there - get random entry
			# msg = "*Whoah there!* That was *too* holy for Robin!"
			word = random.choice(self.adj)
			word = word.strip().capitalize()
			subject = subject.strip().capitalize()
			msg = "*Holy {} {}, Batman!*".format(word, subject)
		else:
			# Get a random one
			word = random.choice(matchList)
			word = word.strip().capitalize()
			subject = subject.strip().capitalize()
			msg = "*Holy {} {}, Batman!*".format(word, subject)
		
		# Check for suppress
		if suppress:
			msg = Nullify.clean(msg)
		
		await ctx.channel.send(msg)
			
		
	@commands.command(pass_context=True)
	async def fart(self, ctx):
		"""PrincessZoey :P"""
		fartList = ["Poot", "Prrrrt", "Thhbbthbbbthhh", "Plllleerrrrffff", "Toot", "Blaaaaahnk", "Squerk"]
		randnum = random.randint(0, len(fartList)-1)
		msg = '{}'.format(fartList[randnum])
		await ctx.channel.send(msg)
		
	@commands.command(pass_context=True)
	async def french(self, ctx):
		"""Speaking French... probably..."""
		fr_list = [ "hon", "fromage", "baguette" ]
		punct   = [ ".", "!", "?", "...", "!!!", "?!" ]
		fr_sentence = []
		for i in range(random.randint(3, 20)):
			fr_sentence.append(random.choice(fr_list))
			if len(fr_sentence) == 1:
				# Capitalize the first letter of the first word
				fr_sentence[0] = fr_sentence[0][:1].upper() + fr_sentence[0][1:]
		totally_french = " ".join(fr_sentence) + random.choice(punct)
		await ctx.send(totally_french)

	def canDisplay(self, server):
		# Check if we can display images
		lastTime = int(self.settings.getServerStat(server, "LastPicture"))
		threshold = int(self.settings.getServerStat(server, "PictureThreshold"))
		if not GetImage.canDisplay( lastTime, threshold ):
			# await self.bot.send_message(channel, 'Too many images at once - please wait a few seconds.')
			return False
		
		# If we made it here - set the LastPicture method
		self.settings.setServerStat(server, "LastPicture", int(time.time()))
		return True

	@commands.command(pass_context=True)
	async def memetemps(self, ctx):
		"""Get Meme Templates"""
		url = "https://api.imgflip.com/get_memes"
		result_json = await DL.async_json(url)
		templates = result_json["data"]["memes"]

		templates_string_list = []
		
		fields = []
		for template in templates:
			fields.append({ "name" : template["name"], "value" : "`" + str(template["id"]) + "`", "inline" : False })
		await Message.Embed(title="Meme Templates", fields=fields).send(ctx)

	@commands.command(pass_context=True)
	async def meme(self, ctx, template_id = None, text_zero = None, text_one = None):
		"""Generate Meme"""

		if not self.canDisplay(ctx.message.guild):
			return

		if text_one == None:
			# Set as space if not included
			text_one = " "

		if template_id == None or text_zero == None or text_one == None:
			msg = "Usage: `{}meme [template_id] [text#1] [text#2]`\n\n Meme Templates can be found using `$memetemps`".format(ctx.prefix)
			await ctx.channel.send(msg)
			return

		templates = await self.getTemps()

		chosenTemp = None
		msg = ''

		idMatch   = FuzzySearch.search(template_id, templates, 'id', 1)
		if idMatch[0]['Ratio'] == 1:
			# Perfect match
			chosenTemp = idMatch[0]['Item']['id']
		else:
			# Imperfect match - assume the name
			nameMatch = FuzzySearch.search(template_id, templates, 'name', 1)
			chosenTemp = nameMatch[0]['Item']['id']
			if nameMatch[0]['Ratio'] < 1:
				# Less than perfect, still
				msg = 'I\'ll assume you meant *{}*.'.format(nameMatch[0]['Item']['name'])

		url = "https://api.imgflip.com/caption_image"
		payload = {'template_id': chosenTemp, 'username':'CorpBot', 'password': 'pooter123', 'text0': text_zero, 'text1': text_one }
		result_json = await DL.async_post_json(url, payload)
		# json.loads(r.text)
		result = result_json["data"]["url"]
		if msg:
			# result = '{}\n{}'.format(msg, result)
			await ctx.channel.send(msg)
		# Download Image - set title as a space so it disappears on upload
		await Message.Embed(image=result, color=ctx.author).send(ctx)
		# await GetImage.get(ctx, result)


	async def getTemps(self):
		url = "https://api.imgflip.com/get_memes"
		result_json = await DL.async_json(url)
		templates = result_json["data"]["memes"]
		if templates:
			return templates
		return None
