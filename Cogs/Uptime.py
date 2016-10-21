import asyncio
import discord
import time
from   operator import itemgetter
from   discord.ext import commands
from   Cogs import ReadableTime

# This is the Uptime module. It keeps track of how long the bot's been up

class Uptime:

	# Init with the bot reference, and a reference to the settings var
	def __init__(self, bot):
		self.bot = bot
		self.startTime = int(time.time())

	def message(self, message):
		# Check the message and see if we should allow it - always yes.
		# This module doesn't need to cancel messages.
		return { 'Ignore' : False, 'Delete' : False}

	@commands.command(pass_context=True)
	async def uptime(self, ctx):
		"""Lists the bot's uptime."""
		currentTime = int(time.time())
		timeString  = ReadableTime.getReadableTimeBetween(self.startTime, currentTime)
		msg = 'I\'ve been up for *{}*.'.format(timeString)
		await self.bot.send_message(ctx.message.channel, msg)