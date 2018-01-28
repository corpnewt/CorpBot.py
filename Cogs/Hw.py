import asyncio
import discord
import time
import argparse
from   operator import itemgetter
from   discord.ext import commands
from   Cogs import ReadableTime
from   Cogs import PCPP
from   Cogs import DisplayName
from   Cogs import Nullify
from   Cogs import Message

def setup(bot):
	# Add the bot and deps
	settings = bot.get_cog("Settings")
	bot.add_cog(Hw(bot, settings))

# This is the Uptime module. It keeps track of how long the bot's been up

class Hw:

	# Init with the bot reference, and a reference to the settings var
	def __init__(self, bot, settings):
		self.bot = bot
		self.settings = settings

	def checkSuppress(self, ctx):
		if not ctx.guild:
			return False
		if self.settings.getServerStat(ctx.guild, "SuppressMentions"):
			return True
		else:
			return False

	# Proof of concept stuff for reloading cog/extension
	def _is_submodule(self, parent, child):
		return parent == child or child.startswith(parent + ".")

	@asyncio.coroutine
	async def on_loaded_extension(self, ext):
		# See if we were loaded
		if not self._is_submodule(ext.__name__, self.__module__):
			return
		# Clear any previous hw setting
		try:
			userList = self.settings.serverDict['GlobalMembers']
		except:
			userList = []
		for user in userList:
			if 'HWActive' in user and user['HWActive'] == True:
				user['HWActive'] = False
		self.settings.serverDict['GlobalMembers'] = userList


	@commands.command(pass_context=True)
	async def cancelhw(self, ctx):
		"""Cancels a current hardware session."""
		if self.settings.getGlobalUserStat(ctx.author, 'HWActive'):
			self.settings.setGlobalUserStat(ctx.author, "HWActive", False)
			await ctx.send("You've left your current hardware session!".format(ctx.prefix))
			return
		await ctx.send("You're not in a current hardware session.")


	@commands.command(pass_context=True)
	async def sethwchannel(self, ctx, *, channel: discord.TextChannel = None):
		"""Sets the channel for hardware (admin only)."""
		
		isAdmin = ctx.message.author.permissions_in(ctx.message.channel).administrator
		# Only allow admins to change server stats
		if not isAdmin:
			await ctx.channel.send('You do not have sufficient privileges to access this command.')
			return

		if channel == None:
			self.settings.setServerStat(ctx.message.guild, "HardwareChannel", "")
			msg = 'Hardware works *only* in pm now.'
			await ctx.channel.send(msg)
			return

		# If we made it this far - then we can add it
		self.settings.setServerStat(ctx.message.guild, "HardwareChannel", channel.id)

		msg = 'Hardware channel set to **{}**.'.format(channel.name)
		await ctx.channel.send(msg)
		
	
	@sethwchannel.error
	async def sethwchannel_error(self, error, ctx):
		# do stuff
		msg = 'sethwchannel Error: {}'.format(error)
		await ctx.channel.send(msg)

	@commands.command(pass_context=True)
	async def pcpp(self, ctx, url = None, style = None, escape = None):
		"""Convert a pcpartpicker.com link into markdown parts. Available styles: normal, md, mdblock, bold, and bolditalic."""
		usage = "Usage: `{}pcpp [url] [style=normal, md, mdblock, bold, bolditalic] [escape=yes/no (optional)]`".format(ctx.prefix)

		# Check if we're suppressing @here and @everyone mentions
		if self.settings.getServerStat(ctx.message.guild, "SuppressMentions"):
			suppress = True
		else:
			suppress = False

		if not style:
			style = 'normal'
		
		if not url:
			await ctx.channel.send(usage)
			return

		if escape == None:
			escape = 'no'
		escape = escape.lower()

		if escape == 'yes' or escape == 'true' or escape == 'on':
			escape = True
		else:
			escape = False
		
		output = await PCPP.getMarkdown(url, style, escape)
		if not output:
			msg = 'Something went wrong!  Make sure you use a valid pcpartpicker link.'
			await ctx.channel.send(msg)
			return
		if len(output) > 2000:
			msg = "That's an *impressive* list of parts - but the max length allowed for messages in Discord is 2000 characters, and you're at *{}*.".format(len(output))
			msg += '\nMaybe see if you can prune up that list a bit and try again?'
			await ctx.channel.send(msg)
			return

		# Check for suppress
		if suppress:
			msg = Nullify.clean(output)
		await ctx.channel.send(output)


	@commands.command(pass_context=True)
	async def mainhw(self, ctx, *, build = None):
		"""Sets a new main build from your build list."""

		if not build:
			await ctx.channel.send("Usage: `{}mainhw [build name or index]`".format(ctx.prefix))
			return

		buildList = self.settings.getGlobalUserStat(ctx.author, "Hardware")
		if buildList == None:
			buildList = []
		buildList = sorted(buildList, key=lambda x:x['Name'].lower())

		mainBuild = None

		# Get build by name first - then by index
		for b in buildList:
			if b['Name'].lower() == build.lower():
				# Found it
				mainBuild = b

		if mainBuild:
			# Found it!
			for b in buildList:
				if b is mainBuild:
					b['Main'] = True
				else:
					b['Main'] = False
			msg = "{} set as main!".format(mainBuild['Name'])
			if self.checkSuppress(ctx):
				msg = Nullify.clean(msg)
			await ctx.channel.send(msg)
			return
				
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
			msg = "{} set as main!".format(mainBuild['Name'])
			if self.checkSuppress(ctx):
				msg = Nullify.clean(msg)
			await ctx.channel.send(msg)
			return

		msg = "I couldn't find that build or index."
		await ctx.channel.send(msg)

	
	@commands.command(pass_context=True)
	async def delhw(self, ctx, *, build = None):
		"""Removes a build from your build list."""

		if not build:
			await ctx.channel.send("Usage: `{}delhw [build name or index]`".format(ctx.prefix))
			return

		buildList = self.settings.getGlobalUserStat(ctx.author, "Hardware")
		if buildList == None:
			buildList = []
		buildList = sorted(buildList, key=lambda x:x['Name'].lower())

		# Get build by name first - then by index
		for b in buildList:
			if b['Name'].lower() == build.lower():
				# Found it
				buildList.remove(b)
				self.settings.setGlobalUserStat(ctx.author, "Hardware", buildList)
				if b['Main'] and len(buildList):
					buildList[0]['Main'] = True
				msg = "{} removed!".format(b['Name'])
				if self.checkSuppress(ctx):
					msg = Nullify.clean(msg)
				await ctx.channel.send(msg)
				return
		try:
			build = int(build)-1
			if build >= 0 and build < len(buildList):
				b = buildList.pop(build)
				self.settings.setGlobalUserStat(ctx.author, "Hardware", buildList)
				if b['Main'] and len(buildList):
					buildList[0]['Main'] = True
				msg = "{} removed!".format(b['Name'])
				if self.checkSuppress(ctx):
					msg = Nullify.clean(msg)
				await ctx.channel.send(msg)
				return
		except:
			pass

		msg = "I couldn't find that build or index."
		await ctx.channel.send(msg)


	@commands.command(pass_context=True)
	async def edithw(self, ctx, *, build = None):
		"""Edits a build from your build list."""
		if not build:
			await ctx.channel.send("Usage: `{}edithw [build name or index]`".format(ctx.prefix))
			return

		hwChannel = None
		if ctx.guild:
			# Not a pm
			hwChannel = self.settings.getServerStat(ctx.guild, "HardwareChannel")
			if not (not hwChannel or hwChannel == ""):
				# We need the channel id
				if not str(hwChannel) == str(ctx.channel.id):
					msg = 'This isn\'t the channel for that...'
					for chan in ctx.guild.channels:
						if str(chan.id) == str(hwChannel):
							msg = 'This isn\'t the channel for that.  Take the hardware talk to the **{}** channel.'.format(chan.name)
					await ctx.channel.send(msg)
					return
				else:
					hwChannel = self.bot.get_channel(hwChannel)
		if not hwChannel:
			# Nothing set - pm
			hwChannel = ctx.author

		# Make sure we're not already in a parts transaction
		if self.settings.getGlobalUserStat(ctx.author, 'HWActive'):
			await ctx.send("You're already in a hardware session!  You can leave with `{}cancelhw`".format(ctx.prefix))
			return

		buildList = self.settings.getGlobalUserStat(ctx.author, "Hardware")
		if buildList == None:
			buildList = []
		buildList = sorted(buildList, key=lambda x:x['Name'].lower())

		mainBuild = None

		# Get build by name first - then by index
		for b in buildList:
			if b['Name'].lower() == build.lower():
				# Found it
				mainBuild = b

		if not mainBuild:
			try:
				build = int(build)-1
				if build >= 0 and build < len(buildList):
					mainBuild = buildList[build]
			except:
				pass

		if not mainBuild:
			msg = "I couldn't find that build or index."
			await ctx.channel.send(msg)
			return

		# Set our HWActive flag
		self.settings.setGlobalUserStat(ctx.author, 'HWActive', True)

		# Here, we have a build
		bname = mainBuild['Name']
		bparts = mainBuild['Hardware']
		if self.checkSuppress(ctx):
			bname = Nullify.clean(bname)
			bparts = Nullify.clean(bparts)
		
		msg = '"{}"\'s current parts:'.format(bname)
		await hwChannel.send(msg)
		if hwChannel == ctx.author and ctx.channel != ctx.author.dm_channel:
			await ctx.message.add_reaction("📬")
		await hwChannel.send(bparts)

		msg = 'Alright, *{}*, what parts does "{}" have now? (Please include *all* parts for this build - you can add new lines with *shift + enter*)\n'.format(DisplayName.name(ctx.author), bname)
		msg += 'You can also pass pcpartpicker links to have them formatted automagically - I can also format them using different styles.\n'
		msg += 'For example: '
		msg += '```https://pcpartpicker.com/list/123456 mdblock``` would format with the markdown block style.\n'
		msg += 'Markdown styles available are *normal, md, mdblock, bold, bolditalic*'
		while True:
			parts = await self.prompt(ctx, msg, hwChannel, DisplayName.name(ctx.author))
			if not parts:
				self.settings.setGlobalUserStat(ctx.author, 'HWActive', False)
				return
			if 'pcpartpicker.com' in parts.content.lower():
				# Possibly a pc partpicker link?
				msg = 'It looks like you sent a pc part picker link - did you want me to try and format that? (y/n/stop)'
				test = await self.confirm(ctx, parts, hwChannel, msg)
				if test == None:
					self.settings.setGlobalUserStat(ctx.author, 'HWActive', False)
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
						self.settings.setGlobalUserStat(ctx.author, 'HWActive', False)
						return
					if len(output) > 2000:
						msg = "That's an *impressive* list of parts - but the max length allowed for messages in Discord is 2000 characters, and you're at *{}*.".format(len(output))
						msg += '\nMaybe see if you can prune up that list a bit and try again?'
						await hwChannel.send(msg)
						self.settings.setGlobalUserStat(ctx.author, 'HWActive', False)
						return
					# Make sure
					conf = await self.confirm(ctx, output, hwChannel, None, ctx.author)
					if conf == None:
						# Timed out
						self.settings.setGlobalUserStat(ctx.author, 'HWActive', False)
						return
					elif conf == False:
						# Didn't get our answer
						msg = 'Alright, *{}*, what parts does "{}" have now? (Please include *all* parts for this build - you can add new lines with *shift + enter*)'.format(DisplayName.name(ctx.author), bname)
						continue

					m = '{} set to:\n{}'.format(bname, output)
					await hwChannel.send(m)
					mainBuild['Hardware'] = output
					self.settings.setGlobalUserStat(ctx.author, "Hardware", buildList)
					break
			mainBuild['Hardware'] = parts.content
			break
		msg = '*{}*, {} was edited successfully!'.format(DisplayName.name(ctx.author), bname)
		self.settings.setGlobalUserStat(ctx.author, 'HWActive', False)
		await hwChannel.send(msg)


	@commands.command(pass_context=True)
	async def renhw(self, ctx, *, build = None):
		"""Renames a build from your build list."""
		if not build:
			await ctx.channel.send("Usage: `{}renhw [build name or index]`".format(ctx.prefix))
			return

		hwChannel = None
		if ctx.guild:
			# Not a pm
			hwChannel = self.settings.getServerStat(ctx.guild, "HardwareChannel")
			if not (not hwChannel or hwChannel == ""):
				# We need the channel id
				if not str(hwChannel) == str(ctx.channel.id):
					msg = 'This isn\'t the channel for that...'
					for chan in ctx.guild.channels:
						if str(chan.id) == str(hwChannel):
							msg = 'This isn\'t the channel for that.  Take the hardware talk to the **{}** channel.'.format(chan.name)
					await ctx.channel.send(msg)
					return
				else:
					hwChannel = self.bot.get_channel(hwChannel)
		if not hwChannel:
			# Nothing set - pm
			hwChannel = ctx.author

		# Make sure we're not already in a parts transaction
		if self.settings.getGlobalUserStat(ctx.author, 'HWActive'):
			await ctx.send("You're already in a hardware session!  You can leave with `{}cancelhw`".format(ctx.prefix))
			return

		buildList = self.settings.getGlobalUserStat(ctx.author, "Hardware")
		if buildList == None:
			buildList = []
		buildList = sorted(buildList, key=lambda x:x['Name'].lower())

		mainBuild = None

		# Get build by name first - then by index
		for b in buildList:
			if b['Name'].lower() == build.lower():
				# Found it
				mainBuild = b

		if not mainBuild:
			try:
				build = int(build)-1
				if build >= 0 and build < len(buildList):
					mainBuild = buildList[build]
			except:
				pass

		if not mainBuild:
			msg = "I couldn't find that build or index."
			await ctx.channel.send(msg)
			return

		# Set our HWActive flag
		self.settings.setGlobalUserStat(ctx.author, 'HWActive', True)

		# Post the dm reaction
		if hwChannel == ctx.author and ctx.channel != ctx.author.dm_channel:
			await ctx.message.add_reaction("📬")

		# Here, we have a build
		bname = mainBuild['Name']
		if self.checkSuppress(ctx):
			bname = Nullify.clean(bname)

		msg = 'Alright, *{}*, what do you want to rename "{}" to?'.format(DisplayName.name(ctx.author), bname)
		while True:
			buildName = await self.prompt(ctx, msg, hwChannel, DisplayName.name(ctx.author))
			if not buildName:
				self.settings.setGlobalUserStat(ctx.author, 'HWActive', False)
				return
			buildExists = False
			for build in buildList:
				if build['Name'].lower() == buildName.content.lower():
					mesg = 'It looks like you already have a build by that name, *{}*.  Try again.'.format(DisplayName.name(ctx.author))
					await hwChannel.send(mesg)
					buildExists = True
					break
			if not buildExists:
				mainBuild['Name'] = buildName.content
				# Flush settings to all servers
				self.settings.setGlobalUserStat(ctx.author, "Hardware", buildList)
				break
		bname2 = buildName.content
		if self.checkSuppress(ctx):
			bname2 = Nullify.clean(bname2)
		msg = '*{}*, {} was renamed to {} successfully!'.format(DisplayName.name(ctx.author), bname, bname2)
		self.settings.setGlobalUserStat(ctx.author, 'HWActive', False)
		await hwChannel.send(msg)
		
		
	@commands.command(pass_context=True)
	async def gethw(self, ctx, *, user = None, search = None):
		"""Searches the user's hardware for a specific search term."""
		if not user:
			usage = "Usage: `{}gethw [user] [search term]`".format(ctx.prefix)
			await ctx.channel.send(usage)
			return
	
		# Let's check for username and search term
		parts = user.split()

		memFromName = None
		buildParts  = None
		
		for j in range(len(parts)):
			# Reverse search direction
			i = len(parts)-1-j
			memFromName = None
			buildParts  = None

			# Name = 0 up to i joined by space
			nameStr =  ' '.join(parts[0:i])
			buildStr = ' '.join(parts[i:])
			
			memFromName = DisplayName.memberForName(nameStr, ctx.guild)
			if memFromName:
				# Got a member - let's check the remainder length, and search!
				if len(buildStr) < 3:
					usage = "Search term must be at least 3 characters."
					await ctx.channel.send(usage)
					return
				buildList = self.settings.getGlobalUserStat(memFromName, "Hardware")
				if buildList == None:
					buildList = []
				buildList = sorted(buildList, key=lambda x:x['Name'].lower())
				foundStr = ''
				foundCt  = 0
				for build in buildList:
					bParts = build['Hardware']
					for line in bParts.splitlines():
						if buildStr.lower() in line.lower():
							foundCt += 1
							foundStr += '{}. **{}**\n   {}\n'.format(foundCt, build['Name'], line.replace("`", ""))

				if len(foundStr):
					# We're in business
					foundStr = "__**\"{}\" Results:**__\n\n".format(buildStr, DisplayName.name(memFromName)) + foundStr
					break
				else:
					# foundStr = 'Nothing found for "{}" in *{}\'s* builds.'.format(buildStr, DisplayName.name(memFromName))
					# Nothing found...
					memFromName = None
					buildStr    = None
		if memFromName and len(foundStr):
			# We're in business
			if self.checkSuppress(ctx):
				foundStr = Nullify.clean(foundStr)
			await Message.Message(message=foundStr).send(ctx)
			return

		# If we're here - then we didn't find a member - set it to the author, and run another quick search
		buildStr  = user

		if len(buildStr) < 3:
			usage = "Search term must be at least 3 characters."
			await ctx.channel.send(usage)
			return

		buildList = self.settings.getGlobalUserStat(ctx.author, "Hardware")
		if buildList == None:
			buildList = []
		buildList = sorted(buildList, key=lambda x:x['Name'].lower())

		foundStr = ''
		foundCt  = 0
		for build in buildList:
			bParts = build['Hardware']
			for line in bParts.splitlines():
				if buildStr.lower() in line.lower():
					foundCt += 1
					foundStr += '{}. **{}**\n   {}\n'.format(foundCt, build['Name'], line.replace("`", ""))

		if len(foundStr):
			# We're in business
			foundStr = "__**\"{}\" Results:**__\n\n".format(buildStr) + foundStr
		else:
			foundStr = 'Nothing found for "{}".'.format(buildStr)
			# Nothing found...
		if self.checkSuppress(ctx):
			foundStr = Nullify.clean(foundStr)
		await Message.Message(message=foundStr).send(ctx)


	@commands.command(pass_context=True)
	async def hw(self, ctx, *, user : str = None, build = None):
		"""Lists the hardware for either the user's default build - or the passed build."""
		if not user:
			user = "{}".format(ctx.author.mention)


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
				if buildList == None:
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
			# Try again with indexes
			for j in range(len(parts)):
				# Reverse search direction
				i = len(parts)-1-j

				# Name = 0 up to i joined by space
				nameStr = ' '.join(parts[0:i])
				buildStr = ' '.join(parts[i:])

				memFromName = DisplayName.memberForName(nameStr, ctx.guild)
				if memFromName:
					buildList = self.settings.getGlobalUserStat(memFromName, "Hardware")
					if buildList == None:
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
			if buildList == None:
				buildList = []
			buildList = sorted(buildList, key=lambda x:x['Name'].lower())
			for build in buildList:
				if build['Name'].lower() == user.lower():
					memFromName = ctx.author
					buildParts = build
					break
			if not memFromName:
				# Okay - *this* time is the last - check for index
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
			await ctx.channel.send(msg)
			return

		if buildParts == None:
			# Check if that user has no builds
			buildList = self.settings.getGlobalUserStat(memFromName, "Hardware")
			if buildList == None:
				buildList = []
			if not len(buildList):
				# No parts!
				msg = '*{}* has no builds on file!  They can add some with the `{}newhw` command.'.format(DisplayName.name(memFromName), ctx.prefix)
				await ctx.channel.send(msg)
				return
			
			# Must be the default build
			for build in buildList:
				if build['Main']:
					buildParts = build
					break

			if not buildParts:
				# Well... uh... no defaults
				msg = "I couldn't find that user/build combo..."
				await ctx.channel.send(msg)
				return
		
		# At this point - we *should* have a user and a build
		msg = "__**{}'s {}:**__\n\n{}".format(DisplayName.name(memFromName), buildParts['Name'], buildParts['Hardware'])
		if self.checkSuppress(ctx):
			msg = Nullify.clean(msg)
		await ctx.channel.send(msg)


	@commands.command(pass_context=True)
	async def rawhw(self, ctx, *, user : str = None, build = None):
		"""Lists the raw markdown for either the user's default build - or the passed build."""
		if not user:
			user = ctx.author.name
	
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
				if buildList == None:
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
			# Try again with indexes
			for j in range(len(parts)):
				# Reverse search direction
				i = len(parts)-1-j

				# Name = 0 up to i joined by space
				nameStr = ' '.join(parts[0:i])
				buildStr = ' '.join(parts[i:])

				memFromName = DisplayName.memberForName(nameStr, ctx.guild)
				if memFromName:
					buildList = self.settings.getGlobalUserStat(memFromName, "Hardware")
					if buildList == None:
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
			if buildList == None:
				buildList = []
			buildList = sorted(buildList, key=lambda x:x['Name'].lower())
			for build in buildList:
				if build['Name'].lower() == user.lower():
					memFromName = ctx.author
					buildParts = build
					break
			if not memFromName:
				# Okay - *this* time is the last - check for index
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
			await ctx.channel.send(msg)
			return

		if buildParts == None:
			# Check if that user has no builds
			buildList = self.settings.getGlobalUserStat(memFromName, "Hardware")
			if buildList == None:
				buildList = []
			if not len(buildList):
				# No parts!
				msg = '*{}* has no builds on file!  They can add some with the `{}newhw` command.'.format(DisplayName.name(memFromName), ctx.prefix)
				await ctx.channel.send(msg)
				return
			
			# Must be the default build
			for build in buildList:
				if build['Main']:
					buildParts = build
					break

			if not buildParts:
				# Well... uh... no defaults
				msg = "I couldn't find that user/build combo..."
				await ctx.channel.send(msg)
				return
		
		# At this point - we *should* have a user and a build
		# Escape all \ with \\
		p = buildParts['Hardware'].replace('\\', '\\\\')
		p = p.replace('*', '\\*')
		p = p.replace('`', '\\`')
		p = p.replace('_', '\\_')
		msg = "__**{}'s {} (Raw Markdown):**__\n\n{}".format(DisplayName.name(memFromName), buildParts['Name'], p)
		if self.checkSuppress(ctx):
			msg = Nullify.clean(msg)
		await ctx.channel.send(msg)
			

	@commands.command(pass_context=True)
	async def listhw(self, ctx, *, user = None):
		"""Lists the builds for the specified user - or yourself if no user passed."""
		usage = 'Usage: `{}listhw [user]`'.format(ctx.prefix)
		if not user:
			user = ctx.author.name
		member = DisplayName.memberForName(user, ctx.guild)
		if not member:
			await ctx.channel.send(usage)
			return
		buildList = self.settings.getGlobalUserStat(member, "Hardware")
		if buildList == None:
			buildList = []
		buildList = sorted(buildList, key=lambda x:x['Name'].lower())
		if not len(buildList):
			msg = '*{}* has no builds on file!  They can add some with the `{}newhw` command.'.format(DisplayName.name(member), ctx.prefix)
			await ctx.channel.send(msg)
			return
		msg = "__**{}'s Builds:**__\n\n".format(DisplayName.name(member))
		i = 1
		for build in buildList:
			msg += '{}. {}'.format(i, build['Name'])
			if build['Main']:
				msg += ' (Main Build)'
			msg += "\n"
			i += 1
		# Cut the last return
		msg = msg[:-1]
		if self.checkSuppress(ctx):
			msg = Nullify.clean(msg)
		# Limit output to 1 page - if more than that, send to pm
		await Message.Message(message=msg).send(ctx)


	@commands.command(pass_context=True)
	async def newhw(self, ctx):
		"""Initiate a new-hardware conversation with the bot."""
		buildList = self.settings.getGlobalUserStat(ctx.author, "Hardware")
		if buildList == None:
			buildList = []
		hwChannel = None
		if ctx.guild:
			# Not a pm
			hwChannel = self.settings.getServerStat(ctx.guild, "HardwareChannel")
			if not (not hwChannel or hwChannel == ""):
				# We need the channel id
				if not str(hwChannel) == str(ctx.channel.id):
					msg = 'This isn\'t the channel for that...'
					for chan in ctx.guild.channels:
						if str(chan.id) == str(hwChannel):
							msg = 'This isn\'t the channel for that.  Take the hardware talk to the **{}** channel.'.format(chan.name)
					await ctx.channel.send(msg)
					return
				else:
					hwChannel = self.bot.get_channel(hwChannel)
		if not hwChannel:
			# Nothing set - pm
			hwChannel = ctx.author

		# Make sure we're not already in a parts transaction
		if self.settings.getGlobalUserStat(ctx.author, 'HWActive'):
			await ctx.send("You're already in a hardware session!  You can leave with `{}cancelhw`".format(ctx.prefix))
			return

		# Set our HWActive flag
		self.settings.setGlobalUserStat(ctx.author, 'HWActive', True)

		msg = 'Alright, *{}*, let\'s add a new build.\n\n'.format(DisplayName.name(ctx.author))
		if len(buildList) == 1:
			msg += 'You currently have *1 build* on file.\n\n'
		else:
			msg += 'You currently have *{} builds* on file.\n\nLet\'s get started!'.format(len(buildList))

		try:
			await hwChannel.send(msg)
		except:
			# Can't send to the destination
			self.settings.setGlobalUserStat(ctx.author, 'HWActive', False)
			if hwChannel == ctx.author:
				# Must not accept pms
				await ctx.send("It looks like you don't accept pms.  Please enable them and try again.")
			return

		if hwChannel == ctx.author and ctx.channel != ctx.author.dm_channel:
			await ctx.message.add_reaction("📬")
		msg = '*{}*, tell me what you\'d like to call this build (type stop to cancel):'.format(DisplayName.name(ctx.author))
		
		# Get the build name
		newBuild = { 'Main': True }
		while True:
			buildName = await self.prompt(ctx, msg, hwChannel, DisplayName.name(ctx.author))
			if not buildName:
				self.settings.setGlobalUserStat(ctx.author, 'HWActive', False)
				return
			buildExists = False
			for build in buildList:
				if build['Name'].lower() == buildName.content.lower():
					mesg = 'It looks like you already have a build by that name, *{}*.  Try again.'.format(DisplayName.name(ctx.author))
					await hwChannel.send(mesg)
					buildExists = True
					break
			if not buildExists:
				newBuild['Name'] = buildName.content
				break
		bname = buildName.content
		if self.checkSuppress(ctx):
			bname = Nullify.clean(bname)
		msg = 'Alright, *{}*, what parts does "{}" have? (Please include *all* parts for this build - you can add new lines with *shift + enter*)\n'.format(DisplayName.name(ctx.author), bname)
		msg += 'You can also pass pcpartpicker links to have them formatted automagically - I can also format them using different styles.\n'
		msg += 'For example: '
		msg += '```https://pcpartpicker.com/list/123456 mdblock``` would format with the markdown block style.\n'
		msg += 'Markdown styles available are *normal, md, mdblock, bold, bolditalic*'
		while True:
			parts = await self.prompt(ctx, msg, hwChannel, DisplayName.name(ctx.author))
			if not parts:
				self.settings.setGlobalUserStat(ctx.author, 'HWActive', False)
				return
			if 'pcpartpicker.com' in parts.content.lower():
				# Possibly a pc partpicker link?
				msg = 'It looks like you sent a pc part picker link - did you want me to try and format that? (y/n/stop)'
				test = await self.confirm(ctx, parts, hwChannel, msg)
				if test == None:
					self.settings.setGlobalUserStat(ctx.author, 'HWActive', False)
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
					#output = PCPP.getMarkdown(parts.content)
					if not output:
						msg = 'Something went wrong!  Make sure you use a valid pcpartpicker link.'
						await hwChannel.send(msg)
						self.settings.setGlobalUserStat(ctx.author, 'HWActive', False)
						return
					if len(output) > 2000:
						msg = "That's an *impressive* list of parts - but the max length allowed for messages in Discord is 2000 characters, and you're at *{}*.".format(len(output))
						msg += '\nMaybe see if you can prune up that list a bit and try again?'
						await hwChannel.send(msg)
						self.settings.setGlobalUserStat(ctx.author, 'HWActive', False)
						return
					# Make sure
					conf = await self.confirm(ctx, output, hwChannel, None, ctx.author)
					if conf == None:
						# Timed out
						self.settings.setGlobalUserStat(ctx.author, 'HWActive', False)
						return
					elif conf == False:
						# Didn't get our answer
						msg = 'Alright, *{}*, what parts does "{}" have? (Please include *all* parts for this build - you can add new lines with *shift + enter*)'.format(DisplayName.name(ctx.author), bname)
						continue
					m = '{} set to:\n{}'.format(bname, output)
					await hwChannel.send(m)
					newBuild['Hardware'] = output
					break
			newBuild['Hardware'] = parts.content
			break

		# Check if we already have a main build
		for build in buildList:
			if build['Main']:
				newBuild['Main'] = False

		buildList.append(newBuild)
		self.settings.setGlobalUserStat(ctx.author, "Hardware", buildList)
		msg = '*{}*, {} was created successfully!'.format(DisplayName.name(ctx.author), bname)
		self.settings.setGlobalUserStat(ctx.author, 'HWActive', False)
		await hwChannel.send(msg)

	# New HW helper methods
	def channelCheck(self, msg, dest = None):
		if self.stillHardwaring(msg.author) == False:
			# any message is a valid check if we're not editing
			return True
		if dest:
			# We have a target channel
			if type(dest) is discord.User or type(dest) is discord.Member:
				dest = dest.dm_channel.id
			elif type(dest) is discord.TextChannel:
				dest = dest.id
			elif type(dest) is discord.Guild:
				dest = dest.get_channel(dest.id).id
			if not dest == msg.channel.id:
				return False 
		else:
			# Just make sure it's in pm or the hw channel
			if msg.channel == discord.TextChannel:
				# Let's check our server stuff
				hwChannel = self.settings.getServerStat(msg.guild, "HardwareChannel")
				if not (not hwChannel or hwChannel == ""):
					# We need the channel id
					if not str(hwChannel) == str(ctx.channel.id):
						return False
				else:
					# Nothing set - pm
					if not type(msg.channel) == discord.DMChannel:
						return False
		return True

	# Makes sure we're still editing - if this gets set to False,
	# that means the user stopped editing/newhw
	def stillHardwaring(self, author):
		return self.settings.getGlobalUserStat(author, "HWActive")

	def confirmCheck(self, msg, dest = None):
		if not self.channelCheck(msg, dest):
			return False
		msgStr = msg.content.lower()
		if msgStr.startswith('y'):
			return True
		if msgStr.startswith('n'):
			return True
		elif msgStr.startswith('stop'):
			return True
		return False

	async def confirm(self, ctx, message, dest = None, m = None, author = None):
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
				msg = '*{}*, I got:'.format(authorName)
			else:
				msg = "I got:"
			if type(message) is str:
				msg2 = message
			else:
				msg2 = '{}'.format(message.content)
			msg3 = 'Is that correct? (y/n/stop)'
			if self.checkSuppress(ctx):
				msg = Nullify.clean(msg)
				msg2 = Nullify.clean(msg2)
				msg3 = Nullify.clean(msg3)
			await dest.send(msg)
			await dest.send(msg2)
			await dest.send(msg3)
		else:
			msg = m
			if self.checkSuppress(ctx):
				msg = Nullify.clean(msg)
			await dest.send(msg)

		while True:
			def littleCheck(m):
				return ctx.author.id == m.author.id and self.confirmCheck(m, dest) and len(m.content)
			try:
				talk = await self.bot.wait_for('message', check=littleCheck, timeout=300)
			except Exception:
				talk = None

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
				elif talk.content.lower().startswith('stop'):
					if authorName:
						msg = "No problem, *{}!*  See you later!".format(authorName)
					else:
						msg = "No problem!  See you later!"
					await dest.send(msg)
					return None
				else:
					return False

	async def prompt(self, ctx, message, dest = None, author = None):
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
		if self.checkSuppress(ctx):
			msg = Nullify.clean(message)
		await dest.send(message)
		while True:
			def littleCheck(m):
				return ctx.author.id == m.author.id and self.channelCheck(m, dest) and len(m.content)
			try:
				talk = await self.bot.wait_for('message', check=littleCheck, timeout=300)
			except Exception:
				talk = None

			# Hardware ended
			if not self.stillHardwaring(ctx.author):
				return None

			if not talk:
				msg = "*{}*, I'm out of time...".format(authorName)
				await dest.send(msg)
				return None
			else:
				# Check for a stop
				if talk.content.lower() == 'stop':
					msg = "No problem, *{}!*  See you later!".format(authorName, ctx.prefix)
					await dest.send(msg)
					return None
				# Make sure
				conf = await self.confirm(ctx, talk, dest, "", author)
				if conf == True:
					# We're sure - return the value
					return talk
				elif conf == False:
					# Not sure - ask again
					return await self.prompt(ctx, message, dest, author)
				else:
					# Timed out
					return None
