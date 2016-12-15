import asyncio
import discord
import time
from   discord.ext import commands
from   operator import itemgetter
from   Cogs import Settings
from   Cogs import ReadableTime
from   Cogs import DisplayName

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
		
		isLocked = self.settings.getServerStat(ctx.message.server, "AdminLock")
		if isLocked.lower() == "yes":
			msg = 'Admin lock is *On*.'
		else:
			msg = 'Admin lock is *Off*.'
			
		await self.bot.send_message(ctx.message.channel, msg)
		
		
	@commands.command(pass_context=True)
	async def rules(self, ctx):
		"""Display the server's rules."""
		rules = self.settings.getServerStat(ctx.message.server, "Rules")
		msg = "*{}* Rules:\n{}".format(ctx.message.server.name, rules)
		await self.bot.send_message(ctx.message.channel, msg)
		
		
	@commands.command(pass_context=True)
	async def ismuted(self, ctx, *, member = None):
		"""Says whether a member is muted in chat."""
			
		if member == None:
			msg = 'Usage: `ismuted [member]`'
			await self.bot.send_message(ctx.message.channel, msg)
			return

		if type(member) is str:
			memberName = member
			member = DisplayName.memberForName(memberName, ctx.message.server)
			if not member:
				msg = 'I couldn\'t find *{}*...'.format(memberName)
				await self.bot.send_message(ctx.message.channel, msg)
				return
				
		isMute = self.settings.getUserStat(member, ctx.message.server, "Muted")

		checkTime = self.settings.getUserStat(member, ctx.message.server, "Cooldown")
		if checkTime:
			checkTime = int(checkTime)
		currentTime = int(time.time())
		checkRead = None

		# Check if they've outlasted their time
		if checkTime and (currentTime >= checkTime):
			# We have passed the check time
			ignore = False
			delete = False
			self.settings.setUserStat(member, ctx.message.server, "Cooldown", None)
			self.settings.setUserStat(member, ctx.message.server, "Muted", "No")
			isMute = self.settings.getUserStat(member, ctx.message.server, "Muted")
		elif checkTime:
			checkRead = ReadableTime.getReadableTimeBetween(currentTime, checkTime)

		if isMute.lower() == "yes":
			if checkRead:
				msg = '{} is *Muted* - *{}* remain.'.format(DisplayName.name(member), checkRead)	
			else:
				msg = '{} is *Muted*.'.format(DisplayName.name(member))	
		else:
			msg = '{} is *Unmuted*.'.format(DisplayName.name(member))
			
		await self.bot.send_message(ctx.message.channel, msg)
		
	@ismuted.error
	async def ismuted_error(self, ctx, error):
		# do stuff
		msg = 'ismuted Error: {}'.format(ctx)
		await self.bot.say(msg)
		
		
	@commands.command(pass_context=True)
	async def listadmin(self, ctx):
		"""Lists admin roles and id's."""
		promoArray = self.settings.getServerStat(ctx.message.server, "AdminArray")
		
		# rows_by_lfname = sorted(rows, key=itemgetter('lname','fname'))
		
		promoSorted = sorted(promoArray, key=itemgetter('Name'))

		if not len(promoSorted):
			roleText = "There are no admin roles set yet.  Use `$addadmin [role]` to add some."
			await self.bot.send_message(ctx.message.channel, roleText)
			return
		
		roleText = "Current Admin Roles:\n"

		for arole in promoSorted:
			for role in ctx.message.server.roles:
				if role.id == arole["ID"]:
					# Found the role ID
					roleText = '{}**{}** (ID : `{}`)\n'.format(roleText, role.name, arole['ID'])

		await self.bot.send_message(ctx.message.channel, roleText)

	@commands.command(pass_context=True)
	async def rolecall(self, ctx, *, role = None):
		"""Lists the number of users in a current role."""

		author  = ctx.message.author
		server  = ctx.message.server
		channel = ctx.message.channel

		if role == None:
			msg = 'Usage: `$rolecall [role]`'
			await self.bot.send_message(channel, msg)
			return
			
		if type(role) is str:
			roleName = role
			role = DisplayName.roleForName(roleName, ctx.message.server)
			if not role:
				msg = 'I couldn\'t find *{}*...'.format(roleName)
				await self.bot.send_message(ctx.message.channel, msg)
				return

		# We have a role
		memberCount = 0
		for member in server.members:
			roles = member.roles
			if role in roles:
				# We found it
				memberCount += 1

		if memberCount == 1:
			msg = 'There is currently *1 user* with the **{}** role.'.format(role.name)
		else:
			msg = 'There are currently *{} users* with the **{}** role.'.format(memberCount, role.name)
		await self.bot.send_message(channel, msg)


	@rolecall.error
	async def rolecall_error(self, ctx, error):
		# do stuff
		msg = 'rolecall Error: {}'.format(ctx)
		await self.bot.say(msg)

	@commands.command(pass_context=True)
	async def clean(self, ctx, messages : int = 100, *, chan : discord.Channel = None):
		"""Cleans the passed number of messages from the given channel - 100 by default (admin only)."""

		author  = ctx.message.author
		server  = ctx.message.server
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
			await self.bot.send_message(channel, 'You do not have sufficient privileges to access this command.')
			return

		if not chan:
			chan = channel

		# Remove original message
		await self.bot.delete_message(ctx.message)
		# Remove the rest
		await self.bot.purge_from(chan, limit=messages)
