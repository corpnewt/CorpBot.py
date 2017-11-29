import datetime
import pytz
from   Cogs import FuzzySearch

def setup(bot):
	# This module isn't actually a cog
    return

def getClockForTime(time_string):
	# Assumes a HH:MM PP format
	try:
		time = time_string.split()
		time = time[0].split(":")
		hour = int(time[0])
		minute = int(time[1])
	except:
		return ""
	clock_string = ""
	if min > 44:
		clock_string = str(hour + 1) if hour < 12 else "1"
	elif min > 14:
		clock_string = str(hour) + "30"
	else:
		clock_string = str(hour)
	return ":clock" + clock_string + ":"

def getUserTime(member, settings, time = None, strft = "%Y-%m-%d %I:%M %p", clock = True):
	# Returns a dict representing the time from the passed member's perspective
	offset = settings.getGlobalUserStat(member, "TimeZone")
	if offset == None:
		offset = settings.getGlobalUserStat(member, "UTCOffset")
	if offset == None:
		# No offset or tz - return UTC
		t = getClockForTime(time.strftime(strft)) if clock, else time.strftime(strft)
		return { "zone" : 'UTC', "time" : t }
		
	# At this point - we need to determine if we have an offset - or possibly a timezone passed
	t = getTimeFromTZ(offset, time, clock)
	if t == None:
		# We did not get a zone
		t = getTimeFromOffset(offset, time, clock)
	return t


def getTimeFromOffset(offset, t = None, strft = "%Y-%m-%d %I:%M %p", clock = True):
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
	ti = getClockForTime(newTime.strftime(strft)) if clock, else newTime.strftime(strft)
	return { "zone" : msg, "time" : ti }


def getTimeFromTZ(tz, t = None, strft = "%Y-%m-%d %I:%M %p", clock = True):
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
		zone_now = pytz.utc.localize(t, is_dst=None).astimezone(zone)
		#zone_now = t.astimezone(zone)
	ti = getClockForTime(zone_now.strftime(strft)) if clock, else zone_now.strftime(strft)
	return { "zone" : tz_list[0]['Item'], "time" : ti}
