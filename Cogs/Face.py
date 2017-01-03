import asyncio
import discord
from   discord.ext import commands
from   Cogs import Settings
from   Cogs import DisplayName

# This is the Face module. It sends faces.

class Face:

	# Init with the bot reference, and a reference to the settings var
	def __init__(self, bot, settings):
		self.bot = bot
		self.settings = settings

	@commands.command(pass_context=True)
	async def lenny(self, ctx, *, message : str = None):
		"""Give me some Lenny."""
		# Log the user
		self.settings.setServerStat(ctx.message.server, "LastLenny", ctx.message.author.id)
		# Remove original message
		await self.bot.delete_message(ctx.message)
		msg = "( ͡° ͜ʖ ͡°)"
		if message:
			msg += "\n{}".format(message)
		await self.bot.send_message(ctx.message.channel, msg)

	@commands.command(pass_context=True)
	async def lastlenny(self, ctx):
		"""Who Lenny'ed last?"""
		lastLen = self.settings.getServerStat(ctx.message.server, "LastLenny")
		msg = 'No one has Lenny\'ed on my watch yet...'
		if lastLen:
			# Got someone
			memberName = DisplayName.name(DisplayName.memberForID(lastLen, ctx.message.server))
			msg = '*{}* was the last person to use the `$lenny` command.'.format(memberName)
		await self.bot.send_message(ctx.message.channel, msg)
		

	@commands.command(pass_context=True)
	async def shrug(self, ctx, *, message : str = None):
		"""Shrug it off."""
		# Log the user
		self.settings.setServerStat(ctx.message.server, "LastShrug", ctx.message.author.id)
		# Remove original message
		await self.bot.delete_message(ctx.message)
		msg = "¯\_(ツ)_/¯"
		if message:
			msg += "\n{}".format(message)
		await self.bot.send_message(ctx.message.channel, msg)

	
	@commands.command(pass_context=True)
	async def lastshrug(self, ctx):
		"""Who shrugged last?"""
		lastLen = self.settings.getServerStat(ctx.message.server, "LastShrug")
		msg = 'No one has shrugged on my watch yet...'
		if lastLen:
			# Got someone
			memberName = DisplayName.name(DisplayName.memberForID(lastLen, ctx.message.server))
			msg = '*{}* was the last person to use the `$shrug` command.'.format(memberName)
		await self.bot.send_message(ctx.message.channel, msg)