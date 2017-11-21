import asyncio
import discord
import time
import os
from   discord.ext import commands
from   datetime import datetime
from   operator import itemgetter
from   Cogs import Settings
from   Cogs import ReadableTime
from   Cogs import DisplayName
from   Cogs import Nullify

def setup(bot):
	# Add the bot and deps
	settings = bot.get_cog("Settings")
	bot.add_cog(Channel(bot, settings))

# This is the admin module.  It holds the admin-only commands
# Everything here *requires* that you're an admin

class Channel:

	# Init with the bot reference, and a reference to the settings var
	def __init__(self, bot, settings):
		self.bot = bot
		self.settings = settings

	def suppressed(self, guild, msg):
		# Check if we're suppressing @here and @everyone mentions
		if self.settings.getServerStat(guild, "SuppressMentions"):
			return Nullify.clean(msg)
		else:
			return msg

	async def member_update(self, before, after):
		server = after.guild

		# Check if the member went offline and log the time
		if after.status == discord.Status.offline:
			currentTime = int(time.time())
			self.settings.setUserStat(after, server, "LastOnline", currentTime)


		# Removed due to spam
		'''self.settings.checkServer(server)
		try:
			channelMOTDList = self.settings.getServerStat(server, "ChannelMOTD")
		except KeyError:
			channelMOTDList = {}

		if len(channelMOTDList) > 0:
			members = 0
			membersOnline = 0
			for member in server.members:
				members += 1
				if not member.status == discord.Status.offline:
					membersOnline += 1

		for id in channelMOTDList:
			channel = self.bot.get_channel(int(id))
			if channel:
				# Got our channel - let's update
				motd = channelMOTDList[id]['MOTD'] # A markdown message of the day
				listOnline = channelMOTDList[id]['ListOnline'] # Yes/No - do we list all online members or not?
				if listOnline:
					if members == 1:
						msg = '{} - ({:,}/{:,} user online)'.format(motd, int(membersOnline), int(members))
					else:
						msg = '{} - ({:,}/{:,} users online)'.format(motd, int(membersOnline), int(members))
				else:
					msg = motd
				try:		
					await channel.edit(topic=msg)
				except Exception:
					# If someone has the wrong perms - we just move on
					continue'''
		

	@commands.command(pass_context=True)
	async def islocked(self, ctx):
		"""Says whether the bot only responds to admins."""
		
		isLocked = self.settings.getServerStat(ctx.message.guild, "AdminLock")
		if isLocked:
			msg = 'Admin lock is *On*.'
		else:
			msg = 'Admin lock is *Off*.'
			
		await ctx.channel.send(msg)
		
		
	@commands.command(pass_context=True)
	async def rules(self, ctx):
		"""Display the server's rules."""
		rules = self.settings.getServerStat(ctx.message.guild, "Rules")
		msg = "*{}* Rules:\n{}".format(self.suppressed(ctx.guild, ctx.guild.name), rules)
		await ctx.channel.send(msg)


	@commands.command(pass_context=True)
	async def listmuted(self, ctx):
		"""Lists the names of those that are muted."""

		# Check if we're suppressing @here and @everyone mentions
		if self.settings.getServerStat(ctx.guild, "SuppressMentions"):
			suppress = True
		else:
			suppress = False

		muteList = self.settings.getServerStat(ctx.guild, "MuteList")
		activeMutes = []
		for entry in muteList:
			member = DisplayName.memberForID(entry['ID'], ctx.guild)
			if member:
				# Found one!
				activeMutes.append(DisplayName.name(member))

		if not len(activeMutes):
			await ctx.channel.send("No one is currently muted.")
			return

		# We have at least one member muted
		msg = 'Currently muted:\n\n'
		msg += ', '.join(activeMutes)

		# Check for suppress
		if suppress:
			msg = Nullify.clean(msg)
		await ctx.channel.send(msg)
		
		
	@commands.command(pass_context=True)
	async def ismuted(self, ctx, *, member = None):
		"""Says whether a member is muted in chat."""

		# Check if we're suppressing @here and @everyone mentions
		if self.settings.getServerStat(ctx.message.guild, "SuppressMentions"):
			suppress = True
		else:
			suppress = False
			
		if member == None:
			msg = 'Usage: `{}ismuted [member]`'.format(ctx.prefix)
			await ctx.channel.send(msg)
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
				
		mutedIn = 0
		channelList = []
		for channel in ctx.guild.channels:
			if not type(channel) is discord.TextChannel:
				continue
			overs = channel.overwrites_for(member)
			if overs.send_messages == False:
				# member can't send messages here
				perms = member.permissions_in(channel)
				if perms.read_messages:
					mutedIn +=1
					channelList.append(channel.name)
				
		if len(channelList):
			# Get time remaining if needed
			#cd = self.settings.getUserStat(member, ctx.message.server, "Cooldown")
			muteList = self.settings.getServerStat(ctx.guild, "MuteList")
			cd = None
			for entry in muteList:
				if str(entry['ID']) == str(member.id):
					# Found them!
					cd = entry['Cooldown']
					
			if not cd == None:
				ct = int(time.time())
				checkRead = ReadableTime.getReadableTimeBetween(ct, cd)
				msg = '*{}* is **muted** in *{}*\n*{}* remain'.format(DisplayName.name(member), ', '.join(channelList), checkRead)
			else:
				msg = '*{}* is **muted** in *{}*.'.format(DisplayName.name(member), ', '.join(channelList))	
		else:
			msg = '{} is **unmuted**.'.format(DisplayName.name(member))
			
		await ctx.channel.send(msg)
		
	@ismuted.error
	async def ismuted_error(self, error, ctx):
		# do stuff
		msg = 'ismuted Error: {}'.format(error)
		await ctx.channel.send(msg)
		
		
	@commands.command(pass_context=True)
	async def listadmin(self, ctx):
		"""Lists admin roles and id's."""

		# Check if we're suppressing @here and @everyone mentions
		if self.settings.getServerStat(ctx.message.guild, "SuppressMentions"):
			suppress = True
		else:
			suppress = False

		promoArray = self.settings.getServerStat(ctx.message.guild, "AdminArray")
		
		# rows_by_lfname = sorted(rows, key=itemgetter('lname','fname'))
		
		promoSorted = sorted(promoArray, key=itemgetter('Name'))

		if not len(promoSorted):
			roleText = "There are no admin roles set yet.  Use `{}addadmin [role]` to add some.".format(ctx.prefix)
			await ctx.channel.send(roleText)
			return
		
		roleText = "__**Current Admin Roles:**__\n\n"

		for arole in promoSorted:
			found = False
			for role in ctx.message.guild.roles:
				if str(role.id) == str(arole["ID"]):
					# Found the role ID
					found = True
					roleText = '{}**{}** (ID : `{}`)\n'.format(roleText, role.name, arole['ID'])
			if not found:
				roleText = '{}**{}** (removed from server)\n'.format(roleText, arole['Name'])

		# Check for suppress
		if suppress:
			roleText = Nullify.clean(roleText)

		await ctx.channel.send(roleText)

	@commands.command(pass_context=True)
	async def rolecall(self, ctx, *, role = None):
		"""Lists the number of users in a current role."""

		# Check if we're suppressing @here and @everyone mentions
		if self.settings.getServerStat(ctx.message.guild, "SuppressMentions"):
			suppress = True
		else:
			suppress = False

		author  = ctx.message.author
		server  = ctx.message.guild
		channel = ctx.message.channel

		if role == None:
			msg = 'Usage: `{}rolecall [role]`'.format(ctx.prefix)
			await channel.send(msg)
			return
			
		if type(role) is str:
			roleName = role
			role = DisplayName.roleForName(roleName, ctx.message.guild)
			if not role:
				msg = 'I couldn\'t find *{}*...'.format(roleName)
				# Check for suppress
				if suppress:
					msg = Nullify.clean(msg)
				await ctx.channel.send(msg)
				return
		
		# Create blank embed
		role_embed = discord.Embed(color=role.color)
		# Get server's icon url if one exists - otherwise grab the default blank Discord avatar
		avURL = server.icon_url
		if not len(avURL):
			avURL = discord.User.default_avatar_url
		# Add the server icon
		# role_embed.set_author(name='{}'.format(role.name), icon_url=avURL)
		role_embed.set_author(name='{}'.format(role.name))

		# We have a role
		memberCount = 0
		memberOnline = 0
		for member in server.members:
			roles = member.roles
			if role in roles:
				# We found it
				memberCount += 1
				if not member.status == discord.Status.offline:
					memberOnline += 1

		'''if memberCount == 1:
			msg = 'There is currently *1 user* with the **{}** role.'.format(role.name)
			role_embed.add_field(name="Members", value='1 user', inline=True)
		else:
			msg = 'There are currently *{} users* with the **{}** role.'.format(memberCount, role.name)
			role_embed.add_field(name="Members", value='{}'.format(memberCount), inline=True)'''
		
		role_embed.add_field(name="Members", value='{:,} of {:,} online.'.format(memberOnline, memberCount), inline=True)
			
		# await channel.send(msg)
		await channel.send(embed=role_embed)


	@rolecall.error
	async def rolecall_error(self, ctx, error):
		# do stuff
		msg = 'rolecall Error: {}'.format(ctx)
		await error.channel.send(msg)


	@commands.command(pass_context=True)
	async def log(self, ctx, messages : int = 25, *, chan : discord.TextChannel = None):
		"""Logs the passed number of messages from the given channel - 25 by default (admin only)."""

		author  = ctx.message.author
		server  = ctx.message.guild
		channel = ctx.message.channel

		# Check for admin status
		isAdmin = author.permissions_in(channel).administrator
		if not isAdmin:
			checkAdmin = self.settings.getServerStat(server, "AdminArray")
			for role in author.roles:
				for aRole in checkAdmin:
					# Get the role that corresponds to the id
					if str(aRole['ID']) == str(role.id):
						isAdmin = True

		if not isAdmin:
			await channel.send('You do not have sufficient privileges to access this command.')
			return

		timeStamp = datetime.today().strftime("%Y-%m-%d %H.%M")
		logFile = 'Logs-{}.txt'.format(timeStamp)

		if not chan:
			chan = channel

		# Remove original message
		await ctx.message.delete()

		mess = await ctx.message.author.send('Saving logs to *{}*...'.format(logFile))

		# Use logs_from instead of purge
		counter = 0
		msg = ''
		async for message in channel.history(limit=messages):
			counter += 1
			msg += message.content + "\n"
			msg += '----Sent-By: ' + message.author.name + '#' + message.author.discriminator + "\n"
			msg += '---------At: ' + message.created_at.strftime("%Y-%m-%d %H.%M") + "\n"
			if message.edited_at:
				msg += '--Edited-At: ' + message.edited_at.strftime("%Y-%m-%d %H.%M") + "\n"
			msg += '\n'

		msg = msg[:-2].encode("utf-8")

		with open(logFile, "wb") as myfile:
			myfile.write(msg)

		
		await mess.edit(content='Uploading *{}*...'.format(logFile))
		await ctx.message.author.send(file=logFile)
		await mess.edit(content='Uploaded *{}!*'.format(logFile))
		os.remove(logFile)
