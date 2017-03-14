import asyncio
import discord
import time
import requests
import urllib
import os
from aiml import Kernel
from os import listdir
from discord.ext import commands
from Cogs import Nullify
from pyquery import PyQuery as pq
from Cogs import FuzzySearch

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

	async def onready(self):
		# We're ready - let's load the bots
		if not os.path.exists(self.botBrain):
			# No brain, let's learn and create one
			files = listdir(self.botDir)
			for file in files:
				self.chatBot.learn(self.botDir + '/' + file)
			# Save brain
			self.chatBot.saveBrain("standard.brn")
		else:
			# Already have a brain - load it
			self.chatBot.bootstrap(brainFile="standard.brn")
		# Learned by this point - let's set our owner's name/gender
		# Start the convo
		self.chatBot.respond('Hello')
		# Bot asks for our Name
		self.chatBot.respond('My name is {}'.format(self.ownerName))
		# Bot asks for our gender
		self.chatBot.respond('I am a {}'.format(self.ownerGender))

	def canChat(self, server):
		# Check if we can display images
		lastTime = int(self.settings.getServerStat(server, "LastChat"))
		threshold = int(self.waitTime)
		currentTime = int(time.time())

		if currentTime < (int(lastTime) + int(threshold)):
			return False
		
		# If we made it here - set the LastPicture method
		self.settings.setServerStat(server, "LastChat", int(time.time()))
		return True

	async def message(self, message):
		# Check the message and see if we should allow it - always yes.
		# This module doesn't need to cancel messages.
		ignore = False
		delete = False
		msg = message.content
		chatChannel = self.settings.getServerStat(message.server, "ChatChannel")
		if chatChannel and not message.author == self.bot.user and not msg.startswith(self.prefix):
			# We have a channel
			if message.channel.id == chatChannel:
				# We're in that channel!
				#ignore = True
				# Strip prefix
				pre = '{}chat '.format(self.prefix)
				msg = message.content
				if msg.lower().startswith(pre):
					msg = msg[len(pre):]
				await self._chat(message.channel, message.server, msg)
		return { 'Ignore' : ignore, 'Delete' : delete}


	@commands.command(pass_context=True)
	async def setchatchannel(self, ctx, *, channel : discord.Channel = None):
		"""Sets the channel for bot chatter."""
		isAdmin = ctx.message.author.permissions_in(ctx.message.channel).administrator
		# Only allow admins to change server stats
		if not isAdmin:
			await self.bot.send_message(ctx.message.channel, 'You do not have sufficient privileges to access this command.')
			return

		if channel == None:
			self.settings.setServerStat(ctx.message.server, "ChatChannel", "")
			msg = 'Chat channel removed - must use the `{}chat [message]` command to chat.'.format(ctx.prefix)
			await self.bot.send_message(ctx.message.channel, msg)
			return

		# If we made it this far - then we can add it
		self.settings.setServerStat(ctx.message.server, "ChatChannel", channel.id)
		msg = 'Chat channel set to **{}**.'.format(channel.name)
		await self.bot.send_message(ctx.message.channel, msg)

	@setchatchannel.error
	async def setchatchannel_error(self, ctx, error):
		# do stuff
		msg = 'setchatchannel Error: {}'.format(ctx)
		await self.bot.say(msg)


	@commands.command(pass_context=True)
	async def chat(self, ctx, *, message = None):
		"""Chats with the bot."""
		await self._chat(ctx.message.channel, ctx.message.server, message)


	async def _chat(self, channel, server, message):
		# Check if we're suppressing @here and @everyone mentions
		if self.settings.getServerStat(server, "SuppressMentions").lower() == "yes":
			suppress = True
		else:
			suppress = False
		if message == None:
			return
		if not self.canChat(server):
			return
		await self.bot.send_typing(channel)
		
		# Sanitize input string
		PERMITTED_CHARS = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ `~!@#$%^&*()_+-=[{}]\|/?.>,<;:'\"" 
		message = "".join(c for c in message if c in PERMITTED_CHARS)

		msg = self.chatBot.respond(message)

		if not msg:
			return
		# Check for suppress
		if suppress:
			msg = Nullify.clean(msg)
		await self.bot.send_message(channel, msg)
