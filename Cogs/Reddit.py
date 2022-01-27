import asyncio, discord, random, requests, time, mimetypes
from   datetime import datetime
from   urllib.parse import quote
from   html.parser import HTMLParser
from   os.path import splitext
from   discord.ext import commands
from   Cogs import Utils, GetImage, Message, ReadableTime, UserTime, DL, Nullify
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
	def __init__(self, bot, settings, posts : int = 100):
		self.bot = bot
		self.settings = settings
		if not type(posts) == int:
			posts = 100
		self.posts = posts
		self.ua = 'CorpNewt DeepThoughtBot'
		self.extList = ["jpg", "jpeg", "png", "gif", "tiff", "tif"]
		self.headList = ["image/jpeg", "image/png", "image/gif", "image/jpg"]
		global Utils, DisplayName
		Utils = self.bot.get_cog("Utils")
		DisplayName = self.bot.get_cog("DisplayName")
		
	def strip_tags(self, html):
		try:
			u = unescape
		except NameError:
			h = HTMLParser()
			u = h.unescape
		html = u(html)
		s = MLStripper()
		s.feed(html)
		return s.get_data()
	
	async def getImageHEAD(self, url):
		response = await DL.async_head_json(url)
		return response['content-type']

	async def getTitle(self, url, answer : bool = False, image : bool = False):
		# Load url - with self.posts number of posts
		r = await DL.async_json(url, {'User-agent': self.ua})
		# If we need an image - make sure we have a valid one
		gotLink = False
		while not gotLink:
			if image:
				gotImage = False
				while not gotImage:
					randnum = random.randint(0,self.posts)
					try:
						theJSON = r["data"]["children"][randnum]["data"]
					except IndexError:
						# Failed - set to none
						theJSON = { "url" : "" }
					if GetImage.get_ext(theJSON["url"]).lower() in self.extList:
						gotImage = True
						gotLink  = True
			else:
				randnum = random.randint(0,self.posts)
				try:
					theJSON = r["data"]["children"][randnum]["data"]
					gotLink = True
				except IndexError:
					theJSON = { "url" : "" }
		if not (answer or image):
			# Just return the title
			return '{}'.format(theJSON["title"])
		if answer or image:
			# We need the image or the answer
			return {'title' : theJSON['title'], 'url' : theJSON["url"]}

	async def getText(self, url):
		# Load url - with self.posts number of posts
		r = await DL.async_json(url, {'User-agent': self.ua})
		gotLink = False
		returnDict = None
		for i in range(0, 10):
			randnum = random.randint(0,self.posts)
			try:
				theJSON = r["data"]["children"][randnum]["data"]
				if 'over_18' in theJSON:
					returnDict = { 'title': theJSON['title'], 'content': self.strip_tags(theJSON['selftext_html']), 'over_18': theJSON['over_18'] }
				else:
					returnDict = { 'title': theJSON['title'], 'content': self.strip_tags(theJSON['selftext_html']), 'over_18': False }
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
		gotLink = False
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
						elif await self.getImageHEAD(imageURL).lower() in self.headList:
							# Check header as a last resort
							theURL = imageURL				
				if not theURL:
					continue
				try:
					u = unescape
				except NameError:
					h = HTMLParser()
					u = h.unescape
				returnDict = { 
					'title': theJSON['title'], 
					'url': u(theURL), 
					'over_18': theJSON['over_18'], 
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
	
	@commands.command(pass_context=True)
	async def ruser(self, ctx, *, user_name = None):
		"""Gets some info on the passed username - attempts to use your username if none provided."""
		if user_name == None:
			user_name = ctx.author.nick if ctx.author.nick else ctx.author.name
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
		created_s = time.gmtime(theJSON["data"]["created_utc"])
		created_dt = datetime(*created_s[:6])
		# Get the actual user time of creation
		created = UserTime.getUserTime(ctx.author, self.settings, created_dt)
		created_string = "{} {}".format(created['time'], created['zone'])
		e["fields"].append({ "name" : "Created", "value" : created_string, "inline" : True })
		e["fields"].append({ "name" : "Link Karma", "value" : "{:,}".format(theJSON["data"]["link_karma"]), "inline" : True })
		e["fields"].append({ "name" : "Comment Karma", "value" : "{:,}".format(theJSON["data"]["comment_karma"]), "inline" : True })
		e["fields"].append({ "name" : "Has Gold", "value" : str(theJSON["data"]["is_gold"]), "inline" : True })
		e["fields"].append({ "name" : "Is Mod", "value" : str(theJSON["data"]["is_mod"]), "inline" : True })
		e["fields"].append({ "name" : "Verified Email", "value" : str(theJSON["data"]["has_verified_email"]), "inline" : True })
		# Send the embed
		await Message.Embed(**e).send(ctx)

	@commands.command(pass_context=True)
	async def nosleep(self, ctx):
		"""I hope you're not tired..."""
		msg = await self.getText('https://www.reddit.com/r/nosleep/top.json?sort=top&t=week&limit=100')
		if not msg: return await ctx.send("Whoops! I couldn't find a working link.")
		mess = '__**{}**__\n\n'.format(msg['title'])
		mess += msg['content']
		await Message.Message(message=Nullify.escape_all(mess,markdown=False)).send(ctx)

	@commands.command(pass_context=True)
	async def joke(self, ctx):
		"""Let's see if reddit can be funny..."""
		msg = await self.getText('https://www.reddit.com/r/jokes/top.json?sort=top&t=week&limit=100')
		if not msg: return await ctx.send("Whoops! I couldn't find a working link.")
		# Check for nsfw - and for now, only allow admins/botadmins to post those
		if msg['over_18']:
			# NSFW - check admin
			if not await Utils.is_bot_admin_reply(ctx,message="You do not have sufficient privileges to access nsfw subreddits."): return
		mess = '*{}*\n\n'.format(msg['title'])
		mess += msg['content']
		await Message.Message(message=Nullify.escape_all(mess,markdown=False)).send(ctx)

	@commands.command(pass_context=True)
	async def dirtyjoke(self, ctx):
		"""Let's see if reddit can be dir-... oh... uh.. funny... (bot-admin only)"""
		# NSFW - check admin
		if not await Utils.is_bot_admin_reply(ctx,message="You do not have sufficient privileges to access nsfw subreddits."): return
		msg = await self.getText('https://www.reddit.com/r/DirtyJokes/top.json?sort=top&t=week&limit=100')
		if not msg: return await ctx.send("Whoops! I couldn't find a working link.")
		mess = '*{}*\n\n'.format(msg['title'])
		mess += msg['content']
		await Message.Message(message=Nullify.escape_all(mess,markdown=False)).send(ctx)
	
	@commands.command(pass_context=True)
	async def lpt(self, ctx):
		"""Become a pro - AT LIFE."""
		msg = await self.getTitle('https://www.reddit.com/r/LifeProTips/top.json?sort=top&t=week&limit=100')
		await ctx.send(Nullify.escape_all(msg,markdown=False))
		
	@commands.command(pass_context=True)
	async def shittylpt(self, ctx):
		"""Your advise is bad, and you should feel bad."""
		msg = await self.getTitle('https://www.reddit.com/r/ShittyLifeProTips/top.json?sort=top&t=week&limit=100')
		await ctx.send(Nullify.escape_all(msg,markdown=False))

	@commands.command(pass_context=True)
	async def thinkdeep(self, ctx):
		"""Spout out some intellectual brilliance."""
		msg = await self.getTitle('https://www.reddit.com/r/showerthoughts/top.json?sort=top&t=week&limit=100')
		await ctx.send(Nullify.escape_all(msg,markdown=False))

	@commands.command(pass_context=True)
	async def brainfart(self, ctx):
		"""Spout out some uh... intellectual brilliance..."""
		msg = await self.getTitle('https://www.reddit.com/r/Showerthoughts/controversial.json?sort=controversial&t=week&limit=100')
		await ctx.send(Nullify.escape_all(msg,markdown=False))

	@commands.command(pass_context=True)
	async def nocontext(self, ctx):
		"""Spout out some intersexual brilliance."""
		msg = await self.getTitle('https://www.reddit.com/r/nocontext/top.json?sort=top&t=week&limit=100')
		await ctx.send(Nullify.escape_all(msg,markdown=False))
		
	@commands.command(pass_context=True)
	async def withcontext(self, ctx):
		"""Spout out some contextual brilliance."""
		msg = await self.getTitle('https://www.reddit.com/r/evenwithcontext/top.json?sort=top&t=week&limit=100')
		await ctx.send(Nullify.escape_all(msg,markdown=False))

	@commands.command(pass_context=True)
	async def question(self, ctx):
		"""Spout out some interstellar questioning... ?"""
		infoDict = await self.getTitle('https://www.reddit.com/r/NoStupidQuestions/top.json?sort=top&t=week&limit=100', True)
		self.settings.setServerStat(ctx.guild, "LastAnswer", infoDict["url"])
		msg = '{}'.format(infoDict["title"])
		await ctx.send(Nullify.escape_all(msg,markdown=False))
		
	@commands.command(pass_context=True)
	async def answer(self, ctx):
		"""Spout out some interstellar answering... ?"""
		answer = self.settings.getServerStat(ctx.guild, "LastAnswer")
		msg = "You need to ask a `{}question` first!".format(ctx.prefix) if not answer else "{}".format(answer)
		await ctx.send(Nullify.escape_all(msg,markdown=False))

	@commands.command(pass_context=True)
	async def redditimage(self, ctx, subreddit = None):
		"""Try to grab an image from an image-based subreddit."""
		if not self.canDisplay(ctx.guild): return
		if not subreddit: return await ctx.send("You need to pass a subreddit name.")
		# Grab our image title and url
		infoDict = await self.getInfo('https://www.reddit.com/r/' + subreddit + '/top.json?sort=top&t=week&limit=100')
		if not infoDict: return await ctx.send("Whoops! I couldn't find a working link.")
		# Check for nsfw - and for now, only allow admins/botadmins to post those
		if infoDict['over_18']:
			# NSFW - check admin
			if not await Utils.is_bot_admin_reply(ctx,message="You do not have sufficient privileges to access nsfw subreddits."): return
		await Message.Embed(title=infoDict["title"], url="https://www.reddit.com"+infoDict["permalink"], image=infoDict["url"], color=ctx.author).send(ctx)

	async def _image_do(self, ctx, url):
		if not self.canDisplay(ctx.guild): return
		# Grab our image title and url
		infoDict = await self.getInfo(url)
		if not infoDict: return await ctx.send("Whoops! I couldn't find a working link.")
		return await Message.Embed(
			title=infoDict["title"], 
			url="https://www.reddit.com"+infoDict["permalink"], 
			image=infoDict["url"], 
			color=ctx.author,
			footer="Score: {:,} | Comments: {:,}".format(
				infoDict["score"],
				infoDict["num_comments"]
			)).send(ctx)

	@commands.command(pass_context=True)
	async def beeple(self, ctx):
		"""A new image every day... for years."""
		await self._image_do(ctx, 'https://www.reddit.com/r/beeple/new.json?limit=100')
	
	@commands.command(pass_context=True)
	async def macsetup(self, ctx):
		"""Feast your eyes upon these setups."""
		await self._image_do(ctx, 'https://www.reddit.com/r/macsetups/top.json?sort=top&t=week&limit=100')	
		
	@commands.command(pass_context=True)
	async def pun(self, ctx):
		"""I don't know, don't ask..."""
		await self._image_do(ctx, 'https://www.reddit.com/r/puns/top.json?sort=top&t=week&limit=100')
	
	@commands.command(pass_context=True)
	async def carmod(self, ctx):
		"""Marvels of modern engineering."""
		await self._image_do(ctx, 'https://www.reddit.com/r/Shitty_Car_Mods/top.json?sort=top&t=week&limit=100')
	
	@commands.command(pass_context=True)
	async def battlestation(self, ctx):
		"""Let's look at some pretty stuff."""
		await self._image_do(ctx, 'https://www.reddit.com/r/battlestations/top.json?sort=top&t=week&limit=100')
		
	@commands.command(pass_context=True)
	async def shittybattlestation(self, ctx):
		"""Let's look at some shitty stuff."""
		await self._image_do(ctx, 'https://www.reddit.com/r/shittybattlestations/top.json?sort=top&t=week&limit=100')

	@commands.command(pass_context=True)
	async def dankmeme(self, ctx):
		"""Only the dankest."""
		await self._image_do(ctx, 'https://www.reddit.com/r/dankmemes/top.json?sort=top&t=week&limit=100')

	@commands.command(pass_context=True)
	async def cablefail(self, ctx):
		"""Might as well be a noose..."""
		await self._image_do(ctx, 'https://www.reddit.com/r/cablefail/top.json?sort=top&t=week&limit=100')

	@commands.command(pass_context=True)
	async def techsupport(self, ctx):
		"""Tech support irl."""
		await self._image_do(ctx, 'https://www.reddit.com/r/techsupportgore/top.json?sort=top&t=week&limit=100')

	@commands.command(pass_context=True)
	async def software(self, ctx):
		"""I uh... I wrote it myself."""
		await self._image_do(ctx, 'https://www.reddit.com/r/softwaregore/top.json?sort=top&t=week&limit=100')

	@commands.command(pass_context=True)
	async def meirl(self, ctx):
		"""Me in real life."""
		await self._image_do(ctx, 'https://www.reddit.com/r/me_irl/top.json?sort=top&t=week&limit=100')

	@commands.command(pass_context=True)
	async def starterpack(self, ctx):
		"""Starterpacks."""
		await self._image_do(ctx, 'https://www.reddit.com/r/starterpacks/top.json?sort=top&t=week&limit=100')

	@commands.command(pass_context=True)
	async def earthporn(self, ctx):
		"""Earth is good."""
		await self._image_do(ctx, 'https://www.reddit.com/r/EarthPorn/top.json?sort=top&t=week&limit=100')
		
	@commands.command(pass_context=True)
	async def wallpaper(self, ctx):
		"""Get something pretty to look at."""
		await self._image_do(ctx, 'https://www.reddit.com/r/wallpapers/top.json?sort=top&t=week&limit=100')
		
	@commands.command(pass_context=True)
	async def abandoned(self, ctx):
		"""Get something abandoned to look at."""
		await self._image_do(ctx, 'https://www.reddit.com/r/abandonedporn/top.json?sort=top&t=week&limit=100')

	@commands.command(pass_context=True)
	async def dragon(self, ctx):
		"""From the past - when great winged beasts soared the skies."""
		await self._image_do(ctx, 'https://www.reddit.com/r/BeardedDragons/top.json?sort=top&t=week&limit=100')

	@commands.command(pass_context=True)
	async def aww(self, ctx):
		"""Whenever you're down - uppify."""
		await self._image_do(ctx, 'https://www.reddit.com/r/aww/top.json?sort=top&t=week&limit=100')
	
	@commands.command(pass_context=True)
	async def randomdog(self, ctx):
		"""Bark if you know whassup."""
		await self._image_do(ctx, 'https://www.reddit.com/r/dogpictures/top.json?sort=top&t=week&limit=100')
		
	@commands.command(pass_context=True)
	async def randomcat(self, ctx):
		"""Meow."""
		await self._image_do(ctx, 'https://www.reddit.com/r/cats/top.json?sort=top&t=week&limit=100')
