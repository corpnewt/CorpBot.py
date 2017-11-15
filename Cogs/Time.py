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

def setup(bot):
	# Add the bot and deps
	settings = bot.get_cog("Settings")
	bot.add_cog(Time(bot, settings))

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
		count = 0
		if not tz_list[0]['Ratio'] == 1:
			# We didn't find a complete match
			msg = 'TimeZone `{}` not found!\n\n'.format(tz.replace('`', '\\`'))
			msg += "Select one of the following close matches - or type `cancel`:\n\n```"
			for t in tz_list:
				count += 1
				msg += "{}. {}\n".format(count, t['Item']).replace('`', '\\`')
			msg += '```'
		else:
			# We got a time zone
			self.settings.setGlobalUserStat(ctx.author, "TimeZone", tz_list[0]['Item'])
			msg = "TimeZone set to *{}!*".format(tz_list[0]['Item'])
		message = await ctx.send(msg)
		if not count:
			return
		# Wait for response
		def littleCheck(c, m):
			if m.author.id != ctx.author.id or m.channel.id != ctx.channel.id:
				return False
			# Check if we're re-running the same command
			if c.command and c.command.name == "settz":
				return True
			# Check for cancellation
			if m.content.lower() == "cancel":
				return True
			try:
				m_int = int(m.content)
			except:
				return False
			if m_int < 1 or m_int > count:
				return False
			return True
		try:
			ind = await self.bot.wait_for('message_context', check=littleCheck, timeout=60)
		except Exception:
			ind = None
		if ind == None or ind[1].content.lower() == "cancel" or (ind[0].command and ind[0].command.name == "tag"):
			# Timed out
			msg = 'TimeZone `{}` not found!'.format(tz.replace('`', '\\`'))
			if suppress:
				msg = Nullify.clean(msg)
			await message.edit(content=msg)
			return
		# Got one
		await message.edit(content=" ")
		# Invoke this command again with the right name
		await ctx.invoke(self.settz, tz=potentialList[int(ind[1].content)-1]['Item'])

	
	@commands.command(pass_context=True)
	async def listtz(self, ctx, *, tz_search = None):
		"""List all the supported TimeZones in PM."""

		msg = ""
		if not tz_search:
			title = "Available TimeZones"
			for tz in pytz.all_timezones:
				msg += tz + "\n"
		else:
			tz_list = FuzzySearch.search(tz_search, pytz.all_timezones)
			title = "Top 3 TimeZone Matches"
			for tz in tz_list:
				msg += tz['Item'] + "\n"

		await Message.EmbedText(title=title, color=ctx.author, description=msg).send(ctx)


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
