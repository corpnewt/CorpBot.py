import datetime, pytz
from discord.ext import commands
from Cogs import FuzzySearch, Settings, DisplayName, Message, Nullify, PickList

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


	def getstrftime(self, ctx):
		use_24 = self.settings.getGlobalUserStat(ctx.author,"Use24HourFormat",False)
		return "%H:%M" if use_24 else "%I:%M %p"


	@commands.command()
	async def settz(self, ctx, *, tz : str = None):
		"""Sets your TimeZone - Overrides your UTC offset - and accounts for DST."""
		await self._settz(ctx,tz=tz)


	@commands.command()
	async def setbottz(self, ctx, *, tz : str = None):
		"""Sets the bot's TimeZone - Overrides their UTC offset - and accounts for DST (owner only)."""
		if not await Utils.is_owner_reply(ctx): return
		await self._settz(ctx,user=self.bot.user,tz=tz)


	async def _settz(self, ctx, user = None, tz = None):
		user = user or ctx.author
		bot = "" if user==ctx.author else "bot"
		if not tz:
			current_tz = self.settings.getGlobalUserStat(user, "TimeZone", None)
			if not current_tz:
				return await ctx.send(
					'Usage: `{0}set{1}tz [Region/City]`\nYou can get a list of available TimeZones with `{0}listtz`'.format(ctx.prefix,bot)
				)
			self.settings.setGlobalUserStat(user, "TimeZone", None)
			return await ctx.send("{} TimeZone (`{}`) has been removed!".format(
				"My" if bot else "*{}*, your".format(DisplayName.name(user)),
				current_tz
			))
		strftime = self.getstrftime(ctx)
		not_found = 'TimeZone `{}` not found!'.format(tz.replace('`', '\\`'))
		# Let's get the timezone list
		tz_list = FuzzySearch.search(tz, pytz.all_timezones, None, 3)
		index = 0
		message = None
		if not tz_list[0]['Ratio'] == 1:
			# Setup and display the picker
			msg = not_found + '\nSelect one of the following close matches:'
			items = []
			for x in tz_list:
				time = self.getTimeFromTZ(x["Item"],strftime=strftime)
				if time: time = time["time"] # Extract the time
				items.append("{} - {}".format(x["Item"],time or "Unknown"))
			index, message = await PickList.Picker(
				title=msg,
				list=items,
				ctx=ctx
			).pick()
			# Check if we errored/cancelled
			if index < 0:
				return await message.edit(content=not_found)
		# We got a time zone
		self.settings.setGlobalUserStat(user, "TimeZone", tz_list[index]['Item'])
		time = self.getTimeFromTZ(tz_list[index]["Item"])
		if time: time = self.getClockForTime(time["time"])
		msg = "{} TimeZone set to `{}` - where it is currently *{}*!".format(
			"My" if bot else "*{}*, your".format(DisplayName.name(user)),
			tz_list[index]['Item'],
			time or "`Unknown`"
		)
		if message:
			await message.edit(content=msg)
		else:
			await ctx.send(msg)

	
	@commands.command()
	async def listtz(self, ctx, *, tz_search = None):
		"""List all the supported TimeZones."""
		msg = ""
		strftime = self.getstrftime(ctx)
		if not tz_search:
			title = "Available TimeZones"
			pad = len(str(len(pytz.all_timezones)))
			for i,tz in enumerate(pytz.all_timezones,start=1):
				time = self.getTimeFromTZ(tz,strftime=strftime)
				if time: time = time["time"] # Extract the time
				msg += "{}. {} - {}\n".format(str(i).rjust(pad),tz,time or "Unknown")
		else:
			tz_list = FuzzySearch.search(tz_search, pytz.all_timezones)
			title = "Top 3 TimeZone Matches"
			for i,tz in enumerate(tz_list,start=1):
				time = self.getTimeFromTZ(tz["Item"],strftime=strftime)
				if time: time = time["time"] # Extract the time
				msg += "{}. {} - {}\n".format(i,tz["Item"],time or "Unknown")

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
			member = ctx.author
		if isinstance(member,str):
			# Try to get a user first
			memberName = member
			member = DisplayName.memberForName(memberName, ctx.guild)
			if not member:
				msg = "Couldn't find user *{}*.".format(Nullify.escape_all(memberName))
				return await ctx.send(msg)
		# We got one
		strftime = self.getstrftime(ctx)
		timezone = self.settings.getGlobalUserStat(member, "TimeZone")
		if timezone is None:
			return await ctx.send('{0} TimeZone yet - they can do so with the `{1}set{2}tz [Region/City]` command.\nYou can get a list of available TimeZones with `{1}listtz`\nThe current UTC time is *{3}*.'.format(
				"My owners have not set my" if member.id==self.bot.user.id else "*{}* hasn't set their".format(DisplayName.name(member)),
				ctx.prefix,
				"bot" if member.id==self.bot.user.id else "",
				self.getClockForTime(datetime.datetime.utcnow().strftime(strftime)))
			)
		time = self.getTimeFromTZ(timezone)
		if time: time = self.getClockForTime(time["time"])
		await ctx.send("{} TimeZone is *{}* - where it is currently *{}*!".format(
			"My" if member.id==self.bot.user.id else "*{}'s*".format(DisplayName.name(member)),
			timezone,
			time
		))

		
	@commands.command()
	async def setoffset(self, ctx, *, offset : str = None):
		"""Set your UTC offset."""
		await self._setoffset(ctx,offset=offset)


	@commands.command()
	async def setbotoffset(self, ctx, *, offset : str = None):
		"""Sets the bot's UTC offset (owner only)."""
		if not await Utils.is_owner_reply(ctx): return
		await self._setoffset(ctx,user=self.bot.user,offset=offset)


	async def _setoffset(self, ctx, user = None, offset = None):
		user = user or ctx.author
		bot = "" if user==ctx.author else "bot"
		if offset is None:
			current_offset = self.settings.getGlobalUserStat(user, "UTCOffset", None)
			if not current_offset:
				return await ctx.send(
					'Usage: `{}set{}offset +-H:M`'.format(ctx.prefix,bot)
				)
			self.settings.setGlobalUserStat(user, "UTCOffset", None)
			return await ctx.send("{} UTC offset (`{}`) has been removed!".format(
				"My" if bot else "*{}*, your".format(DisplayName.name(user)),
				current_offset
			))
		off = self._format_offset(offset,utc_prefix=False)
		if off is None:
			return await ctx.send('Offset has to be in +-H:M!')
		elif off is False:
			return await ctx.send("That offset is out of range!")
		strftime = self.getstrftime(ctx)
		self.settings.setGlobalUserStat(user, "UTCOffset", off)
		time = self.getTimeFromOffset(offset,strftime=strftime)
		if time: time = self.getClockForTime(time["time"])
		return await ctx.send("{} UTC offset has been set to `{}` - where it is currently *{}*!".format(
			"My" if bot else "*{}*, your".format(DisplayName.name(user)),
			self._format_offset(off,utc_prefix=False),
			time or "`Unknown`"
		))


	def _format_offset(self, offset, as_string=True, utc_prefix=True):
		# Formats a +-HH:MM string offset to UTC(+-HH:MM)
		offset = offset.replace("+","")
		try:
			hours,minutes = map(int,offset.split(":"))
		except Exception:
			try:
				hours = int(offset)
				minutes = 0
			except:
				return None
		# Ensure values are within the C int range by applying
		# the offset via timedelta
		try:
			t = datetime.datetime.utcnow()
			td = datetime.timedelta(hours=hours, minutes=minutes)
			t + td
		except OverflowError:
			return False
		# Ensure only hours can be negative
		if minutes < 0: minutes *= -1
		if not as_string:
			# Just getting the hour/minute tuple
			return (hours,minutes)
		# Need to format the string
		if hours == minutes == 0:
			# Just return UTC
			return "UTC+0:0" if utc_prefix else "0:0"
		else:
			return "{}{}:{}".format(
				("UTC+" if hours >= 0 else "UTC") if utc_prefix else "",
				hours,
				minutes
			)


	@commands.command()
	async def offset(self, ctx, *, member = None):
		"""See a member's UTC offset."""
		if member is None:
			member = ctx.author
		if isinstance(member,str):
			# Try to get a user first
			memberName = member
			member = DisplayName.memberForName(memberName, ctx.guild)
			if not member:
				msg = "Couldn't find user *{}*.".format(Nullify.escape_all(memberName))
				return await ctx.send(msg)
		# We got one
		offset = self.settings.getGlobalUserStat(member, "UTCOffset")
		if offset:
			h_m = self._format_offset(offset,as_string=False)
			if h_m in (None,False):
				# Bad value saved
				offset = None
		strftime = self.getstrftime(ctx)
		if offset is None:
			return await ctx.send('{} offset yet - they can do so with the `{}set{}offset [+-offset]` command.\nThe current UTC time is *{}*.'.format(
				"My owners have not set my" if member.id==self.bot.user.id else "*{}* hasn't set their".format(DisplayName.name(member)),
				ctx.prefix,
				"bot" if member.id==self.bot.user.id else "",
				self.getClockForTime(datetime.datetime.utcnow().strftime(strftime)))
			)
		offset = self._format_offset(offset)
		time = self.getTimeFromOffset("{}:{}".format(*h_m),strftime=strftime)
		if time: time = self.getClockForTime(time["time"])
		await ctx.send("{} offset is *{}* - where it is currently *{}*!".format(
			"My" if member.id==self.bot.user.id else "*{}'s*".format(DisplayName.name(member)),
			offset,
			time or "Unknown"
		))


	def _process_12_or_24(self,member,yes_no,reverse=False):
		current = self.settings.getGlobalUserStat(member,"Use24HourFormat",False)
		if yes_no is None:
			# Output what we have
			return "You are currently using *{}-hour* time formatting.".format("24" if current else 12)
		elif yes_no.lower() in ( "1", "yes", "on", "true", "enabled", "enable" ):
			yes_no = not reverse
			msg = "You are set to use *{}-hour* time formatting.".format(12 if reverse else 24)
		elif yes_no.lower() in ( "0", "no", "off", "false", "disabled", "disable" ):
			yes_no = reverse
			msg = "You are set to use *{}-hour* time formatting.".format(24 if reverse else 12)
		else:
			msg = "That's not a valid setting."
			yes_no = current
		if yes_no != current:
			self.settings.setGlobalUserStat(member,"Use24HourFormat",yes_no)
		return msg


	@commands.command()
	async def use24(self, ctx, *, yes_no = None):
		"""Gets or sets whether or not you'd like time results in 24-hour format."""
		await ctx.send(self._process_12_or_24(ctx.author,yes_no))


	@commands.command()
	async def use12(self, ctx, *, yes_no = None):
		"""Gets or sets whether or not you'd like time results in 12-hour format."""
		await ctx.send(self._process_12_or_24(ctx.author,yes_no,reverse=True))


	@commands.command()
	async def time(self, ctx, *, offset : str = None):
		"""Get UTC time +- an offset."""
		timezone = None
		if offset is None:
			member = ctx.author
		else:
			# Try to get a user first
			member = DisplayName.memberForName(offset, ctx.guild)
		strftime = self.getstrftime(ctx)
		if member:
			# We got one
			# Check for timezone first
			offset = self.settings.getGlobalUserStat(member, "TimeZone")
			if offset is None:
				offset = self.settings.getGlobalUserStat(member, "UTCOffset")
		if offset is None:
			msg = '{0} TimeZone or offset yet - they can do so with the `{1}set{2}offset [+-offset]` or `{1}set{2}tz [Region/City]` command.\nThe current UTC time is *{3}*.'.format(
				"My owners have not set my" if member.id==self.bot.user.id else "*{}* hasn't set their".format(DisplayName.name(member)),
				ctx.prefix,
				"bot" if member.id==self.bot.user.id else "",
				self.getClockForTime(datetime.datetime.utcnow().strftime(strftime)))
			return await ctx.send(msg)
		# At this point - we need to determine if we have an offset - or possibly a timezone passed
		t = self.getTimeFromTZ(offset,strftime=strftime)
		if t is None:
			# We did not get an offset
			t = self.getTimeFromOffset(offset,strftime=strftime)
			if t is None:
				return await ctx.send("I couldn't find that TimeZone or offset!")
		t["time"] = self.getClockForTime(t["time"])
		if member:
			msg = "{}; where {}, it's currently *{}*".format(
				t["zone"],
				"I am" if member.id==self.bot.user.id else "*{}* is".format(DisplayName.name(member)),
				t["time"]
			)
		else:
			msg = "{} is currently *{}*".format(
				t["zone"],
				t["time"]
			)
		# Say message
		await ctx.send(msg)


	def getClockForTime(self, time_string):
		try:
			t = time_string.split(" ")[0]
			hour,minute = map(int,t.split(":"))
			if hour > 12:
				hour -= 12
			if hour == 0:
				hour = 12
		except:
			return time_string
		clock_string = ""
		if minute > 44:
			clock_string = str(hour + 1) if hour < 12 else "1"
		elif minute > 14:
			clock_string = str(hour) + "30"
		else:
			clock_string = str(hour)
		return time_string +" :clock" + clock_string + ":"


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
		if hours == 0:
			# No offset
			newTime = t
		else:
			msg += "{}{}".format(
				"+" if hours > 0 else "",
				offset
			)
			try:
				td = datetime.timedelta(hours=hours, minutes=minutes)
				newTime = t + td
			except OverflowError:
				return None # Overflowed
		return {
			"zone":msg,
			"time":newTime.strftime(strftime or "%I:%M %p")
		}


	def getTimeFromTZ(self, tz, t = None, strftime = None, search = True):
		try:
			zone = pytz.timezone(tz)
			assert zone
		except Exception:
			return None
		if t is None:
			zone_now = datetime.datetime.now(zone)
		else:
			zone_now = t.astimezone(zone)
		return {
			"zone":tz,
			"time":zone_now.strftime(strftime or "%I:%M %p")
		}
