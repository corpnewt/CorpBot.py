import discord, time
from   discord.ext import commands
from   Cogs import Utils, PCPP, DisplayName, Message, PickList

def setup(bot):
	# Add the bot and deps
	settings = bot.get_cog("Settings")
	bot.add_cog(Hw(bot, settings))

# This is the Uptime module. It keeps track of how long the bot's been up

class Hw(commands.Cog):

	# Init with the bot reference, and a reference to the settings var
	def __init__(self, bot, settings):
		self.bot = bot
		self.settings = settings
		self.hwactive = {}
		self.charset = "0123456789"
		self.wait_time = 300 # Wait 5 minutes for prompts
		global Utils, DisplayName
		Utils = self.bot.get_cog("Utils")
		DisplayName = self.bot.get_cog("DisplayName")

	def gen_id(self):
		# Just use the current time as that shouldn't ever be the same (unless a user
		# manages to do this twice in < 1 second)
		return str(time.time())

	def _get_comms(self, ctx, backticks=True):
		# Returns a formatted string of commands requiring the hardware channel
		ph = "`{}{}`" if backticks else "{}{}"
		hw_comms = ("newhw","edithw","renhw")
		return ", ".join([ph.format(ctx.prefix,x) for x in hw_comms])

	@commands.command(aliases=["hwcancel"])
	async def cancelhw(self, ctx):
		"""Cancels a current hardware session."""
		if str(ctx.author.id) in self.hwactive:
			self._stop_hw(ctx.author)
			await ctx.send("You've left your current hardware session!".format(ctx.prefix))
			return
		await ctx.send("You're not in a current hardware session.")

	def _stop_hw(self, author):
		if str(author.id) in self.hwactive:
			del self.hwactive[str(author.id)]

	@commands.command()
	async def sethwchannel(self, ctx, *, channel: discord.TextChannel = None):
		"""Sets the channel for hardware (admin only)."""
		
		if not await Utils.is_admin_reply(ctx): return

		if channel is None:
			self.settings.setServerStat(ctx.guild, "HardwareChannel", "")
			return await ctx.send("{} commands now work *only* in pm.".format(self._get_comms(ctx)))

		# If we made it this far - then we can add it
		self.settings.setServerStat(ctx.guild, "HardwareChannel", channel.id)

		await ctx.send("{} commands now work in {} - or in pm.".format(self._get_comms(ctx),channel.mention))
	
	@sethwchannel.error
	async def sethwchannel_error(self, error, ctx):
		# do stuff
		msg = 'sethwchannel Error: {}'.format(error)
		await ctx.send(msg)

	@commands.command(aliases=["gethwchannel","listhwchannel"])
	async def hwchannel(self, ctx):
		"""Lists the current channel for hardware - if any."""

		channel = None
		chan_id = self.settings.getServerStat(ctx.guild, "HardwareChannel", None)
		if chan_id:
			channel = ctx.guild.get_channel(int(chan_id))
		if not channel: # Only in dm
			return await ctx.send("{} commands work *only* in pm.".format(self._get_comms(ctx)))
		await ctx.send("{} commands work in the {} channel - or in pm.".format(self._get_comms(ctx),channel.mention))

	@commands.command()
	async def pcpp(self, ctx, url = None, style = None, escape = None):
		"""Convert a pcpartpicker.com link into markdown parts. Available styles: normal, md, mdblock, bold, and bolditalic."""
		usage = "Usage: `{}pcpp [url] [style=normal, md, mdblock, bold, bolditalic] [escape=yes/no (optional)]`".format(ctx.prefix)
		if not style:
			style = 'normal'
		if not url:
			return await ctx.send(usage)
		if escape is None:
			escape = 'no'
		escape = escape.lower() in ["yes","true","on","enable","enabled","1"]
		
		output = await PCPP.getMarkdown(url, style, escape)
		if not output:
			msg = 'Something went wrong!  Make sure you use a valid pcpartpicker link.'
			return await ctx.send(msg)
		if len(output) > 2000:
			msg = "That's an *impressive* list of parts - but the max length allowed for messages in Discord is 2000 characters, and you're at *{}*.".format(len(output))
			msg += '\nMaybe see if you can prune up that list a bit and try again?'
			return await ctx.send(msg)
		await ctx.send(output)

	@commands.command(aliases=["hwmain"])
	async def mainhw(self, ctx, *, build = None):
		"""Sets a new main build from your build list."""
		await self._mainhw(ctx, build=build)

	@commands.command(aliases=["hwbotmain"])
	async def mainbothw(self, ctx, *, build = None):
		"""Sets a new main build from the bot's build list (owner only)."""
		if not await Utils.is_owner_reply(ctx): return
		await self._mainhw(ctx, user=self.bot.user, build=build)

	async def _mainhw(self, ctx, user = None, build = None):
		user = user or ctx.author
		bot = "" if user==ctx.author else "bot"
		if not build:
			return await ctx.send("Usage: `{}main{}hw [build name or number]`".format(ctx.prefix,bot))

		buildList = self.settings.getGlobalUserStat(user, "Hardware")
		if buildList is None:
			buildList = []
		buildList = sorted(buildList, key=lambda x:x['Name'].lower())

		mainBuild = None

		# Get build by name first - then by number
		for b in buildList:
			if b['Name'].lower() == build.lower():
				# Found it
				mainBuild = b
				break

		if mainBuild:
			# Found it!
			for b in buildList:
				if b is mainBuild:
					b['Main'] = True
				else:
					b['Main'] = False
			self.settings.setGlobalUserStat(user, "Hardware", buildList)
			msg = "{} set as main!".format(mainBuild['Name'])
			return await ctx.send(Utils.suppressed(ctx,msg))
				
		try:
			build = int(build)-1
			if build >= 0 and build < len(buildList):
				mainBuild = buildList[build]
		except:
			pass

		if mainBuild:
			# Found it!
			for b in buildList:
				if b is mainBuild:
					b['Main'] = True
				else:
					b['Main'] = False
			self.settings.setGlobalUserStat(user, "Hardware", buildList)
			msg = "{} set as main!".format(mainBuild['Name'])
			return await ctx.send(Utils.suppressed(ctx,msg))

		msg = "I couldn't find that build or number."
		await ctx.send(msg)

	
	@commands.command(aliases=["hwdel","remhw","hwrem","hwdelete","deletehw","hwremove","removehw"])
	async def delhw(self, ctx, *, build = None):
		"""Removes a build from your build list."""
		await self._delhw(ctx, build=build)

	@commands.command(aliases=["hwbotdel","rembothw","hwbotrem"])
	async def delbothw(self, ctx, *, build = None):
		"""Removes a build from the bot's build list (owner only)."""
		if not await Utils.is_owner_reply(ctx): return
		await self._delhw(ctx, user=self.bot.user, build=build)

	async def _delhw(self, ctx, user = None, build = None):
		user = user or ctx.author
		bot = "" if user==ctx.author else "bot"
		if not build:
			return await ctx.send("Usage: `{}del{}hw [build name or number]`".format(ctx.prefix,bot))

		buildList = self.settings.getGlobalUserStat(user, "Hardware")
		if buildList is None:
			buildList = []
		buildList = sorted(buildList, key=lambda x:x['Name'].lower())

		# Get build by name first - then by number
		for b in buildList:
			if b['Name'].lower() == build.lower():
				# Found it
				buildList.remove(b)
				if b['Main'] and len(buildList):
					buildList[0]['Main'] = True
				self.settings.setGlobalUserStat(user, "Hardware", buildList)
				msg = "{} removed!".format(b['Name'])
				return await ctx.send(Utils.suppressed(ctx,msg))
		try:
			build = int(build)-1
			if build >= 0 and build < len(buildList):
				b = buildList.pop(build)
				if b['Main'] and len(buildList):
					buildList[0]['Main'] = True
				self.settings.setGlobalUserStat(user, "Hardware", buildList)
				msg = "{} removed!".format(b['Name'])
				return await ctx.send(Utils.suppressed(ctx,msg))
		except:
			pass

		msg = "I couldn't find that build or number."
		await ctx.send(msg)


	@commands.command(aliases=["hwedit"])
	async def edithw(self, ctx, *, build = None):
		"""Edits a build from your build list."""
		await self._edithw(ctx, build=build)

	@commands.command()
	async def editbothw(self, ctx, *, build = None):
		"""Edits a build from the bot's build list (owner only)."""
		if not await Utils.is_owner_reply(ctx): return
		await self._edithw(ctx, user=self.bot.user, build=build)

	async def _edithw(self, ctx, user = None, build = None):
		user = user or ctx.author
		you_i,you_i_lower,your_my,bot = ("You","you","your","") if user==ctx.author else ("I","I","my","bot")
		hwChannel = None
		if ctx.guild:
			# Not a pm
			hwChannel = self.settings.getServerStat(ctx.guild,"HardwareChannel")
			if hwChannel:
				# Resolve the id to the channel itself
				hwChannel = self.bot.get_channel(int(hwChannel))
				if hwChannel and hwChannel != ctx.channel:
					return await ctx.send("This isn't the channel for that.  Please take the hardware talk to {} - or to pm.".format(hwChannel.mention))
		if not hwChannel:
			# Nothing set - pm
			hwChannel = ctx.author

		# Make sure we're not already in a parts transaction
		if str(ctx.author.id) in self.hwactive:
			return await ctx.send("You're already in a hardware session!  You can leave with `{}cancelhw`".format(ctx.prefix))

		buildList = self.settings.getGlobalUserStat(user, "Hardware")
		if buildList is None:
			buildList = []
		if not len(buildList):
			# No parts!
			msg = '{} have no builds on file!  You can add some with the `{}new{}hw` command.'.format(you_i,ctx.prefix,bot)
			return await ctx.send(msg)
		buildList = sorted(buildList, key=lambda x:x['Name'].lower())

		mainBuild = None

		# Get build by name first - then by number
		if build is not None:
			for b in buildList:
				if b['Name'].lower() == build.lower():
					# Found it
					mainBuild = b
					break

			if not mainBuild:
				try:
					build = int(build)-1
					if build >= 0 and build < len(buildList):
						mainBuild = buildList[build]
				except:
					pass
		else:
			# No build passed - get the main if it exists
			for b in buildList:
				if b['Main']:
					mainBuild = b
					break

		if not mainBuild:
			msg = "I couldn't find that build or number."
			return await ctx.send(msg)

		# Set our HWActive flag
		hw_id = self.gen_id()
		self.hwactive[str(ctx.author.id)] = hw_id

		# Here, we have a build
		bname = Utils.suppressed(ctx,mainBuild['Name'])
		bparts = Utils.suppressed(ctx,mainBuild['Hardware'])
		
		msg = '"{}"\'s current parts:'.format(bname)
		try:
			await hwChannel.send(msg)
		except:
			# Can't send to the destination
			self._stop_hw(ctx.author)
			if hwChannel == ctx.author:
				# Must not accept pms
				await ctx.send("It looks like you don't accept pms.  Please enable them and try again.")
			return
		if hwChannel == ctx.author and not isinstance(ctx.channel,discord.DMChannel):
			await ctx.message.add_reaction("📬")
		await hwChannel.send(bparts)

		msg = 'Alright, *{}*, what parts does "{}" have now? (Please include *all* parts for this build - you can add new lines with *shift + enter*)\n'.format(DisplayName.name(ctx.author), bname)
		msg += 'You can also pass pcpartpicker links to have them formatted automagically - I can also format them using different styles.\n'
		msg += 'For example: '
		msg += '```https://pcpartpicker.com/list/123456 mdblock``` would format with the markdown block style.\n'
		msg += 'Markdown styles available are *normal, md, mdblock, bold, bolditalic* (type `stop` to cancel)'
		while True:
			parts = await self.prompt(hw_id, ctx, msg, hwChannel, DisplayName.name(ctx.author))
			if not parts:
				self._stop_hw(ctx.author)
				return
			if 'pcpartpicker.com' in parts.content.lower():
				# Possibly a pc partpicker link?
				msg = 'It looks like you sent a pc part picker link - did you want me to try and format that? (`y`/`n`/`stop`)'
				test = await self.confirm(hw_id, ctx, parts, hwChannel, msg)
				if test is None:
					self._stop_hw(ctx.author)
					return
				elif test == True:
					partList = parts.content.split()
					if len(partList) == 1:
						partList.append(None)
					output = None
					try:
						output = await PCPP.getMarkdown(partList[0], partList[1], False)
					except:
						pass
					if not output:
						msg = 'Something went wrong!  Make sure you use a valid pcpartpicker link.'
						await hwChannel.send(msg)
						self._stop_hw(ctx.author)
						return
					if len(output) > 2000:
						msg = "That's an *impressive* list of parts - but the max length allowed for messages in Discord is 2000 characters, and you're at *{}*.".format(len(output))
						msg += '\nMaybe see if you can prune up that list a bit and try again?'
						await hwChannel.send(msg)
						self._stop_hw(ctx.author)
						return
					# Make sure
					conf = await self.confirm(hw_id, ctx, output, hwChannel, None, ctx.author)
					if conf is None:
						# Timed out
						self._stop_hw(ctx.author)
						return
					elif conf == False:
						# Didn't get our answer
						msg = 'Alright, *{}*, what parts does "{}" have now? (Please include *all* parts for this build - you can add new lines with *shift + enter* - type `stop` to cancel)'.format(DisplayName.name(ctx.author), bname)
						continue

					m = '{} set to:\n{}'.format(bname, output)
					await hwChannel.send(m)
					mainBuild['Hardware'] = output
					self.settings.setGlobalUserStat(user, "Hardware", buildList)
					break
			mainBuild['Hardware'] = parts.content
			self.settings.setGlobalUserStat(user, "Hardware", buildList)
			break
		msg = '*{}*, {} was edited successfully!'.format(DisplayName.name(ctx.author), bname)
		self._stop_hw(ctx.author)
		await hwChannel.send(msg)


	@commands.command(aliases=["hwren","renamehw","hwrename"])
	async def renhw(self, ctx, *, build = None):
		"""Renames a build from your build list."""
		await self._renhw(ctx, build=build)

	@commands.command(aliases=["hwbotren"])
	async def renbothw(self, ctx, *, build = None):
		"""Renames a build from the bot's build list (owner only)."""
		if not await Utils.is_owner_reply(ctx): return
		await self._renhw(ctx, user=self.bot.user, build=build)

	async def _renhw(self, ctx, user = None, build = None):
		user = user or ctx.author
		you_i,you_i_lower,your_my,bot = ("You","you","your","") if user==ctx.author else ("I","I","my","bot")
		hwChannel = None
		if ctx.guild:
			# Not a pm
			hwChannel = self.settings.getServerStat(ctx.guild,"HardwareChannel")
			if hwChannel:
				# Resolve the id to the channel itself
				hwChannel = self.bot.get_channel(int(hwChannel))
				if hwChannel and hwChannel != ctx.channel:
					return await ctx.send("This isn't the channel for that.  Please take the hardware talk to {} - or to pm.".format(hwChannel.mention))
		if not hwChannel:
			# Nothing set - pm
			hwChannel = ctx.author

		# Make sure we're not already in a parts transaction
		if str(ctx.author.id) in self.hwactive:
			return await ctx.send("You're already in a hardware session!  You can leave with `{}cancelhw`".format(ctx.prefix))

		buildList = self.settings.getGlobalUserStat(user, "Hardware")
		if buildList is None:
			buildList = []
		if not len(buildList):
			# No parts!
			msg = '{} have no builds on file!  You can add some with the `{}new{}hw` command.'.format(
				you_i,
				ctx.prefix,
				bot
			)
			return await ctx.send(msg)
		buildList = sorted(buildList, key=lambda x:x['Name'].lower())

		mainBuild = None

		# Get build by name first - then by number
		if build is not None:
			for b in buildList:
				if b['Name'].lower() == build.lower():
					# Found it
					mainBuild = b
					break

			if not mainBuild:
				try:
					build = int(build)-1
					if build >= 0 and build < len(buildList):
						mainBuild = buildList[build]
				except:
					pass
		else:
			# No build passed - get the main if it exists
			for b in buildList:
				if b['Main']:
					mainBuild = b
					break

		if not mainBuild:
			msg = "I couldn't find that build or number."
			return await ctx.send(msg)

		# Set our HWActive flag
		hw_id = self.gen_id()
		self.hwactive[str(ctx.author.id)] = hw_id

		# Post the dm reaction
		if hwChannel == ctx.author and not isinstance(ctx.channel,discord.DMChannel):
			await ctx.message.add_reaction("📬")

		# Here, we have a build
		bname = Utils.suppressed(ctx,mainBuild['Name'])

		msg = 'Alright, *{}*, what do you want to rename "{}" to?'.format(DisplayName.name(ctx.author), bname)
		while True:
			try:
				buildName = await self.prompt(hw_id, ctx, msg, hwChannel, DisplayName.name(ctx.author))
			except:
				# Can't send to the destination
				self._stop_hw(ctx.author)
				if hwChannel == ctx.author:
					# Must not accept pms
					await ctx.send("It looks like you don't accept pms.  Please enable them and try again.")
				return
			if not buildName:
				return self._stop_hw(ctx.author)
			buildExists = False
			for build in buildList:
				if build['Name'].lower() == buildName.content.lower():
					mesg = 'It looks like {} already have a build by that name, *{}*.  Try again.'.format(you_i_lower,DisplayName.name(ctx.author))
					await hwChannel.send(mesg)
					buildExists = True
					break
			if not buildExists:
				mainBuild['Name'] = buildName.content
				# Flush settings to all servers
				self.settings.setGlobalUserStat(user, "Hardware", buildList)
				break
		bname2 = Utils.suppressed(ctx,buildName.content)
		msg = '*{}*, {} was renamed to {} successfully!'.format(DisplayName.name(ctx.author), bname, bname2)
		self._stop_hw(ctx.author)
		await hwChannel.send(msg)
		
		
	@commands.command(aliases=["hwget","searchhw","hwsearch"])
	async def gethw(self, ctx, *, user = None, search = None):
		"""Searches the user's hardware for a specific search term."""
		if not user:
			usage = "Usage: `{}gethw [user] [search term]`".format(ctx.prefix)
			return await ctx.send(usage)
	
		# Let's check for username and search term
		parts = user.split()
		memFromName = None
		entries = []
		for j in range(len(parts)):
			# Reverse search direction
			i = len(parts)-1-j
			memFromName = None
			# Name = 0 up to i joined by space
			nameStr =  ' '.join(parts[0:i])
			buildStr = ' '.join(parts[i:])
			
			memFromName = DisplayName.memberForName(nameStr, ctx.guild)
			if memFromName:
				# Got a member - let's check the remainder length, and search!
				if len(buildStr) < 3:
					usage = "Search term must be at least 3 characters."
					return await ctx.send(usage)
				buildList = self.settings.getGlobalUserStat(memFromName, "Hardware", [])
				buildList = sorted(buildList, key=lambda x:x['Name'].lower())
				for build in buildList:
					bParts = build['Hardware']
					for line in bParts.splitlines():
						if buildStr.lower() in line.lower():
							entries.append({"name":"{}. {}".format(len(entries)+1,build["Name"]),"value":line})
				if len(entries):
					# We're in business
					return await PickList.PagePicker(title="Search results for \"{}\" ({:,} total)".format(buildStr, len(entries)),list=entries,ctx=ctx).pick()

		# If we're here - then we didn't find a member - set it to the author, and run another quick search
		buildStr  = user
		if len(buildStr) < 3:
			usage = "Search term must be at least 3 characters."
			return await ctx.send(usage)
		buildList = self.settings.getGlobalUserStat(ctx.author, "Hardware", [])
		buildList = sorted(buildList, key=lambda x:x['Name'].lower())
		for build in buildList:
			bParts = build['Hardware']
			for line in bParts.splitlines():
				if buildStr.lower() in line.lower():
					entries.append({"name":"{}. {}".format(len(entries)+1,build["Name"]),"value":line})
		if len(entries):
			# We're in business
			return await PickList.PagePicker(title="Search results for \"{}\" ({:,} total)".format(buildStr, len(entries)),list=entries,ctx=ctx).pick()
		return await Message.EmbedText(title="Nothing found for that search.",color=ctx.author).send(ctx)


	@commands.command()
	async def hw(self, ctx, *, user : str = None, build = None):
		"""Lists the hardware for either the user's default build - or the passed build."""
		if not user: user = ctx.author.mention

		# Let's check for username and build name
		parts = user.split()

		memFromName = None
		buildParts  = None

		for j in range(len(parts)):
			# Reverse search direction
			i = len(parts)-1-j

			# Name = 0 up to i joined by space
			nameStr = ' '.join(parts[0:i])
			buildStr = ' '.join(parts[i:])

			memFromName = DisplayName.memberForName(nameStr, ctx.guild)
			if memFromName:
				buildList = self.settings.getGlobalUserStat(memFromName, "Hardware")
				if buildList is None:
					buildList = []
				for build in buildList:
					if build['Name'].lower() == buildStr.lower():
						# Ha! Found it!
						buildParts = build
						break
				if buildParts:
					# We're in business
					break
				else:
					memFromName = None

		if not memFromName:
			# Try again with numbers
			for j in range(len(parts)):
				# Reverse search direction
				i = len(parts)-1-j

				# Name = 0 up to i joined by space
				nameStr = ' '.join(parts[0:i])
				buildStr = ' '.join(parts[i:])

				memFromName = DisplayName.memberForName(nameStr, ctx.guild)
				if memFromName:
					buildList = self.settings.getGlobalUserStat(memFromName, "Hardware")
					if buildList is None:
						buildList = []
					buildList = sorted(buildList, key=lambda x:x['Name'].lower())
					try:
						buildStr = int(buildStr)-1
						if buildStr >= 0 and buildStr < len(buildList):
							buildParts = buildList[buildStr]
					except Exception:
						memFromName = None
						buildParts  = None
					if buildParts:
						# We're in business
						break
					else:
						memFromName = None		

		if not memFromName:
			# One last shot - check if it's a build for us
			buildList = self.settings.getGlobalUserStat(ctx.author, "Hardware")
			if buildList is None:
				buildList = []
			buildList = sorted(buildList, key=lambda x:x['Name'].lower())
			for build in buildList:
				if build['Name'].lower() == user.lower():
					memFromName = ctx.author
					buildParts = build
					break
			if not memFromName:
				# Okay - *this* time is the last - check for number
				try:
					user_as_build = int(user)-1
					if user_as_build >= 0 and user_as_build < len(buildList):
						buildParts = buildList[user_as_build]
						memFromName = ctx.author
				except Exception:
					pass
		
		if not memFromName:
			# Last check for a user passed as the only param
			memFromName = DisplayName.memberForName(user, ctx.guild)
		
		if not memFromName:
			# We couldn't find them :(
			msg = "I couldn't find that user/build combo..."
			return await ctx.send(msg)

		if buildParts is None:
			# Check if that user has no builds
			buildList = self.settings.getGlobalUserStat(memFromName, "Hardware")
			if buildList is None:
				buildList = []
			if not len(buildList):
				# No parts!
				msg = '*{}* has no builds on file!  They can add some with the `{}newhw` command.'.format(DisplayName.name(memFromName), ctx.prefix)
				return await ctx.send(msg)
			
			# Must be the default build
			for build in buildList:
				if build['Main']:
					buildParts = build
					break

			if not buildParts:
				# Well... uh... no defaults
				msg = "I couldn't find that user/build combo..."
				return await ctx.send(msg)
		
		# At this point - we *should* have a user and a build
		name = DisplayName.name(memFromName)
		msg_head = "__**{}'{} {}:**__\n\n".format(name,"" if name[-1:].lower()=="s" else "s", buildParts['Name'])
		msg = msg_head + buildParts['Hardware']
		if len(msg) > 2000: # is there somwhere the discord char count is defined, to avoid hardcoding?
			msg = buildParts['Hardware'] # if the header pushes us over the limit, omit it and send just the string
		await ctx.send(Utils.suppressed(ctx,msg))


	@commands.command(aliases=["hwraw"])
	async def rawhw(self, ctx, *, user : str = None, build = None):
		"""Lists the raw markdown for either the user's default build - or the passed build."""
		if not user: user = ctx.author.mention
	
		# Let's check for username and build name
		parts = user.split()

		memFromName = None
		buildParts  = None

		for j in range(len(parts)):
			# Reverse search direction
			i = len(parts)-1-j

			# Name = 0 up to i joined by space
			nameStr = ' '.join(parts[0:i])
			buildStr = ' '.join(parts[i:])

			memFromName = DisplayName.memberForName(nameStr, ctx.guild)
			if memFromName:
				buildList = self.settings.getGlobalUserStat(memFromName, "Hardware")
				if buildList is None:
					buildList = []
				for build in buildList:
					if build['Name'].lower() == buildStr.lower():
						# Ha! Found it!
						buildParts = build
						break
				if buildParts:
					# We're in business
					break
				else:
					memFromName = None

		if not memFromName:
			# Try again with numbers
			for j in range(len(parts)):
				# Reverse search direction
				i = len(parts)-1-j

				# Name = 0 up to i joined by space
				nameStr = ' '.join(parts[0:i])
				buildStr = ' '.join(parts[i:])

				memFromName = DisplayName.memberForName(nameStr, ctx.guild)
				if memFromName:
					buildList = self.settings.getGlobalUserStat(memFromName, "Hardware")
					if buildList is None:
						buildList = []
					buildList = sorted(buildList, key=lambda x:x['Name'].lower())
					try:
						buildStr = int(buildStr)-1
						if buildStr >= 0 and buildStr < len(buildList):
							buildParts = buildList[buildStr]
					except Exception:
						memFromName = None
						buildParts  = None
					if buildParts:
						# We're in business
						break
					else:
						memFromName = None		

		if not memFromName:
			# One last shot - check if it's a build for us
			buildList = self.settings.getGlobalUserStat(ctx.author, "Hardware")
			if buildList is None:
				buildList = []
			buildList = sorted(buildList, key=lambda x:x['Name'].lower())
			for build in buildList:
				if build['Name'].lower() == user.lower():
					memFromName = ctx.author
					buildParts = build
					break
			if not memFromName:
				# Okay - *this* time is the last - check for number
				try:
					user_as_build = int(user)-1
					if user_as_build >= 0 and user_as_build < len(buildList):
						buildParts = buildList[user_as_build]
						memFromName = ctx.author
				except Exception:
					pass
		
		if not memFromName:
			# Last check for a user passed as the only param
			memFromName = DisplayName.memberForName(user, ctx.guild)
		
		if not memFromName:
			# We couldn't find them :(
			msg = "I couldn't find that user/build combo..."
			return await ctx.send(msg)

		if buildParts is None:
			# Check if that user has no builds
			buildList = self.settings.getGlobalUserStat(memFromName, "Hardware")
			if buildList is None:
				buildList = []
			if not len(buildList):
				# No parts!
				msg = '*{}* has no builds on file!  They can add some with the `{}newhw` command.'.format(DisplayName.name(memFromName), ctx.prefix)
				return await ctx.send(msg)
			
			# Must be the default build
			for build in buildList:
				if build['Main']:
					buildParts = build
					break

			if not buildParts:
				# Well... uh... no defaults
				msg = "I couldn't find that user/build combo..."
				return await ctx.send(msg)
		
		# At this point - we *should* have a user and a build
		p = discord.utils.escape_markdown(buildParts['Hardware'])
		name = DisplayName.name(memFromName)
		msg = "__**{}'{} {} (Raw Markdown):**__\n\n{}".format(name,"" if name[-1:].lower()=="s" else "s", buildParts['Name'], p)
		await ctx.send(Utils.suppressed(ctx,msg))
			

	@commands.command(aliases=["hwlist"])
	async def listhw(self, ctx, *, user = None):
		"""Lists the builds for the specified user - or yourself if no user passed."""
		usage = 'Usage: `{}listhw [user]`'.format(ctx.prefix)
		if not user: user = ctx.author.mention
		member = DisplayName.memberForName(user, ctx.guild)
		if not member:
			return await ctx.send(usage)
		buildList = self.settings.getGlobalUserStat(member, "Hardware")
		if buildList is None:
			buildList = []
		buildList = sorted(buildList, key=lambda x:x['Name'].lower())
		if not len(buildList):
			msg = '*{}* has no builds on file!  They can add some with the `{}newhw` command.'.format(DisplayName.name(member), ctx.prefix)
			return await ctx.send(msg)
		items = [{"name":"{}. {}".format(i,x["Name"]+(" (Main Build)" if x["Main"] else "")),"value":Utils.truncate_string(x["Hardware"])} for i,x in enumerate(buildList,start=1)]
		return await PickList.PagePicker(title="{}'s Builds ({:,} total)".format(DisplayName.name(member),len(buildList)),list=items,ctx=ctx).pick()

	@commands.command(aliases=["hwl"])
	async def lhw(self, ctx, *, user = None):
		"""Lists only the titles of the builds for the specified user - or yourself if no user passed."""
		usage = 'Usage: `{}lhw [user]`'.format(ctx.prefix)
		if not user: user = ctx.author.mention
		member = DisplayName.memberForName(user, ctx.guild)
		if not member: return await ctx.send(usage)
		buildList = self.settings.getGlobalUserStat(member, "Hardware", [])
		buildList = sorted(buildList, key=lambda x:x['Name'].lower())
		if not len(buildList):
			msg = '*{}* has no builds on file!  They can add some with the `{}newhw` command.'.format(DisplayName.name(member), ctx.prefix)
			return await ctx.send(msg)
		desc = "\n".join([Utils.truncate_string("{}. {}".format(i,x["Name"]+(" (Main Build)" if x["Main"] else ""))) for i,x in enumerate(buildList,start=1)])
		return await PickList.PagePicker(
			title="{}'s Builds ({:,} total)".format(DisplayName.name(member),len(buildList)),
			description=desc,
			ctx=ctx
		).pick()

	@commands.command(aliases=["hwnew","hwadd","addhw"])
	async def newhw(self, ctx):
		"""Initiate a new-hardware conversation with the bot.  The hardware added will also be set as the Main Build."""
		await self._newhw(ctx)

	@commands.command(aliases=["addbothw"])
	async def newbothw(self, ctx):
		"""Initiates a new-hardware conversation for the bot's hardware.  The hardware added will also be set as the bot's Main Build (owner only)."""
		if not await Utils.is_owner_reply(ctx): return
		await self._newhw(ctx, self.bot.user)

	async def _newhw(self, ctx, user=None):
		user = user or ctx.author
		you_i,you_i_lower,your_my,bot = ("You","you","your","") if user==ctx.author else ("I","I","my","bot")
		buildList = self.settings.getGlobalUserStat(user, "Hardware")
		if buildList is None:
			buildList = []
		hwChannel = None
		if ctx.guild:
			# Not a pm
			hwChannel = self.settings.getServerStat(ctx.guild,"HardwareChannel")
			if hwChannel:
				# Resolve the id to the channel itself
				hwChannel = self.bot.get_channel(int(hwChannel))
				if hwChannel and hwChannel != ctx.channel:
					return await ctx.send("This isn't the channel for that.  Please take the hardware talk to {} - or to pm.".format(hwChannel.mention))
		if not hwChannel:
			# Nothing set - pm
			hwChannel = ctx.author

		# Make sure we're not already in a parts transaction
		if str(ctx.author.id) in self.hwactive:
			return await ctx.send("You're already in a hardware session!  You can leave with `{}cancelhw`".format(ctx.prefix))

		# Set our HWActive flag
		hw_id = self.gen_id()
		self.hwactive[str(ctx.author.id)] = hw_id

		msg = 'Alright, *{}*, let\'s add a new {}build.\n\n'.format(DisplayName.name(ctx.author),"" if ctx.author==user else "bot ")
		if len(buildList) == 1:
			msg += '{} currently have *1 build* on file.\n\n'.format(you_i)
		else:
			msg += '{} currently have *{} builds* on file.\n\nLet\'s get started!'.format(you_i, len(buildList))

		try:
			await hwChannel.send(msg)
		except:
			# Can't send to the destination
			self._stop_hw(ctx.author)
			if hwChannel == ctx.author:
				# Must not accept pms
				await ctx.send("It looks like you don't accept pms.  Please enable them and try again.")
			return

		if hwChannel == ctx.author and not isinstance(ctx.channel,discord.DMChannel):
			await ctx.message.add_reaction("📬")
		msg = '*{}*, tell me what you\'d like to call this build (type `stop` to cancel):'.format(DisplayName.name(ctx.author))
		
		# Get the build name
		newBuild = { 'Main': True }
		while True:
			buildName = await self.prompt(hw_id, ctx, msg, hwChannel, DisplayName.name(ctx.author))
			if not buildName:
				self._stop_hw(ctx.author)
				return
			buildExists = False
			for build in buildList:
				if build['Name'].lower() == buildName.content.lower():
					mesg = 'It looks like {} already have a build by that name, *{}*.  Try again.'.format(you_i_lower,DisplayName.name(ctx.author))
					await hwChannel.send(mesg)
					buildExists = True
					break
			if not buildExists:
				newBuild['Name'] = buildName.content
				break
		bname = Utils.suppressed(ctx,buildName.content)
		msg = 'Alright, *{}*, what parts does "{}" have? (Please include *all* parts for this build - you can add new lines with *shift + enter*)\n'.format(DisplayName.name(ctx.author), bname)
		msg += 'You can also pass pcpartpicker links to have them formatted automagically - I can also format them using different styles.\n'
		msg += 'For example: '
		msg += '```https://pcpartpicker.com/list/123456 mdblock``` would format with the markdown block style.\n'
		msg += 'Markdown styles available are *normal, md, mdblock, bold, bolditalic* (type `stop` to cancel)'
		while True:
			parts = await self.prompt(hw_id, ctx, msg, hwChannel, DisplayName.name(ctx.author))
			if not parts:
				self._stop_hw(ctx.author)
				return
			if 'pcpartpicker.com' in parts.content.lower():
				# Possibly a pc partpicker link?
				msg = 'It looks like you sent a pc part picker link - did you want me to try and format that? (`y`/`n`/`stop`)'
				test = await self.confirm(hw_id, ctx, parts, hwChannel, msg)
				if test is None:
					return self._stop_hw(ctx.author)
				elif test == True:
					partList = parts.content.split()
					if len(partList) == 1:
						partList.append(None)
					output = None
					try:
						output = await PCPP.getMarkdown(partList[0], partList[1], False)
					except:
						pass
					#output = PCPP.getMarkdown(parts.content)
					if not output:
						msg = 'Something went wrong!  Make sure you use a valid pcpartpicker link.'
						await hwChannel.send(msg)
						return self._stop_hw(ctx.author)
					if len(output) > 2000:
						msg = "That's an *impressive* list of parts - but the max length allowed for messages in Discord is 2000 characters, and you're at *{}*.".format(len(output))
						msg += '\nMaybe see if you can prune up that list a bit and try again?'
						await hwChannel.send(msg)
						return self._stop_hw(ctx.author)
					# Make sure
					conf = await self.confirm(hw_id, ctx, output, hwChannel, None, ctx.author)
					if conf is None:
						# Timed out
						return self._stop_hw(ctx.author)
					elif conf == False:
						# Didn't get our answer
						msg = 'Alright, *{}*, what parts does "{}" have? (Please include *all* parts for this build - you can add new lines with *shift + enter* - type `stop` to cancel)'.format(DisplayName.name(ctx.author), bname)
						continue
					m = '{} set to:\n{}'.format(bname, output)
					await hwChannel.send(m)
					newBuild['Hardware'] = output
					break
			newBuild['Hardware'] = parts.content
			break

		# Check if we already have a main build and clear it
		for build in buildList:
			if build['Main']:
				build['Main'] = False

		buildList.append(newBuild)
		self.settings.setGlobalUserStat(user, "Hardware", buildList)
		msg = "*{0}*, {1} was created successfully!  It has been set as {2} **main build**.  To view {2} main build, you can use `{3}hw` - or to change which is {2} main, use `{3}main{4}hw [build name or number]`".format(
			DisplayName.name(ctx.author),
			bname,
			your_my,
			ctx.prefix,
			bot
		)
		self._stop_hw(ctx.author)
		await hwChannel.send(msg)

	# New HW helper methods
	def channelCheck(self, msg, dest = None):
		if not self.stillHardwaring(msg.author):
			# any message is a valid check if we're not editing
			return True
		if dest:
			# We have a target channel
			if isinstance(dest,(discord.User,discord.Member)):
				if isinstance(msg.channel,discord.DMChannel) and dest.id == msg.author.id:
					return True
				return False # Didn't match
			elif isinstance(dest,discord.TextChannel):
				dest = dest.id
			elif isinstance(discord.Guild):
				dest = getattr(dest.get_channel(dest.id),"id",None)
			# If we got here - we're comparing to the channel id
			if dest != msg.channel.id:
				return False 
		else:
			# Just make sure it's in pm or the hw channel
			if isinstance(msg.channel,discord.TextChannel):
				# Let's check our server stuff
				hwChannel = self.settings.getServerStat(msg.guild, "HardwareChannel")
				if hwChannel:
					# We need the channel id
					if not str(hwChannel) == str(ctx.channel.id):
						return False
				else:
					# Nothing set - pm
					if not isinstance(msg.channel,discord.DMChannel):
						return False
		return True

	# Makes sure we're still editing - if this gets set to False,
	# that means the user stopped editing/newhw
	def stillHardwaring(self, author):
		return str(author.id) in self.hwactive

	def confirmCheck(self, msg, dest = None):
		if not self.channelCheck(msg, dest):
			return False
		msgStr = msg.content.lower()
		if msgStr.startswith(('y','n','stop','cancel')):
			return True
		return False

	async def confirm(self, hw_id, ctx, message, dest = None, m = None, author = None):
		# Get author name
		authorName = None
		if author:
			if type(author) is str:
				authorName = author
			else:
				try:
					authorName = DisplayName.name(author)
				except Exception:
					pass
		else:
			if message:
				try:
					author = message.author
				except Exception:
					pass
			try:
				authorName = DisplayName.name(message.author)
			except Exception:
				pass

		if not dest:
			dest = message.channel
		if not m:
			if authorName:
				msg = '*{}*, I got:'.format(Utils.suppressed(ctx,authorName))
			else:
				msg = "I got:"
			if type(message) is str:
				msg2 = Utils.suppressed(ctx,message)
			else:
				msg2 = '{}'.format(Utils.suppressed(ctx,message.content))
			msg3 = 'Is that correct? (`y`/`n`/`stop`)'
			await dest.send(msg)
			await dest.send(msg2)
			await dest.send(msg3)
		else:
			msg = m
			await dest.send(Utils.suppressed(ctx,msg))

		while True:
			def littleCheck(m):
				return ctx.author.id == m.author.id and m.content and self.confirmCheck(m,dest)
			try:
				talk = await self.bot.wait_for('message', check=littleCheck, timeout=self.wait_time)
			except Exception as e:
				print(e)
				talk = None

			# See if we're still in the right context
			if not hw_id == self.hwactive.get(str(ctx.author.id),None):
				return None

			# Hardware ended
			if not self.stillHardwaring(ctx.author):
				return None

			if not talk:
				if authorName:
					msg = "*{}*, I'm out of time...".format(authorName)
				else:
					msg = "I'm out of time..."
				await dest.send(msg)
				return None
			else:
				# We got something
				if talk.content.lower().startswith('y'):
					return True
				elif talk.content.lower().startswith(('stop','cancel')):
					if authorName:
						msg = "No problem, *{}!*  See you later!".format(authorName)
					else:
						msg = "No problem!  See you later!"
					await dest.send(msg)
					return None
				else:
					return False

	async def prompt(self, hw_id, ctx, message, dest = None, author = None):
		# Get author name
		authorName = None
		if author:
			if type(author) is str:
				authorName = author
			else:
				try:
					authorName = DisplayName.name(author)
				except Exception:
					pass
		else:
			if message:
				try:
					author = message.author
				except Exception:
					pass
			try:
				authorName = DisplayName.name(message.author)
			except Exception:
				pass

		if not dest:
			dest = ctx.channel
		await dest.send(Utils.suppressed(ctx,message))
		while True:
			def littleCheck(m):
				return ctx.author.id == m.author.id and m.content and self.channelCheck(m,dest)
			try:
				talk = await self.bot.wait_for('message', check=littleCheck, timeout=self.wait_time)
			except:
				talk = None

			# See if we're still in the right context
			if not hw_id == self.hwactive.get(str(ctx.author.id),None):
				return None

			# Hardware ended
			if not self.stillHardwaring(ctx.author):
				return None

			if not talk:
				msg = "*{}*, I'm out of time...".format(authorName)
				await dest.send(msg)
				return None
			else:
				# Check for a stop
				if talk.content.lower().startswith(('stop','cancel')):
					msg = "No problem, *{}!*  See you later!".format(authorName, ctx.prefix)
					await dest.send(msg)
					return None
				# Make sure
				conf = await self.confirm(hw_id, ctx, talk, dest, "", author)
				if conf == True:
					# We're sure - return the value
					return talk
				elif conf == False:
					# Not sure - ask again
					return await self.prompt(hw_id, ctx, message, dest, author)
				else:
					# Timed out
					return None
