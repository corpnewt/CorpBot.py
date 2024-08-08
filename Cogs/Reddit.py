import asyncio, discord, random, requests, time, mimetypes
from   datetime import datetime
from   urllib.parse import quote
from   html.parser import HTMLParser
from   os.path import splitext
from   discord.ext import commands
from   Cogs import Utils, GetImage, Message, ReadableTime, DL, Nullify, PickList
from   pyquery import PyQuery as pq
try:
	from urllib.parse import urlparse
except ImportError:
	from urlparse import urlparse
try:
	from html import unescape
except ImportError:
	pass

def setup(bot):
	# Add the bot and deps
	settings = bot.get_cog("Settings")
	bot.add_cog(Reddit(bot, settings))

# This module grabs Reddit posts and selects one at random

class MLStripper(HTMLParser):
	def __init__(self):
		super().__init__()
		self.reset()
		self.fed = []
	def handle_data(self, d):
		self.fed.append(d)
	def get_data(self):
		return ''.join(self.fed)

class Reddit(commands.Cog):

	# Init with the bot reference, and a reference to the settings var and xp var
	def __init__(self, bot, settings):
		self.bot = bot
		self.settings = settings
		self.ua = 'CorpNewt DeepThoughtBot'
		self.extList = ["jpg", "jpeg", "png", "gif", "tiff", "tif"]
		self.headList = ["image/jpeg", "image/png", "image/gif", "image/jpg"]
		global Utils, DisplayName
		Utils = self.bot.get_cog("Utils")
		DisplayName = self.bot.get_cog("DisplayName")
		
	def unescape(self,text):
		try:
			u = unescape
		except NameError:
			h = HTMLParser()
			u = h.unescape
		return u(text)

	def strip_tags(self, html):
		html = self.unescape(html)
		s = MLStripper()
		s.feed(html)
		return s.get_data()
	
	
	async def getImageHEAD(self, url):
		response = await DL.async_head_json(url)
		return response['content-type']


	async def getImageHEAD(self, url):
		response = await DL.async_head_json(url)
		return response['content-type']

	async def getTitle(self, url, answer : bool = False, image : bool = False):
		try:
			r = await DL.async_json(url, {'User-agent': self.ua})
			numPosts = len(r['data']['children'])
		except Exception:
			numPosts = 0
		if numPosts <= 0:
			# No links
			return None
		# If we need an image - make sure we have a valid one
		gotLink = False
		while not gotLink:
			if image:
				gotImage = False
				while not gotImage:
					randnum = random.randint(0,numPosts-1)
					try:
						theJSON = r["data"]["children"][randnum]["data"]
					except IndexError:
						# Failed - set to none
						theJSON = { "url" : "" }
					if GetImage.get_ext(theJSON["url"]).lower() in self.extList:
						gotImage = True
						gotLink  = True
			else:
				randnum = random.randint(0,numPosts-1)
				try:
					theJSON = r["data"]["children"][randnum]["data"]
					gotLink = True
				except IndexError:
					theJSON = { "url" : "" }
		if not (answer or image):
			# Just return the title
			return '{} ([Go To Thread](<{}>))'.format(self.unescape(theJSON["title"]),theJSON["url"])
		if answer or image:
			# We need the image or the answer
			return {'title' : self.unescape(theJSON['title']), 'url' : theJSON["url"]}

	async def getText(self, url):
		try:
			r = await DL.async_json(url, {'User-agent': self.ua})
			numPosts = len(r['data']['children'])
		except Exception:
			numPosts = 0
		if numPosts <= 0:
			# No links
			return None
		returnDict = None
		for i in range(0, 10):
			randnum = random.randint(0,numPosts-1)
			try:
				theJSON = r["data"]["children"][randnum]["data"]
				returnDict = {
					"title": self.unescape(theJSON["title"]),
					"content": self.strip_tags(theJSON["selftext_html"] or ""),
					"over_18": theJSON.get("over_18",False),
					"url": theJSON["url"],
					'score' : theJSON['score'], 
					'num_comments' : theJSON['num_comments']
				}
				break
			except IndexError:
				continue
		return returnDict
	
	async def getInfo(self, url):
		# Let's try using reddit's json info to get our images
		try:
			r = await DL.async_json(url, {'User-agent': self.ua})
			numPosts = len(r['data']['children'])
		except Exception:
			numPosts = 0
		if numPosts <= 0:
			# No links
			return None
		returnDict = None
		for i in range(0, 10):
			randnum = random.randint(0, numPosts-1)
			try:
				theJSON = r["data"]["children"][randnum]["data"]
				theURL = None
				if 'preview' in theJSON:
					# We've got images right in the json
					theURL = theJSON['preview']['images'][0]['source']['url']
				else:
					# No images - let's check the url
					imageURL = theJSON['url']
					if 'imgur.com/a/' in imageURL.lower():
						# It's an imgur album
						response = await DL.async_text(imageURL)
						dom = pq(response.text)
						# Get the first image
						image = dom('.image-list-link')[0]
						image = pq(image).attr('href').split('/')[2]
						theURL = 'http://i.imgur.com/{}.jpg'.format(image)
					else:
						# Not an imgur album - let's try for a single image
						if GetImage.get_ext(imageURL).lower() in self.extList:
							theURL = imageURL
							theURL = imageURL
						elif await self.getImageHEAD(imageURL).lower() in self.headList:
							# Check header as a last resort
							theURL = imageURL				
							theURL = imageURL		
						elif await self.getImageHEAD(imageURL).lower() in self.headList:
							# Check header as a last resort
							theURL = imageURL				
				if not theURL:
					continue
				returnDict = { 
					'title': self.unescape(theJSON['title']), 
					'url': self.unescape(theURL), 
					'over_18': theJSON.get('over_18',False), 
					'permalink': theJSON['permalink'], 
					'score' : theJSON['score'], 
					'num_comments' : theJSON['num_comments'] }
				break
			except Exception:
				continue
		return returnDict
			
	def canDisplay(self, server):
		# Check if we can display images
		lastTime = int(self.settings.getServerStat(server, "LastPicture"))
		threshold = int(self.settings.getServerStat(server, "PictureThreshold"))
		if not GetImage.canDisplay( lastTime, threshold ):
			# await channel.send('Too many images at once - please wait a few seconds.')
			return False
		# If we made it here - set the LastPicture method
		self.settings.setServerStat(server, "LastPicture", int(time.time()))
		return True
	
	@commands.command()
	async def ruser(self, ctx, *, user_name = None):
		"""Gets some info on the passed username - attempts to use your username if none provided."""
		user_name = user_name or ctx.author.display_name
		# Get the info
		url = "https://www.reddit.com/user/{}/about.json?raw_json=1".format(quote(user_name))
		# Giving a 200 response for some things that aren't found
		try:
			theJSON = await DL.async_json(url, {'User-agent': self.ua})
		except:
			# Assume that we couldn't find that user
			error = "Make sure you're passing a valid reddit username."
			return await Message.EmbedText(title="An error occurred!", description=error, color=ctx.author).send(ctx)
		# Returns:  {"message": "Not Found", "error": 404}  if not found
		if "message" in theJSON:
			error = theJSON.get("error", "An error has occurred.")
			return await Message.EmbedText(title=theJSON["message"], description=str(error), color=ctx.author).send(ctx)
		# Build our embed
		e = { 
			"title" : "/u/" + theJSON["data"]["name"],
			"url" : "https://www.reddit.com/user/" + theJSON["data"]["name"],
			"color" : ctx.author, 
			"fields" : [] }

		# Get the unix timestamp for the account creation
		ts = int(theJSON["data"]["created_utc"])
		created_string = "<t:{}> (<t:{}:R>)".format(ts,ts)

		e["fields"].append({ "name" : "Created", "value" : created_string, "inline" : True })
		e["fields"].append({ "name" : "Link Karma", "value" : "{:,}".format(theJSON["data"]["link_karma"]), "inline" : True })
		e["fields"].append({ "name" : "Comment Karma", "value" : "{:,}".format(theJSON["data"]["comment_karma"]), "inline" : True })
		e["fields"].append({ "name" : "Has Gold", "value" : str(theJSON["data"]["is_gold"]), "inline" : True })
		e["fields"].append({ "name" : "Is Mod", "value" : str(theJSON["data"]["is_mod"]), "inline" : True })
		e["fields"].append({ "name" : "Verified Email", "value" : str(theJSON["data"]["has_verified_email"]), "inline" : True })
		# Send the embed
		await Message.Embed(**e).send(ctx)

	@commands.command()
	async def nosleep(self, ctx):
		"""I hope you're not tired..."""
		message = await Message.Embed(
			title="Fumbling through reddit posts...",
			color=ctx.author
		).send(ctx)
		msg = await self.getText('https://www.reddit.com/r/nosleep/top.json?sort=top&t=week&limit=100')
		if not msg:
			return await Message.Embed(title="Whoops! I couldn't find a working link.").send(ctx.message)
		return await PickList.PagePicker(
			url=msg["url"],
			title=msg["title"],
			description=msg["content"],
			timeout=600, # Allow 10 minutes before we stop watching the picker
			ctx=ctx,
			footer="Score: {:,} | Comments: {:,}".format(
				msg["score"],
				msg["num_comments"]
			),
			message=message
		).pick()

	@commands.command()
	async def joke(self, ctx):
		"""Let's see if reddit can be funny..."""
		message = await Message.Embed(
			title="Fumbling through reddit posts...",
			color=ctx.author
		).send(ctx)
		msg = await self.getText('https://www.reddit.com/r/jokes/top.json?sort=top&t=week&limit=100')
		if not msg:
			return await Message.Embed(title="Whoops! I couldn't find a working link.").send(ctx,message)
		# Check for nsfw - and for now, only allow admins/botadmins to post those
		if msg['over_18']:
			# NSFW - check admin
			if not await Utils.is_bot_admin_reply(ctx,message="You do not have sufficient privileges to access nsfw subreddits."): return
		return await PickList.PagePicker(
			url=msg["url"],
			title=msg["title"],
			description=msg["content"],
			timeout=600, # Allow 10 minutes before we stop watching the picker
			ctx=ctx,
			footer="Score: {:,} | Comments: {:,}".format(
				msg["score"],
				msg["num_comments"]
			),
			message=message
		).pick()
	
	@commands.command()
	async def lpt(self, ctx):
		"""Become a pro - AT LIFE."""
		msg = await self.getTitle('https://www.reddit.com/r/LifeProTips/top.json?sort=top&t=week&limit=100')
		await ctx.send(Nullify.escape_all(msg,markdown=False))
		
	@commands.command()
	async def shittylpt(self, ctx):
		"""Your advise is bad, and you should feel bad."""
		msg = await self.getTitle('https://www.reddit.com/r/ShittyLifeProTips/top.json?sort=top&t=week&limit=100')
		await ctx.send(Nullify.escape_all(msg,markdown=False))

	@commands.command()
	async def thinkdeep(self, ctx):
		"""Spout out some intellectual brilliance."""
		msg = await self.getTitle('https://www.reddit.com/r/showerthoughts/top.json?sort=top&t=week&limit=100')
		await ctx.send(Nullify.escape_all(msg,markdown=False))

	@commands.command()
	async def brainfart(self, ctx):
		"""Spout out some uh... intellectual brilliance..."""
		msg = await self.getTitle('https://www.reddit.com/r/Showerthoughts/controversial.json?sort=controversial&t=week&limit=100')
		await ctx.send(Nullify.escape_all(msg,markdown=False))

	@commands.command()
	async def nocontext(self, ctx):
		"""Spout out some intersexual brilliance."""
		msg = await self.getTitle('https://www.reddit.com/r/nocontext/top.json?sort=top&t=week&limit=100')
		await ctx.send(Nullify.escape_all(msg,markdown=False))
		
	@commands.command()
	async def withcontext(self, ctx):
		"""Spout out some contextual brilliance."""
		msg = await self.getTitle('https://www.reddit.com/r/evenwithcontext/top.json?sort=top&t=week&limit=100')
		await ctx.send(Nullify.escape_all(msg,markdown=False))

	@commands.command()
	async def question(self, ctx):
		"""Spout out some interstellar questioning... ?"""
		infoDict = await self.getTitle('https://www.reddit.com/r/NoStupidQuestions/top.json?sort=top&t=week&limit=100', True)
		self.settings.setServerStat(ctx.guild, "LastAnswer", infoDict["url"])
		msg = '{} ([Go To Thread](<{}>))'.format(infoDict["title"],infoDict["url"])
		await ctx.send(Nullify.escape_all(msg,markdown=False))
		
	@commands.command()
	async def answer(self, ctx):
		"""Spout out some interstellar answering... ?"""
		answer = self.settings.getServerStat(ctx.guild, "LastAnswer")
		msg = "You need to ask a `{}question` first!".format(ctx.prefix) if not answer else "{}".format(answer)
		await ctx.send(Nullify.escape_all(msg,markdown=False))

	@commands.command(aliases=["rimage","reddit"])
	async def redditimage(self, ctx, subreddit = None):
		"""Try to grab an image from an image-based subreddit."""
		if not subreddit: return await ctx.send("You need to pass a subreddit name.")
		await self._image_do(ctx,'https://www.reddit.com/r/{}'.format(quote(subreddit)))
		
	async def _image_do(self, ctx, url, get_top=True):
		if not self.canDisplay(ctx.guild): return
		# Grab our image title and url
		message = await Message.Embed(
			title="Fumbling through reddit posts...",
			color=ctx.author
		).send(ctx)
		infoDict = None
		if get_top:
			for t in ("week","month","year",""):
				u = "{}/top.json?sort=top&{}limit=100".format(
					url,
					"t={}&".format(t) if t else ""
				)
				infoDict = await self.getInfo(u)
				if infoDict: break
		else:
			infoDict = await self.getInfo(url)
		if not infoDict:
			return await Message.Embed(title="Whoops! I couldn't find a working link.").send(ctx,message)
		# Check for nsfw - and for now, only allow admins/botadmins to post those
		if infoDict['over_18']:
			# NSFW - check admin
			if not await Utils.is_bot_admin_reply(ctx,message="You do not have sufficient privileges to access nsfw subreddits."): return
		return await Message.Embed(
			title=infoDict["title"], 
			url="https://www.reddit.com"+infoDict["permalink"], 
			image=infoDict["url"], 
			color=ctx.author,
			footer="Score: {:,} | Comments: {:,}".format(
				infoDict["score"],
				infoDict["num_comments"]
			)).send(ctx,message)

	@commands.command()
	async def beeple(self, ctx):
		"""A new image every day... for years."""
		await self._image_do(ctx,'https://www.reddit.com/r/beeple/new.json?limit=100', get_top=False)
	
	@commands.command()
	async def macsetup(self, ctx):
		"""Feast your eyes upon these setups."""
		await self._image_do(ctx,'https://www.reddit.com/r/macsetups')
		
	@commands.command()
	async def pun(self, ctx):
		"""I don't know, don't ask..."""
		await self._image_do(ctx,'https://www.reddit.com/r/puns')
	
	@commands.command()
	async def carmod(self, ctx):
		"""Marvels of modern engineering."""
		await self._image_do(ctx,'https://www.reddit.com/r/Shitty_Car_Mods')
	
	@commands.command()
	async def battlestation(self, ctx):
		"""Let's look at some pretty stuff."""
		await self._image_do(ctx,'https://www.reddit.com/r/battlestations')
		
	@commands.command()
	async def shittybattlestation(self, ctx):
		"""Let's look at some shitty stuff."""
		await self._image_do(ctx,'https://www.reddit.com/r/shittybattlestations')

	@commands.command()
	async def dankmeme(self, ctx):
		"""Only the dankest."""
		await self._image_do(ctx,'https://www.reddit.com/r/dankmemes')

	@commands.command()
	async def cablefail(self, ctx):
		"""Might as well be a noose..."""
		await self._image_do(ctx,'https://www.reddit.com/r/cablefail')

	@commands.command()
	async def techsupport(self, ctx):
		"""Tech support irl."""
		await self._image_do(ctx,'https://www.reddit.com/r/techsupportgore')

	@commands.command()
	async def software(self, ctx):
		"""I uh... I wrote it myself."""
		await self._image_do(ctx,'https://www.reddit.com/r/softwaregore')

	@commands.command()
	async def meirl(self, ctx):
		"""Me in real life."""
		await self._image_do(ctx,'https://www.reddit.com/r/me_irl')

	@commands.command()
	async def starterpack(self, ctx):
		"""Starterpacks."""
		await self._image_do(ctx,'https://www.reddit.com/r/starterpacks')

	@commands.command()
	async def earthporn(self, ctx):
		"""Earth is good."""
		await self._image_do(ctx,'https://www.reddit.com/r/EarthPorn')
		
	@commands.command()
	async def wallpaper(self, ctx):
		"""Get something pretty to look at."""
		await self._image_do(ctx,'https://www.reddit.com/r/wallpapers')
		
	@commands.command()
	async def abandoned(self, ctx):
		"""Get something abandoned to look at."""
		await self._image_do(ctx,'https://www.reddit.com/r/abandonedporn')

	@commands.command()
	async def dragon(self, ctx):
		"""From the past - when great winged beasts soared the skies."""
		await self._image_do(ctx,'https://www.reddit.com/r/BeardedDragons')

	@commands.command()
	async def aww(self, ctx):
		"""Whenever you're down - uppify."""
		await self._image_do(ctx,'https://www.reddit.com/r/aww')
	
	@commands.command()
	async def randomdog(self, ctx):
		"""Bark if you know whassup."""
		await self._image_do(ctx,'https://www.reddit.com/r/dogpictures')
		
	@commands.command()
	async def randomcat(self, ctx):
		"""Meow."""
		await self._image_do(ctx,'https://www.reddit.com/r/cats')
