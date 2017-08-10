import asyncio
import discord
import datetime
import pytz
from   discord.ext import commands
from   Cogs import FuzzySearch
from   Cogs import Settings
from   Cogs import DisplayName
from   Cogs import Message
from   Cogs import Nullify

class Time:

	# Init with the bot reference, and a reference to the settings var
	def __init__(self, bot, settings):
		self.bot = bot
		self.settings = settings


	@commands.command(pass_context=True)
	async def settz(self, ctx, *, tz : str = None):
		"""Sets your TimeZone - Overrides your UTC offset - and accounts for DST."""
		usage = 'Usage: `{}settz [Region/City]`\nYou can get a list of available TimeZones with `{}listtz`'.format(ctx.prefix, ctx.prefix)
		if not tz:
			self.settings.setGlobalUserStat(ctx.author, "TimeZone", None)
			await ctx.channel.send("*{}*, your TimeZone has been removed!".format(DisplayName.name(ctx.author)))
			return
		
		# Let's get the timezone list
		tz_list = FuzzySearch.search(tz, pytz.all_timezones, None, 3)
		if not tz_list[0]['Ratio'] == 1:
			# We didn't find a complete match
			msg = "I couldn't find that TimeZone!\n\nMaybe you meant one of the following?\n```"
			for tz in tz_list:
				msg += tz['Item'] + "\n"
			msg += '```'
			await ctx.channel.send(msg)
			return
		# We got a time zone
		self.settings.setGlobalUserStat(ctx.author, "TimeZone", tz_list[0]['Item'])
		await ctx.channel.send("TimeZone set to *{}!*".format(tz_list[0]['Item']))

	
	@commands.command(pass_context=True)
	async def listtz(self, ctx, *, tz_search = None):
		"""List all the supported TimeZones in PM."""

		if not tz_search:
			msg = "__Available TimeZones:__\n\n"
			for tz in pytz.all_timezones:
				msg += tz + "\n"
		else:
			tz_list = FuzzySearch.search(tz_search, pytz.all_timezones)
			msg = "__Top 3 TimeZone Matches:__\n\n"
			for tz in tz_list:
				msg += tz['Item'] + "\n"

		await Message.say(self.bot, msg, ctx.channel, ctx.author, 1)


	@commands.command(pass_context=True)
	async def tz(self, ctx, *, member = None):
		"""See a member's TimeZone."""
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
		timezone = self.settings.getGlobalUserStat(member, "TimeZone")
		if timezone == None:
			msg = '*{}* hasn\'t set their TimeZone yet - they can do so with the `{}settz [Region/City]` command.'.format(DisplayName.name(member), ctx.prefix)
			await ctx.channel.send(msg)
			return

		msg = '*{}\'s* TimeZone is *{}*'.format(DisplayName.name(member), timezone)
		await ctx.channel.send(msg)

		
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
		offset = self.settings.getGlobalUserStat(member, "UTCOffset")
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
		timezone = None
		if offset == None:
			member = ctx.message.author
		else:
			# Try to get a user first
			member = DisplayName.memberForName(offset, ctx.message.guild)

		if member:
			# We got one
			# Check for timezone first
			offset = self.settings.getGlobalUserStat(member, "TimeZone")
			if offset == None:
				offset = self.settings.getGlobalUserStat(member, "UTCOffset")
		
		if offset == None:
			msg = '*{}* hasn\'t set their TimeZone or offset yet - they can do so with the `{}setoffset [+-offset]` or `{}settz [Region/City]` command.\nThe current UTC time is *{}*.'.format(DisplayName.name(member), ctx.prefix, ctx.prefix, datetime.datetime.utcnow().strftime("%I:%M %p"))
			await ctx.channel.send(msg)
			return

		# At this point - we need to determine if we have an offset - or possibly a timezone passed
		t = self.getTimeFromTZ(offset)
		if t == None:
			# We did not get an offset
			t = self.getTimeFromOffset(offset)
			if t == None:
				await ctx.channel.send("I couldn't find that TimeZone or offset!")
				return

		if member:
			msg = '{}; where *{}* is, it\'s currently *{}*'.format(t["zone"], DisplayName.name(member), t["time"])
		else:
			msg = '{} is currently *{}*'.format(t["zone"], t["time"])
		
		# Say message
		await ctx.channel.send(msg)
		
		
	def getUserTime(self, member, settings, time = None):
		# Returns a dict representing the time from the passed member's perspective
		offset = settings.getGlobalUserStat(member, "TimeZone")
		if offset == None:
			offset = settings.getGlobalUserStat(member, "UTCOffset")
		if offset == None:
			# No offset or tz
			return { "zone" : None, "time" : time.strftime("%I:%M %p") }
			
		# At this point - we need to determine if we have an offset - or possibly a timezone passed
		t = self.getTimeFromTZ(offset, time)
		if t == None:
			# We did not get a zone
			t = self.getTimeFromOffset(offset, time)
		return t


	def getTimeFromOffset(self, offset, t = None):
		offset = offset.replace('+', '')
		# Split time string by : and get hour/minute values
		try:
			hours, minutes = map(int, offset.split(':'))
		except Exception:
			try:
				hours = int(offset)
				minutes = 0
			except Exception:
				return None
				# await ctx.channel.send('Offset has to be in +-H:M!')
				# return
		msg = 'UTC'
		# Get the time
		if t == None:
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
		return { "zone" : msg, "time" : newTime.strftime("%I:%M %p") }


	def getTimeFromTZ(self, tz, t = None):
		# Assume sanitized zones - as they're pulled from pytz
		# Let's get the timezone list
		tz_list = FuzzySearch.search(tz, pytz.all_timezones, None, 3)
		if not tz_list[0]['Ratio'] == 1:
			# We didn't find a complete match
			return None
		zone = pytz.timezone(tz_list[0]['Item'])
		if t == None:
			zone_now = datetime.datetime.now(zone)
		else:
			zone_now = t.astimezone(zone)
		return { "zone" : tz_list[0]['Item'], "time" : zone_now.strftime("%I:%M %p") }
