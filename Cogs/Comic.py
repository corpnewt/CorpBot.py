import asyncio
import discord
import random
import requests
import time
import datetime as dt
from   discord.ext import commands
from   Cogs import Settings
from   Cogs import GetImage
from   Cogs import ComicHelper

# This module will probably get comics... *finges crossed*

class Comic:

	# Init with the bot reference, and a reference to the settings var
	def __init__(self, bot, settings):
		self.bot = bot
		self.settings = settings
		
	def message(self, message):
		# Check the message and see if we should allow it - always yes.
		# This module doesn't need to cancel messages.
		return { 'Ignore' : False, 'Delete' : False}
	
	def getRandDateBetween(self, first, last):
		# Takes two date strings "MM-DD-YYYY" and
		# returns a dict of day, month, and year values
		# from a random date between them
		fDate = first.split("-")
		fJDate = ComicHelper.date_to_jd(int(fDate[2]), int(fDate[0]), int(fDate[1]))
		lDate = last.split("-")
		lJDate = ComicHelper.date_to_jd(int(lDate[2]), int(lDate[0]), int(lDate[1]))
		
		# Get random Julian Date
		randJDate = random.uniform(fJDate, lJDate)
		
		# Convert to gregorian
		gDate = ComicHelper.jd_to_date(randJDate)
		yea   = int(gDate[0])
		mon   = int(gDate[1])
		day   = int(gDate[2])
		
		# Make sure all months/days are double digits
		if (int(mon) < 10):
			mon = "0"+str(mon)
		if (int(day) < 10):
			day = "0"+str(day)
		
		# Build our dict and return it
		newDate = { "Year" : str(yea), "Month" : str(mon), "Day" : str(day)}
		return newDate
		
	
	def dateDict(self, date):
		# Takes a MM-DD-YYYY string or array
		# and converts it to a dict
		if type(date) == str:
			# Split by "-"
			date = date.split("-")
		
		yea   = int(date[2])
		mon   = int(date[0])
		day   = int(date[1])
		# Make sure all months/days are double digits
		if (int(mon) < 10):
			mon = "0"+str(mon)
		if (int(day) < 10):
			day = "0"+str(day)
		# Build our dict and return it
		newDate = { "Year" : str(yea), "Month" : str(mon), "Day" : str(day)}
		return newDate
		
		
		
	def isDateBetween(self, check, first, last):
		# Takes three date strings "MM-DD-YYY" and
		# returns whether the first is between the next two
		fDate = first.split("-")
		fJDate = ComicHelper.date_to_jd(int(fDate[2]), int(fDate[0]), int(fDate[1]))
		lDate = last.split("-")
		lJDate = ComicHelper.date_to_jd(int(lDate[2]), int(lDate[0]), int(lDate[1]))
		cDate = check.split("-")
		cJDate = ComicHelper.date_to_jd(int(cDate[2]), int(cDate[0]), int(cDate[1]))
		
		if cJDate <= lJDate and cJDate >= fJDate:
			return True
		else:
			return False
			
	def dateIsValid(self, date : str = None):
		# Checks if a passed date is a valid MM-DD-YYYY string
		if not date:
			# Auto to today's date
			date = dt.datetime.today().strftime("%m-%d-%Y")
		try:
			startDate = date.split("-")
		except ValueError:
			# Doesn't split by -?  Not valid
			return False
			
		if len(startDate) < 3:
			# Not enough values
			return False
			
		for d in startDate:
			try:
				int(d)
			except ValueError:
				return False
		
		return True
		
	def canDisplay(self, server):
		# Check if we can display images
		lastTime = int(self.settings.getServerStat(server, "LastPicture"))
		threshold = int(self.settings.getServerStat(server, "PictureThreshold"))
		if not GetImage.canDisplay( lastTime, threshold ):
			# await self.bot.send_message(channel, 'Too many images at once - please wait a few seconds.')
			return False
		
		# If we made it here - set the LastPicture method
		self.settings.setServerStat(server, "LastPicture", int(time.time()))
		return True

	
	def buildDilbertURL(self, date):
		return "http://dilbert.com/strip/" + str(date['Year']) + "-" + str(date['Month']) + "-" + str(date['Day'])
		
	  # ####### #
	 # Dilbert #
	# ####### #
	@commands.command(pass_context=True)
	async def randilbert(self, ctx):
		"""Randomly picks and displays a Dilbert comic."""
		
		channel = ctx.message.channel
		author  = ctx.message.author
		server  = ctx.message.server
		
		if not self.canDisplay(server):
			return
		
		# Get some preliminary values
		todayDate = dt.datetime.today().strftime("%m-%d-%Y")
		# Can't be before this date.
		firstDate = "04-16-1989"

		# Start a loop to find a comic
		gotComic = False
		tries = 0
		while not gotComic:
	
			if tries >= 10:
				break
		
			# Try to get a valid comic
			date      = self.getRandDateBetween(firstDate, todayDate)
			url       = self.buildDilbertURL(date)
			imageHTML = ComicHelper.getImageHTML(url)
			
			if imageHTML:
				# Got it!
				gotComic = True
				
			# Increment try counter
			tries += 1	
		
		if tries >= 10:
			msg = 'Failed to find working link.'
			await self.bot.send_message(channel, msg)
			return
		
		# Got a comic link
		imageURL  = ComicHelper.getImageURL(imageHTML)
		imageDisplayName = ComicHelper.getImageTitle(imageHTML)
		
		# Download Image
		await GetImage.get(imageURL, self.bot, channel, imageDisplayName)
		
		
	@commands.command(pass_context=True)
	async def dilbert(self, ctx, date : str = None):
		"""Displays the Dilbert comic for the passed date (MM-DD-YYYY)."""
		
		channel = ctx.message.channel
		author  = ctx.message.author
		server  = ctx.message.server
		
		if not self.canDisplay(server):
			return
			
		if not date:
			# Auto to today's date
			date = dt.datetime.today().strftime("%m-%d-%Y")
			
		if not self.dateIsValid(date):
			msg = 'Usage: `$dilbert "[date MM-DD-YYYY]"`'
			await self.bot.send_message(channel, msg)
			return
		
		# Can't be after this date
		todayDate = dt.datetime.today().strftime("%m-%d-%Y")
		# Can't be before this date.
		firstDate = "04-16-1989"
		
		if not self.isDateBetween(date, firstDate, todayDate):
			msg = "Date out of range. Must be between {} and {}".format(firstDate, todayDate)
			await self.bot.send_message(channel, msg)
			return
		
		# Build our url and check if it's valid
		url       = self.buildDilbertURL(self.dateDict(date))
		imageHTML = ComicHelper.getImageHTML(url)
		
		if not imageHTML:
			msg = 'No comic found for *{}*'.format(date)
			await self.bot.send_message(channel, msg)
			return
			
		# Got a comic link
		imageURL  = ComicHelper.getImageURL(imageHTML)
		imageDisplayName = ComicHelper.getImageTitle(imageHTML)
		
		# Download Image
		await GetImage.get(imageURL, self.bot, channel, imageDisplayName)
		
	  # #### #
	 # XKCD #
	# #### #
	@commands.command(pass_context=True)
	async def randxkcd(self, ctx):
		"""Displays a random XKCD comic."""
		
		channel = ctx.message.channel
		author  = ctx.message.author
		server  = ctx.message.server
		
		if not self.canDisplay(server):
			return
		
		# Must be a comic number
		archiveURL = "http://xkcd.com/archive/"
		archiveHTML = ComicHelper.getImageHTML(archiveURL)
		newest = int(ComicHelper.getNewestXKCD(archiveHTML))
		
		# Start a loop to find a comic
		gotComic = False
		tries = 0
		while not gotComic:
	
			if tries >= 10:
				break
		
			# Build our url
			date = random.randint(1, newest)
			comicURL = "http://xkcd.com/" + str(date) + "/"

			# now we get the actual comic info
			imageHTML = ComicHelper.getImageHTML(comicURL)
		
			if imageHTML:
				gotComic = True
			
			tries += 1
			
		if tries >= 10:
			msg = 'Failed to find working link.'
			await self.bot.send_message(channel, msg)
			return
		
		# Got a comic link
		imageURL = ComicHelper.getXKCDImageURL(imageHTML)
		imageDisplayName = ComicHelper.getXKCDImageTitle(imageHTML)
		title = '{} *({})*'.format(imageDisplayName, date)

		# Download Image
		await GetImage.get(imageURL, self.bot, channel, title)


	@commands.command(pass_context=True)
	async def xkcd(self, ctx, date : str = None):
		"""Displays the XKCD comic for the passed date (MM-DD-YYYY) or comic number if found."""
		
		channel = ctx.message.channel
		author  = ctx.message.author
		server  = ctx.message.server
		
		if not self.canDisplay(server):
			return
			
		if not date:
			# Auto to today's date
			date = dt.datetime.today().strftime("%m-%d-%Y")
			
		if not self.dateIsValid(date):
			# If it's an int - let's see if it fits
			try:
				date = int(date)
			except:
				msg = 'Usage: `$xkcd "[date MM-DD-YYYY]"`'
				await self.bot.send_message(channel, msg)
				return
			# Must be a comic number
			archiveURL = "http://xkcd.com/archive/"
			archiveHTML = ComicHelper.getImageHTML(archiveURL)
			newest = int(ComicHelper.getNewestXKCD(archiveHTML))
			if int(date) > int(newest) or int(date) < 1:
				msg = "Comic out of range. Must be between 1 and {}".format(newest)
				await self.bot.send_message(channel, msg)
				return
			comicURL = "/" + str(date) + "/"
		else:
			# Can't be after this date.
			todayDate = dt.datetime.today().strftime("%m-%d-%Y")
			# Can't be before this date.
			firstDate = "01-01-2006"

			if not self.isDateBetween(date, firstDate, todayDate):
				msg = "Date out of range. Must be between {} and {}".format(firstDate, todayDate)
				await self.bot.send_message(channel, msg)
				return
			# Get date in a dict (Month, Day, Year)
			dateDict = self.dateDict(date)
			# Get URL
			archiveURL = "http://xkcd.com/archive/"
			archiveHTML = ComicHelper.getImageHTML(archiveURL)

			xkcdDate = "{}-{}-{}".format(int(dateDict['Year']), int(dateDict['Month']), int(dateDict['Day']))
			comicURL = ComicHelper.getXKCDURL( archiveHTML, xkcdDate )
		
		if not comicURL:
			msg = 'No comic found for *{}*'.format(date)
			await self.bot.send_message(channel, msg)
			return
		
		comicNumber = comicURL.replace('/', '').strip()
		comicURL = "http://xkcd.com" + comicURL

		# now we get the actual comic info
		imageHTML = ComicHelper.getImageHTML(comicURL)
		imageURL = ComicHelper.getXKCDImageURL(imageHTML)
		imageDisplayName = ComicHelper.getXKCDImageTitle(imageHTML)
		title = '{} *({})*'.format(imageDisplayName, comicNumber)
		# Download Image
		await GetImage.get(imageURL, self.bot, channel, title)
		
		
	  # ################### #
	 # Cyanide & Happiness #	
	# ################### #	
		
	@commands.command(pass_context=True)
	async def randcyanide(self, ctx):
		"""Randomly picks and displays a Cyanide & Happiness comic."""
		
		channel = ctx.message.channel
		author  = ctx.message.author
		server  = ctx.message.server
		
		if not self.canDisplay(server):
			return
		
		# Can't be after this date.
		todayDate = dt.datetime.today().strftime("%m-%d-%Y")
		# Can't be before this date.
		firstDate = "01-26-2005"

		# Get a random Julian date between the first comic and today
		gotComic = False
		tries = 0
		while not gotComic:
		
			if tries >= 10:
				break
						
			date = self.getRandDateBetween(firstDate, todayDate)

			# Get Arvhive URL
			getURL = "http://explosm.net/comics/archive/" + date['Year'] + "/" + date['Month']
		
			# Retrieve html and info
			imageHTML = ComicHelper.getImageHTML(getURL)
			if imageHTML:
				imagePage = ComicHelper.getCHURL(imageHTML, date['Year'] + "." + date['Month'] + "." + date['Day'])
				if imagePage:
					comicHTML = ComicHelper.getImageHTML(imagePage)
					if comicHTML:
						imageURL  = ComicHelper.getCHImageURL( comicHTML )
						if imageURL:
							gotComic = True
				
			tries += 1
			
		if tries >= 10:
			msg = 'Failed to find working link.'
			await self.bot.send_message(channel, msg)
			return
			
		imageDisplayName = "Cyanide & Happiness " + date['Year'] + "-" + date['Month'] + "-" + date['Day']
		# Download Image
		await GetImage.get(imageURL, self.bot, channel, imageDisplayName)



	@commands.command(pass_context=True)
	async def cyanide(self, ctx, date : str = None):
		"""Displays the Cyanide & Happiness comic for the passed date (MM-DD-YYYY) if found."""
		
		channel = ctx.message.channel
		author  = ctx.message.author
		server  = ctx.message.server
		
		if not self.canDisplay(server):
			return
			
		if not date:
			# Auto to today's date
			date = dt.datetime.today().strftime("%m-%d-%Y")
			
		if not self.dateIsValid(date):
			msg = 'Usage: `$cyanide "[date MM-DD-YYYY]"`'
			await self.bot.send_message(channel, msg)
			return

		# Can't be after this date.
		todayDate = dt.datetime.today().strftime("%m-%d-%Y")
		# Can't be before this date.
		firstDate = "01-26-2005"

		if not self.isDateBetween(date, firstDate, todayDate):
			msg = "Date out of range. Must be between {} and {}".format(firstDate, todayDate)
			await self.bot.send_message(channel, msg)
			return

		dateDict = self.dateDict(date)	
		# Get Arvhive URL
		getURL = "http://explosm.net/comics/archive/" + dateDict['Year'] + "/" + dateDict['Month']

		gotComic = False
		imageHTML = ComicHelper.getImageHTML(getURL)
		if imageHTML:
			imagePage = ComicHelper.getCHURL(imageHTML, dateDict['Year'] + "." + dateDict['Month'] + "." + dateDict['Day'])
			if imagePage:
				comicHTML = ComicHelper.getImageHTML(imagePage)
				if comicHTML:
					imageURL  = ComicHelper.getCHImageURL( comicHTML )
					if imageURL:
						gotComic = True
		
		if not gotComic:
			msg = 'No comic found for *{}*'.format(date)
			await self.bot.send_message(channel, msg)
			return
		
		imageDisplayName = "Cyanide & Happiness " + dateDict['Year'] + "-" + dateDict['Month'] + "-" + dateDict['Day']
		# Download Image
		await GetImage.get(imageURL, self.bot, channel, imageDisplayName)
		
		
	  # ############### #
	 # Calvin & Hobbes #
	# ############### #
	
	@commands.command(pass_context=True)
	async def randcalvin(self, ctx):
		"""Randomly picks and displays a Calvin & Hobbes comic."""
		
		channel = ctx.message.channel
		author  = ctx.message.author
		server  = ctx.message.server
		
		if not self.canDisplay(server):
			return

		# Can't be after this date.
		todayDate = "12-31-1995"
		# Can't be before this date.
		firstDate = "11-18-1985"

		gotComic = False
		tries = 0
		while not gotComic:
		
			if tries >= 10:
				break
						
			date = self.getRandDateBetween(firstDate, todayDate)
			# Get URL
			getURL = "http://marcel-oehler.marcellosendos.ch/comics/ch/" + date['Year'] + "/" + date['Month'] + "/" + date['Year'] + date['Month'] + date['Day'] + ".gif"

			# Retrieve html and info
			imageHTML = ComicHelper.getImageHTML(getURL)
		
			if imageHTML:
				imageURL  = getURL
				gotComic = True
				
			tries += 1
			
		if tries >= 10:
			msg = 'Failed to find working link.'
			await self.bot.send_message(channel, msg)
			return
			
		imageDisplayName = "Calvin & Hobbes " + date['Year'] + "-" + date['Month'] + "-" + date['Day']
		# Download Image
		await GetImage.get(imageURL, self.bot, channel, imageDisplayName)



	@commands.command(pass_context=True)
	async def calvin(self, ctx, date : str = None):
		"""Displays the Calvin & Hobbes comic for the passed date (MM-DD-YYYY) if found."""
		
		channel = ctx.message.channel
		author  = ctx.message.author
		server  = ctx.message.server
		
		if not self.canDisplay(server):
			return
			
		if not date:
			# Auto to the last Calvin & Hobbes comic
			date = "12-31-1995"
			
		if not self.dateIsValid(date):
			msg = 'Usage: `$calvin "[date MM-DD-YYYY]"`'
			await self.bot.send_message(channel, msg)
			return

		# Can't be after this date.
		todayDate = "12-31-1995"
		# Can't be before this date.
		firstDate = "11-18-1985"

		if not self.isDateBetween(date, firstDate, todayDate):
			msg = "Date out of range. Must be between {} and {}".format(firstDate, todayDate)
			await self.bot.send_message(channel, msg)
			return

		dateDict = self.dateDict(date)
		# Get URL
		getURL = "http://marcel-oehler.marcellosendos.ch/comics/ch/" + dateDict['Year'] + "/" + dateDict['Month'] + "/" + dateDict['Year'] + dateDict['Month'] + dateDict['Day'] + ".gif"

		# Retrieve html and info
		imageHTML = ComicHelper.getImageHTML(getURL)
		
		if not imageHTML:
			msg = 'No comic found for *{}*'.format(date)
			await self.bot.send_message(channel, msg)
			return

		imageDisplayName = "Calvin & Hobbes " + dateDict['Year'] + "-" + dateDict['Month'] + "-" + dateDict['Day']
		# Download Image
		await GetImage.get(getURL, self.bot, channel, imageDisplayName)
		
		
	  # ####################### #
	 # Garfield Minus Garfield #
	# ####################### #
	
	@commands.command(pass_context=True)
	async def randgmg(self, ctx):
		"""Randomly picks and displays a Garfield Minus Garfield comic."""
		
		channel = ctx.message.channel
		author  = ctx.message.author
		server  = ctx.message.server
		
		if not self.canDisplay(server):
			return

		# Can't be after this date.
		todayDate = dt.datetime.today().strftime("%m-%d-%Y")
		# Can't be before this date.
		firstDate = "02-13-2008"

		# Get a random Julian date between the first comic and today
		gotComic = False
		tries = 0
		while not gotComic:
		
			if tries >= 10:
				break
				
			date = self.getRandDateBetween(firstDate, todayDate)
			# Get URL
			getURL = "http://garfieldminusgarfield.net/day/" + date['Year'] + "/" + date['Month'] + "/" + date['Day']
			# Retrieve html and info
			imageHTML = ComicHelper.getImageHTML(getURL)
		
			if imageHTML:
				imageURL  = ComicHelper.getGMGImageURL(imageHTML)
				if imageURL:
					gotComic = True
				
			tries += 1

		if tries >= 10:
			msg = 'Failed to find working link.'
			await self.bot.send_message(channel, msg)
			return
		
		imageDisplayName = "Day " + date['Year'] + "-" + date['Month'] + "-" + date['Day']
		# Download Image
		await GetImage.get(imageURL, self.bot, channel, imageDisplayName)



	@commands.command(pass_context=True)
	async def gmg(self, ctx, date : str = None):
		"""Displays the Garfield Minus Garfield comic for the passed date (MM-DD-YYYY) if found."""
		
		channel = ctx.message.channel
		author  = ctx.message.author
		server  = ctx.message.server
		
		if not self.canDisplay(server):
			return
			
		if not date:
			# Auto to today
			date = dt.datetime.today().strftime("%m-%d-%Y")
			
		if not self.dateIsValid(date):
			msg = 'Usage: `$gmg "[date MM-DD-YYYY]"`'
			await self.bot.send_message(channel, msg)
			return

		# Can't be after this date.
		todayDate = dt.datetime.today().strftime("%m-%d-%Y")
		# Can't be before this date.
		firstDate = "02-13-2008"

		if not self.isDateBetween(date, firstDate, todayDate):
			msg = "Date out of range. Must be between {} and {}".format(firstDate, todayDate)
			await self.bot.send_message(channel, msg)
			return

		dateDict = self.dateDict(date)

		# Get URL
		getURL = "http://garfieldminusgarfield.net/day/" + dateDict['Year'] + "/" + dateDict['Month'] + "/" + dateDict['Day']
		
		# Retrieve html and info
		imageHTML = ComicHelper.getImageHTML(getURL)
		
		# Comment out to test
		'''if imageHTML == None:
			msg = 'No comic found for *{}*'.format(date)
			await self.bot.send_message(channel, msg)
			return'''
		
		imageURL  = ComicHelper.getGMGImageURL(imageHTML)

		if not imageURL:
			msg = 'No comic found for *{}*'.format(date)
			await self.bot.send_message(channel, msg)
			return

		imageDisplayName = "Day " + dateDict['Year'] + "-" + dateDict['Month'] + "-" + dateDict['Day']
		# Download Image
		await GetImage.get(imageURL, self.bot, channel, imageDisplayName)
		
		
	  # ######## #
	 # Garfield #
	# ######## #
		
	@commands.command(pass_context=True)
	async def randgarfield(self, ctx):
		"""Randomly picks and displays a Garfield comic."""
		
		channel = ctx.message.channel
		author  = ctx.message.author
		server  = ctx.message.server
		
		if not self.canDisplay(server):
			return

		# Can't be after this date.
		todayDate = dt.datetime.today().strftime("%m-%d-%Y")
		# Can't be before this date.
		firstDate = "06-19-1978"

		# Get a random Julian date between the first comic and today
		gotComic = False
		tries = 0
		while not gotComic:
		
			if tries >= 10:
				break
				
			date = self.getRandDateBetween(firstDate, todayDate)
			# Get URL
			getURL = "https://garfield.com/comic/" + date['Year'] + "/" + date['Month'] + "/" + date['Day']
			# Retrieve html and info
			imageHTML = ComicHelper.getImageHTML(getURL)
		
			if imageHTML:
				imageURL  = ComicHelper.getGImageURL(imageHTML)
				if imageURL:
					gotComic = True
				
			tries += 1

		if tries >= 10:
			msg = 'Failed to find working link.'
			await self.bot.send_message(channel, msg)
			return
		
		imageDisplayName = "Day " + date['Year'] + "-" + date['Month'] + "-" + date['Day']
		# Download Image
		await GetImage.get(imageURL, self.bot, channel, imageDisplayName)
		
	@commands.command(pass_context=True)
	async def garfield(self, ctx, date : str = None):
		"""Displays the Garfield comic for the passed date (MM-DD-YYYY) if found."""
		
		channel = ctx.message.channel
		author  = ctx.message.author
		server  = ctx.message.server
		
		if not self.canDisplay(server):
			return
			
		if not date:
			# Auto to today
			date = dt.datetime.today().strftime("%m-%d-%Y")
			
		if not self.dateIsValid(date):
			msg = 'Usage: `$garfield "[date MM-DD-YYYY]"`'
			await self.bot.send_message(channel, msg)
			return

		# Can't be after this date.
		todayDate = dt.datetime.today().strftime("%m-%d-%Y")
		# Can't be before this date.
		firstDate = "06-19-1978"

		if not self.isDateBetween(date, firstDate, todayDate):
			msg = "Date out of range. Must be between {} and {}".format(firstDate, todayDate)
			await self.bot.send_message(channel, msg)
			return

		dateDict = self.dateDict(date)

		# Get URL
		getURL = "https://garfield.com/comic/" + dateDict['Year'] + "/" + dateDict['Month'] + "/" + dateDict['Day']
		
		# Retrieve html and info
		imageHTML = ComicHelper.getImageHTML(getURL)
		
		# Comment out to test
		'''if imageHTML == None:
			msg = 'No comic found for *{}*'.format(date)
			await self.bot.send_message(channel, msg)
			return'''
		
		imageURL  = ComicHelper.getGImageURL(imageHTML)

		if not imageURL:
			msg = 'No comic found for *{}*'.format(date)
			await self.bot.send_message(channel, msg)
			return

		imageDisplayName = "Day " + dateDict['Year'] + "-" + dateDict['Month'] + "-" + dateDict['Day']
		# Download Image
		await GetImage.get(imageURL, self.bot, channel, imageDisplayName)
		
		
	  # ####### #	
	 # Peanuts #
	# ####### #
	
	@commands.command(pass_context=True)
	async def randpeanuts(self, ctx):
		"""Randomly picks and displays a Peanuts comic."""
		
		channel = ctx.message.channel
		author  = ctx.message.author
		server  = ctx.message.server
		
		if not self.canDisplay(server):
			return

		# Can't be after this date.
		todayDate = dt.datetime.today().strftime("%m-%d-%Y")
		# Can't be before this date.
		firstDate = "10-02-1950"

		# Get a random Julian date between the first comic and today
		gotComic = False
		tries = 0
		while not gotComic:
		
			if tries >= 10:
				break
				
			date = self.getRandDateBetween(firstDate, todayDate)
			# Get URL
			getURL = "http://www.gocomics.com/printable/peanuts/" + date['Year'] + "/" + date['Month'] + "/" + date['Day']
			# Retrieve html and info
			imageHTML = ComicHelper.getImageHTML(getURL)
		
			if imageHTML:
				imageURL  = ComicHelper.getPeanutsImageURL(imageHTML)
				if imageURL:
					gotComic = True
				
			tries += 1

		if tries >= 10:
			msg = 'Failed to find working link.'
			await self.bot.send_message(channel, msg)
			return
		
		imageDisplayName = "Day " + date['Year'] + "-" + date['Month'] + "-" + date['Day']
		# Download Image
		await GetImage.get(imageURL, self.bot, channel, imageDisplayName)
		
	@commands.command(pass_context=True)
	async def peanuts(self, ctx, date : str = None):
		"""Displays the Peanuts comic for the passed date (MM-DD-YYYY) if found."""
		
		channel = ctx.message.channel
		author  = ctx.message.author
		server  = ctx.message.server
		
		if not self.canDisplay(server):
			return
			
		if not date:
			# Auto to today
			date = dt.datetime.today().strftime("%m-%d-%Y")
			
		if not self.dateIsValid(date):
			msg = 'Usage: `$garfield "[date MM-DD-YYYY]"`'
			await self.bot.send_message(channel, msg)
			return

		# Can't be after this date.
		todayDate = dt.datetime.today().strftime("%m-%d-%Y")
		# Can't be before this date.
		firstDate = "10-02-1950"

		if not self.isDateBetween(date, firstDate, todayDate):
			msg = "Date out of range. Must be between {} and {}".format(firstDate, todayDate)
			await self.bot.send_message(channel, msg)
			return

		dateDict = self.dateDict(date)

		# Get URL
		getURL = "http://www.gocomics.com/printable/peanuts/" + dateDict['Year'] + "/" + dateDict['Month'] + "/" + dateDict['Day']
		
		# Retrieve html and info
		imageHTML = ComicHelper.getImageHTML(getURL)
		
		# Comment out to test
		'''if imageHTML == None:
			msg = 'No comic found for *{}*'.format(date)
			await self.bot.send_message(channel, msg)
			return'''
		
		imageURL  = ComicHelper.getPeanutsImageURL(imageHTML)

		if not imageURL:
			msg = 'No comic found for *{}*'.format(date)
			await self.bot.send_message(channel, msg)
			return

		imageDisplayName = "Day " + dateDict['Year'] + "-" + dateDict['Month'] + "-" + dateDict['Day']
		# Download Image
		await GetImage.get(imageURL, self.bot, channel, imageDisplayName)