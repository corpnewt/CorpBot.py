import asyncio, discord, time, random, warnings, re, giphypop
from   operator import itemgetter
from   discord.ext import commands
from   Cogs import Utils, GetImage, Message, DisplayName

async def setup(bot):
	# Add the bot and deps
	settings = bot.get_cog("Settings")
	bot.add_cog(Giphy(bot, settings))

class Giphy(commands.Cog):

	# Init with the bot reference, and a reference to the settings var and xp var
	def __init__(self, bot, settings):
		self.bot = bot
		self.settings = settings
		self.ua = 'CorpNewt DeepThoughtBot'
		# Instantiate giphypop, but suppress the warning message
		with warnings.catch_warnings():
			warnings.simplefilter("ignore")
			self.giphy = giphypop.Giphy()
		global Utils, DisplayName
		Utils = self.bot.get_cog("Utils")
		DisplayName = self.bot.get_cog("DisplayName")
			
	def canDisplay(self, server):
		# Check if we can display images
		lastTime = int(self.settings.getServerStat(server, "LastPicture"))
		threshold = int(self.settings.getServerStat(server, "PictureThreshold"))
		if not GetImage.canDisplay( lastTime, threshold ):
			# await channel.send('Too many images at once - please wait a few seconds.')
			return False
		# If we made it here - set the LastPicture method
		self.settings.setServerStat(server, "LastPicture", int(time.time()))
		return True

	@commands.command(pass_context=True)
	async def addgif(self, ctx, *, role : str = None):
		"""Adds a new role to the gif list (admin only)."""
		usage = 'Usage: `{}addgif [role]`'.format(ctx.prefix)
		if not await Utils.is_admin_reply(ctx): return
		if role == None:
			return await ctx.send(usage)
		roleName = role
		if type(role) is str:
			if role.lower() == "everyone" or role.lower() == "@everyone":
				role = ctx.guild.default_role
			else:
				role = DisplayName.roleForName(roleName, ctx.guild)
			if not role:
				msg = 'I couldn\'t find *{}*...'.format(roleName)
				return await ctx.send(Utils.suppressed(ctx,msg))
		# Now we see if we already have that role in our list
		promoArray = self.settings.getServerStat(ctx.guild, "GifArray")
		if any(x for x in promoArray if str(x["ID"]) == str(role.id)):
			msg = '**{}** is already in the list.'.format(role.name)
			return await ctx.send(Utils.suppressed(ctx,msg))
		# If we made it this far - then we can add it
		promoArray.append({ 'ID' : role.id, 'Name' : role.name })
		self.settings.setServerStat(ctx.guild, "GifArray", promoArray)
		msg = '**{}** added to list.'.format(role.name)
		await ctx.send(Utils.suppressed(ctx,msg))
		
	@commands.command(pass_context=True)
	async def removegif(self, ctx, *, role : str = None):
		"""Removes a role from the gif list (admin only)."""
		usage = 'Usage: `{}removegif [role]`'.format(ctx.prefix)
		if not await Utils.is_admin_reply(ctx): return
		if role == None:
			return await ctx.send(usage)
		# Name placeholder
		roleName = role
		if type(role) is str:
			if role.lower() == "everyone" or role.lower() == "@everyone":
				role = ctx.guild.default_role
			else:
				role = DisplayName.roleForName(role, ctx.guild)
		# If we're here - then the role is a real one
		promoArray = self.settings.getServerStat(ctx.guild, "GifArray")
		# Check by id first, then by name
		found_role = next((x for x in promoArray if str(x["ID"])==str(role.id)),False)
		if not found_role:
			found_role = next((x for x in promoArray if x["Name"].lower()==role.name.lower()),False)
		if found_role:
			promoArray.remove(found_role)
			self.settings.setServerStat(ctx.guild, "GifArray", promoArray)
			msg = '**{}** removed successfully.'.format(found_role['Name'])
			return await ctx.send(Utils.suppressed(ctx,msg))
		# If we made it this far - then we didn't find it
		msg = '**{}** not found in list.'.format(role)
		await ctx.send(Utils.suppressed(ctx,msg))

	@commands.command(pass_context=True)
	async def listgif(self, ctx):
		"""Lists gif roles and id's."""
		promoArray = self.settings.getServerStat(ctx.guild, "GifArray")
		promoSorted = sorted(promoArray, key=itemgetter('Name'))
		if not len(promoSorted):
			roleText = "There are no gif roles set yet.  Use `{}addgif [role]` to add some.".format(ctx.prefix)
			return await ctx.channel.send(roleText)
		roleText = "__**Current Gif Roles:**__\n\n"
		for arole in promoSorted:
			role = ctx.guild.get_role(int(arole["ID"]))
			roleText += "**{}** (removed from server)\n".format(arole["Name"]) if role is None else "**{}** (ID : `{}`)\n".format(role.name, arole["ID"])
		await ctx.send(Utils.suppressed(ctx,roleText))

	@commands.command(pass_context=True)
	async def gif(self, ctx, *, gif = None):
		"""Search for some giphy!"""
		if not Utils.is_bot_admin(ctx):
			gif_array = self.settings.getServerStat(ctx.guild, "GifArray", [])
			if not any(x for x in gif_array for y in ctx.author.roles if str(x["ID"]) == str(y.id)):
				return await ctx.send("You do not have sufficient privileges to access this command.")
		if not self.canDisplay(ctx.guild):
			return

		if not gif == None:
			gif = re.sub(r'([^\s\w]|_)+', '', gif)

		my_gif = None

		if gif == None:
			# Random
			try:
				my_gif = self.giphy.random_gif()
			except Exception:
				my_gif = None
		else:
			try:
				my_gif = random.choice(list(self.giphy.search(phrase=gif, limit=20)))
			except Exception:
				my_gif = None
		
		if my_gif == None:
			return await ctx.send("I couldn't get a working link!")
		
		try:
			gif_url = my_gif["original"]["url"].split("?")[0]
		except:
			gif_url = None
		if not gif_url:
			return await ctx.send("I couldn't get a working link!")
		try:
			title = my_gif["raw_data"]["title"]
		except:
			title = "Gif for \"{}\"".format(gif)	
		await Message.Embed(title=title, image=gif_url, url=gif_url, color=ctx.author).send(ctx)