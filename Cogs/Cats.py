import asyncio
import discord
import random
import time
from   os.path import splitext
from   discord.ext import commands
from   Cogs import Settings
from   Cogs import GetImage
from   Cogs import DL

def setup(bot):
	# Add the bot and deps
	settings = bot.get_cog("Settings")
	bot.add_cog(Cats(bot, settings))

# This module grabs Reddit posts and selects one at random

class Cats:

	# Init with the bot reference, and a reference to the settings var and xp var
	def __init__(self, bot, settings, posts : int = 100):
		self.bot = bot
		self.settings = settings
		if not type(posts) == int:
			posts = 100
		self.posts = posts
		self.ua = 'CorpNewt DeepThoughtBot'
			
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
	async def randomcat(self, ctx):
		"""Meow."""
		
		channel = ctx.message.channel
		author  = ctx.message.author
		server  = ctx.message.guild
		
		if not self.canDisplay(server):
			return
		
		url = 'http://random.cat/meow'

		# Grab our image url
		r = await DL.async_json(url, headers = {'User-agent': self.ua})
		if not r:
			await ctx.send("Hmmm - something went wrong...")
			return

		catURL = r['file']
		
		await GetImage.get(ctx, catURL, 'A cat for you!', self.ua)