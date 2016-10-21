import asyncio
import discord
import random
import requests
import time
from   os.path import splitext
from   discord.ext import commands
from   Cogs import Settings
from   Cogs import GetImage

try:
    from urllib.parse import urlparse
except ImportError:
    from urlparse import urlparse

# This module grabs Reddit posts and selects one at random

class Reddit:

	# Init with the bot reference, and a reference to the settings var and xp var
	def __init__(self, bot, settings, posts : int = 100):
		self.bot = bot
		self.settings = settings
		if not type(posts) == int:
			posts = 100
		self.posts = posts
		self.ua = 'CorpNewt DeepThoughtBot'
		
	def message(self, message):
		# Check the message and see if we should allow it - always yes.
		# This module doesn't need to cancel messages.
		return { 'Ignore' : False, 'Delete' : False}

	def getTitle(self, url, answer : bool = False, image : bool = False):
		# Load url - with self.posts number of posts
		r = requests.get(url, headers = {'User-agent': self.ua})
		# If we need an image - make sure we have a valid one
		if image:
			extList = ["jpg", "jpeg", "png", "gif", "tiff", "tif"]
			gotImage = False
			while not gotImage:
				randnum = random.randint(0,self.posts)
				theJSON = r.json()["data"]["children"][randnum]["data"]
				if GetImage.get_ext(theJSON["url"]) in extList:
					gotImage = True
		else:
			randnum = random.randint(0,self.posts)
			theJSON = r.json()["data"]["children"][randnum]["data"]
		
		if not (answer or image):
			# Just return the title
			return '{}'.format(theJSON["title"])
		if answer or image:
			# We need the image or the answer
			return {'title' : theJSON['title'], 'url' : theJSON["url"]}
			
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
	async def thinkdeep(self, ctx):
		"""Spout out some intellectual brilliance."""
		msg = self.getTitle('https://www.reddit.com/r/showerthoughts/top.json?sort=top&t=week&limit=100')
		await self.bot.send_message(ctx.message.channel, msg)
		

	@commands.command(pass_context=True)
	async def brainfart(self, ctx):
		"""Spout out some uh... intellectual brilliance..."""
		msg = self.getTitle('https://www.reddit.com/r/Showerthoughts/controversial.json?sort=controversial&t=week&limit=100')
		await self.bot.send_message(ctx.message.channel, msg)


	@commands.command(pass_context=True)
	async def nocontext(self, ctx):
		"""Spout out some intersexual brilliance."""
		msg = self.getTitle('https://www.reddit.com/r/nocontext/top.json?sort=top&t=week&limit=100')
		await self.bot.send_message(ctx.message.channel, msg)
		

	@commands.command(pass_context=True)
	async def question(self, ctx):
		"""Spout out some interstellar questioning... ?"""
		infoDict = self.getTitle('https://www.reddit.com/r/NoStupidQuestions/top.json?sort=top&t=week&limit=100', True)
		self.settings.setServerStat(ctx.message.server, "LastAnswer", infoDict["url"])
		msg = '{}'.format(infoDict["title"])
		await self.bot.send_message(ctx.message.channel, msg)
		
		
	@commands.command(pass_context=True)
	async def answer(self, ctx):
		"""Spout out some interstellar answering... ?"""
		answer = self.settings.getServerStat(ctx.message.server, "LastAnswer")
		if answer == "":
			msg = 'You need to ask a `$question` first!'
		else:
			msg = '{}'.format(answer)
		await self.bot.send_message(ctx.message.channel, msg)

		
	@commands.command(pass_context=True)
	async def meirl(self, ctx):
		"""Me in real life."""
		
		channel = ctx.message.channel
		author  = ctx.message.author
		server  = ctx.message.server
		
		if not self.canDisplay(server):
			return
		
		# Grab our image title and url
		infoDict = self.getTitle('https://www.reddit.com/r/me_irl/top.json?sort=top&t=week&limit=100', False, True)
		
		await GetImage.get(infoDict['url'], self.bot, channel, infoDict['title'], self.ua)


	@commands.command(pass_context=True)
	async def starterpack(self, ctx):
		"""Starterpacks."""
		
		channel = ctx.message.channel
		author  = ctx.message.author
		server  = ctx.message.server
		
		if not self.canDisplay(server):
			return
		
		# Grab our image title and url
		infoDict = self.getTitle('https://www.reddit.com/r/starterpacks/top.json?sort=top&t=week&limit=100', False, True)
		
		await GetImage.get(infoDict['url'], self.bot, channel, infoDict['title'], self.ua)


	@commands.command(pass_context=True)
	async def earthporn(self, ctx):
		"""Earth is good."""
		
		channel = ctx.message.channel
		author  = ctx.message.author
		server  = ctx.message.server
		
		if not self.canDisplay(server):
			return
		
		# Grab our image title and url
		infoDict = self.getTitle('https://www.reddit.com/r/EarthPorn/top.json?sort=top&t=week&limit=100', False, True)
		
		await GetImage.get(infoDict['url'], self.bot, channel, infoDict['title'], self.ua)

		
	@commands.command(pass_context=True)
	async def wallpaper(self, ctx):
		"""Get something pretty to look at."""
		
		channel = ctx.message.channel
		author  = ctx.message.author
		server  = ctx.message.server
		
		if not self.canDisplay(server):
			return
		
		# Grab our image title and url
		infoDict = self.getTitle('https://www.reddit.com/r/wallpapers/top.json?sort=top&t=week&limit=100', False, True)
		
		await GetImage.get(infoDict['url'], self.bot, channel, infoDict['title'], self.ua)
		
		
	@commands.command(pass_context=True)
	async def abandoned(self, ctx):
		"""Get something abandoned to look at."""
		
		channel = ctx.message.channel
		author  = ctx.message.author
		server  = ctx.message.server
		
		if not self.canDisplay(server):
			return
		
		# Grab our image title and url
		infoDict = self.getTitle('https://www.reddit.com/r/abandonedporn/top.json?sort=top&t=week&limit=100', False, True)
		
		await GetImage.get(infoDict['url'], self.bot, channel, infoDict['title'], self.ua)