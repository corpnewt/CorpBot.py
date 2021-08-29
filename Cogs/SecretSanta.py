import discord, random, re, json, os, tempfile, shutil
from   discord.ext import commands
from   Cogs import Utils, DisplayName, DL

def setup(bot):
	# Add the bot
	settings = bot.get_cog("Settings")
	bot.add_cog(SecretSanta(bot,settings))

class SecretSanta(commands.Cog):

	# Init with the bot reference, and a reference to the settings var
	def __init__(self, bot, settings):
		self.bot = bot
		self.settings = settings
		global Utils, DisplayName
		Utils = self.bot.get_cog("Utils")
		DisplayName = self.bot.get_cog("DisplayName")
		self.regexUserName = re.compile(r"\[\[user\]\]", re.IGNORECASE)
		self.regexUserPing = re.compile(r"\[\[atuser\]\]", re.IGNORECASE)
		self.regexServer   = re.compile(r"\[\[server\]\]", re.IGNORECASE)
		""" Setting names used:
			SSAllowed     = a boolean denoting whether this server has been allowed to use the SS module (owner only)
			SSRole        = the id of the current SS role
			SSMessage     = the raw SS message - defaults to:
							[[atuser]], here is your private Secret Santa bio channel.  Only you and admins can see it.  
							You can use it to write up some helpful info for whoever draws your name.
		"""

	async def download(self, url):
		url = url.strip("<>")
		# Set up a temp directory
		dirpath = tempfile.mkdtemp()
		tempFileName = url.rsplit('/', 1)[-1]
		# Strip question mark
		tempFileName = tempFileName.split('?')[0]
		filePath = dirpath + "/" + tempFileName
		rImage = None
		try:
			rImage = await DL.async_dl(url)
		except:
			pass
		if not rImage:
			self.remove(dirpath)
			return None
		with open(filePath, 'wb') as f:
			f.write(rImage)
		# Check if the file exists
		if not os.path.exists(filePath):
			self.remove(dirpath)
			return None
		return filePath
		
	def remove(self, path):
		if not path == None and os.path.exists(path):
			shutil.rmtree(os.path.dirname(path), ignore_errors=True)

	async def _channel_message(self, ctx, member, allow_mentions=False):
		# Sends the welcome message when a new Secret Santa channel is created for a user
		message = self.settings.getServerStat(ctx.guild, "SSMessage")
		if message == None:
			return None
		# Let's regex and replace [[user]] [[atuser]] and [[server]]
		message = re.sub(self.regexUserName, "{}".format(DisplayName.name(member)), message)
		message = re.sub(self.regexUserPing, "{}".format(member.mention), message)
		message = re.sub(self.regexServer,   "{}".format(ctx.guild.name), message)
		am = discord.AllowedMentions.all() if allow_mentions else discord.AllowedMentions.none()
		return await ctx.send(message,allowed_mentions=am)

	@commands.command()
	async def setssrole(self, ctx, *, role = None):
		"""Sets the Secret Santa role, or clears it if no role passed (bot-admin only)."""
		if not self.settings.getServerStat(ctx.guild,"SSAllowed",False):
			return await ctx.send("The Secret Santa module has not been allowed on this server.\nOne of my owners can enable it with `{}allowss yes`.".format(ctx.prefix))
		# Check if we're suppressing @here and @everyone mentions
		# Verify perms - bot-admin
		if not await Utils.is_bot_admin_reply(ctx): return
		if role == None:
			self.settings.setServerStat(ctx.guild, "SSRole", "")
			msg = 'Secret Santa role has been *removed*.'
			return await ctx.send(msg)
		if type(role) is str:
			if role == "everyone":
				role = "@everyone"
			roleName = role
			role = DisplayName.roleForName(roleName, ctx.guild)
			if not role:
				msg = 'I couldn\'t find *{}*...'.format(roleName)
				return await ctx.send(Utils.suppressed(ctx,msg))
		# If we made it this far - then we can add it
		self.settings.setServerStat(ctx.guild, "SSRole", role.id)
		msg = 'Secret Santa role has been set to **{}**.'.format(role.name)
		return await ctx.send(Utils.suppressed(ctx,msg))

	@commands.command()
	async def getssrole(self, ctx):
		"""Lists the current Secret Santa role."""
		if not self.settings.getServerStat(ctx.guild,"SSAllowed",False):
			return await ctx.send("The Secret Santa module has not been allowed on this server.\nOne of my owners can enable it with `{}allowss yes`.".format(ctx.prefix))
		# Check if we're suppressing @here and @everyone mentions
		# See if we have the setting set at all
		role = self.settings.getServerStat(ctx.guild,"SSRole","")
		if role in [None,""]:
			return await ctx.send("There is no Secret Santa role set. You can set it with the `{}setssrole [role]` command.".format(ctx.prefix))
		# Role is set - let's get its name
		vowels = "aeiou"
		arole = next((x for x in ctx.guild.roles if str(x.id) == str(role)),None)
		if not arole:
			return await ctx.send("There is no role that matches id: `{}`. You can change this with the `{}setssrole [role]` command.".format(role,ctx.prefix))
		if arole.name[:1].lower() in vowels:
			msg = 'You need to be an **{}** to participate in Secret Santa.'.format(arole.name)
		else:
			msg = 'You need to be a **{}** to participate in Secret Santa.'.format(arole.name)
		return await ctx.send(Utils.suppressed(ctx,msg))

	@commands.command()
	async def sscreatechannels(self, ctx, *, category = None):
		"""Creates the private channels for all users with the Secret Santa role under the supplied category (bot-admin only)."""
		if not self.settings.getServerStat(ctx.guild,"SSAllowed",False):
			return await ctx.send("The Secret Santa module has not been allowed on this server.\nOne of my owners can enable it with `{}allowss yes`.".format(ctx.prefix))
		if not await Utils.is_bot_admin_reply(ctx): return
		# Check if our category exists - if not, create it
		if not category:
			return await ctx.send('You must supply a category for the Secret Santa channels.')
		category_name = category # Save for later
		category = DisplayName.channelForName(category_name,ctx.guild,"category")
		if not category:
			# Create it
			category = await ctx.guild.create_category_channel(category_name)
		# Make sure we even have a role setup and that it's valid
		role = self.settings.getServerStat(ctx.guild,"SSRole","")
		if role in [None,""]:
			return await ctx.send("There is no Secret Santa role set. You can set it with the `{}setssrole [role]` command.".format(ctx.prefix))
		# Verify it corresponds to a real role
		arole = next((x for x in ctx.guild.roles if str(x.id) == str(role)),None)
		if not arole:
			return await ctx.send("There is no role that matches id: `{}`. You can change this with the `{}setssrole [role]` command.".format(role,ctx.prefix))
		# We have a clean slate - let's get a list of non-bot users with the SSRole
		participants = [x for x in ctx.guild.members if not x.bot and arole in x.roles]
		# Verify we have a minimum of 3 participants - otherwise we can't randomize
		if len(participants) < 3:
			# No one has the role, it seems.
			msg = "Not enough users are participating in the Secret Santa drawing - 3 or more need the **{}** role to participate.".format(arole.name)
			return await ctx.send(Utils.suppressed(ctx,msg))
		m = await ctx.send("Iterating and adding Secret Santa channels...")
		# We now have a clean slate, valid role, and enough particpiants - let's create the channels
		channels = 0
		for x in participants:
			# Create a channel with the user's id as the name
			overwrites = {
				ctx.guild.default_role: discord.PermissionOverwrite(read_messages=False),
				x: discord.PermissionOverwrite(read_messages=True)
			}
			channel = await ctx.guild.create_text_channel(str(x.id), overwrites=overwrites, category=category)
			channels += 1
			await self._channel_message(channel,x,allow_mentions=True)
		await m.edit(content="Created {} Secret Santa channel{}!".format(channels,"" if channels == 1 else "s"))

	@commands.command()
	async def ssremovechannels(self, ctx, *, category = None):
		"""Removes all Secret Santa channels under a given category whose names correspond to active user's id (bot-admin only)."""
		if not self.settings.getServerStat(ctx.guild,"SSAllowed",False):
			return await ctx.send("The Secret Santa module has not been allowed on this server.\nOne of my owners can enable it with `{}allowss yes`.".format(ctx.prefix))
		if not await Utils.is_bot_admin_reply(ctx): return
		if not category:
			return await ctx.send('You must supply the category for the Secret Santa channels.')
		category = DisplayName.channelForName(category,ctx.guild,"category")
		if not category:
			return await ctx.send("I couldn't locate that category...")
		m = await ctx.send("Iterating and removing Secret Santa channels...")
		channels_total   = len(category.channels)
		channels_removed = 0
		channels_located = 0
		for x in category.text_channels:
			try:
				name = int(x.name)
			except:
				continue
			member = ctx.guild.get_member(name)
			if not member:
				# Channel name doesn't correspond with an existing member
				continue
			channels_located += 1
			# Remove the channel
			try:
				await x.delete(reason="Secret Santa channel removed per the ssremovechannels command.")
				channels_removed += 1
			except:
				continue
		# Remove the category channel if the removed and located channels were the same length
		cat_removed = False
		if channels_total == channels_removed:
			try:
				await category.delete(reason="Secret Santa channel removed per the ssremovechannels command.")
				cat_removed = True
			except:
				pass
		# Give some stats!
		msg = "Out of {} channel{}, {} {} resovled to user ids, {} {} removed.  The category was {} removed.".format(
			channels_total, "" if channels_total == 1 else "s",
			channels_located, "was" if channels_located == 1 else "were",
			channels_removed, "was" if channels_removed == 1 else "were",
			"also" if cat_removed else "not"
		)
		# List our stats
		await m.edit(content=msg)

	@commands.command()
	async def ssgenreport(self, ctx, *, category = None):
		"""Randomly pairs users for Secret Santa and uploads a ss.json report (bot-admin only)."""
		if not self.settings.getServerStat(ctx.guild,"SSAllowed",False):
			return await ctx.send("The Secret Santa module has not been allowed on this server.\nOne of my owners can enable it with `{}allowss yes`.".format(ctx.prefix))
		# We need to make sure that we have channels setup, they're all valid, and the correspond to existing users with
		# the SSRole
		if not await Utils.is_bot_admin_reply(ctx): return
		if not category:
			return await ctx.send('You must supply the category for the Secret Santa channels.')
		category = DisplayName.channelForName(category,ctx.guild,"category")
		if not category:
			return await ctx.send("I couldn't locate that category...")
		# Get our users by resolving the text channel names to user ids, then shuffle
		m = await ctx.send("Gathering and shuffling participants...")
		participants = []
		for x in category.text_channels:
			try:
				name = int(x.name)
			except:
				continue
			member = ctx.guild.get_member(name)
			if not member:
				# Channel name doesn't correspond with an existing member
				continue
			participants.append(member)
		if len(participants) < 3:
			await ctx.send("Not enough channels resolved to users for the Secret Santa drawing.  3 or more are required.")
			return
		# Shuffle the list, copy it, and rotate one to the right
		random.shuffle(participants)
		partners = participants[1:]
		partners.append(participants[0])
		results = {"category":{"name":category.name,"id":category.id},"swaps":[]}
		await m.edit(content="Organizing results...")
		for x in range(len(participants)):
			results["swaps"].append({
				"to_name"   : participants[x].name + "#" + participants[x].discriminator,
				"to_id"     : participants[x].id,
				"from_name" : partners[x].name + "#" + partners[x].discriminator,
				"from_id"   : partners[x].id
			})
		# results = dict(zip(participants,partners))
		await m.edit(content="Generating and uploading Secret_Santa_{}.json...".format(ctx.guild.id))
		# Save it as a json file and upload
		json.dump(results,open("Secret_Santa_{}.json".format(ctx.guild.id),"w"),indent=2)
		# Upload it
		await ctx.send(file=discord.File(fp="Secret_Santa_{}.json".format(ctx.guild.id), filename="Secret_Santa_{}.json".format(ctx.guild.id)))
		# Remove the file
		os.remove("Secret_Santa_{}.json".format(ctx.guild.id))
		# Remove the prior message
		await m.delete()

	@commands.command()
	async def ssapplyreport(self, ctx, *, url = None):
		"""Applies the passed ss.json file's settings and gives the Secret Santa channels to the target with read-only perms (bot-admin only).  Accepts a url - or picks the first attachment."""
		if not self.settings.getServerStat(ctx.guild,"SSAllowed",False):
			return await ctx.send("The Secret Santa module has not been allowed on this server.\nOne of my owners can enable it with `{}allowss yes`.".format(ctx.prefix))
		if not await Utils.is_bot_admin_reply(ctx): return
		if url == None and len(ctx.message.attachments) == 0:
			return await ctx.send("Usage: `{}ssapplyreport [url or attachment]`".format(ctx.prefix))
		if url == None:
			url = ctx.message.attachments[0].url
		message = await ctx.send("Downloading...")
		path = await self.download(url)
		if not path:
			return await message.edit(content="I guess I couldn't get that json document...  Make sure you're passing a valid url or attachment.")
		# Load the actual data
		await message.edit(content="Loading json data...")
		try:
			data = json.load(open(path))
		except Exception as e:
			return await message.edit(content="Incorrectly formatted json.\n{}".format(str(e)))
		# Verify it's a dict
		if not isinstance(data, dict) or not "category" in data or not "swaps" in data:
			return await message.edit(content="Incorrectly organized json data.")
		# Get our category from it
		if not data.get("category",{}).get("id",None):
			return await message.edit(content="Incorrectly organized json data.")
		category = None
		try:
			cat_id = int(data["category"]["id"])
		except:
			# Not an int - bail
			pass
		category = ctx.guild.get_channel(cat_id)
		if not category or not isinstance(category, discord.CategoryChannel):
			return await message.edit(content="Incorrectly organized json data.")
		swap_list = data["swaps"]
		# Build a list of all the needed data
		resolved = []
		for x in swap_list:
			# Resolve the to and from users - and get the channel
			try:
				to_user = ctx.guild.get_member(x["to_id"])
				from_user = ctx.guild.get_member(x["from_id"])
				channel = next((x for x in category.text_channels if x.name == str(to_user.id)),None)
			except:
				return await message.edit(content="There were errors merging the data.  Please review the report for errors.")
			if not all([to_user, from_user, channel]):
				return await message.edit(content="There were errors merging the data.  Please review the report for errors.")
			# Add them to the array
			resolved.append({"to":to_user,"from":from_user,"chan":channel})
		# Iterate through the resolved list and apply the changes
		await message.edit(content="Iterating and applying changes...")
		for swap in resolved:
			# Apply the overrides to allow the from_user to see the channel - but not change anything
			# will first remove to_user's ability to see the channel
			await swap["chan"].set_permissions(swap["to"], overwrite=None)
			await swap["chan"].set_permissions(swap["from"], read_messages=True, send_messages=False, add_reactions=False)
		await message.edit(content="Updated {} channel{}!".format(len(resolved),"" if len(resolved)==1 else "s"))

	@commands.command()
	async def ssrevert(self, ctx, *, category = None):
		"""Returns ownership of the Secret Santa channels to their original owners if found (bot-admin only)."""
		if not self.settings.getServerStat(ctx.guild,"SSAllowed",False):
			return await ctx.send("The Secret Santa module has not been allowed on this server.\nOne of my owners can enable it with `{}allowss yes`.".format(ctx.prefix))
		if not await Utils.is_bot_admin_reply(ctx): return
		# Check if our category exists - if not, create it
		if not category:
			return await ctx.send('You must supply a category for the Secret Santa channels.')
		category = DisplayName.channelForName(category,ctx.guild,"category")
		if not category:
			return await ctx.send("I couldn't locate that category...")
		m = await ctx.send("Iterating and removing Secret Santa channels...")
		channels_total    = len(category.channels)
		channels_reverted = 0
		channels_located  = 0
		for x in category.text_channels:
			try:
				name = int(x.name)
			except:
				# Not following our naming convention - ignore
				continue
			channels_located += 1
			overs = x.overwrites
			# Walk the overwrites and remove them all
			for over in overs:
				# Only adjust user overwrites
				if not isinstance(over,discord.Member):
					continue
				await x.set_permissions(over,overwrite=None)
			# Try to get our original member
			member = ctx.guild.get_member(name)
			if not member:
				# Channel name doesn't correspond with an existing member
				continue
			# We got a member - let's set their overwrites
			await x.set_permissions(member,read_messages=True)
			channels_reverted += 1
		# Give some stats!
		msg = "Out of {} channel{}, {} {} resovled to user ids, {} {} reverted.".format(
			channels_total, "" if channels_total == 1 else "s",
			channels_located, "was" if channels_located == 1 else "were",
			channels_reverted, "was" if channels_reverted == 1 else "were"
		)
		# List our stats
		await m.edit(content=msg)

	@commands.command()
	async def setssmessage(self, ctx, *, message = None):
		"""Sets the Secret Santa channel create message (bot-admin only). 
		Available Options:
		
		[[user]]   = user name
		[[atuser]] = user mention
		[[server]] = server name"""
		if not self.settings.getServerStat(ctx.guild,"SSAllowed",False):
			return await ctx.send("The Secret Santa module has not been allowed on this server.\nOne of my owners can enable it with `{}allowss yes`.".format(ctx.prefix))
		if not await Utils.is_bot_admin_reply(ctx): return
		if message == None:
			self.settings.setServerStat(ctx.guild, "SSMessage", None)
			return await ctx.send('Secret Santa channel create message removed!')
		self.settings.setServerStat(ctx.guild, "SSMessage", message)
		await ctx.send('Secret Santa channel create message updated!\n\nHere\'s a preview:')
		await self._channel_message(ctx,ctx.author)

	@commands.command()
	async def rawssmessage(self, ctx):
		"""Prints the raw markdown for the Secret Santa channel create message (bot-admin only)."""
		if not self.settings.getServerStat(ctx.guild,"SSAllowed",False):
			return await ctx.send("The Secret Santa module has not been allowed on this server.\nOne of my owners can enable it with `{}allowss yes`.".format(ctx.prefix))
		if not await Utils.is_bot_admin_reply(ctx): return
		message = self.settings.getServerStat(ctx.guild, "SSMessage", None)
		if message in [None,""]:
			return await ctx.send('Secret Santa channel create message not setup.  You can do so with the `{}setssmessage [message]` command.'.format(ctx.prefix))
		# Escape the markdown
		message = discord.utils.escape_markdown(message)
		await ctx.send(message)

	@commands.command()
	async def testssmessage(self, ctx):
		"""Prints the current Secret Santa channel create message (bot-admin only)."""
		if not self.settings.getServerStat(ctx.guild,"SSAllowed",False):
			return await ctx.send("The Secret Santa module has not been allowed on this server.\nOne of my owners can enable it with `{}allowss yes`.".format(ctx.prefix))
		if not await Utils.is_bot_admin_reply(ctx): return
		message = self.settings.getServerStat(ctx.guild, "SSMessage", None)
		if message in [None,""]:
			return await ctx.send('Secret Santa channel create message not setup.  You can do so with the `{}setssmessage [message]` command.'.format(ctx.prefix))
		await self._channel_message(ctx,ctx.author)

	@commands.command()
	async def allowss(self, ctx, *, yes_no = None):
		"""Sets whether the Secret Santa module is enabled (owner only; always off by default)."""
		if not await Utils.is_owner_reply(ctx): return
		await ctx.send(Utils.yes_no_setting(ctx,"Secret Santa","SSAllowed",yes_no))