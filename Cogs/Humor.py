import discord, random, time, os, PIL, textwrap
from discord.ext import commands
from urllib.parse import quote
from PIL import Image, ImageDraw, ImageFont, ImageEnhance
from Cogs import Message, FuzzySearch, GetImage, Utils, DL, DisplayName, PickList

def setup(bot):
	# Add the bot and deps
	settings = bot.get_cog("Settings")
	bot.add_cog(Humor(bot, settings))

# This module is for random funny things I guess...

class Humor(commands.Cog):

	def __init__(self, bot, settings, listName = "Adjectives.txt"):
		self.bot = bot
		global Utils, DisplayName
		Utils = self.bot.get_cog("Utils")
		DisplayName = self.bot.get_cog("DisplayName")
		self.settings = settings
		# Setup our adjective list
		self.adj = []
		marks = map(chr, range(768, 879))
		self.marks = list(marks)
		if os.path.exists(listName):
			with open(listName) as f:
				for line in f:
					self.adj.append(line)
		try: self.image = Image.open('images/dosomething.png')
		except: self.image = Image.new("RGBA",(500,500),(0,0,0,0))
		try: self.s_image = Image.open("images/Stardew.png")
		except: self.s_image = Image.new("RGBA",(319,111),(0,0,0,0))
		try: self.slap_image = Image.open("images/slap.png")
		except: self.slap_image = Image.new("RGBA",(800,600),(0,0,0,0))
		self.slap_words = ("walloped","slapped","demolished","obliterated","bonked","smacked")
		self.stardew_gifts = (
			"prismatic shard",
			"seaweed",
			"green algae",
			"diamond",
			"red mushrooms",
			"wool",
			"coal",
			"duck feather",
			"cave carrot",
			"solar essence",
			"vinegar",
			"sweet gem berry",
			"truffle",
			"fish",
			"snail",
			"frozen tear",
			"chicken statue",
			"bone flute",
			"pufferfish",
			"Joja Cola",
			"trash",
			"egg",
			"crispy bass",
			"fish taco",
			"cookie",
			"garlic",
			"weeds",
			"honey",
			"gizmo",
			"cloth",
			"geode"
		)
		self.stardew_responses = (
			"I'm just here for my annual check-up! Don't worry, I'm not preg... I mean, I'm not sick! Heh.",
			"...I hate this.",
			"Buh... Life.",
			"You wish to date me? After how I treated you at first?",
			"What do you want? Leave me alone.",
			"You!!! Was that some kind of sick prank?! Those are very private!",
			"Did you know that my nephew loves 'Beer'? I gave it to him one year and he wouldn't stop talking about it.",
			"Ugh... that's such a stupid gift.",
			"Don't you have work to do?",
			"I'm just here for the free coffee.",
			"I'll be honest. I don't want to dance with you",
			"Me?... Oh, I'm thankful for... how about I just show you when we get home tonight?",
			"Thanks!",
			"Oh, is it my birthday today? I guess it is. Thanks. This is nice.",
			"I wanted to talk to you in private...",
			"Ew... No.",
			"Sometimes I stop and realize that I'm nothing more than a bag of juicy, squishy flesh.",
			"Ah... an Fish Taco! Thanks.",
			"No u.",
			"Thanks... I hate it.",
			"I really should scrub my floorboards today. I think an algae is starting to form.",
			"That was some way to ring in the new year last night...",
			"You scared me, sneaking into my room like that!",
			"So there you have it. You probably figured I hated this chair.",
			"This... Are you trying to hurt me even more?",
			"I thought we had something special... I guess I was wrong.",
			"This... They gave this to me in Gotoro prison camp. I've been trying to forget about that. *shudder*",
			"If I stay perfectly still, perhaps a resplendent butterfly will bless my nose with a landing.",
			"My basket! Thank you. This means a lot to me.",
			"But... You don't need to try and 'help' me... I know best how to live my own life... okay?",
			"This is a great gift. Thank you!",
			"Oh, a birthday gift! Thank you.",
			"All my customers... Here?!?",
			"Grr... sounds like these raccoons are back again. Filthy varmints...",
			"Sometimes I look for crawdads in the river. Don't tell Aunt Marnie... but I fed one to a cow once."
		)
					
	@commands.command()
	async def zalgo(self, ctx, *, message = None):
		"""Ỉ s̰hͨo̹u̳lͪd͆ r͈͍e͓̬a͓͜lͨ̈l̘̇y̡͟ h͚͆a̵͢v͐͑eͦ̓ i͋̍̕n̵̰ͤs͖̟̟t͔ͤ̉ǎ͓͐ḻ̪ͨl̦͒̂ḙ͕͉d͏̖̏ ṡ̢ͬö̹͗m̬͔̌e̵̤͕ a̸̫͓͗n̹ͥ̓͋t̴͍͊̍i̝̿̾̕v̪̈̈͜i̷̞̋̄r̦̅́͡u͓̎̀̿s̖̜̉͌..."""
		if message is None: return await ctx.send("Usage: `{}zalgo [message]`".format(ctx.prefix))		
		words = message.split()
		try:
			iterations = int(words[len(words)-1])
			words = words[:-1]
		except Exception:
			iterations = 1

		iterations = 100 if iterations > 100 else 1 if iterations < 1 else iterations
			
		zalgo = " ".join(words)
		for i in range(iterations):
			if len(zalgo) > 2000:
				break
			zalgo = self._zalgo(zalgo)
		
		zalgo = zalgo[:2000]

		zalgo = Utils.suppressed(ctx,zalgo)
		await Message.Message(message=zalgo).send(ctx)
		
	def _zalgo(self, text):
		words = text.split()
		zalgo = ' '.join(''.join(c + ''.join(random.choice(self.marks)
				for _ in range(i // 2 + 1)) * c.isalnum()
				for c in word)
				for i, word in enumerate(words))
		return zalgo

	@commands.command()
	async def holy(self, ctx, *, subject : str = None):
		"""Time to backup the Batman!"""
		
		if subject is None: return await ctx.send("Usage: `{}holy [subject]`".format(ctx.prefix))

		matchList = [a for a in self.adj if a[0].lower() == subject[0].lower()]
		word = random.choice(matchList if len(matchList) else self.adj)
		word = word.strip().capitalize()
		subject = subject.strip().capitalize()
		msg = "*Holy {} {}, Batman!*".format(word, subject)
		
		msg = Utils.suppressed(ctx,msg)
		await ctx.send(msg)
		
	@commands.command()
	async def fart(self, ctx):
		"""PrincessZoey :P"""
		fartList = ["Poot", "Prrrrt", "Thhbbthbbbthhh", "Plllleerrrrffff", "Toot", "Blaaaaahnk", "Squerk"]
		await ctx.send(random.choice(fartList))
		
	@commands.command()
	async def french(self, ctx):
		"""Speaking French... probably..."""
		fr_list = [ "hon", "fromage", "baguette" ]
		punct   = [ ".", "!", "?", "...", "!!!", "?!" ]
		fr_sentence = [random.choice(fr_list) for i in range(random.randint(3,20))]
		# Capitalize the first letter of the first word
		fr_sentence[0] = fr_sentence[0].capitalize()
		totally_french = " ".join(fr_sentence) + random.choice(punct)
		await ctx.send(totally_french)

	@commands.command()
	async def german(self, ctx):
		"""Speaking German... probably..."""
		de_list = [ "BIER", "sauerkraut", "auto", "weißwurst", "KRANKENWAGEN" ]
		punct   = [ ".", "!", "?", "...", "!!!", "?!" ]
		de_sentence = [random.choice(de_list) for i in range(random.randint(3,20))]
		if random.randint(0,1):
			# Toss "rindfleischetikettierungsüberwachungsaufgabenübertragungsgesetz" in there somewhere
			de_sentence[random.randint(0,len(de_sentence)-1)] = "rindfleischetikettierungsüberwachungsaufgabenübertragungsgesetz"
		# Capitalize the first letter of the first word
		de_sentence[0] = de_sentence[0].capitalize()
		totally_german = " ".join(de_sentence) + random.choice(punct)
		await ctx.send(totally_german)

	def canDisplay(self, server):
		# Check if we can display images
		lastTime = int(self.settings.getServerStat(server, "LastPicture", 0))
		threshold = int(self.settings.getServerStat(server, "PictureThreshold", 0))
		if not GetImage.canDisplay( lastTime, threshold ):
			# await self.bot.send_message(channel, 'Too many images at once - please wait a few seconds.')
			return False
		
		# If we made it here - set the LastPicture method
		self.settings.setServerStat(server, "LastPicture", int(time.time()))
		return True

	@commands.command()
	async def memetemps(self, ctx):
		"""Get Meme Templates"""
		url = "https://api.imgflip.com/get_memes"
		result_json = await DL.async_json(url)
		templates = result_json["data"]["memes"]		
		fields = []
		for template in templates:
			fields.append({ "name" : template["name"], "value" : "`{}` [Link]({})".format(template["id"],"https://imgflip.com/memegenerator/{}".format(template["id"])) })
		await PickList.PagePicker(title="Meme Templates",color=ctx.author,list=fields,ctx=ctx).pick()

	async def _get_meme(self,chosenTemp,box_text):
		url = "https://api.imgflip.com/caption_image"
		payload = {'template_id': chosenTemp["id"], 'username':'CorpBot', 'password': 'pooter123'}
		# Add the text to the payload
		for i,x in enumerate(box_text[:chosenTemp["box_count"]]):
			payload["boxes[{}][text]".format(i)] = x.upper()
		result_json = await DL.async_post_json(url, payload)
		return result_json["data"]["url"]

	async def _get_id_name_from_url(self,url):
		html = await DL.async_text(url)
		meme_id   = html.split("<p>Template ID: ")[1].split("<")[0]
		meme_name = html.split('<h1 id="mtm-title">')[1].split("<")[0]
		for x in (" Template"," Meme"):
			if meme_name.endswith(x):
				meme_name = meme_name[:-len(x)]
		return (meme_id,meme_name)

	@commands.command()
	async def meme(self, ctx, template_id = None, *box_text):
		"""Generate Memes!  You can get a list of meme templates with the memetemps command.  If any fields have spaces, they must be enclosed in quotes."""

		if not self.canDisplay(ctx.message.guild): return

		if template_id is None or not len(box_text):
			msg = "Usage: `{}meme [template_id] [text#1] [text#2]`\n\n Meme Templates can be found using `$memetemps`".format(ctx.prefix)
			return await ctx.send(msg)

		message = await Message.Embed(
			title="Preparing to meme...",
			color=ctx.author,
			footer="Powered by imgflip.com"
		).send(ctx)

		templates = await self.getTemps()
		# Check if the template_id is a valid int, and try to load that one
		try:
			template_id = str(int(template_id))
			chosenTemp = next((x for x in templates if x["id"] == template_id),{"id":template_id,"name":template_id,"box_count":len(box_text)})
			if chosenTemp["name"] == chosenTemp["id"]:
				# Try to resolve the name
				try:
					_,chosenTemp["name"] = await self._get_id_name_from_url(
						"https://imgflip.com/memetemplate/{}".format(chosenTemp["id"])
					)
				except:
					pass
		except:
			# Try to use imgflip's search
			try:
				search_html = await DL.async_text("https://imgflip.com/memesearch?q={}".format(quote(template_id)))
				closest_meme_template = "https://imgflip.com/memetemplate/{}".format(
					search_html.split('<h3 class="mt-title">')[1].strip().split("\n")[0].split('href="/meme/')[1].split('"')[0]
				)
				# Load the template HTML and scrape the info
				meme_id,meme_name = await self._get_id_name_from_url(closest_meme_template)
				chosenTemp = {"id":meme_id,"name":meme_name,"box_count":len(box_text)}
			except:
				# Fuzzy match by name
				chosenTemp = FuzzySearch.search(template_id, templates,"name",1)[0]["Item"]
		# Actually get the meme
		try: result = await self._get_meme(chosenTemp,box_text)
		except: return await Message.Embed(title="Something went wrong :(").edit(ctx,message)
		
		await Message.Embed(
			url=result,
			title=" - ".join([x for x in box_text[:chosenTemp["box_count"]] if x != " "]),
			image=result,
			footer='Powered by imgflip.com - using template id {}{}'.format(chosenTemp["id"],": "+chosenTemp["name"] if chosenTemp["name"]!=chosenTemp["id"] else "")
		).edit(ctx,message)

	async def getTemps(self):
		url = "https://api.imgflip.com/get_memes"
		result_json = await DL.async_json(url)
		templates = result_json["data"]["memes"]
		if templates:
			return templates
		return None

	@commands.command()
	async def poke(self, ctx, *, url = None):
		"""Pokes the passed url/user/uploaded image."""

		if not self.canDisplay(ctx.guild):
			return
		if url is None and len(ctx.message.attachments) == 0:
			return await ctx.send("Usage: `{}poke [url, user, or attachment]`".format(ctx.prefix))
		if url is None:
			url = ctx.message.attachments[0].url
		# Let's check if the "url" is actually a user
		test_user = DisplayName.memberForName(url, ctx.guild)
		if test_user:
			# Got a user!
			url = Utils.get_avatar(test_user)
		image = self.image.copy()
		message = await ctx.send("Preparing to poke...")
		path = await GetImage.download(url)
		if not path:
			return await message.edit(content="I guess I couldn't poke that...  Make sure you're passing a valid url, user, or attachment.")
		# We should have the image - let's open it and convert to a single frame
		try:
			img = Image.open(path)
			img = img.convert('RGBA')
			# Let's ensure it's the right size, and place it in the right spot
			t_max   = int(image.width*.38)
			t_ratio = min(t_max/img.width,t_max/img.height)
			t_w = int(img.width*t_ratio)
			t_h = int(img.height*t_ratio)
			img = img.resize((t_w,t_h),resample=PIL.Image.LANCZOS)
			# Paste our other image on top
			image.paste(img,(int(image.width*.6),int(image.height*.98)-t_h),mask=img)
			image.save('images/dosomethingnow.png')
			await ctx.send(file=discord.File(fp='images/dosomethingnow.png'))
			await message.delete()
			os.remove('images/dosomethingnow.png')
		except Exception as e:
			print(e)
			pass
		if os.path.exists(path):
			GetImage.remove(path)

	@commands.command()
	async def fry(self, ctx, *, url = None):
		"""Fry up some memes."""

		if not self.canDisplay(ctx.guild): return
		if url is None and len(ctx.message.attachments) == 0:
			return await ctx.send("Usage: `{}fry [url, user, or attachment]`".format(ctx.prefix))
		if url is None: url = ctx.message.attachments[0].url
		# Let's check if the "url" is actually a user
		test_user = DisplayName.memberForName(url, ctx.guild)
		if test_user:
			# Got a user!
			url = Utils.get_avatar(test_user)
		message = await ctx.send("Preparing to fry...")
		path = await GetImage.download(url)
		if not path:
			return await message.edit(content="I guess I couldn't fry that...  Make sure you're passing a valid url, user, or attachment.")
		# We should have the image - let's open it and convert to a single frame
		try:
			# Credit for the frying goes to Flame442
			img = Image.open(path).convert("RGBA")
			e = ImageEnhance.Sharpness(img)
			img = e.enhance(100)
			e = ImageEnhance.Contrast(img)
			img = e.enhance(100)
			e = ImageEnhance.Brightness(img)
			img = e.enhance(.27)
			r, b, g, a = img.split()
			e = ImageEnhance.Brightness(r)
			r = e.enhance(4)
			e = ImageEnhance.Brightness(g)
			g = e.enhance(1.75)
			e = ImageEnhance.Brightness(b)
			b = e.enhance(.6)
			img = Image.merge('RGBA', (r, g, b, a))
			e = ImageEnhance.Brightness(img)
			img = e.enhance(1.5)
			img.save('images/fried.png')
			await ctx.send(file=discord.File(fp='images/fried.png'))
			await message.delete()
			os.remove('images/fried.png')
		except Exception as e:
			print(e)
			pass
		if os.path.exists(path):
			GetImage.remove(path)

	@commands.command()
	async def stardew(self, ctx, *, user = None):
		"""Test your luck with another user."""

		# Set some defaults
		name_max_w = 88
		name_max_h = 12
		if not self.canDisplay(ctx.guild):
			return
		# Let's check if the "url" is actually a user
		test_user = DisplayName.memberForName(user, ctx.guild)
		if not test_user:
			return await ctx.send("Usage: `{}stardew [user]`".format(ctx.prefix))
		# Got a user!
		user = Utils.get_avatar(test_user)
		# User profile pic needs to be formatted to 64x65 pixels - and the top left corner is at
		# (221,15)
		image = self.s_image.copy()
		if not image.width == 319 or not image.height == 111:
			image = image.resize((319,111),resample=PIL.Image.LANCZOS)
		item = random.choice(self.stardew_gifts)
		message = await ctx.send("Gifting *{}* to {}...".format(item,DisplayName.name(test_user)))
		path = await GetImage.download(user)
		if not path:
			return await message.edit(content="I guess I couldn't gift that...  Make sure you're passing a valid user.")
		# We should have the image - let's open it and convert to a single frame
		try:
			img = Image.open(path)
			img = img.convert('RGBA')
			# Let's ensure it's the right size, and place it in the right spot
			img = img.resize((64,65))
			# Paste our other image on top
			image.paste(img,(221,15),mask=img)
			# Write the user's name in the name box - starts at (209,99)
			d = ImageDraw.Draw(image)
			name_text = test_user.display_name
			name_size = name_max_h # max size for the name to fit
			l,t,r,b = d.textbbox((0,0),name_text,font=ImageFont.truetype("fonts/stardew.ttf",name_size))
			t_w,t_h = r-l,b-t
			# 210 starting x, 88 max w
			t_w = d.textlength(name_text,font=ImageFont.truetype("fonts/stardew.ttf",name_size))
			if t_w > name_max_w:
				name_size = int(t_h*(name_max_w/t_w)+2)
				l,t,r,b = d.textbbox((0,0),name_text,font=ImageFont.truetype("fonts/stardew.ttf",name_size))
				t_w,t_h = r-l,b-t
				t_w = d.textlength(name_text,font=ImageFont.truetype("fonts/stardew.ttf",name_size))
			d.text((209+(88-t_w)/2,88+(12-t_h)/2),test_user.display_name,font=ImageFont.truetype("fonts/stardew.ttf",name_size),fill=(86,22,12))
			# Get the response - origin is (10,10), each row height is 14
			rows = textwrap.wrap(
				random.choice(self.stardew_responses),
				30,
				break_long_words=True,
				replace_whitespace=False
				)
			for index,row in enumerate(rows[:6]):
				d.text((11+2,10+14*index),row,font=ImageFont.truetype("fonts/stardew.ttf",15),fill=(86,22,12))
			# Resize to triple and save
			image = image.resize((319*3,111*3),PIL.Image.NEAREST)
			image.save('images/Stardewnow.png')
			await ctx.send(file=discord.File(fp='images/Stardewnow.png'))
			# await message.delete(delay=2)
			await message.edit(content="Gifted *{}* to {}.".format(item,DisplayName.name(test_user)))
			os.remove('images/Stardewnow.png')
		except Exception as e:
			print(e)
			return await message.edit(content="I guess I couldn't draw that image :(")
		finally:
			if os.path.exists(path):
				GetImage.remove(path)

	@commands.command()
	async def slap(self, ctx, *, user = None):
		"""It's easier than talking... probably?"""

		if not self.canDisplay(ctx.guild):
			return
		# Let's check if the "url" is actually a user
		test_user = DisplayName.memberForName(user, ctx.guild)
		if not test_user:
			return await ctx.send("Usage: `{}slap [user]`".format(ctx.prefix))
		# Got a user!
		user = Utils.get_avatar(ctx.author)
		targ = Utils.get_avatar(test_user)
		image = self.slap_image.copy()
		# The slapper's image will be 300x300, the slaped user's image will be 350x350
		# The top left corner of the slapper is at (487, 17)
		# The top left of the slapped user is at (167, 124)
		if not image.width == 800 or not image.height == 600:
			image = image.resize((800,600),resample=PIL.Image.LANCZOS)
		message = await Message.EmbedText(title="Winding up...",color=ctx.author).send(ctx)
		ouch_msg = "Ouch!  That wind-up hurt my arm...  Make sure you're passing a valid user."
		user_path = await GetImage.download(user)
		if not user_path: return await Message.EmbedText(title=ouch_msg,description="I couldn't get the slapper's avatar :(").edit(ctx,message)
		targ_path = await GetImage.download(targ)
		if not targ_path: return await Message.EmbedText(title=ouch_msg,description="I couldn't get the slapped user's avatar :(").edit(ctx,message)
		# We should have the images - let's open them and convert to a single frame
		try:
			# Gather the slapper image
			user_img = Image.open(user_path)
			user_img = user_img.convert('RGBA')
			# Let's ensure it's the right size, and place it in the right spot
			user_img = user_img.resize((300,300))
			# Paste our other image on top
			image.paste(user_img,(487,17),mask=user_img)
			# Get the slapped user image
			targ_img = Image.open(targ_path)
			targ_img = targ_img.convert('RGBA')
			# Let's ensure it's the right size, and place it in the right spot
			targ_img = targ_img.resize((350,350))
			# Paste our other image on top
			image.paste(targ_img,(167,124),mask=targ_img)
			image.save('images/slapnow.png')
			await Message.Embed(
				title="Looks like someone got {}!".format(random.choice(self.slap_words)),
				description="{} was {} by {}!".format(test_user.mention,random.choice(self.slap_words),ctx.author.mention),
				file="images/slapnow.png"
			).edit(ctx,message)
			os.remove('images/slapnow.png')
		except Exception as e:
			print(e)
			pass
		for path in (user_path,targ_path):
			if os.path.exists(path): GetImage.remove(path)
