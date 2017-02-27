import asyncio
import discord
import time
import requests
import urllib
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
		self.botID = 'b0a6a41a5e345c23' # Lisa
		self.botName = 'Lisa'
		self.botList = []

	async def onready(self):
		# We're ready - let's load the bots
		await self._getBots()

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

	def find_first_between( self, source, start_sep, end_sep ):
		result=[]
		tmp=source.split(start_sep)
		for par in tmp:
			if end_sep in par:
				result.append(par.split(end_sep)[0])
		if len(result) == 0:
			return None
		else:
			return result[0]

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
	async def setpersonality(self, ctx, *, name = None):
		"""Sets the bots personality (owner only).  List available here:  http://pandorabots.com/botmaster/en/mostactive"""
		
		channel = ctx.message.channel
		author  = ctx.message.author
		server  = ctx.message.server

		# Only allow owner to change server stats
		serverDict = self.settings.serverDict

		try:
			owner = serverDict['Owner']
		except KeyError:
			owner = None

		if owner == None:
			# No owner set
			msg = 'I have not been claimed, *yet*.'
			await self.bot.send_message(channel, msg)
			return
		else:
			if not author.id == owner:
				msg = 'You are not the *true* owner of me.  Only the rightful owner can change my personality.'
				await self.bot.send_message(channel, msg)
				return
		
		# Update bot list
		await self._getBots()
		if name == None:
			await self.bot.send_message(ctx.message.channel, 'You need to specify a bot name.  List here:  http://pandorabots.com/botmaster/en/mostactive')
			return
		
		# Fuzzy match
		nameMatch = FuzzySearch.search(name, self.botList, 'Name', 1)
		self.botID = nameMatch[0]['Item']['ID']
		self.botName = nameMatch[0]['Item']['Name']
		if nameMatch[0]['Ratio'] < 1:
			# Not a perfect match - state assumption
			msg = "I'll assume you meant *{}.*  Personality set!".format(nameMatch[0]['Item']['Name'])
		else:
			# Perfect match
			msg = "Personality set to *{}!*".format(nameMatch[0]['Item']['Name'])
		await self.bot.send_message(ctx.message.channel, msg)
		

	@commands.command(pass_context=True)
	async def personality(self, ctx):
		"""Lists the bot's current personality."""
		msg = 'My current personality is *{}*.'.format(self.botName)
		await self.bot.send_message(ctx.message.channel, msg)


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


	async def _getBots(self):
		# Get the available bots

		url = "http://pandorabots.com/botmaster/en/mostactive"
		r = requests.request('POST', url)

		doc = pq(r.text)

		r.close()

		startIndex = 15 # Found by stupid trial and error
		endIndex = len(doc('body').find('table').children())-1

		botList=[]

		for i in range(startIndex, endIndex):
			# Let's get our stuff.
			theDoc = doc('body').find('table').children().eq(i)
			botString = str(theDoc.children().eq(1).children().eq(0))
			botid   = self.find_first_between(botString, '/pandora/talk?botid=', '" target=')
			botName = self.find_first_between(botString, '">', '</a>')

			if botid and botName:
				# Add to our list
				botList.append({ 'Name': botName, 'ID': botid })

		self.botList = botList


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
		# message = message.replace('/', '')
		quotes = urllib.parse.quote(message)

		# Setup request
		payload = 'botcust2=b5abd28d7f2caa9b&input=' + quotes
		options = {
            'hostname': 'sheepridge.pandorabots.com',
            'port': 80,
            'path': '/pandora/talk?botid=' + self.botID + '&skin=custom_input',
            'method': 'POST',
            'headers': {
                'Content-Type': 'application/x-www-form-urlencoded',
                'Host': 'sheepridge.pandorabots.com',
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.12; rv:53.0) Gecko/20100101 Firefox/53.0',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                # 'Accept-Encoding': 'gzip, deflate',
                'Referer': 'http://sheepridge.pandorabots.com/pandora/talk?botid=b69b8d517e345aba&skin=custom_input',
                'Content-Type': 'application/x-www-form-urlencoded',
                'Cookie': 'botcust2=b5abd28d7f2caa9b',
                'Content-Length': len(payload),
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': 1
            }
		}

		url = "http://pandorabots.com/pandora/talk?botid=b0a6a41a5e345c23"
		r = requests.request('POST', url, params=options)

		if not r:
			await self.bot.send_message(channel, "I'm sorry - I can't talk right now.")
			return
		r2 = requests.request('POST', url, params=payload)
		if not r2:
			await self.bot.send_message(channel, "I'm sorry - I can't talk right now.")
			return
		doc = pq(r2.text)

		r2.close()

		chLen = len(doc('body').children())
		response = str(doc('body').children().eq(6))
		res = response.split('</b> ')
		if not len(res) > 1:
			await self.bot.send_message(channel, "I'm sorry - I can't talk right now.")
			return

		msg = res[1]

		if not msg:
			return
		# Check for suppress
		if suppress:
			msg = Nullify.clean(msg)
		await self.bot.send_message(channel, msg)