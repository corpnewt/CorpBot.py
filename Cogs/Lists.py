import asyncio
import discord
import time
from   discord.ext import commands
from   Cogs import Settings
from   Cogs import ReadableTime
from   Cogs import DisplayName
from   Cogs import Nullify
from   Cogs import FuzzySearch
from   Cogs import Message
from   Cogs import PickList

def setup(bot):
	# Add the bot and deps
	settings = bot.get_cog("Settings")
	bot.add_cog(Lists(bot, settings))

# This is the lists module.

class Lists:

	# Init with the bot reference, and a reference to the settings var
	def __init__(self, bot, settings):
		self.bot = bot
		self.settings = settings
		self.alt_lists = [ { 
			"command" : "hack",
			"list" : "Hacks"
		}, { 
			"command" : "link",
			"list" : "Links"
		}, { 
			"command" : "tag",
			"list" : "Tags"
		} ]
		
		
	'''async def onjoin(self, member, server):
		# Resolve our status based on the most occurances of UTCOffset
		newVal = self.settings.getGlobalUserStat(member, "Parts", server)
		self.settings.setUserStat(member, server, "Parts", newVal)'''

		
	@commands.command(pass_context=True)
	async def addlink(self, ctx, name : str = None, *, link : str = None):
		"""Add a link to the link list."""

		# Check if we're suppressing @here and @everyone mentions
		if self.settings.getServerStat(ctx.message.guild, "SuppressMentions"):
			suppress = True
		else:
			suppress = False
		
		channel = ctx.message.channel
		author  = ctx.message.author
		server  = ctx.message.guild
		
		# Check for role requirements
		requiredRole = self.settings.getServerStat(server, "RequiredLinkRole")
		if requiredRole == "":
			#admin only
			isAdmin = author.permissions_in(channel).administrator
			if not isAdmin:
				await channel.send('You do not have sufficient privileges to access this command.')
				return
		else:
			#role requirement
			hasPerms = False
			for role in author.roles:
				if str(role.id) == str(requiredRole):
					hasPerms = True
			if not hasPerms and not ctx.message.author.permissions_in(ctx.message.channel).administrator:
				await channel.send('You do not have sufficient privileges to access this command.')
				return
				
		# Passed role requirements!
		if name == None or link == None:
			msg = 'Usage: `{}addlink "[link name]" [url]`'.format(ctx.prefix)
			await channel.send(msg)
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
		# Check for suppress
		if suppress:
			msg = Nullify.clean(msg)
		await channel.send(msg)
		
		
	@commands.command(pass_context=True)
	async def removelink(self, ctx, *, name : str = None):
		"""Remove a link from the link list."""
		
		channel = ctx.message.channel
		author  = ctx.message.author
		server  = ctx.message.guild

		# Check if we're suppressing @here and @everyone mentions
		if self.settings.getServerStat(ctx.message.guild, "SuppressMentions"):
			suppress = True
		else:
			suppress = False
		
		# Check for role requirements
		requiredRole = self.settings.getServerStat(server, "RequiredLinkRole")
		if requiredRole == "":
			#admin only
			isAdmin = author.permissions_in(channel).administrator
			if not isAdmin:
				await channel.send('You do not have sufficient privileges to access this command.')
				return
		else:
			#role requirement
			hasPerms = False
			for role in author.roles:
				if str(role.id) == str(requiredRole):
					hasPerms = True
			if not hasPerms and not ctx.message.author.permissions_in(ctx.message.channel).administrator:
				await channel.send('You do not have sufficient privileges to access this command.')
				return
		
		if name == None:
			msg = 'Usage: `{}removelink "[link name]"`'.format(ctx.prefix)
			await channel.send(msg)
			return

		linkList = self.settings.getServerStat(server, "Links")
		if not linkList or linkList == []:
			msg = 'No links in list!  You can add some with the `{}addlink "[link name]" [url]` command!'.format(ctx.prefix)
			await channel.send(msg)
			return

		for alink in linkList:
			if alink['Name'].lower() == name.lower():
				linkList.remove(alink)
				self.settings.setServerStat(server, "Links", linkList)
				msg = '*{}* removed from link list!'.format(alink['Name'])
				# Check for suppress
				if suppress:
					msg = Nullify.clean(msg)
				await channel.send(msg)
				return

		msg = '*{}* not found in link list!'.format(name)
		# Check for suppress
		if suppress:
			msg = Nullify.clean(msg)
		await channel.send(msg)


	@commands.command(pass_context=True)
	async def link(self, ctx, *, name : str = None):
		"""Retrieve a link from the link list."""
		
		our_list = "Links"
		
		channel = ctx.message.channel
		author  = ctx.message.author
		server  = ctx.message.guild

		# Check if we're suppressing @here and @everyone mentions
		if self.settings.getServerStat(ctx.message.guild, "SuppressMentions"):
			suppress = True
		else:
			suppress = False
		
		if not name:
			msg = 'Usage: `{}link "[link name]"`'.format(ctx.prefix)
			await channel.send(msg)
			return

		linkList = self.settings.getServerStat(server, our_list)
		# Check others
		other_commands = []
		other_names    = []
		for i in self.alt_lists:
			if i["list"] == our_list:
				# Our list - skip
				continue
			check_list = self.settings.getServerStat(server, i["list"])
			if any(x["Name"].lower() == name.lower() for x in check_list):
				# Add the list
				other_commands.append(i)
				other_names.append(ctx.prefix + i["command"] + " " + name.replace('`', ''))
				
		if not linkList or linkList == []:
			no_links = 'No links in list!  You can add some with the `{}addlink "[link name]" [url]` command!'.format(ctx.prefix)
			if not len(other_commands):
				# No other matches
				await ctx.send(no_links)
				return
			msg = no_links + "\n\nMaybe you meant:"
			index, message = await PickList.Picker(
				title=msg,
				list=other_names,
				ctx=ctx
			).pick()
			# Check if we errored/cancelled
			if index < 0:
				await message.edit(content=no_links)
				return
			# Got something
			await message.edit(content="`{}`".format(other_names[index]))
			# Invoke
			await ctx.invoke(self.bot.all_commands.get(other_commands[index]["command"]), name=name)
			return

		for alink in linkList:
			if alink['Name'].lower() == name.lower():
				msg = '**{}:**\n{}'.format(alink['Name'], alink['URL'])
				# Check for suppress
				if suppress:
					msg = Nullify.clean(msg)
				await channel.send(msg)
				return
				
		not_found = 'Link `{}` not found!'.format(name.replace('`', '\\`'))
		# No tag - let's fuzzy search
		potentialList = FuzzySearch.search(name, linkList, 'Name')
		if len(potentialList):
			# Setup and display the picker
			msg = not_found + '\n\nSelect one of the following close matches:'
			p_list = [x["Item"]["Name"] for x in potentialList]
			p_list.extend(other_names)
			index, message = await PickList.Picker(
				title=msg,
				list=p_list,
				ctx=ctx
			).pick()
			# Check if we errored/cancelled
			if index < 0:
				await message.edit(content=not_found)
				return
			# Check if we have another command
			if index >= len(potentialList):
				# We're into our other list
				await message.edit(content="`{}`".format(other_names[index - len(potentialList)]))
				# Invoke
				await ctx.invoke(self.bot.all_commands.get(other_commands[index - len(potentialList)]["command"]), name=name)
				return
			# Display the link
			for alink in linkList:
				if alink["Name"] == potentialList[index]["Item"]["Name"]:
					msg = '**{}:**\n{}'.format(alink['Name'], alink['URL'])
					# Check for suppress
					if suppress:
						msg = Nullify.clean(msg)
					await message.edit(content=msg)
					return
			await message.edit(content="Link `{}` no longer exists!".format(
				potentialList[index]["Item"]["Name"].replace('`', '\\`'))
			)
			return
		# Here we have no potentials
		await ctx.send(not_found)
		return
		
	@commands.command(pass_context=True)
	async def rawlink(self, ctx, *, name : str = None):
		"""Retrieve a link's raw markdown from the link list."""
		
		channel = ctx.message.channel
		author  = ctx.message.author
		server  = ctx.message.guild

		# Check if we're suppressing @here and @everyone mentions
		if self.settings.getServerStat(ctx.message.guild, "SuppressMentions"):
			suppress = True
		else:
			suppress = False
		
		if not name:
			msg = 'Usage: `{}rawlink "[link name]"`'.format(ctx.prefix)
			await channel.send(msg)
			return

		linkList = self.settings.getServerStat(server, "Links")
		if not linkList or linkList == []:
			msg = 'No links in list!  You can add some with the `{}addlink "[link name]" [url]` command!'.format(ctx.prefix)
			await channel.send(msg)
			return

		for alink in linkList:
			if alink['Name'].lower() == name.lower():
				msg = '**{}:**\n{}'.format(alink['Name'], alink['URL'].replace('\\', '\\\\').replace('*', '\\*').replace('`', '\\`').replace('_', '\\_'))
				# Check for suppress
				if suppress:
					msg = Nullify.clean(msg)
				await channel.send(msg)
				return
				
		not_found = 'Link `{}` not found!'.format(name.replace('`', '\\`'))
		# No tag - let's fuzzy search
		potentialList = FuzzySearch.search(name, linkList, 'Name')
		if len(potentialList):
			# Setup and display the picker
			msg = not_found + '\n\nSelect one of the following close matches:'
			index, message = await PickList.Picker(
				title=msg,
				list=[x["Item"]["Name"] for x in potentialList],
				ctx=ctx
			).pick()
			# Check if we errored/cancelled
			if index < 0:
				await message.edit(content=not_found)
				return
			# Display the link
			for alink in linkList:
				if alink["Name"] == potentialList[index]["Item"]["Name"]:
					msg = '**{}:**\n{}'.format(alink['Name'], alink['URL'].replace('\\', '\\\\').replace('*', '\\*').replace('`', '\\`').replace('_', '\\_'))
					# Check for suppress
					if suppress:
						msg = Nullify.clean(msg)
					await message.edit(content=msg)
					return
			await message.edit(content="Link `{}` no longer exists!".format(
				potentialList[index]["Item"]["Name"].replace('`', '\\`'))
			)
			return
		# Here we have no potentials
		await ctx.send(not_found)
		return

	@commands.command(pass_context=True)
	async def linkinfo(self, ctx, *, name : str = None):
		"""Displays info about a link from the link list."""

		channel = ctx.message.channel
		author  = ctx.message.author
		server  = ctx.message.guild

		# Check if we're suppressing @here and @everyone mentions
		if self.settings.getServerStat(ctx.message.guild, "SuppressMentions"):
			suppress = True
		else:
			suppress = False
		
		if not name:
			msg = 'Usage: `{}linkinfo "[link name]"`'.format(ctx.prefix)
			await channel.send(msg)
			return

		linkList = self.settings.getServerStat(server, "Links")
		if not linkList or linkList == []:
			msg = 'No links in list!  You can add some with the `{}addlink "[link name]" [url]` command!'.format(ctx.prefix)
			await channel.send(msg)
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
				# Check for suppress
				if suppress:
					msg = Nullify.clean(msg)
				await channel.send(msg)
				return
				
		msg = 'Link "*{}*" not found!'.format(name)
		# Check for suppress
		if suppress:
			msg = Nullify.clean(msg)
		await channel.send(msg)

	@commands.command(pass_context=True)
	async def links(self, ctx):
		"""List all links in the link list."""
		
		channel = ctx.message.channel
		author  = ctx.message.author
		server  = ctx.message.guild

		# Check if we're suppressing @here and @everyone mentions
		if self.settings.getServerStat(ctx.message.guild, "SuppressMentions"):
			suppress = True
		else:
			suppress = False

		argList = ctx.message.content.split()

		if len(argList) > 1:
			extraArgs = ' '.join(argList[1:len(argList)])
			# We have a random attempt at a passed variable - Thanks Sydney!
			# Invoke this command again with the right name
			await ctx.invoke(self.link, name=extraArgs)
			return
		
		linkList = self.settings.getServerStat(server, "Links")
		if linkList == None or linkList == []:
			msg = 'No links in list!  You can add some with the `{}addlink "[link name]" [url]` command!'.format(ctx.prefix)
			await channel.send(msg)
			return
			
		# Sort by link name
		sep = "\n"
		linkList = sorted(linkList, key=lambda x:x['Name'].lower())
		linkText = "Current Links:\n\n"
		for alink in linkList:
			linkText = '{}*{}*{}'.format(linkText, alink['Name'], sep)

		# Speak the link list while cutting off the end ", "
		# Check for suppress
		if suppress:
			linkText = Nullify.clean(linkText)
		await Message.Message(message=linkText[:-len(sep)]).send(ctx)
		
		
	@commands.command(pass_context=True)
	async def rawlinks(self, ctx):
		"""List raw markdown of all links in the link list."""
		
		channel = ctx.message.channel
		author  = ctx.message.author
		server  = ctx.message.guild

		# Check if we're suppressing @here and @everyone mentions
		if self.settings.getServerStat(ctx.message.guild, "SuppressMentions"):
			suppress = True
		else:
			suppress = False

		argList = ctx.message.content.split()

		if len(argList) > 1:
			extraArgs = ' '.join(argList[1:len(argList)])
			# We have a random attempt at a passed variable - Thanks Sydney!
			extraArgs = extraArgs.replace('`', '\\`')
			msg = 'You passed `{}` to this command - are you sure you didn\'t mean `{}link {}`?'.format(extraArgs, ctx.prefix, extraArgs)
			# Check for suppress
			if suppress:
				msg = Nullify.clean(msg)
			await channel.send(msg)
			return
		
		linkList = self.settings.getServerStat(server, "Links")
		if linkList == None or linkList == []:
			msg = 'No links in list!  You can add some with the `{}addlink "[link name]" [url]` command!'.format(ctx.prefix)
			await channel.send(msg)
			return
			
		# Sort by link name
		linkList = sorted(linkList, key=lambda x:x['Name'].lower())
		linkText = "Current Links:\n\n"
		for alink in linkList:
			linkText += '`{}`, '.format(alink['Name'].replace('`', '\\`'))

		# Speak the link list while cutting off the end ", "
		# Check for suppress
		if suppress:
			linkText = Nullify.clean(linkText)
		await Message.Message(message=linkText[:-2]).send(ctx)


	@commands.command(pass_context=True)
	async def linkrole(self, ctx):
		"""Lists the required role to add links."""

		# Check if we're suppressing @here and @everyone mentions
		if self.settings.getServerStat(ctx.message.guild, "SuppressMentions"):
			suppress = True
		else:
			suppress = False

		role = self.settings.getServerStat(ctx.message.guild, "RequiredLinkRole")
		if role == None or role == "":
			msg = '**Only Admins** can add links.'.format(ctx)
			await ctx.channel.send(msg)
		else:
			# Role is set - let's get its name
			found = False
			for arole in ctx.message.guild.roles:
				if str(arole.id) == str(role):
					found = True
					vowels = "aeiou"
					if arole.name[:1].lower() in vowels:
						msg = 'You need to be an **{}** to add links.'.format(arole.name)
					else:
						msg = 'You need to be a **{}** to add links.'.format(arole.name)
			if not found:
				msg = 'There is no role that matches id: `{}` - consider updating this setting.'.format(role)
			# Check for suppress
			if suppress:
				msg = Nullify.clean(msg)
			await ctx.channel.send(msg)
		
		
	@commands.command(pass_context=True)
	async def addhack(self, ctx, name : str = None, *, hack : str = None):
		"""Add a hack to the hack list."""
		
		channel = ctx.message.channel
		author  = ctx.message.author
		server  = ctx.message.guild

		# Check if we're suppressing @here and @everyone mentions
		if self.settings.getServerStat(ctx.message.guild, "SuppressMentions"):
			suppress = True
		else:
			suppress = False
		
		# Check for role requirements
		requiredRole = self.settings.getServerStat(server, "RequiredHackRole")
		if requiredRole == "":
			#admin only
			isAdmin = author.permissions_in(channel).administrator
			if not isAdmin:
				await channel.send('You do not have sufficient privileges to access this command.')
				return
		else:
			#role requirement
			hasPerms = False
			for role in author.roles:
				if str(role.id) == str(requiredRole):
					hasPerms = True
			if not hasPerms and not ctx.message.author.permissions_in(ctx.message.channel).administrator:
				await channel.send('You do not have sufficient privileges to access this command.')
				return
				
		# Passed role requirements!
		if name == None or hack == None:
			msg = 'Usage: `{}addhack "[hack name]" [hack]`'.format(ctx.prefix)
			await channel.send(msg)
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
			msg = '*{}* added to hack list!'.format(name)
		
		self.settings.setServerStat(server, "Hacks", hackList)
		# Check for suppress
		if suppress:
			msg = Nullify.clean(msg)
		await channel.send(msg)

		
		
	@commands.command(pass_context=True)
	async def removehack(self, ctx, *, name : str = None):
		"""Remove a hack from the hack list."""
		
		channel = ctx.message.channel
		author  = ctx.message.author
		server  = ctx.message.guild

		# Check if we're suppressing @here and @everyone mentions
		if self.settings.getServerStat(ctx.message.guild, "SuppressMentions"):
			suppress = True
		else:
			suppress = False
		
		# Check for role requirements
		requiredRole = self.settings.getServerStat(server, "RequiredHackRole")
		if requiredRole == "":
			#admin only
			isAdmin = author.permissions_in(channel).administrator
			if not isAdmin:
				await channel.send('You do not have sufficient privileges to access this command.')
				return
		else:
			#role requirement
			hasPerms = False
			for role in author.roles:
				if str(role.id) == str(requiredRole):
					hasPerms = True
			if not hasPerms and not ctx.message.author.permissions_in(ctx.message.channel).administrator:
				await channel.send('You do not have sufficient privileges to access this command.')
				return
		
		if name == None:
			msg = 'Usage: `{}removehack "[hack name]"`'.format(ctx.prefix)
			await channel.send(msg)
			return

		linkList = self.settings.getServerStat(server, "Hacks")
		if not linkList or linkList == []:
			msg = 'No hacks in list!  You can add some with the `{}addhack "[hack name]" [hack]` command!'.format(ctx.prefix)
			await channel.send(msg)
			return

		for alink in linkList:
			if alink['Name'].lower() == name.lower():
				linkList.remove(alink)
				self.settings.setServerStat(server, "Hacks", linkList)
				msg = '*{}* removed from hack list!'.format(alink['Name'])
				# Check for suppress
				if suppress:
					msg = Nullify.clean(msg)
				await ctx.channel.send(msg)
				return

		msg = '*{}* not found in hack list!'.format(name)
		# Check for suppress
		if suppress:
			msg = Nullify.clean(msg)
		await channel.send(msg)


	@commands.command(pass_context=True)
	async def hack(self, ctx, *, name : str = None):
		"""Retrieve a hack from the hack list."""
		
		our_list = "Hacks"
		
		channel = ctx.message.channel
		author  = ctx.message.author
		server  = ctx.message.guild

		# Check if we're suppressing @here and @everyone mentions
		if self.settings.getServerStat(ctx.message.guild, "SuppressMentions"):
			suppress = True
		else:
			suppress = False
		
		if not name:
			msg = 'Usage: `{}hack "[hack name]"`'.format(ctx.prefix)
			await channel.send(msg)
			return

		linkList = self.settings.getServerStat(server, "Hacks")
		# Check others
		other_commands = []
		other_names    = []
		for i in self.alt_lists:
			if i["list"] == our_list:
				# Our list - skip
				continue
			check_list = self.settings.getServerStat(server, i["list"])
			if any(x["Name"].lower() == name.lower() for x in check_list):
				# Add the list
				other_commands.append(i)
				other_names.append(ctx.prefix + i["command"] + " " + name.replace('`', ''))
				
		if not linkList or linkList == []:
			no_links = 'No hacks in list!  You can add some with the `{}addhack "[hack name]" [hack]` command!'.format(ctx.prefix)
			if not len(other_commands):
				# No other matches
				await ctx.send(no_links)
				return
			msg = no_links + "\n\nMaybe you meant:"
			index, message = await PickList.Picker(
				title=msg,
				list=other_names,
				ctx=ctx
			).pick()
			# Check if we errored/cancelled
			if index < 0:
				await message.edit(content=no_links)
				return
			# Got something
			await message.edit(content="`{}`".format(other_names[index]))
			# Invoke
			await ctx.invoke(self.bot.all_commands.get(other_commands[index]["command"]), name=name)
			return

		for alink in linkList:
			if alink['Name'].lower() == name.lower():
				msg = '**{}:**\n{}'.format(alink['Name'], alink['Hack'])
				# Check for suppress
				if suppress:
					msg = Nullify.clean(msg)
				await channel.send(msg)
				return
		
		not_found = 'Hack `{}` not found!'.format(name.replace('`', '\\`'))
		# No tag - let's fuzzy search
		potentialList = FuzzySearch.search(name, linkList, 'Name')
		if len(potentialList):
			# Setup and display the picker
			msg = not_found + '\n\nSelect one of the following close matches:'
			p_list = [x["Item"]["Name"] for x in potentialList]
			p_list.extend(other_names)
			index, message = await PickList.Picker(
				title=msg,
				list=p_list,
				ctx=ctx
			).pick()
			# Check if we errored/cancelled
			if index < 0:
				await message.edit(content=not_found)
				return
			# Check if we have another command
			if index >= len(potentialList):
				# We're into our other list
				await message.edit(content="`{}`".format(other_names[index - len(potentialList)]))
				# Invoke
				await ctx.invoke(self.bot.all_commands.get(other_commands[index - len(potentialList)]["command"]), name=name)
				return
			# Display the link
			for alink in linkList:
				if alink["Name"] == potentialList[index]["Item"]["Name"]:
					msg = '**{}:**\n{}'.format(alink['Name'], alink['Hack'])
					# Check for suppress
					if suppress:
						msg = Nullify.clean(msg)
					await message.edit(content=msg)
					return
			await message.edit(content="Hack `{}` no longer exists!".format(
				potentialList[index]["Item"]["Name"].replace('`', '\\`'))
			)
			return
		# Here we have no potentials
		await ctx.send(not_found)
		return
		
	@commands.command(pass_context=True)
	async def rawhack(self, ctx, *, name : str = None):
		"""Retrieve a hack's raw markdown from the hack list."""
		
		channel = ctx.message.channel
		author  = ctx.message.author
		server  = ctx.message.guild

		# Check if we're suppressing @here and @everyone mentions
		if self.settings.getServerStat(ctx.message.guild, "SuppressMentions"):
			suppress = True
		else:
			suppress = False
		
		if not name:
			msg = 'Usage: `{}rawhack "[hack name]"`'.format(ctx.prefix)
			await channel.send(msg)
			return

		linkList = self.settings.getServerStat(server, "Hacks")
		if not linkList or linkList == []:
			msg = 'No hacks in list!  You can add some with the `{}addhack "[hack name]" [hack]` command!'.format(ctx.prefix)
			await channel.send(msg)
			return

		for alink in linkList:
			if alink['Name'].lower() == name.lower():
				msg = '**{}:**\n{}'.format(alink['Name'], alink['Hack'].replace('\\', '\\\\').replace('*', '\\*').replace('`', '\\`').replace('_', '\\_'))
				# Check for suppress
				if suppress:
					msg = Nullify.clean(msg)
				await channel.send(msg)
				return
		
		not_found = 'Hack `{}` not found!'.format(name.replace('`', '\\`'))
		# No tag - let's fuzzy search
		potentialList = FuzzySearch.search(name, linkList, 'Name')
		if len(potentialList):
			# Setup and display the picker
			msg = not_found + '\n\nSelect one of the following close matches:'
			index, message = await PickList.Picker(
				title=msg,
				list=[x["Item"]["Name"] for x in potentialList],
				ctx=ctx
			).pick()
			# Check if we errored/cancelled
			if index < 0:
				await message.edit(content=not_found)
				return
			# Display the link
			for alink in linkList:
				if alink["Name"] == potentialList[index]["Item"]["Name"]:
					msg = '**{}:**\n{}'.format(alink['Name'], alink['Hack'].replace('\\', '\\\\').replace('*', '\\*').replace('`', '\\`').replace('_', '\\_'))
					# Check for suppress
					if suppress:
						msg = Nullify.clean(msg)
					await message.edit(content=msg)
					return
			await message.edit(content="Hack `{}` no longer exists!".format(
				potentialList[index]["Item"]["Name"].replace('`', '\\`'))
			)
			return
		# Here we have no potentials
		await ctx.send(not_found)
		return

	@commands.command(pass_context=True)
	async def hackinfo(self, ctx, *, name : str = None):
		"""Displays info about a hack from the hack list."""

		channel = ctx.message.channel
		author  = ctx.message.author
		server  = ctx.message.guild

		# Check if we're suppressing @here and @everyone mentions
		if self.settings.getServerStat(ctx.message.guild, "SuppressMentions"):
			suppress = True
		else:
			suppress = False
		
		if not name:
			msg = 'Usage: `{}hackinfo "[hack name]"`'.format(ctx.prefix)
			await channel.send(msg)
			return

		linkList = self.settings.getServerStat(server, "Hacks")
		if not linkList or linkList == []:
			msg = 'No hacks in list!  You can add some with the `{}addhack "[hack name]" [hack]` command!'.format(ctx.prefix)
			await channel.send(msg)
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
				# Check for suppress
				if suppress:
					msg = Nullify.clean(msg)
				await channel.send(msg)
				return
		msg = 'Hack "*{}*" not found!'.format(name)
		# Check for suppress
		if suppress:
			msg = Nullify.clean(msg)	
		await channel.send(msg)


	@commands.command(pass_context=True)
	async def hacks(self, ctx):
		"""List all hacks in the hack list."""
		
		channel = ctx.message.channel
		author  = ctx.message.author
		server  = ctx.message.guild

		# Check if we're suppressing @here and @everyone mentions
		if self.settings.getServerStat(ctx.message.guild, "SuppressMentions"):
			suppress = True
		else:
			suppress = False
		
		argList = ctx.message.content.split()

		if len(argList) > 1:
			extraArgs = ' '.join(argList[1:len(argList)])
			# We have a random attempt at a passed variable - Thanks Sydney!
			# Invoke this command again with the right name
			await ctx.invoke(self.hack, name=extraArgs)
			return

		linkList = self.settings.getServerStat(server, "Hacks")
		if not linkList or linkList == []:
			msg = 'No hacks in list!  You can add some with the `{}addhack "[hack name]" [hack]` command!'.format(ctx.prefix)
			await channel.send(msg)
			return

		# Sort by link name
		sep = "\n"
		linkList = sorted(linkList, key=lambda x:x['Name'].lower())
		linkText = "Current Hacks:\n\n"

		for alink in linkList:
			linkText = '{}*{}*{}'.format(linkText, alink['Name'], sep)

		# Speak the hack list while cutting off the end ", "
		# Check for suppress
		if suppress:
			linkText = Nullify.clean(linkText)
		await Message.Message(message=linkText[:-len(sep)]).send(ctx)
		
		
	@commands.command(pass_context=True)
	async def rawhacks(self, ctx):
		"""List raw markdown of all hacks in the hack list."""
		
		channel = ctx.message.channel
		author  = ctx.message.author
		server  = ctx.message.guild

		# Check if we're suppressing @here and @everyone mentions
		if self.settings.getServerStat(ctx.message.guild, "SuppressMentions"):
			suppress = True
		else:
			suppress = False
		
		argList = ctx.message.content.split()

		if len(argList) > 1:
			extraArgs = ' '.join(argList[1:len(argList)])
			# We have a random attempt at a passed variable - Thanks Sydney!
			extraArgs = extraArgs.replace('`', '\\`')
			msg = 'You passed `{}` to this command - are you sure you didn\'t mean `{}hack {}`?'.format(extraArgs, ctx.prefix, extraArgs)
			# Check for suppress
			if suppress:
				msg = Nullify.clean(msg)
			await channel.send(msg)
			return

		linkList = self.settings.getServerStat(server, "Hacks")
		if not linkList or linkList == []:
			msg = 'No hacks in list!  You can add some with the `{}addhack "[hack name]" [hack]` command!'.format(ctx.prefix)
			await channel.send(msg)
			return

		# Sort by link name
		linkList = sorted(linkList, key=lambda x:x['Name'].lower())
		linkText = "Current Hacks:\n\n"

		for alink in linkList:
			linkText += '`{}`, '.format(alink['Name'].replace('`', '\\`'))

		# Speak the hack list while cutting off the end ", "
		# Check for suppress
		if suppress:
			linkText = Nullify.clean(linkText)
		await Message.Message(message=linkText[:-2]).send(ctx)


	@commands.command(pass_context=True)
	async def hackrole(self, ctx):
		"""Lists the required role to add hacks."""

		# Check if we're suppressing @here and @everyone mentions
		if self.settings.getServerStat(ctx.message.guild, "SuppressMentions"):
			suppress = True
		else:
			suppress = False

		role = self.settings.getServerStat(ctx.message.guild, "RequiredHackRole")
		if role == None or role == "":
			msg = '**Only Admins** can add hacks.'.format(ctx)
			await ctx.channel.send(msg)
		else:
			# Role is set - let's get its name
			found = False
			for arole in ctx.message.guild.roles:
				if str(arole.id) == str(role):
					found = True
					vowels = "aeiou"
					if arole.name[:1].lower() in vowels:
						msg = 'You need to be an **{}** to add hacks.'.format(arole.name)
					else:
						msg = 'You need to be a **{}** to add hacks.'.format(arole.name)
			if not found:
				msg = 'There is no role that matches id: `{}` - consider updating this setting.'.format(role)
			# Check for suppress
			if suppress:
				msg = Nullify.clean(msg)
			await ctx.channel.send(msg)
		
		
	@commands.command(pass_context=True)
	async def parts(self, ctx, *, member = None):
		"""Retrieve a member's parts list. DEPRECATED - Use hw instead."""
		
		channel = ctx.message.channel
		author  = ctx.message.author
		server  = ctx.message.guild

		# Check if we're suppressing @here and @everyone mentions
		if self.settings.getServerStat(ctx.message.guild, "SuppressMentions"):
			suppress = True
		else:
			suppress = False
		
		if member is None:
			member = ctx.message.author
			
		if type(member) is str:
			memberName = member
			member = DisplayName.memberForName(memberName, ctx.message.guild)
			if not member:
				msg = 'I couldn\'t find *{}*...'.format(memberName)
				# Check for suppress
				if suppress:
					msg = Nullify.clean(msg)
				await ctx.channel.send(msg)
				return

		parts = self.settings.getGlobalUserStat(member, "Parts")
		
		if not parts or parts == "":
			msg = '*{}* has not added their parts yet!  ~~They can add them with the `{}setparts [parts text]` command!~~ DEPRECATED - Use `{}newhw` instead.'.format(DisplayName.name(member), ctx.prefix, ctx.prefix)
			await channel.send(msg)
			return

		msg = '***{}\'s*** **Parts (DEPRECATED - Use {}hw instead):**\n\n{}'.format(DisplayName.name(member), ctx.prefix, parts)
		# Check for suppress
		if suppress:
			msg = Nullify.clean(msg)
		await channel.send(msg)

	@parts.error
	async def parts_error(self, ctx, error):
		# do stuff
		msg = 'parts Error: {}'.format(ctx)
		await error.channel.send(msg)


	@commands.command(pass_context=True)
	async def rawparts(self, ctx, *, member = None):
		"""Retrieve the raw markdown for a member's parts list. DEPRECATED - Use rawhw instead."""
		
		channel = ctx.message.channel
		author  = ctx.message.author
		server  = ctx.message.guild

		# Check if we're suppressing @here and @everyone mentions
		if self.settings.getServerStat(ctx.message.guild, "SuppressMentions"):
			suppress = True
		else:
			suppress = False
		
		if member is None:
			member = ctx.message.author
			
		if type(member) is str:
			memberName = member
			member = DisplayName.memberForName(memberName, ctx.message.guild)
			if not member:
				msg = 'I couldn\'t find *{}*...'.format(memberName)
				# Check for suppress
				if suppress:
					msg = Nullify.clean(msg)
				await ctx.channel.send(msg)
				return

		parts = self.settings.getGlobalUserStat(member, "Parts")
		
		if not parts or parts == "":
			msg = '*{}* has not added their parts yet!  ~~They can add them with the `{}setparts [parts text]` command!~~ DEPRECATED - Use `{}newhw` instead.'.format(DisplayName.name(member), ctx.prefix, ctx.prefix)
			await channel.send(msg)
			return

		p = parts.replace('\\', '\\\\')
		p = p.replace('*', '\\*')
		p = p.replace('`', '\\`')
		p = p.replace('_', '\\_')

		msg = '***{}\'s*** **Parts (DEPRECATED - Use {}hw instead):**\n\n{}'.format(DisplayName.name(member), ctx.prefix, p)
		# Check for suppress
		if suppress:
			msg = Nullify.clean(msg)
		await channel.send(msg)

	@parts.error
	async def parts_error(self, ctx, error):
		# do stuff
		msg = 'parts Error: {}'.format(ctx)
		await error.channel.send(msg)
		
		
	@commands.command(pass_context=True)
	async def setparts(self, ctx, *, parts : str = None):
		"""Set your own parts - can be a url, formatted text, or nothing to clear. DEPRECATED - Use newhw instead."""
		
		channel = ctx.message.channel
		author  = ctx.message.author
		server  = ctx.message.guild

		# Check if we're suppressing @here and @everyone mentions
		if self.settings.getServerStat(ctx.message.guild, "SuppressMentions"):
			suppress = True
		else:
			suppress = False

		if not parts:
			parts = ""
			
		self.settings.setGlobalUserStat(author, "Parts", parts)
		msg = '*{}\'s* parts have been set to (DEPRECATED - Use {}newhw instead):\n{}'.format(DisplayName.name(author), ctx.prefix, parts)
		# Check for suppress
		if suppress:
			msg = Nullify.clean(msg)
		await channel.send(msg)
		
		
	@commands.command(pass_context=True)
	async def partstemp(self, ctx):
		"""Gives a copy & paste style template for setting a parts list."""
		msg = '\{}setparts \`\`\`      CPU : \n   Cooler : \n     MOBO : \n      GPU : \n      RAM : \n      SSD : \n      HDD : \n      PSU : \n     Case : \nWiFi + BT : \n Lighting : \n Keyboard : \n    Mouse : \n  Monitor : \n      DAC : \n Speakers : \`\`\`'.format(ctx.prefix)	
		await ctx.channel.send(msg)
		
	@commands.command(pass_context=True)
	async def online(self, ctx):
		"""Lists the number of users online."""
		server = ctx.message.guild
		members = membersOnline = bots = botsOnline = 0
		for member in server.members:
			if member.bot:
				bots += 1
				if not member.status == discord.Status.offline:
					botsOnline += 1
			else:
				members += 1
				if not member.status == discord.Status.offline:
					membersOnline += 1
		await Message.Embed(
			title="Member Stats",
			description="Current member information for {}".format(server.name),
			fields=[
				{ "name" : "Members", "value" : "└─ {:,}/{:,} online ({:,g}%)".format(membersOnline, members, round((membersOnline/members)*100, 2)), "inline" : False},
				{ "name" : "Bots", "value" : "└─ {:,}/{:,} online ({:,g}%)".format(botsOnline, bots, round((botsOnline/bots)*100, 2)), "inline" : False},
				{ "name" : "Total", "value" : "└─ {:,}/{:,} online ({:,g}%)".format(membersOnline + botsOnline, len(server.members), round(((membersOnline + botsOnline)/len(server.members))*100, 2)), "inline" : False}
			],
			color=ctx.message.author).send(ctx)
		#msg = 'There are *{:,}* out of *{:,}* (*{:.2f}%*) users online.'.format(membersOnline, members, (membersOnline/members)*100)
		#await ctx.channel.send(msg)


	@commands.command(pass_context=True)
	async def lastonline(self, ctx, *, member = None):
		"""Lists the last time a user was online if known."""

		author  = ctx.message.author
		server  = ctx.message.guild
		channel = ctx.message.channel

		# Check if we're suppressing @here and @everyone mentions
		if self.settings.getServerStat(ctx.message.guild, "SuppressMentions"):
			suppress = True
		else:
			suppress = False

		if not member:
			msg = 'Usage: `{}lastonline "[member]"`'.format(ctx.prefix)
			await channel.send(msg)
			return

		if type(member) is str:
			memberName = member
			member = DisplayName.memberForName(memberName, ctx.message.guild)
			if not member:
				msg = 'I couldn\'t find *{}*...'.format(memberName)
				# Check for suppress
				if suppress:
					msg = Nullify.clean(msg)
				await ctx.channel.send(msg)
				return
		name = DisplayName.name(member)

		# We have a member here
		if not member.status == discord.Status.offline:
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

		await ctx.channel.send(msg)

	@lastonline.error
	async def lastonline_error(self, ctx, error):
		# do stuff
		msg = 'lastonline Error: {}'.format(ctx)
		await error.channel.send(msg)
