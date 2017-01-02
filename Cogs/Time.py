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
	async def time(self, ctx, offset : str = '0:0'):
		"""Get UTC time +- an offset."""

		# Split time string by : and get hour/minute values
		try:
			hours, minutes = map(int, offset.split(':'))
		except Exception:
			try:
				hours = int(offset)
				minutes = 0
			except Exception:
				await self.bot.say('Offset has to be in +-H:M!')
				return

		msg = 'UTC'
		# Get the time
		t = datetime.datetime.utcnow()
		# Apply offset
		if hours > 0:
			# Apply positive offset
			msg += '+{}'.format(offset)
			td = datetime.timedelta(hours=hours, minutes=minutes)
			newTime = t + td
		elif hours < 0:
			# Apply negative offset
			msg += '{}'.format(offset)
			td = datetime.timedelta(hours=(-1*hours), minutes=(-1*minutes))
			newTime = t - td
		else:
			# No offset
			newTime = t

		msg = '{} is currently *{}*'.format(msg, newTime.strftime("%I:%M %p"))
		# Say message
		await self.bot.send_message(ctx.message.channel, msg)