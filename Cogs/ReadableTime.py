import datetime, calendar

def setup(bot):
	# This module isn't actually a cog
    return

def get_months(timeBetween, reverse):
    now = datetime.datetime.now()
    month = now.month
    year = now.year

    total = 0
    months = 0

    while True:
        month_days = calendar.monthrange(year, month)[1]
        month_seconds = month_days * 86400

        if timeBetween >= month_seconds:
            months += 1
            timeBetween -= month_seconds
            total += month_seconds

            if reverse:
                if month > 1:
                    month -= 1
                else:
                    month = 12
                    year -= 1
            else:
                if month < 12:
                    month += 1
                else:
                    month = 1
                    year += 1
        else:
            break

    return months, total

def getReadableTimeBetween(first, last, reverse=False):
    # A helper function to make a readable string between two times
    timeBetween = int(last-first)

    months, total = get_months(timeBetween, reverse)
    timeBetween -= total
    
    weeks   = int(timeBetween/604800)
    days    = int((timeBetween-(weeks*604800))/86400)
    hours   = int((timeBetween-(days*86400 + weeks*604800))/3600)
    minutes = int((timeBetween-(hours*3600 + days*86400 + weeks*604800))/60)
    seconds = int(timeBetween-(minutes*60 + hours*3600 + days*86400 + weeks*604800))
    msg = ""
    
    if months > 0:
        msg += "1 month, " if months == 1 else "{:,} months, ".format(months)
    if weeks > 0:
        msg += "1 week, " if weeks == 1 else "{:,} weeks, ".format(weeks)
    if days > 0:
        msg += "1 day, " if days == 1 else "{:,} days, ".format(days)
    if hours > 0:
        msg += "1 hour, " if hours == 1 else "{:,} hours, ".format(hours)
    if minutes > 0:
        msg += "1 minute, " if minutes == 1 else "{:,} minutes, ".format(minutes)
    if seconds > 0:
        msg += "1 second, " if seconds == 1 else "{:,} seconds, ".format(seconds)

    if msg == "":
        return "0 seconds"
    else:
        return msg[:-2]	