import asyncio
import discord
import time
import os
import random
import math
import numpy as np
from   PIL import Image
from   discord.ext import commands
from   Cogs import GetImage
from   Cogs import DisplayName
from   Cogs import Message

def setup(bot):
	# Add the bot and deps
	settings = bot.get_cog("Settings")
	bot.add_cog(Printer(bot, settings))

class Printer:

	# Init with the bot reference
	def __init__(self, bot, settings):
		self.bot = bot
		self.settings = settings

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

	def _ascii(self, image):
		try:
			chars = np.asarray(list(' .,:;irsXA253hMHGS#9B&@'))
			f, WCF, GCF = image, 7/4, .6
			img = Image.open(image)
			# Make sure we have frame 1
			img = img.convert('RGBA')
			
			# Let's scale down
			w, h = 0, 0
			adjust = 2
			w = img.size[0]*adjust
			h = img.size[1]

			# Make sure we're under max params of 50h, 50w
			ratio = 1
			max_wide = 80
			if h*2 > w:
				if h > max_wide/adjust:
					ratio = max_wide/adjust/h
			else:
				if w > max_wide:
					ratio = max_wide/w
			h = ratio * h
			w = ratio * w

			# Shrink to an area of 1900 or so (allows for extra chars)
			target = 1900
			if w*h > target:
				r = h/w
				w1 = math.sqrt(target/r)
				h1 = target/w1
				w = w1
				h = h1

			S = ( round(w), round(h) )
			img = np.sum( np.asarray( img.resize(S) ), axis=2)
			img -= img.min()
			img = (1.0 - img/img.max())**GCF*(chars.size-1)
			a = "\n".join( ("".join(r) for r in chars[len(chars)-img.astype(int)-1]))
			a = "```\n" + a + "```"
			return a
		except Exception:
			pass
		return False

	@commands.command(pass_context=True)
	async def printavi(self, ctx, *, member = None):
		"""Returns a url to the passed member's avatar."""
		if member == None:
			# Assume author
			member = ctx.author
		if type(member) is str:
			new_mem = DisplayName.memberForName(member, ctx.guild)
			if not new_mem:
				await ctx.send("I couldn't find that member...")
				return
			member = new_mem
		url = member.avatar_url
		if not len(url):
			url = member.default_avatar_url
		url = url.split("?size=")[0]
		name = DisplayName.name(member)
		if name[-1].lower() == "s":
			name += "' Avatar"
		else:
			name += "'s Avatar"
		await Message.Embed(title=name, image=url, color=ctx.author).send(ctx)
		# await ctx.send(url)

	@commands.command(pass_context=True)
	async def print(self, ctx, *, url = None):
		"""DOT MATRIX.  Accepts a url - or picks the first attachment."""
		if not self.canDisplay(ctx.guild):
			return
		if url == None and len(ctx.message.attachments) == 0:
			await ctx.send("Usage: `{}print [url or attachment]`".format(ctx.prefix))
			return

		if url == None:
			url = ctx.message.attachments[0].url

		# Let's check if the "url" is actually a user
		test_user = DisplayName.memberForName(url, ctx.guild)
		if test_user:
			# Got a user!
			url = test_user.avatar_url
			if not len(url):
				url = test_user.default_avatar_url
			url = url.split("?size=")[0]

		message = await ctx.send("Downloading...")
		
		path = await GetImage.download(url)
		if not path:
			await message.edit(content="I guess I couldn't print that one...  Make sure you're passing a valid url or attachment.")
			return

		# Prant that shaz
		final = self._ascii(path)
		if os.path.exists(path):
			GetImage.remove(path)
		if not final:
			await message.edit(content="I couldn't print that image...  Make sure you're pointing me to a valid image file.")
			return
		if len(final) > 2000:
			# Too many bigs
			await message.edit(content="Whoops!  I ran out of ink - maybe try a different image.")
			return

		print_sounds = [ "ZZzzzzzt", "Bzzt", "Vvvvrrrr", "Chhhaakkakaka", "Errrttt", "Kkkkkkkktttt", "Eeehhhnnkkk" ]

		msg = "Printing..."
		await message.edit(content=msg)
		for i in range(5):
			await asyncio.sleep(1)
			msg += " " + random.choice(print_sounds) + "..."
			await message.edit(content=msg)

		await asyncio.sleep(1)
		await message.edit(content=final)
