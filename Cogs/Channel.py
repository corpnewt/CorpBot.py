import asyncio
import discord
import time
from   discord.ext import commands
from   operator import itemgetter
from   Cogs import Settings
from   Cogs import ReadableTime
from   Cogs import DisplayName
from   Cogs import Nullify

# This is the admin module.  It holds the admin-only commands
# Everything here *requires* that you're an admin

class Channel:

	# Init with the bot reference, and a reference to the settings var
	def __init__(self, bot, settings):
		self.bot = bot
		self.settings = settings
		
	@commands.command(pass_context=True)
	async def islocked(self, ctx):
		"""Says whether the bot only responds to admins."""
		
		isLocked = self.settings.getServerStat(ctx.message.guild, "AdminLock")
		if isLocked.lower() == "yes":
			msg = 'Admin lock is *On*.'
		else:
			msg = 'Admin lock is *Off*.'
			
		await ctx.channel.send(msg)
		
		
	@commands.command(pass_context=True)
	async def rules(self, ctx):
		"""Display the server's rules."""
		rules = self.settings.getServerStat(ctx.message.guild, "Rules")
		msg = "*{}* Rules:\n{}".format(ctx.message.guild.name, rules)
		await ctx.channel.send(msg)
		
		
	@commands.command(pass_context=True)
	async def ismuted(self, ctx, *, member = None):
		"""Says whether a member is muted in chat."""

		# Check if we're suppressing @here and @everyone mentions
		if self.settings.getServerStat(ctx.message.guild, "SuppressMentions").lower() == "yes":
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
				
		isMute = self.settings.getUserStat(member, ctx.message.guild, "Muted")

		checkTime = self.settings.getUserStat(member, ctx.message.guild, "Cooldown")
		if checkTime:
			checkTime = int(checkTime)
		currentTime = int(time.time())
		checkRead = None

		# Check if they've outlasted their time
		if checkTime and (currentTime >= checkTime):
			# We have passed the check time
			ignore = False
			delete = False
			self.settings.setUserStat(member, ctx.message.guild, "Cooldown", None)
			self.settings.setUserStat(member, ctx.message.guild, "Muted", "No")
			isMute = self.settings.getUserStat(member, ctx.message.guild, "Muted")
		elif checkTime:
			checkRead = ReadableTime.getReadableTimeBetween(currentTime, checkTime)

		if isMute.lower() == "yes":
			if checkRead:
				msg = '*{}* is *Muted* - *{}* remain.'.format(DisplayName.name(member), checkRead)	
			else:
				msg = '*{}* is *Muted*.'.format(DisplayName.name(member))	
		else:
			msg = '{} is *Unmuted*.'.format(DisplayName.name(member))
			
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
		if self.settings.getServerStat(ctx.message.guild, "SuppressMentions").lower() == "yes":
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
		
		roleText = "Current Admin Roles:\n"

		for arole in promoSorted:
			found = False
			for role in ctx.message.guild.roles:
				if role.id == arole["ID"]:
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
		if self.settings.getServerStat(ctx.message.guild, "SuppressMentions").lower() == "yes":
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
		for member in server.members:
			roles = member.roles
			if role in roles:
				# We found it
				memberCount += 1

		'''if memberCount == 1:
			msg = 'There is currently *1 user* with the **{}** role.'.format(role.name)
			role_embed.add_field(name="Members", value='1 user', inline=True)
		else:
			msg = 'There are currently *{} users* with the **{}** role.'.format(memberCount, role.name)
			role_embed.add_field(name="Members", value='{}'.format(memberCount), inline=True)'''
		
		role_embed.add_field(name="Members", value='{}'.format(memberCount), inline=True)
			
		# await channel.send(msg)
		await channel.send(embed=role_embed)


	@rolecall.error
	async def rolecall_error(self, ctx, error):
		# do stuff
		msg = 'rolecall Error: {}'.format(ctx)
		await error.channel.send(msg)

	@commands.command(pass_context=True)
	async def clean(self, ctx, messages : int = 100, *, chan : discord.TextChannel = None):
		"""Cleans the passed number of messages from the given channel - 100 by default (admin only)."""

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
					if aRole['ID'] == role.id:
						isAdmin = True

		if not isAdmin:
			await channel.send('You do not have sufficient privileges to access this command.')
			return

		if not chan:
			chan = channel

		# Remove original message
		await ctx.message.delete()
		# Remove the rest
		await chan.purge(limit=messages)
