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
from   Cogs import UserTime
from   Cogs import PickList

def setup(bot):
	# Add the bot and deps
	settings = bot.get_cog("Settings")
	bot.add_cog(Time(bot, settings))

class Time(commands.Cog):

	# Init with the bot reference, and a reference to the settings var
	def __init__(self, bot, settings):
		self.bot = bot
		self.settings = settings
		global Utils, DisplayName
		Utils = self.bot.get_cog("Utils")
		DisplayName = self.bot.get_cog("DisplayName")


	@commands.command()
	async def settz(self, ctx, *, tz : str = None):
		"""Sets your TimeZone - Overrides your UTC offset - and accounts for DST."""
		usage = 'Usage: `{}settz [Region/City]`\nYou can get a list of available TimeZones with `{}listtz`'.format(ctx.prefix, ctx.prefix)
		if not tz:
			self.settings.setGlobalUserStat(ctx.author, "TimeZone", None)
			await ctx.channel.send("*{}*, your TimeZone has been removed!".format(DisplayName.name(ctx.author)))
			return
		
		not_found = 'TimeZone `{}` not found!'.format(tz.replace('`', '\\`'))
		# Let's get the timezone list
		tz_list = FuzzySearch.search(tz, pytz.all_timezones, None, 3)
		if not tz_list[0]['Ratio'] == 1:
			# Setup and display the picker
			msg = not_found + '\nSelect one of the following close matches:'
			index, message = await PickList.Picker(
				title=msg,
				list=[x["Item"] for x in tz_list],
				ctx=ctx
			).pick()
			# Check if we errored/cancelled
			if index < 0:
				return await message.edit(content=not_found)
			# We got a time zone
			self.settings.setGlobalUserStat(ctx.author, "TimeZone", tz_list[index]['Item'])
			return await message.edit(content="TimeZone set to `{}`!".format(tz_list[index]['Item']))
		# We got a time zone
		self.settings.setGlobalUserStat(ctx.author, "TimeZone", tz_list[0]['Item'])
		msg = "TimeZone set to `{}`!".format(tz_list[0]['Item'])
		message = await ctx.send(msg)

	
	@commands.command()
	async def listtz(self, ctx, *, tz_search = None):
		"""List all the supported TimeZones."""

		msg = ""
		if not tz_search:
			title = "Available TimeZones"
			pad = len(str(len(pytz.all_timezones)))
			for i,tz in enumerate(pytz.all_timezones,start=1):
				msg += "{}. {}\n".format(str(i).rjust(pad),tz)
		else:
			tz_list = FuzzySearch.search(tz_search, pytz.all_timezones)
			title = "Top 3 TimeZone Matches"
			for i,tz in enumerate(tz_list,start=1):
				msg += "{}. {}\n".format(i,tz["Item"])

		return await PickList.PagePicker(
			title=title,
			description=msg,
			ctx=ctx,
			d_header="```\n",
			d_footer="```"
		).pick()


	@commands.command()
	async def tz(self, ctx, *, member = None):
		"""See a member's TimeZone."""
		if member is None:
			member = ctx.message.author

		if type(member) == str:
			# Try to get a user first
			memberName = member
			member = DisplayName.memberForName(memberName, ctx.message.guild)
			if not member:
				msg = 'Couldn\'t find user *{}*.'.format(Nullify.escape_all(memberName))
				return await ctx.channel.send(msg)

		# We got one
		timezone = self.settings.getGlobalUserStat(member, "TimeZone")
		if timezone is None:
			msg = '*{}* hasn\'t set their TimeZone yet - they can do so with the `{}settz [Region/City]` command.'.format(DisplayName.name(member), ctx.prefix)
			return await ctx.channel.send(msg)

		msg = '*{}\'s* TimeZone is *{}*'.format(DisplayName.name(member), timezone)
		await ctx.channel.send(msg)

		
	@commands.command()
	async def setoffset(self, ctx, *, offset : str = None):
		"""Set your UTC offset."""

		if offset is None:
			self.settings.setGlobalUserStat(ctx.message.author, "UTCOffset", None)
			msg = '*{}*, your UTC offset has been removed!'.format(DisplayName.name(ctx.message.author))
			return await ctx.channel.send(msg)

		offset = offset.replace('+', '')

		# Split time string by : and get hour/minute values
		try:
			hours, minutes = map(int, offset.split(':'))
		except Exception:
			try:
				hours = int(offset)
				minutes = 0
			except Exception:
				return await ctx.channel.send('Offset has to be in +-H:M!')
		off = "{}:{}".format(hours, minutes)
		self.settings.setGlobalUserStat(ctx.message.author, "UTCOffset", off)
		msg = '*{}*, your UTC offset has been set to `{}`!'.format(DisplayName.name(ctx.message.author), off)
		await ctx.channel.send(msg)


	@commands.command()
	async def offset(self, ctx, *, member = None):
		"""See a member's UTC offset."""

		if member is None:
			member = ctx.message.author

		if type(member) == str:
			# Try to get a user first
			memberName = member
			member = DisplayName.memberForName(memberName, ctx.message.guild)
			if not member:
				msg = 'Couldn\'t find user *{}*.'.format(Nullify.escape_all(memberName))
				return await ctx.channel.send(msg)

		# We got one
		offset = self.settings.getGlobalUserStat(member, "UTCOffset")
		if offset is None:
			msg = '*{}* hasn\'t set their offset yet - they can do so with the `{}setoffset [+-offset]` command.'.format(DisplayName.name(member), ctx.prefix)
			return await ctx.channel.send(msg)

		# Split time string by : and get hour/minute values
		try:
			hours, minutes = map(int, offset.split(':'))
		except Exception:
			try:
				hours = int(offset)
				minutes = 0
			except Exception:
				return await ctx.channel.send('Offset has to be in +-H:M!')
		
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


	@commands.command()
	async def use24(self, ctx, *, yes_no = None):
		"""Gets or sets whether or not you'd like time results in 24-hour format."""

		current = self.settings.getGlobalUserStat(ctx.author,"Use24HourFormat",False)
		if yes_no is None:
			# Output what we have
			return await ctx.send(
				"You are currently using *{}-hour* time formatting.".format("24" if current else 12)
			)
		elif yes_no.lower() in ( "1", "yes", "on", "true", "enabled", "enable" ):
			yes_no = True
			msg = "You are set to use *24-hour* time formatting."
		elif yes_no.lower() in ( "0", "no", "off", "false", "disabled", "disable" ):
			yes_no = False
			msg = "You are set to use *12-hour* time formatting."
		else:
			msg = "That's not a valid setting."
			yes_no = current
		if yes_no != current:
			self.settings.setGlobalUserStat(ctx.author,"Use24HourFormat",yes_no)
		await ctx.send(msg)


	@commands.command()
	async def time(self, ctx, *, offset : str = None):
		"""Get UTC time +- an offset."""
		timezone = None
		if offset is None:
			member = ctx.message.author
		else:
			# Try to get a user first
			member = DisplayName.memberForName(offset, ctx.message.guild)

		use_24 = self.settings.getGlobalUserStat(ctx.author,"Use24HourFormat",False)
		strftime = "%H:%M" if use_24 else "%I:%M %p"

		print(use_24,strftime)

		if member:
			# We got one
			# Check for timezone first
			offset = self.settings.getGlobalUserStat(member, "TimeZone")
			if offset is None:
				offset = self.settings.getGlobalUserStat(member, "UTCOffset")
		
		if offset is None:
			msg = '*{}* hasn\'t set their TimeZone or offset yet - they can do so with the `{}setoffset [+-offset]` or `{}settz [Region/City]` command.\nThe current UTC time is *{}*.'.format(
				DisplayName.name(member),
				ctx.prefix,
				ctx.prefix,
				UserTime.getClockForTime(datetime.datetime.utcnow().strftime(strftime)))
			return await ctx.channel.send(msg)

		# At this point - we need to determine if we have an offset - or possibly a timezone passed
		t = self.getTimeFromTZ(offset,strftime=strftime)
		if t is None:
			# We did not get an offset
			t = self.getTimeFromOffset(offset,strftime=strftime)
			if t is None:
				return await ctx.channel.send("I couldn't find that TimeZone or offset!")
		t["time"] = UserTime.getClockForTime(t["time"])
		if member:
			msg = '{}; where *{}* is, it\'s currently *{}*'.format(t["zone"], DisplayName.name(member), t["time"])
		else:
			msg = '{} is currently *{}*'.format(t["zone"], t["time"])
		
		# Say message
		await ctx.channel.send(msg)


	def getTimeFromOffset(self, offset, t = None, strftime = None):
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
		msg = 'UTC'
		# Get the time
		if t is None:
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
		return { "zone" : msg, "time" : newTime.strftime(strftime or "%I:%M %p") }


	def getTimeFromTZ(self, tz, t = None, strftime = None):
		# Assume sanitized zones - as they're pulled from pytz
		# Let's get the timezone list
		tz_list = FuzzySearch.search(tz, pytz.all_timezones, None, 3)
		if not tz_list[0]['Ratio'] == 1:
			# We didn't find a complete match
			return None
		zone = pytz.timezone(tz_list[0]['Item'])
		if t is None:
			zone_now = datetime.datetime.now(zone)
		else:
			zone_now = t.astimezone(zone)
		return { "zone" : tz_list[0]['Item'], "time" : zone_now.strftime(strftime or "%I:%M %p") }
