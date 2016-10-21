import asyncio
import discord
from   discord.ext import commands
from   Cogs import Settings

# This is the Bot module - it contains things like nickname, status, etc

class Bot:

	# Init with the bot reference, and a reference to the settings var
	def __init__(self, bot, settings):
		self.bot = bot
		self.settings = settings
		
	def message(self, message):
		# Check the message and see if we should allow it - always yes.
		# This module doesn't need to cancel messages.
		return { 'Ignore' : False, 'Delete' : False}
		
	@commands.command(pass_context=True)
	async def nickname(self, ctx, name : str = None):
		"""Set the bot's nickname (admin-only)."""
		
		isAdmin = ctx.message.author.permissions_in(ctx.message.channel).administrator
		# Only allow admins to change server stats
		if not isAdmin:
			await self.bot.send_message(ctx.message.channel, 'You do not have sufficient privileges to access this command.')
			return
		
		# Let's get the bot's member in the current server
		botName = "{}#{}".format(self.bot.user.name, self.bot.user.discriminator)
		botMember = ctx.message.server.get_member_named(botName)
		await self.bot.change_nickname(botMember, name)
		
	@commands.command(pass_context=True)
	async def playgame(self, ctx, game : str = None):
		"""Sets the playing status of the bot (admin only)."""
		isAdmin = ctx.message.author.permissions_in(ctx.message.channel).administrator
		# Only allow admins to change server stats
		if not isAdmin:
			await self.bot.send_message(ctx.message.channel, 'You do not have sufficient privileges to access this command.')
			return

		if game == None:
			await self.bot.change_presence(game=None)
			return

		await self.bot.change_presence(game=discord.Game(name=game))

	@commands.command(pass_context=True)
	async def setbotparts(self, ctx, parts : str = None):
		"""Set the bot's parts - can be a url, formatted text, or nothing to clear."""
		
		isAdmin = ctx.message.author.permissions_in(ctx.message.channel).administrator
		# Only allow admins to change server stats
		if not isAdmin:
			await self.bot.send_message(ctx.message.channel, 'You do not have sufficient privileges to access this command.')
			return

		channel = ctx.message.channel
		author  = ctx.message.author
		server  = ctx.message.server

		if not parts:
			parts = ""
			
		self.settings.setUserStat(self.bot.user, server, "Parts", parts)
		msg = '*{}\'s* parts have been set to:\n{}'.format(self.bot.user.name, parts)
		await self.bot.send_message(channel, msg)