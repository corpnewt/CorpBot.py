import asyncio
import discord
import time
import os
from aiml import Kernel
from os import listdir
from discord.ext import commands
from Cogs import Nullify
from pyquery import PyQuery as pq
from Cogs import FuzzySearch
from Cogs import DisplayName

def setup(bot):
	# Add the bot and deps
	settings = bot.get_cog("Settings")
	c_bot = ChatterBot(bot, settings)
	c_bot._load()
	bot.add_cog(c_bot)
	

class ChatterBot:

	# Init with the bot reference, and a reference to the settings var
	def __init__(self, bot, settings, prefix : str = '$'):
		self.bot = bot
		self.settings = settings
		self.prefix = prefix
		self.waitTime = 4 # Wait time in seconds
		self.botDir = 'standard'
		self.botBrain = 'standard.brn'
		self.botList = []
		self.ownerName = "CorpNewt"
		self.ownerGender = "man"
		self.timeout = 3
		self.chatBot = Kernel()

	def _load(self):
		# We're ready - let's load the bots
		if not os.path.exists(self.botBrain):
			# No brain, let's learn and create one
			files = listdir(self.botDir)
			for file in files:
				# Omit files starting with .
				if file.startswith("."):
					continue
				self.chatBot.learn(self.botDir + '/' + file)
			# Save brain
			self.chatBot.saveBrain(self.botBrain)
		else:
			# Already have a brain - load it
			self.chatBot.bootstrap(brainFile=self.botBrain)
		# Learned by this point - let's set our owner's name/gender
		# Start the convo
		self.chatBot.respond('Hello')
		# Bot asks for our Name
		self.chatBot.respond('My name is {}'.format(self.ownerName))
		# Bot asks for our gender
		self.chatBot.respond('I am a {}'.format(self.ownerGender))

	def canChat(self, server):
		# Check if we can chat
		lastTime = int(self.settings.getServerStat(server, "LastChat"))
		threshold = int(self.waitTime)
		currentTime = int(time.time())

		if currentTime < (int(lastTime) + int(threshold)):
			return False
		
		# If we made it here - set the LastPicture method
		self.settings.setServerStat(server, "LastChat", int(time.time()))
		return True
	
	async def killcheck(self, message):
		ignore = False
		for cog in self.bot.cogs:
			real_cog = self.bot.get_cog(cog)
			if real_cog == self:
				# Don't check ourself
				continue
			try:
				check = await real_cog.test_message(message)
			except AttributeError:
				try:
					check = await real_cog.message(message)
				except AttributeError:
					continue
			if not type(check) is dict:
				# Force it to be a dict
				check = {}
			try:
				if check['Ignore']:
					ignore = True
			except KeyError:
				pass
		return ignore


	async def message(self, message):
		# Check the message and see if we should allow it - always yes.
		# This module doesn't need to cancel messages.
		msg = message.content
		chatChannel = self.settings.getServerStat(message.guild, "ChatChannel")
		the_prefix = await self.bot.command_prefix(self.bot, message)
		if chatChannel and not message.author.id == self.bot.user.id and not msg.startswith(the_prefix):
			# We have a channel
			# Now we check if we're hungry/dead and respond accordingly
			if await self.killcheck(message):
				return { "Ignore" : True, "Delete" : False }
			if str(message.channel.id) == str(chatChannel):
				# We're in that channel!
				#ignore = True
				# Strip prefix
				msg = message.content
				await self._chat(message.channel, message.guild, msg)
		return { 'Ignore' : False, 'Delete' : False}


	@commands.command(pass_context=True)
	async def setchatchannel(self, ctx, *, channel : discord.TextChannel = None):
		"""Sets the channel for bot chatter."""
		isAdmin = ctx.message.author.permissions_in(ctx.message.channel).administrator
		# Only allow admins to change server stats
		if not isAdmin:
			await ctx.message.channel.send('You do not have sufficient privileges to access this command.')
			return

		if channel == None:
			self.settings.setServerStat(ctx.message.guild, "ChatChannel", "")
			msg = 'Chat channel removed - must use the `{}chat [message]` command to chat.'.format(ctx.prefix)
			await ctx.message.channel.send(msg)
			return

		# If we made it this far - then we can add it
		self.settings.setServerStat(ctx.message.guild, "ChatChannel", channel.id)
		msg = 'Chat channel set to **{}**.'.format(channel.name)
		await ctx.message.channel.send(msg)

	@setchatchannel.error
	async def setchatchannel_error(self, error, ctx):
		# do stuff
		msg = 'setchatchannel Error: {}'.format(error)
		await ctx.channel.send(msg)


	@commands.command(pass_context=True)
	async def chat(self, ctx, *, message = None):
		"""Chats with the bot."""
		await self._chat(ctx.message.channel, ctx.message.guild, message)


	async def _chat(self, channel, server, message):
		# Check if we're suppressing @here and @everyone mentions

		message = DisplayName.clean_message(message, bot=self.bot, server=server)

		if self.settings.getServerStat(server, "SuppressMentions"):
			suppress = True
		else:
			suppress = False
		if message == None:
			return
		if not self.canChat(server):
			return
		await channel.trigger_typing()

		msg = self.chatBot.respond(message)

		if not msg:
			return
		# Check for suppress
		if suppress:
			msg = Nullify.clean(msg)
		await channel.send(msg)
