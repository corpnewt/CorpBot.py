import random
import math
import datetime as dt
from   pyquery import PyQuery as pq
from   Cogs import DL
from   urllib.parse import unquote

try:
    # Python 2.6-2.7
    from HTMLParser import HTMLParser
except ImportError:
    # Python 3
    from html.parser import HTMLParser

def setup(bot):
	# Not a cog - pass
	pass

# This module contains all the shit methods used for getting comic URLs... ugh.

def julianDate(my_date):
	# Takes a date string MM-DD-YYYY and
	# returns Julian Date
	date = my_date.split("-")

	month = int(date[0])
	day   = int(date[1])
	year  = int(date[2])

	month=(month-14)/12
	year=year+4800
	JDate=1461*(year+month)/4+367*(month-2-12*month)/12-(3*((year+month+100)/100))/4+day-32075
	return JDate

# Function from:  https://gist.github.com/jiffyclub/1294443
def date_to_jd(year,month,day):
	if month == 1 or month == 2:
		yearp = year - 1
		monthp = month + 12
	else:
		yearp = year
		monthp = month
	# this checks where we are in relation to October 15, 1582, the beginning
	# of the Gregorian calendar.
	if ((year < 1582) or
		(year == 1582 and month < 10) or
		(year == 1582 and month == 10 and day < 15)):
		# before start of Gregorian calendar
		B = 0
	else:
		# after start of Gregorian calendar
		A = math.trunc(yearp / 100.)
		B = 2 - A + math.trunc(A / 4.)
	if yearp < 0:
		C = math.trunc((365.25 * yearp) - 0.75)
	else:
		C = math.trunc(365.25 * yearp)

	D = math.trunc(30.6001 * (monthp + 1))

	jd = B + C + D + day + 1720994.5
	return jd

# Function from:  https://gist.github.com/jiffyclub/1294443
def jd_to_date(jd):
	jd = jd + 0.5
	F, I = math.modf(jd)
	I = int(I)
	A = math.trunc((I - 1867216.25)/36524.25)
	if I > 2299160:
		B = I + 1 + A - math.trunc(A / 4.)
	else:
		B = I
	C = B + 1524
	D = math.trunc((C - 122.1) / 365.25)
	E = math.trunc(365.25 * D)
	G = math.trunc((C - E) / 30.6001)
	day = C - E + F - math.trunc(30.6001 * G)
	if G < 13.5:
		month = G - 1
	else:
		month = G - 13
	if month > 2.5:
		year = D - 4716
	else:
		year = D - 4715
	return year, month, day
	
	# Find string between 2 strings
def find_between( s, first, last ):
    try:
        start = s.index( first ) + len( first )
        end = s.index( last, start )
        return s[start:end]
    except ValueError:
        return ""

def find_first_between( source, start_sep, end_sep ):
	result=[]
	tmp=source.split(start_sep)
	for par in tmp:
		if end_sep in par:
			result.append(par.split(end_sep)[0])
	if len(result) == 0:
		return None
	else:
		return result[0]

def find_last_between( source, start_sep, end_sep ):
	result=[]
	tmp=source.split(start_sep)
	for par in tmp:
		if end_sep in par:
			result.append(par.split(end_sep)[0])
	if len(result) == 0:
		return None
	else:
		return result[len(result)-1] # Return last item

async def getImageHTML ( url, ua : str = '' ):
    try:
        return await DL.async_text(url, {'User-Agent': ua})
    except Exception as e:
        return None

def getImageURL ( html ):
    imageURL = find_between( html, "data-image=", "data-date=" )
    return imageURL.replace('"', '').strip()

def getImageTitle ( html ):
    imageTitle = find_between( html, "data-title=", "data-tags=" )
    h = HTMLParser()
    imageTitle = h.unescape(imageTitle)
    #print(h.unescape(imageTitle))
    return imageTitle.replace('"', '').strip()

# C&H Methods

def getCHURL ( html, date ):
	# YYYY.MM.DD format
	# <a href="[comic url]">2005.01.31</a>
	comicBlock = find_last_between( html, '<a href="', "\">" + date + "</a>")
	
	if not comicBlock:
		return None
	else:
		return comicBlock.replace('"', '').strip()
		
		
