import asyncio
import discord
import time
import random
import giphypop
import re
from   operator import itemgetter
from   discord.ext import commands
from   Cogs import GetImage
from   Cogs import Message
from   Cogs import Nullify
from   Cogs import DisplayName

def setup(bot):
	# Add the bot and deps
	settings = bot.get_cog("Settings")
	bot.add_cog(Giphy(bot, settings))

class Giphy:

	# Init with the bot reference, and a reference to the settings var and xp var
	def __init__(self, bot, settings):
		self.bot = bot
		self.settings = settings
		self.ua = 'CorpNewt DeepThoughtBot'
		self.giphy = giphypop.Giphy()
			
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

		# Check if we're suppressing @here and @everyone mentions
		if self.settings.getServerStat(ctx.message.guild, "SuppressMentions"):
			suppress = True
		else:
			suppress = False

		isAdmin = ctx.message.author.permissions_in(ctx.message.channel).administrator
		# Only allow admins to change server stats
		if not isAdmin:
			await ctx.message.channel.send('You do not have sufficient privileges to access this command.')
			return

		if role == None:
			await ctx.message.channel.send(usage)
			return

		roleName = role
		if type(role) is str:
			if role.lower() == "everyone" or role.lower() == "@everyone":
				role = ctx.guild.default_role
			else:
				role = DisplayName.roleForName(roleName, ctx.guild)
			if not role:
				msg = 'I couldn\'t find *{}*...'.format(roleName)
				# Check for suppress
				if suppress:
					msg = Nullify.clean(msg)
				await ctx.message.channel.send(msg)
				return

		# Now we see if we already have that role in our list
		promoArray = self.settings.getServerStat(ctx.message.guild, "GifArray")

		for aRole in promoArray:
			# Get the role that corresponds to the id
			if str(aRole['ID']) == str(role.id):
				# We found it - throw an error message and return
				msg = '**{}** is already in the list.'.format(role.name)
				# Check for suppress
				if suppress:
					msg = Nullify.clean(msg)
				await ctx.message.channel.send(msg)
				return

		# If we made it this far - then we can add it
		promoArray.append({ 'ID' : role.id, 'Name' : role.name })
		self.settings.setServerStat(ctx.message.guild, "GifArray", promoArray)

		msg = '**{}** added to list.'.format(role.name)
		# Check for suppress
		if suppress:
			msg = Nullify.clean(msg)
		await ctx.message.channel.send(msg)
		return

	@addgif.error
	async def addgif_error(self, ctx, error):
		# do stuff
		msg = 'addgif Error: {}'.format(error)
		await ctx.send(msg)
		
		
	@commands.command(pass_context=True)
	async def removegif(self, ctx, *, role : str = None):
		"""Removes a role from the gif list (admin only)."""

		usage = 'Usage: `{}removegif [role]`'.format(ctx.prefix)

		# Check if we're suppressing @here and @everyone mentions
		if self.settings.getServerStat(ctx.message.guild, "SuppressMentions"):
			suppress = True
		else:
			suppress = False

		isAdmin = ctx.message.author.permissions_in(ctx.message.channel).administrator
		# Only allow admins to change server stats
		if not isAdmin:
			await ctx.message.channel.send('You do not have sufficient privileges to access this command.')
			return

		if role == None:
			await ctx.message.channel.send(usage)
			return

		# Name placeholder
		roleName = role
		if type(role) is str:
			if role.lower() == "everyone" or role.lower() == "@everyone":
				role = ctx.guild.default_role
			else:
				role = DisplayName.roleForName(role, ctx.guild)

		# If we're here - then the role is a real one
		promoArray = self.settings.getServerStat(ctx.message.guild, "GifArray")

		for aRole in promoArray:
			# Check for Name
			if aRole['Name'].lower() == roleName.lower():
				# We found it - let's remove it
				promoArray.remove(aRole)
				self.settings.setServerStat(ctx.message.guild, "GifArray", promoArray)
				msg = '**{}** removed successfully.'.format(aRole['Name'])
				# Check for suppress
				if suppress:
					msg = Nullify.clean(msg)
				await ctx.message.channel.send(msg)
				return

			# Get the role that corresponds to the id
			if role and (str(aRole['ID']) == str(role.id)):
				# We found it - let's remove it
				promoArray.remove(aRole)
				self.settings.setServerStat(ctx.message.guild, "GifArray", promoArray)
				msg = '**{}** removed successfully.'.format(role.name)
				# Check for suppress
				if suppress:
					msg = Nullify.clean(msg)
				await ctx.message.channel.send(msg)
				return

		# If we made it this far - then we didn't find it
		msg = '**{}** not found in list.'.format(aRole['Name'])
		# Check for suppress
		if suppress:
			msg = Nullify.clean(msg)
		await ctx.message.channel.send(msg)

	@removegif.error
	async def removegif_error(self, error, ctx):
		# do stuff
		msg = 'removegif Error: {}'.format(error)
		await ctx.channel.send(msg)

	@commands.command(pass_context=True)
	async def listgif(self, ctx):
		"""Lists gif roles and id's."""

		# Check if we're suppressing @here and @everyone mentions
		if self.settings.getServerStat(ctx.message.guild, "SuppressMentions"):
			suppress = True
		else:
			suppress = False

		promoArray = self.settings.getServerStat(ctx.message.guild, "GifArray")
		
		# rows_by_lfname = sorted(rows, key=itemgetter('lname','fname'))
		
		promoSorted = sorted(promoArray, key=itemgetter('Name'))

		if not len(promoSorted):
			roleText = "There are no gif roles set yet.  Use `{}addgif [role]` to add some.".format(ctx.prefix)
			await ctx.channel.send(roleText)
			return
		
		roleText = "__**Current Gif Roles:**__\n\n"

		for arole in promoSorted:
			found = False
			for role in ctx.message.guild.roles:
				if str(role.id) == str(arole["ID"]):
					# Found the role ID
					found = True
					roleText = '{}**{}** (ID : `{}`)\n'.format(roleText, role.name, arole['ID'])
			if not found:
				roleText = '{}**{}** (removed from server)\n'.format(roleText, arole['Name'])

		# Check for suppress
		if suppress:
			roleText = Nullify.clean(roleText)

		await ctx.channel.send(roleText)

	@commands.command(pass_context=True)
	async def gif(self, ctx, *, gif = None):
		"""Search for some giphy!"""
		channel = ctx.message.channel
		author  = ctx.message.author
		server  = ctx.message.guild

		# Check if we're admin - or can use this command
		isAdmin = ctx.message.author.permissions_in(ctx.message.channel).administrator
		if not isAdmin:
			checkAdmin = self.settings.getServerStat(ctx.message.guild, "GifArray")
			for role in ctx.message.author.roles:
				for aRole in checkAdmin:
					# Get the role that corresponds to the id
					if str(aRole['ID']) == str(role.id):
						isAdmin = True
		# Only allow admins to change server stats
		if not isAdmin:
			await ctx.channel.send('You do not have sufficient privileges to access this command.')
			return

		if not self.canDisplay(server):
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
				my_gif = self.giphy.search(phrase=gif, limit=20)
				my_gif = list(my_gif)
				my_gif = random.choice(my_gif)
			except Exception:
				my_gif = None
		
		if my_gif == None:
			await ctx.send("I couldn't get a working link!")
			return
		
		try:
			gif_url = my_gif["original"]["url"].split("?")[0]
		except:
			gif_url = None
		try:
			title = my_gif["raw_data"]["title"]
		except:
			title = "Gif for \"{}\"".format(gif)
		if not gif_url:
			await ctx.send("I couldn't get a working link!")
			return
			
		# Download Image
		await Message.Embed(title=title, image=gif_url, url=gif_url, color=ctx.author).send(ctx)
		# await ctx.send(my_gif)
