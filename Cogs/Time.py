import asyncio
import discord
import datetime
from   discord.ext import commands
from   Cogs import Settings

class Time:

	# Init with the bot reference, and a reference to the settings var
	def __init__(self, bot):
		self.bot = bot

	@commands.command(pass_context=True)
	async def time(self, ctx, offset : int = 0):
		"""Get UTC time +- an offset."""

		msg = 'UTC'
		# Get the time
		t = datetime.datetime.utcnow()
		# Apply offset
		if offset > 0:
			# Apply positive offset
			msg += '+{}'.format(offset)
			td = datetime.timedelta(hours=offset)
			newTime = t + td
		elif offset < 0:
			# Apply negative offset
			msg += '{}'.format(offset)
			td = datetime.timedelta(hours=(-1*offset))
			newTime = t - td
		else:
			# No offset
			newTime = t

		msg = '{} is currently *{}*'.format(msg, newTime.strftime("%I:%M %p"))
		# Say message
		await self.bot.send_message(ctx.message.channel, msg)