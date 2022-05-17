import datetime, pytz
from   Cogs import FuzzySearch

def setup(bot):
	# This module isn't actually a cog
    return

def getClockForTime(time_string):
	# Assumes a HH:MM PP format
	try:
		t = time_string.split(" ")
		if len(t) == 2:
			t = t[0].split(":")
		elif len(t) == 3:
			t = t[1].split(":")
		else:
			return time_string
		hour = int(t[0])
		minute = int(t[1])
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

def getUserTime(member, settings, time = None, strft = "%Y-%m-%d %I:%M %p", clock = True, force = None):
	# Returns a dict representing the time from the passed member's perspective
	if force: offset = force
	else:
		offset = settings.getGlobalUserStat(member,"TimeZone",None)
		if not offset: offset = settings.getGlobalUserStat(member,"UTCOffset",None)
	if not offset:
		# No offset or tz - return UTC
		t = getClockForTime(time.strftime(strft)) if clock else time.strftime(strft)
		return { "zone" : 'UTC', "time" : t, "vanity" : "{} {}".format(t,"UTC") }
	# At this point - we need to determine if we have an offset - or possibly a timezone passed
	t = getTimeFromTZ(offset, time, strft, clock)
	if not t:
		# We did not get a zone
		t = getTimeFromOffset(offset, time, strft, clock)
	t["vanity"] = "{} {}".format(t["time"],t["zone"])
	return t

def getTimeFromOffset(offset, t = None, strft = "%Y-%m-%d %I:%M %p", clock = True):
	offset = offset.replace('+', '')
	# Split time string by : and get hour/minute values
	try:
		hours, minutes = map(int, offset.split(':'))
	except:
		try:
			hours = int(offset)
			minutes = 0
		except:
			return None
	msg = 'UTC'
	# Get the time
	if not t:
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
	if clock:
		ti = getClockForTime(newTime.strftime(strft))
	else:
		ti = newTime.strftime(strft)
	return { "zone" : msg, "time" : ti }


def getTimeFromTZ(tz, t = None, strft = "%Y-%m-%d %I:%M %p", clock = True):
	# Assume sanitized zones - as they're pulled from pytz
	# Let's get the timezone list
	zone = next((pytz.timezone(x) for x in pytz.all_timezones if x.lower() == tz.lower()),None)
	if not zone: return
	zone_now = t.replace(tzinfo=pytz.utc).astimezone(zone) if t else datetime.datetime.now(zone)
	ti = getClockForTime(zone_now.strftime(strft)) if clock else zone_now.strftime(strft)
	return { "zone" : str(zone), "time" : ti}