def getCHImageURL ( html ):
	# comicBlock = find_last_between( html, 'div id="comic-container"', "</div>")
	
	# if comicBlock == None:
		# return None
	
	imageURL = find_last_between( html, 'id="main-comic" src=', '>' )
	
	if not imageURL:
		return None
	
	imageURL = imageURL.replace('"', '').strip()
	
	imageURL = imageURL.split("?t=")[0]
	
	if imageURL[0:2] == "//":
		# Add http?
		imageURL = "http:" + imageURL
	if imageURL[-1:] == "/":
		# Strip trailing /
		return imageURL[0:-1]
	else:
		return imageURL

	
# XKCD Methods	

def getNewestXKCD ( html ):
	comicBlock = find_last_between( html, 'div id="middleContainer"', "</div>")
	
	if not comicBlock:
		return None
	
	imageURL = find_first_between( comicBlock, "href=", " title=" )
	imageURL = imageURL.replace('/', '').strip()
	return imageURL.replace('"', '').strip()
	
def getXKCDURL ( html, date ):
	# YYYY-M(M)-D(D) format
	# <a href="/17/" title="2006-1-1">What If</a>
	comicBlock = find_last_between( html, 'div id="comic"', "</div>")
	
	if not comicBlock:
		return None
	
	imageURL = find_first_between( html, "href=", " title=\"" + date + "\"" )
	if imageURL == None:
		return None
	else:
		return imageURL.replace('"', '').strip()

def getXKCDImageURL ( html ):
	comicBlock = find_last_between( html, 'div id="comic"', "</div>")
	
	if not comicBlock:
		return None
	
	imageURL = find_last_between( comicBlock, "img src=", "title=" )
	imageURL = imageURL.replace('"', '').strip()
	
	if imageURL[0:2] == "//":
		# Add http?
		return "http:" + imageURL
	else:
		return imageURL

def getXKCDImageTitle ( html ):
	comicBlock = find_last_between( html, 'div id="comic"', "</div>")
	
	if not comicBlock:
		return None
	
	imageTitle = find_last_between( comicBlock, "alt=", ">" )
	# Drop srcset= if there
	imageTitle = imageTitle.split('srcset=')[0]
	h = HTMLParser()
	imageTitle = h.unescape(imageTitle)
	imageTitle = imageTitle.replace('"', '').strip()
	imageTitle = imageTitle.replace('/', '').strip()
	return imageTitle

def getXKCDImageText ( html ):
	comicBlock = find_last_between( html, 'div id="comic"', "</div>")
	
	if not comicBlock:
		return None
	
	imageText = find_last_between( comicBlock, 'title="', '" ' )
	parser = HTMLParser()
	imageText = parser.unescape(imageText)
	return unquote(imageText)

# Garfield Minus Garfield Methods

def getGMGImageURL ( html ):
	if not html:
		return None
		
	comicBlock = find_last_between( html, 'div class="photo"', "</a>")
	
	if not comicBlock:
		return None
	
	imageURL = find_last_between( comicBlock, "img src=", " alt=" )
	imageURL = imageURL.replace('"', '').strip()
	
	return imageURL	
	
# Garfield Methods

def getGImageURL ( html ):
	if not html:
		return None
		
	comicBlock = find_last_between( html, 'img class="img-responsive" src=', ' width')
	
	if not comicBlock:
		return None

	imageURL = comicBlock.replace('"', '').strip()
	
	return imageURL	
	
# Peanuts Methods

def getPeanutsImageURL ( html ):
	if not html:
		return None

	dom = pq(html)

	pic = dom('picture.img-fluid.item-comic-image')
	pic = str(pic).strip().replace('\r', '').replace('\n', ' ').replace('\t', ' ')

	comicBlock = find_last_between( pic, 'src=', '/>')
	
	if not comicBlock:
		return None

	imageURL = comicBlock.replace('"', '').strip()
	
	return imageURL	
