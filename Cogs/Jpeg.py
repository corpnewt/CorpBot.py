import discord, time, os
from PIL import Image
from discord.ext import commands
from Cogs import GetImage, DisplayName, Message

def setup(bot):
	# Add the bot and deps
	settings = bot.get_cog("Settings")
	bot.add_cog(Jpeg(bot, settings))

class Jpeg(commands.Cog):

	# Init with the bot reference
	def __init__(self, bot, settings):
		self.bot = bot
		self.settings = settings
		global Utils, DisplayName
		Utils = self.bot.get_cog("Utils")
		DisplayName = self.bot.get_cog("DisplayName")

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
	async def jpeg(self, ctx, *, url = None):
		"""MOAR JPEG!  Accepts a url - or picks the first attachment."""
		if not self.canDisplay(ctx.guild):
			return
		if url is None and not ctx.message.attachments:
			return await ctx.send("Usage: `{}jpeg [url or attachment]`".format(ctx.prefix))

		if url is None:
			url = ctx.message.attachments[0].url
			
		# Let's check if the "url" is actually a user
		test_user = DisplayName.memberForName(url, ctx.guild)
		if test_user:
			# Got a user!
			url = Utils.get_avatar(test_user)
		
		message = await Message.Embed(description="Downloading...", color=ctx.author).send(ctx)
		
		path = await GetImage.download(url)
		if not path:
			return await Message.Embed(title="An error occurred!", description="I guess I couldn't jpeg that one...  Make sure you're passing a valid url or attachment.").edit(ctx, message)

		message = await Message.Embed(description="Jpegifying...").edit(ctx, message)
		fn = os.path.basename(path)
		dn = os.path.dirname(path)
		# JPEEEEEEEEGGGGG
		try:
			i = Image.open(path)
			# Get the first frame, and replace transparency with black
			i = i.convert("RGBA")
			bg = Image.new(i.mode[:-1],i.size,"black")
			bg.paste(i,i.split()[-1])
			i = bg
			# Resize the image to half - and save it with extreme compression
			w,h = i.size
			i = i.resize((int(w/2),int(h/2)))
			# Save it to a temp image path
			half_name = os.path.join(dn,"half-"+fn)
			i.save(half_name,"JPEG",quality=1)
			# Load it again - then resize it up
			i = Image.open(half_name)
			i = i.resize((int(w*2),int(h*2)))
			# Remove the old, and save it again
			os.remove(half_name)
			os.remove(path)
			# Save it to a path ending in .jpg/.jpeg
			if not path.lower().endswith((".jpg",".jpeg")):
				path = os.path.join(dn,fn+".jpg")
			i.save(path,"JPEG",quality=1)
		except:
			await Message.Embed(title="An error occurred!", description="I couldn't jpegify that image...  Make sure you're pointing me to a valid image file.").edit(ctx, message)
			if os.path.exists(path):
				GetImage.remove(path)
			return

		message = await Message.Embed(description="Uploading...").edit(ctx, message)
		message = await Message.Embed(file=path, title="Moar Jpeg!").edit(ctx, message)
		GetImage.remove(path)
