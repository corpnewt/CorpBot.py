import asyncio
import discord
import time
import os
from   PIL import Image
from   discord.ext import commands
from   Cogs import GetImage
from   Cogs import DisplayName

def setup(bot):
	# Add the bot and deps
	settings = bot.get_cog("Settings")
	bot.add_cog(Jpeg(bot, settings))

class Jpeg:

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

	def _jpeg(self, image, compression = 1):
		try:
			img = Image.open(image)
			# Get frame 1
			img = img.convert('RGBA')
			img = self._remove_transparency(img)
			img.save(image, 'JPEG', quality=compression)
		except Exception:
			return False
		return True

	def _remove_transparency(self, image, fill_color = 'black'):
		if image.mode in ('RGBA', 'LA'):
			background = Image.new(image.mode[:-1], image.size, fill_color)
			background.paste(image, image.split()[-1])
			image = background
		return image


	@commands.command(pass_context=True)
	async def jpeg(self, ctx, *, url = None):
		"""MOAR JPEG!  Accepts a url - or picks the first attachment."""
		if not self.canDisplay(ctx.guild):
			return
		if url == None and len(ctx.message.attachments) == 0:
			await ctx.send("Usage: `{}jpeg [url or attachment]`".format(ctx.prefix))
			return

		if url == None:
			url = ctx.message.attachments[0].url
			
		# Let's check if the "url" is actually a user
		test_user = DisplayName.memberForName(url, ctx.guild)
		if test_user:
			# Got a user!
			url = test_user.avatar_url if len(test_user.avatar_url) else test_user.default_avatar_url
			url = url.split("?size=")[0]
			
		message = await ctx.send("Downloading...")
		
		path = await GetImage.download(url)
		if not path:
			await message.edit(content="I guess I couldn't jpeg that one...  Make sure you're passing a valid url or attachment.")
			return

		await message.edit(content="Jpegifying...")
		# JPEEEEEEEEGGGGG
		if not self._jpeg(path):
			await message.edit(content="I couldn't jpegify that image...  Make sure you're pointing me to a valid image file.")
			if os.path.exists(path):
				GetImage.remove(path)
			return

		await message.edit(content="Uploading...")
		await GetImage.upload(path, self.bot, ctx.channel)
		await message.edit(content=" ")
		GetImage.remove(path)
