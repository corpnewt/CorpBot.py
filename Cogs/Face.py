import asyncio
import discord
from   discord.ext import commands

# This is the Face module. It sends faces.

class Face:

	# Init with the bot reference, and a reference to the settings var
	def __init__(self, bot):
		self.bot = bot

	@commands.command(pass_context=True)
	async def lenny(self, ctx, *, message : str = None):
		"""Give me some Lenny."""
		# Remove original message
		await self.bot.delete_message(ctx.message)
		msg = "( ͡° ͜ʖ ͡°)"
		if message:
			msg += "\n{}".format(message)
		await self.bot.send_message(ctx.message.channel, msg)

	@commands.command(pass_context=True)
	async def shrug(self, ctx, *, message : str = None):
		"""Shrug it off."""
		# Remove original message
		await self.bot.delete_message(ctx.message)
		msg = "¯\_(ツ)_/¯"
		if message:
			msg += "\n{}".format(message)
		await self.bot.send_message(ctx.message.channel, msg)

	
