import asyncio
import discord
import datetime
from   discord.ext import commands
from   Cogs import Settings
from   Cogs import DisplayName

class Time:

	# Init with the bot reference, and a reference to the settings var
	def __init__(self, bot, settings):
		self.bot = bot
		self.settings = settings

	@commands.command(pass_context=True)
	async def setoffset(self, ctx, *, offset : str = None):
		"""Set your UTC offset."""

		if offset == None:
			self.settings.setGlobalUserStat(ctx.message.author, "UTCOffset", None)
			msg = '*{}*, your UTC offset has been removed!'.format(DisplayName.name(ctx.message.author))
			await ctx.channel.send(msg)
			return

		offset = offset.replace('+', '')

		# Split time string by : and get hour/minute values
		try:
			hours, minutes = map(int, offset.split(':'))
		except Exception:
			try:
				hours = int(offset)
				minutes = 0
			except Exception:
				await ctx.channel.send('Offset has to be in +-H:M!')
				return
		off = "{}:{}".format(hours, minutes)
		self.settings.setGlobalUserStat(ctx.message.author, "UTCOffset", off)
		msg = '*{}*, your UTC offset has been set to *{}!*'.format(DisplayName.name(ctx.message.author), off)
		await ctx.channel.send(msg)

	@commands.command(pass_context=True)
	async def offset(self, ctx, *, member = None):
		"""See a member's UTC offset."""

		# Check if we're suppressing @here and @everyone mentions
		if self.settings.getServerStat(ctx.message.guild, "SuppressMentions").lower() == "yes":
			suppress = True
		else:
			suppress = False

		if member == None:
			member = ctx.message.author

		if type(member) == str:
			# Try to get a user first
			memberName = member
			member = DisplayName.memberForName(memberName, ctx.message.guild)
			if not member:
				msg = 'Couldn\'t find user *{}*.'.format(memberName)
				# Check for suppress
				if suppress:
					msg = Nullify.clean(msg)
				await ctx.channel.send(msg)
				return

		# We got one
		offset = self.settings.getUserStat(member, ctx.message.guild, "UTCOffset")
		if offset == None:
			msg = '*{}* hasn\'t set their offset yet - they can do so with the `{}setoffset [+-offset]` command.'.format(DisplayName.name(member), ctx.prefix)
			await ctx.channel.send(msg)
			return

		# Split time string by : and get hour/minute values
		try:
			hours, minutes = map(int, offset.split(':'))
		except Exception:
			try:
				hours = int(offset)
				minutes = 0
			except Exception:
				await ctx.channel.send('Offset has to be in +-H:M!')
				return
		
		msg = 'UTC'
		# Apply offset
		if hours > 0:
			# Apply positive offset
			msg += '+{}'.format(offset)
		elif hours < 0:
			# Apply negative offset
			msg += '{}'.format(offset)

		msg = '*{}\'s* offset is *{}*'.format(DisplayName.name(member), msg)
		await ctx.channel.send(msg)



	@commands.command(pass_context=True)
	async def time(self, ctx, *, offset : str = None):
		"""Get UTC time +- an offset."""

		if offset == None:
			member = ctx.message.author
		else:
			# Try to get a user first
			member = DisplayName.memberForName(offset, ctx.message.guild)

		if member:
			# We got one
			offset = self.settings.getUserStat(member, ctx.message.guild, "UTCOffset")
		
		if offset == None:
			msg = '*{}* hasn\'t set their offset yet - they can do so with the `{}setoffset [+-offset]` command.\nThe current UTC time is *{}*.'.format(DisplayName.name(member), ctx.prefix, datetime.datetime.utcnow().strftime("%I:%M %p"))
			await ctx.channel.send(msg)
			return

		offset = offset.replace('+', '')

		# Split time string by : and get hour/minute values
		try:
			hours, minutes = map(int, offset.split(':'))
		except Exception:
			try:
				hours = int(offset)
				minutes = 0
			except Exception:
				await ctx.channel.send('Offset has to be in +-H:M!')
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

		if member:
			msg = '{}; where *{}* is, it\'s currently *{}*'.format(msg, DisplayName.name(member), newTime.strftime("%I:%M %p"))
		else:
			msg = '{} is currently *{}*'.format(msg, newTime.strftime("%I:%M %p"))
		# Say message
		await ctx.channel.send(msg)
