import asyncio
import discord
from   operator import itemgetter
from   discord.ext import commands

# This is the Uptime module. It keeps track of how long the bot's been up

class DrBeer:

	# Init with the bot reference, and a reference to the settings var
	def __init__(self, bot):
		self.bot = bot

	def message(self, message):
		# Check the message and see if we should allow it - always yes.
		# This module doesn't need to cancel messages.
		return { 'Ignore' : False, 'Delete' : False}

	@commands.command(pass_context=True)
	async def drbeer(self, ctx):
		"""Put yourself in your place."""
		msg = "Hey, yall. Quit ya horsin' around now. Can't you see I'm busy tryin'a shoot'n all them summersquash?"
		await self.bot.send_message(ctx.message.channel, msg)