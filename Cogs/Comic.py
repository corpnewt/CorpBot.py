import random
import datetime as dt
from discord.ext import commands
from urllib.parse import unquote
from html.parser import HTMLParser
try:
	from html import unescape
except ImportError:
	from html.parser import HTMLParser
from Cogs import DL, Message

def setup(bot):
	settings = bot.get_cog("Settings")
	bot.add_cog(Comic(bot, settings))

class MLStripper(HTMLParser):
	def __init__(self):
		super().__init__()
		self.reset()
		self.fed = []
	def handle_data(self, d):
		self.fed.append(d)
	def get_data(self):
		return ''.join(self.fed)

class Comic(commands.Cog):

	def __init__(self, bot, settings):
		self.bot = bot
		self.settings = settings
		self.max_tries = 10
		self.comic_data = {
			"beetle-bailey": {
				"name": "Beetle Bailey",
				"url": "https://comicskingdom.com/beetle-bailey-1/{}-{}-{}",
				"keys": ["year","month","day"],
				"first_date": "10-05-1953",
				"comic_url": [
					{"find":'class="ck-panel',"index":1},
					{"find":'src="/_next/image?url=',"index":1},
					{"find":"&amp;w=","index":0}
				]
			},
			"calvin": {
				"name": "Calvin & Hobbes",
				"url": "https://www.gocomics.com/calvinandhobbes/{}/{}/{}",
				"keys": ["year","month","day"],
				"first_date": "11-18-1985",
				"comic_url": [
					{"find":'data-image="',"index":-1},
					{"find":'"',"index":0}
				]
			},
			"cyanide": {
				"name": "Cyanide & Happiness",
				"url": "https://explosm.net/comics/{}/",
				"comic_number": True,
				"first_date": 15,
				"archive_url": "http://explosm.net/comics/archive/{}/{}",
				"archive_keys": ["year","month"],
				"latest_url": [
					{"find":'id="comic-author">',"index":0},
					{"find":'a href="/comics/',"index":-1},
					{"find":'/"',"index":0}
				],
				"date_url": [
					{"find":"{}.{}.{}","keys":["year","month","day"],"index":0},
					{"find":'a href="/comics/',"index":-1},
					{"find":'/"',"index":0}
				],
				"comic_url": [
					{"find":'"main-comic" src="',"index":-1},
					{"find":'"',"index":0}
				],
			},
			"dilbert": {
				"name": "Dilbert",
				"url": "https://dilbert.com/strip/{}-{}-{}",
				"keys": ["year","month","day"],
				"first_date": "04-16-1989",
				"comic_url": [
					{"find":'data-image="',"index":-1},
					{"find":'"',"index":0}
				],
				"comic_title": [
					{"find":'data-title="',"index":-1},
					{"find":'"',"index":0},
					{"find":"Dilbert Comic for ","index":0}
				]
			},
			"farside": {
				"name": "The Far Side",
				"url": "https://www.thefarside.com/{}/{}/{}",
				"keys": ["year","month","day"],
				"first_date": "today-2",
				"comic_url": [
					{"find":'data-src="',"index":1},
					{"find":'"',"index":0}
				],
				"comic_desc": [
					{"find":'data-src="',"index":1}, # Don't accidentally pull from the next commic
					{"find":'class="figure-caption">',"index":1},
					{"find":"</figcaption","index":0}
				],
				"comic_title": [
					{"find":'data-src="',"index":1}, # Don't accidentally pull from the next commic
					{"find":'alt="',"index":1},
					{"find":'"',"index":0}
				]
			},
			"garfield": {
				"name": "Garfield",
				"url": "https://www.gocomics.com/garfield/{}/{}/{}",
				"keys": ["year","month","day"],
				"first_date": "06-19-1978",
				"comic_url": [
					{"find":'data-image="',"index":-1},
					{"find":'"',"index":0}
				]
			},
			"gmg": {
				"name": "Garfield Minus Garfield",
				"url": "https://garfieldminusgarfield.net/day/{}/{}/{}",
				"keys": ["year","month","day"],
				"first_date": "02-13-2008",
				"comic_url": [
					{"find":'<img class="post_media_photo image" src="',"index":-1},
					{"find":'<img src="',"index":-1},
					{"find":'"',"index":0}
				]
			},
			"peanuts": {
				"name": "Peanuts",
				"url": "https://www.gocomics.com/peanuts/{}/{}/{}",
				"keys": ["year","month","day"],
				"first_date": "10-02-1950",
				"comic_url": [
					{"find":'data-image="',"index":-1},
					{"find":'"',"index":0}
				]
			},
			"xkcd": {
				"name": "XKCD",
				"comic_number": True,
				"first_date": 1,
				"archive_url": "https://xkcd.com/archive/",
				"latest_url": [
					{"find":"<h1>Comics:</h1>","index":-1},
					{"find":'a href="/',"index":1},
					{"find":'/" title="',"index":0}
				],
				"date_url": [
					{"find":'title="{}-{}-{}"',"keys":["year","month","day"],"index":0},
					{"find":'a href="/',"index":-1},
					{"find":'/"',"index":0}
				],
				"url": "https://xkcd.com/{}/",
				"comic_url": [
					{"find":"(for hotlinking/embedding): ","index":1},
					{"find":"\n","index":0},
					{"find":'<a href= "',"index":-1},
					{"find":'">',"index":0}
				],
				"comic_desc": [
					{"find":'<div id="comic">',"index":-1},
					{"find":'title="',"index":1},
					{"find":'"',"index":0}
				],
				"comic_title": [
					{"find":'<div id="comic">',"index":-1},
					{"find":'alt="',"index":1},
					{"find":'"',"index":0}
				],
				"padded": False
			}
		}

	def _julian_day(self,gregorian_day):
		# Takes a date string MM-DD-YYYY and returns the Julian day
		M,D,Y = [int(x) for x in gregorian_day.split("-")]
		return dt.date(Y,M,D).toordinal() + 1721424.5

	def _gregorian_day(self,julian_day):
		# Takes a Julian day and returns MM-DD-YYYY in Gregorian
		return dt.date.fromordinal(int(julian_day-1721424.5)).strftime("%m-%d-%Y")

	def _date_dict(self,date,padded=True):
		if isinstance(date,(int,float)):
			date = self._gregorian_day(date)
		m,d,y = [str(int(x)).rjust(2,"0") if padded else str(int(x)) for x in date.split("-")]
		return {"month":m,"day":d,"year":y}

	async def _get_last_comic_number(self,comic_data,date=None,month_adjust=0):
		if month_adjust >= 10: return (None,None) # Adjusted too far :(
		today = dt.datetime.today()
		if month_adjust: # We need to adjust months
			today = dt.datetime(today.year-1,12,1) if today.month == 1 else dt.datetime(today.year,today.month-1,1)
		# Helper to return the highest comic number for a given comic and source html
		date_dict = self._date_dict(today.strftime("%m-%d-%Y") if date is None else date,padded=comic_data.get("padded",True))
		try: 
			archive_url = comic_data["archive_url"].format(*[date_dict[x] for x in comic_data.get("archive_keys",[])])
			archive_html = await DL.async_text(archive_url)
		except:
			return (None,None)
		latest_comic = self._walk_replace(archive_html,comic_data["latest_url"])
		if not latest_comic: return (None,None)
		# Try to cast the number as int - if not possible, set the month back by one
		try: latest_comic = int(latest_comic)
		except: return await self._get_last_comic_number(comic_data,date,month_adjust+1)
		return (latest_comic,archive_html)

	def _resolve_first_date(self,comic_data):
		first_date = comic_data.get("first_date")
		if first_date is None: return # borked
		if isinstance(first_date,str) and first_date.lower().startswith("today"):
			# First date is a reference to today - pull an offset if needed
			try: offset = int(first_date[len("today"):])
			except: offset = 0
			# Set it to the actual date +- the offset as needed
			fd = dt.datetime.today()
			if offset: fd += dt.timedelta(days=offset)
			# Get it formatted as MM-DD-YYYY
			first_date = fd.strftime("%m-%d-%Y")
		return first_date

	async def _get_random_comic(self,comic_data):
		# Try to get a random comic between the first_date/last_date, or between custom indexes (XKCD)
		latest_tuple = None
		use_number = comic_data.get("comic_number",False)
		if use_number:
			# We're using numbers - not dates
			latest_tuple = await self._get_last_comic_number(comic_data)
			if latest_tuple[0] is None: return None # borken
			first = comic_data["first_date"]
			last  = latest_tuple[0]
		else:
			# Using dates, organize them into julian days
			first_date = self._resolve_first_date(comic_data)
			if first_date is None: return # Borken
			first = self._julian_day(first_date)
			last  = self._julian_day(comic_data.get("last_date",dt.datetime.today().strftime("%m-%d-%Y")))
		for x in range(self.max_tries):
			# Generate a random date
			date = random.randint(int(first),int(last))
			if not use_number: date = self._gregorian_day(date+0.5)
			comic = await self._get_comic(comic_data,date,latest_tuple)
			if comic: return comic
		return None

	def _walk_replace(self,search_text,steps,key_dict=None):
		text = search_text
		for step in steps:
			try:
				if key_dict: text = text.split(step["find"].format(*[key_dict[x] for x in step.get("keys",[])]))[step["index"]]
				else: text = text.split(step["find"])[step["index"]]
			except: return None
		return text

	async def _get_comic(self,comic_data,date=None,latest_tuple=None):
		# Attempts to retrieve the comic at the passed date
		first_date = self._resolve_first_date(comic_data)
		if first_date is None: return None # Malformed comic data - first date must be defined
		if comic_data.get("comic_number",False):
			# Gather the latest comic number and archive info
			if latest_tuple: latest,archive_html = latest_tuple
			else: latest,archive_html = await self._get_last_comic_number(comic_data, date if not isinstance(date,int) else None)
			if latest is None: return None # Failed to get the info
			date = latest if date is None else date # Set it to the latest if None
			if not isinstance(date,int):
				date_dict = self._date_dict(date,padded=comic_data.get("padded",True))
				# We have a date to check for
				date = self._walk_replace(archive_html, comic_data["date_url"], date_dict)
				if not date: return None
				try: date = int(date)
				except: pass
			# We got a comic number - let's use that in our url
			url = comic_data["url"].format(date)
		else:
			# Use today's date if none passed
			date = dt.datetime.today().strftime("%m-%d-%Y") if date is None else date
			# We're using date-oriented urls
			last_date = comic_data.get("last_date",dt.datetime.today().strftime("%m-%d-%Y")) # Last supplied date, or today
			# Gather our julian days for comparison
			first_julian,last_julian,date_julian = [self._julian_day(x) for x in (first_date,last_date,date)]
			if not first_julian <= date_julian <= last_julian: return None # Out of our date range
			# We have a valid date - let's format the url and gather the html
			date_dict = self._date_dict(date,padded=comic_data.get("padded",True))
			url = comic_data["url"].format(*[date_dict[x] for x in comic_data["keys"]])
		try: html = await DL.async_text(url, {'User-Agent': ''})
		except: return None # Failed to get the HTML, bail
		# Let's locate our comic by walking the search steps
		comic_url = self._walk_replace(html, comic_data["comic_url"])
		if not comic_url: return None
		if comic_url.startswith("//"): comic_url = "https:"+comic_url
		if comic_url.startswith(("http%3A%2F%2F","https%3A%2F%2F")): comic_url = unquote(comic_url)
		if not comic_url.lower().startswith(("http://","https://")): return None
		try:
			u = unescape
		except NameError:
			h = HTMLParser()
			u = h.unescape
		def strip_tags(html): # Helper to remove <i>...</i> type tags
			html = u(html)
			s = MLStripper()
			s.feed(html)
			return s.get_data()
		# Check if we need to get title text
		comic_title = self._walk_replace(html, comic_data["comic_title"]) if len(comic_data.get("comic_title",[])) else comic_data["name"]
		if not comic_title: comic_title = comic_data["name"]
		comic_title += " ({}{})".format("#" if isinstance(date,int) else "", date)
		comic_title = strip_tags(unquote(comic_title))
		# Check if we need to get a description
		comic_desc = self._walk_replace(html, comic_data["comic_desc"]) if len(comic_data.get("comic_desc",[])) else None
		comic_desc = strip_tags(unquote(comic_desc)) if comic_desc else None
		return {"image":comic_url,"url":url,"title":comic_title,"description":comic_desc}

	async def _display_comic(self, ctx, comic, date = None, random = False):
		# Helper to display the comic, or post an error if there was an issue
		message = await Message.EmbedText(
			title="Locating comic...",
			description="Feeling around in the dark trying to find a {} comic...".format(self.comic_data[comic]["name"]),
			color=ctx.author
		).send(ctx)
		if date and isinstance(date,str):
			date = date.replace("/","-").replace(".","-").replace(" ","-").replace(" ","-")
			date= "-".join([x.rjust(2,"0") for x in date.split("-") if x][:3])
		if random:
			desc = "a random {} comic".format(self.comic_data[comic]["name"])
			try: comic_out = await self._get_random_comic(self.comic_data[comic])
			except: comic_out = None
		else:
			desc = "{} comic {}".format(self.comic_data[comic]["name"],date if isinstance(date,int) else "for today" if date==None else "for "+date)
			try: comic_out = await self._get_comic(self.comic_data[comic],date)
			except Exception as e:
				comic_out = None
		if not comic_out:
			return await Message.EmbedText(
				title=self.comic_data[comic]["name"]+" Error",
				description="Could not get {} :(".format(desc),
				color=ctx.author
			).edit(ctx,message)
		comic_out["color"] = ctx.author
		return await Message.EmbedText(**comic_out).edit(ctx,message)

	@commands.command()
	async def beetle(self, ctx, *, date=None):
		"""Displays the Beetle Bailey comic for the passed date (MM-DD-YYYY) from 10-05-1953 to today if found."""
		await self._display_comic(ctx, "beetle-bailey", date=date)

	@commands.command()
	async def randbeetle(self, ctx):
		"""Displays a random Beetle Bailey comic from 10-05-1953 to today."""
		await self._display_comic(ctx, "beetle-bailey", random=True)

	@commands.command()
	async def calvin(self, ctx, *, date=None):
		"""Displays the Calvin & Hobbes comic for the passed date (MM-DD-YYYY) from 11-18-1985 to today if found."""
		await self._display_comic(ctx, "calvin", date=date)

	@commands.command()
	async def randcalvin(self, ctx):
		"""Displays a random Calvin & Hobbes comic from 11-18-1985 to today."""
		await self._display_comic(ctx, "calvin", random=True)

	# Commented out as 
	'''@commands.command()
	async def cyanide(self, ctx, *, date=None):
		"""Displays the Cyanide & Happiness comic for the passed date (MM-DD-YYYY) from 01-26-2005 to today or comic number if found."""
		try: date = int(date)
		except: pass
		await self._display_comic(ctx, "cyanide", date=date)

	@commands.command()
	async def randcyanide(self, ctx):
		"""Displays a random Cyanide & Happiness comic from 01-26-2005 to today."""
		await self._display_comic(ctx, "cyanide", random=True)

	@commands.command()
	async def dilbert(self, ctx, *, date=None):
		"""Displays the Dilbert comic for the passed date (MM-DD-YYYY) from 04-16-1989 to today if found."""
		await self._display_comic(ctx, "dilbert", date=date)

	@commands.command()
	async def randilbert(self, ctx):
		"""Displays a random Dilbert comic from 04-16-1989 to today."""
		await self._display_comic(ctx, "dilbert", random=True)'''

	@commands.command()
	async def farside(self, ctx, *, date=None):
		"""Displays the Far Side comic for the passed date (MM-DD-YYYY) from 2 days ago to today if found."""
		await self._display_comic(ctx, "farside", date=date)

	@commands.command()
	async def randfarside(self, ctx):
		"""Displays a random Far Side comic from 2 days ago to today."""
		await self._display_comic(ctx, "farside", random=True)

	@commands.command()
	async def garfield(self, ctx, *, date=None):
		"""Displays the Garfield comic for the passed date (MM-DD-YYYY) from 06-19-1978 to today if found."""
		await self._display_comic(ctx, "garfield", date=date)

	@commands.command()
	async def randgarfield(self, ctx):
		"""Displays a random Garfield comic from 06-19-1978 to today."""
		await self._display_comic(ctx, "garfield", random=True)

	@commands.command()
	async def gmg(self, ctx, *, date=None):
		"""Displays the Garfield Minus Garfield comic for the passed date (MM-DD-YYYY) from 02-13-2008 to today if found."""
		await self._display_comic(ctx, "gmg", date=date)

	@commands.command()
	async def randgmg(self, ctx):
		"""Displays a random Garfield Minus Garfield comic from 02-13-2008 to today."""
		await self._display_comic(ctx, "gmg", random=True)

	@commands.command()
	async def peanuts(self, ctx, *, date=None):
		"""Displays the Peanuts comic for the passed date (MM-DD-YYYY) from 10-02-1950 to today if found."""
		await self._display_comic(ctx, "peanuts", date=date)

	@commands.command()
	async def randpeanuts(self, ctx):
		"""Displays a random Peanuts comic from 10-02-1950 to today."""
		await self._display_comic(ctx, "peanuts", random=True)

	@commands.command()
	async def xkcd(self, ctx, *, date=None):
		"""Displays the XKCD comic for the passed date (MM-DD-YYYY) from 01-01-2006 to today or comic number if found."""
		try: date = int(date)
		except: pass
		await self._display_comic(ctx, "xkcd", date=date)

	@commands.command()
	async def randxkcd(self, ctx):
		"""Displays a random XKCD comic from 01-01-2006 to today."""
		await self._display_comic(ctx, "xkcd", random=True)
