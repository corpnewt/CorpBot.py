import asyncio
import discord
import time
from   operator import itemgetter
from   discord.ext import commands
from   Cogs import Settings
from   Cogs import ReadableTime
from   Cogs import DisplayName

# This is the lists module.

class Lists:

	# Init with the bot reference, and a reference to the settings var
	def __init__(self, bot, settings):
		self.bot = bot
		self.settings = settings

	def message(self, message):
		# Check the message and see if we should allow it - always yes.
		# This module doesn't need to cancel messages.
		return { 'Ignore' : False, 'Delete' : False}

		
	@commands.command(pass_context=True)
	async def addlink(self, ctx, name : str = None, link : str = None):
		"""Add a link to the link list."""
		
		channel = ctx.message.channel
		author  = ctx.message.author
		server  = ctx.message.server
		
		# Check for role requirements
		requiredRole = self.settings.getServerStat(server, "RequiredLinkRole")
		if requiredRole == "":
			#admin only
			isAdmin = author.permissions_in(channel).administrator
			if not isAdmin:
				await self.bot.send_message(channel, 'You do not have sufficient privileges to access this command.')
				return
		else:
			#role requirement
			hasPerms = False
			for role in author.roles:
				if role.id == requiredRole:
					hasPerms = True
			if not hasPerms:
				await self.bot.send_message(channel, 'You do not have sufficient privileges to access this command.')
				return
				
		# Passed role requirements!
		if not (name or link):
			msg = 'Usage: `$addlink "[link name]" [url]`'
			await self.bot.send_message(channel, msg)
			return

		linkList = self.settings.getServerStat(server, "Links")
		if not linkList:
			linkList = []
		
		found = False
		currentTime = int(time.time())	
		for alink in linkList:
			if alink['Name'].lower() == name.lower():
				# The link exists!
				msg = '*{}* updated!'.format(name)
				alink['URL'] = link
				alink['UpdatedBy'] = DisplayName.name(author)
				alink['UpdatedID'] = author.id
				alink['Updated'] = currentTime
				found = True
		if not found:	
			linkList.append({"Name" : name, "URL" : link, "CreatedBy" : DisplayName.name(author), "CreatedID": author.id, "Created" : currentTime})
			msg = '*{}* added to link list!'.format(name)
		
		self.settings.setServerStat(server, "Links", linkList)
		await self.bot.send_message(channel, msg)
		
		
	@commands.command(pass_context=True)
	async def removelink(self, ctx, name : str = None):
		"""Remove a link from the link list."""
		
		channel = ctx.message.channel
		author  = ctx.message.author
		server  = ctx.message.server
		
		# Check for role requirements
		requiredRole = self.settings.getServerStat(server, "RequiredLinkRole")
		if requiredRole == "":
			#admin only
			isAdmin = author.permissions_in(channel).administrator
			if not isAdmin:
				await self.bot.send_message(channel, 'You do not have sufficient privileges to access this command.')
				return
		else:
			#role requirement
			hasPerms = False
			for role in author.roles:
				if role.id == requiredRole:
					hasPerms = True
			if not hasPerms:
				await self.bot.send_message(channel, 'You do not have sufficient privileges to access this command.')
				return
		
		if name == None:
			msg = 'Usage: `$removelink "[link name]"`'
			await self.bot.send_message(channel, msg)
			return

		linkList = self.settings.getServerStat(server, "Links")
		if not linkList or linkList == []:
			msg = 'No links in list!  You can add some with the `$addlink "[link name]" [url]` command!'
			await self.bot.send_message(channel, msg)
			return

		for alink in linkList:
			if alink['Name'].lower() == name.lower():
				linkList.remove(alink)
				self.settings.setServerStat(server, "Links", linkList)
				msg = '*{}* removed from link list!'.format(name)
				await self.bot.send_message(channel, msg)
				return

		msg = '*{}* not found in link list!'.format(name)
		await self.bot.send_message(channel, msg)


	@commands.command(pass_context=True)
	async def link(self, ctx, name : str = None):
		"""Retrieve a link from the link list."""
		
		channel = ctx.message.channel
		author  = ctx.message.author
		server  = ctx.message.server
		
		if not name:
			msg = 'Usage: `$link "[link name]"`'
			await self.bot.send_message(channel, msg)
			return

		linkList = self.settings.getServerStat(server, "Links")
		if not linkList or linkList == []:
			msg = 'No links in list!  You can add some with the `$addlink "[link name]" [url]` command!'
			await self.bot.send_message(channel, msg)
			return

		for alink in linkList:
			if alink['Name'].lower() == name.lower():
				msg = '**{}:**\n{}'.format(alink['Name'], alink['URL'])
				await self.bot.send_message(channel, msg)
				return
				
		await self.bot.send_message(channel, 'Link "*{}*" not found!'.format(name))		

	@commands.command(pass_context=True)
	async def linkinfo(self, ctx, name : str = None):
		"""Displays info about a link from the link list."""

		channel = ctx.message.channel
		author  = ctx.message.author
		server  = ctx.message.server
		
		if not name:
			msg = 'Usage: `$linkinfo "[link name]"`'
			await self.bot.send_message(channel, msg)
			return

		linkList = self.settings.getServerStat(server, "Links")
		if not linkList or linkList == []:
			msg = 'No links in list!  You can add some with the `$addlink "[link name]" [url]` command!'
			await self.bot.send_message(channel, msg)
			return

		for alink in linkList:
			if alink['Name'].lower() == name.lower():
				currentTime = int(time.time())
				msg = '**{}:**'.format(alink['Name'])
				try:
					memID = DisplayName.memberForID(alink['CreatedID'], server)
				except KeyError as e:
					memID = None
				if memID:
					msg = '{}\nCreated By: *{}*'.format(msg, DisplayName.name(memID))
				else:
					try:	
						msg = '{}\nCreated By: *{}*'.format(msg, alink['CreatedBy'])
					except KeyError as e:
						msg = '{}\nCreated By: `UNKNOWN`'.format(msg)
				try:
					createdTime = int(alink['Created'])
					timeString  = ReadableTime.getReadableTimeBetween(createdTime, currentTime)
					msg = '{}\nCreated : *{}* ago'.format(msg, timeString)
				except KeyError as e:
					pass
				try:
					msg = '{}\nUpdated By: *{}*'.format(msg, alink['UpdatedBy'])
				except KeyError as e:
					pass
				try:
					createdTime = alink['Updated']
					createdTime = int(createdTime)
					timeString  = ReadableTime.getReadableTimeBetween(createdTime, currentTime)
					msg = '{}\nUpdated : *{}* ago'.format(msg, timeString)
				except:
					pass
				await self.bot.send_message(channel, msg)
				return
				
		await self.bot.send_message(channel, 'Link "*{}*" not found!'.format(name))


	@commands.command(pass_context=True)
	async def links(self, ctx):
		"""List all links in the link list."""
		
		channel = ctx.message.channel
		author  = ctx.message.author
		server  = ctx.message.server
		
		linkList = self.settings.getServerStat(server, "Links")
		if linkList == None or linkList == []:
			msg = 'No links in list!  You can add some with the `$addlink "[link name]" [url]` command!'
			await self.bot.send_message(channel, msg)
			return
			
		# Sort by link name
		linkList = sorted(linkList, key=itemgetter('Name'))
		linkText = "Current Links:\n\n"
		for alink in linkList:
			linkText = '{}*{}*, '.format(linkText, alink['Name'])

		# Speak the link list while cutting off the end ", "
		await self.bot.send_message(channel, linkText[:-2])


	@commands.command(pass_context=True)
	async def linkrole(self, ctx):
		"""Lists the required role to add links."""
		role = self.settings.getServerStat(ctx.message.server, "RequiredLinkRole")
		if role == None or role == "":
			msg = '**Only Admins** can add links.'.format(ctx)
			await self.bot.say(msg)
		else:
			# Role is set - let's get its name
			found = False
			for arole in ctx.message.server.roles:
				if arole.id == role:
					found = True
					msg = 'You need to be a/an **{}** to add links.'.format(arole.name)
			if not found:
				msg = 'There is no role that matches id: `{}` - consider updating this setting.'.format(role)
			await self.bot.send_message(ctx.message.channel, msg)
		
		
	@commands.command(pass_context=True)
	async def addhack(self, ctx, name : str = None, hack : str = None):
		"""Add a hack to the hack list."""
		
		channel = ctx.message.channel
		author  = ctx.message.author
		server  = ctx.message.server
		
		# Check for role requirements
		requiredRole = self.settings.getServerStat(server, "RequiredHackRole")
		if requiredRole == "":
			#admin only
			isAdmin = author.permissions_in(channel).administrator
			if not isAdmin:
				await self.bot.send_message(channel, 'You do not have sufficient privileges to access this command.')
				return
		else:
			#role requirement
			hasPerms = False
			for role in author.roles:
				if role.id == requiredRole:
					hasPerms = True
			if not hasPerms:
				await self.bot.send_message(ctx.message.channel, 'You do not have sufficient privileges to access this command.')
				return
				
		# Passed role requirements!
		if not (name or hack):
			msg = 'Usage: `$addlink "[hack name]" [hack]`'
			await self.bot.send_message(channel, msg)
			return

		hackList = self.settings.getServerStat(server, "Hacks")
		if hackList == None:
			hackList = []

		found = False
		currentTime = int(time.time())
		for ahack in hackList:
			if ahack['Name'].lower() == name.lower():
				# The hack exists!
				msg = '*{}* updated!'.format(name)
				ahack['Hack'] = hack
				ahack['UpdatedBy'] = author.name
				ahack['UpdatedID'] = DisplayName.name(author)
				ahack['Updated'] = currentTime
				found = True
		if not found:		
			hackList.append({"Name" : name, "Hack" : hack, "CreatedBy" : DisplayName.name(author), "CreatedID": author.id, "Created" : currentTime})
			msg = '*{}* added to link list!'.format(name)
		
		self.settings.setServerStat(server, "Hacks", hackList)
		await self.bot.send_message(channel, msg)

		
		
	@commands.command(pass_context=True)
	async def removehack(self, ctx, name : str = None):
		"""Remove a hack from the hack list."""
		
		channel = ctx.message.channel
		author  = ctx.message.author
		server  = ctx.message.server
		
		# Check for role requirements
		requiredRole = self.settings.getServerStat(server, "RequiredHackRole")
		if requiredRole == "":
			#admin only
			isAdmin = author.permissions_in(channel).administrator
			if not isAdmin:
				await self.bot.send_message(channel, 'You do not have sufficient privileges to access this command.')
				return
		else:
			#role requirement
			hasPerms = False
			for role in author.roles:
				if role.id == requiredRole:
					hasPerms = True
			if not hasPerms:
				await self.bot.send_message(channel, 'You do not have sufficient privileges to access this command.')
				return
		
		if name == None:
			msg = 'Usage: `$removehack "[hack name]"`'
			await self.bot.send_message(channel, msg)
			return

		linkList = self.settings.getServerStat(server, "Hacks")
		if not linkList or linkList == []:
			msg = 'No hacks in list!  You can add some with the `$addhack "[hack name]" [hack]` command!'
			await self.bot.send_message(channel, msg)
			return

		for alink in linkList:
			if alink['Name'].lower() == name.lower():
				linkList.remove(alink)
				self.settings.setServerStat(server, "Hacks", linkList)
				msg = '*{}* removed from hack list!'.format(name)
				await self.bot.send_message(ctx.message.channel, msg)
				return

		msg = '*{}* not found in hack list!'.format(name)
		await self.bot.send_message(channel, msg)


	@commands.command(pass_context=True)
	async def hack(self, ctx, name : str = None):
		"""Retrieve a hack from the hack list."""
		
		channel = ctx.message.channel
		author  = ctx.message.author
		server  = ctx.message.server
		
		if not name:
			msg = 'Usage: `$hack "[hack name]"`'
			await self.bot.send_message(channel, msg)
			return

		linkList = self.settings.getServerStat(server, "Hacks")
		if not linkList or linkList == []:
			msg = 'No hacks in list!  You can add some with the `$addhack "[hack name]" [hack]` command!'
			await self.bot.send_message(channel, msg)
			return

		for alink in linkList:
			if alink['Name'].lower() == name.lower():
				msg = '**{}:**\n{}'.format(alink['Name'], alink['Hack'])
				await self.bot.send_message(channel, msg)
				return
				
		await self.bot.send_message(channel, 'Hack "*{}*" not found!'.format(name))

	@commands.command(pass_context=True)
	async def hackinfo(self, ctx, name : str = None):
		"""Displays info about a hack from the hack list."""

		channel = ctx.message.channel
		author  = ctx.message.author
		server  = ctx.message.server
		
		if not name:
			msg = 'Usage: `$hackinfo "[hack name]"`'
			await self.bot.send_message(channel, msg)
			return

		linkList = self.settings.getServerStat(server, "Hacks")
		if not linkList or linkList == []:
			msg = 'No hacks in list!  You can add some with the `$addhack "[hack name]" [hack]` command!'
			await self.bot.send_message(channel, msg)
			return

		for alink in linkList:
			if alink['Name'].lower() == name.lower():
				currentTime = int(time.time())
				msg = '**{}:**'.format(alink['Name'])
				try:
					memID = DisplayName.memberForID(alink['CreatedID'], server)
				except KeyError as e:
					memID = None
				if memID:
					msg = '{}\nCreated By: *{}*'.format(msg, DisplayName.name(memID))
				else:
					try:	
						msg = '{}\nCreated By: *{}*'.format(msg, alink['CreatedBy'])
					except KeyError as e:
						msg = '{}\nCreated By: `UNKNOWN`'.format(msg)
				try:
					createdTime = int(alink['Created'])
					timeString  = ReadableTime.getReadableTimeBetween(createdTime, currentTime)
					msg = '{}\nCreated : *{}* ago'.format(msg, timeString)
				except KeyError as e:
					pass
				try:
					msg = '{}\nUpdated By: *{}*'.format(msg, alink['UpdatedBy'])
				except KeyError as e:
					pass
				try:
					createdTime = alink['Updated']
					createdTime = int(createdTime)
					timeString  = ReadableTime.getReadableTimeBetween(createdTime, currentTime)
					msg = '{}\nUpdated : *{}* ago'.format(msg, timeString)
				except:
					pass
				await self.bot.send_message(channel, msg)
				return
				
		await self.bot.send_message(channel, 'Hack "*{}*" not found!'.format(name))


	@commands.command(pass_context=True)
	async def hacks(self, ctx):
		"""List all hacks in the hack list."""
		
		channel = ctx.message.channel
		author  = ctx.message.author
		server  = ctx.message.server
		
		linkList = self.settings.getServerStat(server, "Hacks")
		if not linkList or linkList == []:
			msg = 'No hacks in list!  You can add some with the `$addhack "[hack name]" [hack]` command!'
			await self.bot.send_message(channel, msg)
			return

		# Sort by link name
		linkList = sorted(linkList, key=itemgetter('Name'))
		linkText = "Current Hacks:\n\n"

		for alink in linkList:
			linkText = '{}*{}*, '.format(linkText, alink['Name'])

		# Speak the hack list while cutting off the end ", "
		await self.bot.send_message(channel, linkText[:-2])


	@commands.command(pass_context=True)
	async def hackrole(self, ctx):
		"""Lists the required role to add hacks."""
		role = self.settings.getServerStat(ctx.message.server, "RequiredHackRole")
		if role == None or role == "":
			msg = '**Only Admins** can add hacks.'.format(ctx)
			await self.bot.say(msg)
		else:
			# Role is set - let's get its name
			found = False
			for arole in ctx.message.server.roles:
				if arole.id == role:
					found = True
					msg = 'You need to be a/an **{}** to add hacks.'.format(arole.name)
			if not found:
				msg = 'There is no role that matches id: `{}` - consider updating this setting.'.format(role)
			await self.bot.send_message(ctx.message.channel, msg)
		
		
	@commands.command(pass_context=True)
	async def parts(self, ctx, member : discord.Member = None):
		"""Retrieve a member's parts list."""
		
		channel = ctx.message.channel
		author  = ctx.message.author
		server  = ctx.message.server
		
		if member == None:
			member = author

		if type(member) is str:
			try:
				member = discord.utils.get(server.members, name=member)
			except:
				print("That member does not exist")
				return

		parts = self.settings.getUserStat(member, server, "Parts")
		
		if not parts or parts == "":
			msg = '*{}* has not added their parts yet!  They can add them with the `$setparts "[parts text]"` command!'.format(DisplayName.name(member))
			await self.bot.send_message(channel, msg)
			return

		msg = '***{}\'s*** **Parts:**\n{}'.format(DisplayName.name(member), parts)
		await self.bot.send_message(channel, msg)
		
		
	@commands.command(pass_context=True)
	async def setparts(self, ctx, parts : str = None):
		"""Set your own parts - can be a url, formatted text, or nothing to clear."""
		
		channel = ctx.message.channel
		author  = ctx.message.author
		server  = ctx.message.server

		if not parts:
			parts = ""
			
		self.settings.setUserStat(author, server, "Parts", parts)
		msg = '*{}\'s* parts have been set to:\n{}'.format(DisplayName.name(author), parts)
		await self.bot.send_message(channel, msg)
		
		
	@commands.command(pass_context=True)
	async def partstemp(self, ctx):
		"""Gives a copy & paste style template for setting a parts list."""
		msg = '\$setparts \"\`\`\`      CPU : \n   Cooler : \n     MOBO : \n      GPU : \n      RAM : \n      SSD : \n      HDD : \n      PSU : \n     Case : \nWiFi + BT : \n Lighting : \n Keyboard : \n    Mouse : \n  Monitor : \n      DAC : \n Speakers : \`\`\`\"'	
		await self.bot.send_message(ctx.message.channel, msg)
		
	@commands.command(pass_context=True)
	async def online(self, ctx):
		"""Lists the number of users online."""
		server = ctx.message.server
		members = 0
		membersOnline = 0
		for member in server.members:
			members += 1
			if str(member.status).lower() == "online":
				membersOnline += 1
		msg = 'There are *{}* out of *{}* users online.'.format(membersOnline, members)
		await self.bot.send_message(ctx.message.channel, msg)


	@commands.command(pass_context=True)
	async def lastonline(self, ctx, member : discord.Member = None):
		"""Lists the last time a user was online if known."""

		author  = ctx.message.author
		server  = ctx.message.server
		channel = ctx.message.channel

		if not member:
			msg = 'Usage: `$lastonline "[member]"`'
			await self.bot.send_message(channel, msg)
			return

		if type(member) is str:
			try:
				member = discord.utils.get(server.members, name=member)
			except:
				print("That member does not exist")
				return
		name = DisplayName.name(member)

		# We have a member here
		if not str(member.status).lower() == "offline":
			msg = '*{}* is here right now.'.format(name)
		else:
			lastOnline = self.settings.getUserStat(member, server, "LastOnline")
			if lastOnline == "Unknown":
				self.settings.setUserStat(member, server, "LastOnline", None)
				lastOnline = None
			if lastOnline:
				currentTime = int(time.time())
				timeString  = ReadableTime.getReadableTimeBetween(int(lastOnline), currentTime)
				msg = 'The last time I saw *{}* was *{} ago*.'.format(name, timeString)
			else:
				msg = 'I don\'t know when *{}* was last online.  Sorry.'.format(name)

		await self.bot.send_message(ctx.message.channel, msg)

	@lastonline.error
	async def lastonline_error(self, ctx, error):
		# do stuff
		msg = 'lastonline Error: {}'.format(ctx)
		await self.bot.say(msg)