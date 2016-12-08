import asyncio
import discord
from   discord.ext import commands

# This is the Face module. It sends faces.

class Face:

	# Init with the bot reference, and a reference to the settings var
	def __init__(self, bot):
		self.bot = bot

	@commands.command(pass_context=True)
	async def lenny(self, ctx):
		"""Give me some Lenny."""
		# Remove original message
		await self.bot.delete_message(ctx.message)
		await self.bot.send_message(ctx.message.channel, "( ͡° ͜ʖ ͡°)")

	@commands.command(pass_context=True)
	async def shrug(self, ctx):
		"""Shrug it off."""
		# Remove original message
		await self.bot.delete_message(ctx.message)
		await self.bot.send_message(ctx.message.channel, "¯\_(ツ)_/¯")

	