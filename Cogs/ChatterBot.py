import asyncio, discord, time, os
from discord.ext import commands
from aiml import Kernel
from Cogs import Utils, DisplayName

async def setup(bot):
	# Add the bot and deps
	settings = bot.get_cog("Settings")
	c_bot = ChatterBot(bot, settings)
	c_bot._load()
	await bot.add_cog(c_bot)
	

class ChatterBot(commands.Cog):

	# Init with the bot reference, and a reference to the settings var
	def __init__(self, bot, settings, prefix : str = '$'):
		self.bot = bot
		self.settings = settings
		self.prefix = prefix
		self.waitTime = 4 # Wait time in seconds
		self.botDir = 'standard'
		self.botBrain = 'standard.brn'
		self.botList = []
		self.lastChat = None
		self.timeout = 3
		self.chatBot = Kernel()
		global Utils, DisplayName
		Utils = self.bot.get_cog("Utils")
		DisplayName = self.bot.get_cog("DisplayName")

	def _load(self):
		# We're ready - let's load the bots
		if not os.path.exists(self.botBrain):
			# No brain, let's learn and create one
			files = os.listdir(self.botDir)
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

	def canChat(self, server):
		if not server: return True # No settings to check here
		# Check if we can chat
		lastTime = int(self.settings.getServerStat(server, "LastChat", 0))
		threshold = int(self.waitTime)
		currentTime = int(time.time())

		if currentTime < (int(lastTime) + int(threshold)):
			return False
		
		# If we made it here - set the LastPicture method
		self.settings.setServerStat(server, "LastChat", int(time.time()))
		return True
	
	async def killcheck(self, message):
		for cog in self.bot.cogs:
			real_cog = self.bot.get_cog(cog)
			if real_cog == self: continue
			try: check = await real_cog.test_message(message)
			except AttributeError:
				try: check = await real_cog.message(message)
				except AttributeError: continue
			if not isinstance(check,dict): continue
			if check.get("Ignore"): return True
		return False


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
				ctx = await self.bot.get_context(message)
				await self._chat(ctx, msg)
		return { 'Ignore' : False, 'Delete' : False}


	@commands.command()
	async def setchatchannel(self, ctx, *, channel : discord.TextChannel = None):
		"""Sets the channel for bot chatter."""
		if not await Utils.is_admin_reply(ctx): return

		if channel == None:
			self.settings.setServerStat(ctx.guild, "ChatChannel", "")
			msg = 'Chat channel removed - must use the `{}chat [message]` command to chat.'.format(ctx.prefix)
			await ctx.send(msg)
			return

		# If we made it this far - then we can add it
		self.settings.setServerStat(ctx.guild, "ChatChannel", channel.id)
		msg = 'Chat channel set to **{}**.'.format(channel.name)
		await ctx.send(msg)

	@setchatchannel.error
	async def setchatchannel_error(self, error, ctx):
		# do stuff
		msg = 'setchatchannel Error: {}'.format(error)
		await ctx.send(msg)


	@commands.command()
	async def chat(self, ctx, *, message = None):
		"""Chats with the bot."""
		await self._chat(ctx, message)


	async def _chat(self, ctx, message):
		# Check if we're suppressing @here and @everyone mentions
		message = Utils.suppressed(ctx,message,force=True)
		if message == None or not self.canChat(ctx.guild):
			return
		await ctx.trigger_typing()

		# Check if the message we're responding to is from a new user
		# and retain that info as needed.
		if ctx.author != self.lastChat:
			self.lastChat = ctx.author
			self.chatBot.respond("My name is {}".format(DisplayName.name(ctx.author)))
			self.chatBot.respond("I am genderless")
		
		msg = self.chatBot.respond(message)
		msg = msg if msg else "I don't know what to say..."
		if len(msg) > 2000: msg = msg[:1997]+"..." # Fix for > 2000 chars
		await ctx.send(msg)
