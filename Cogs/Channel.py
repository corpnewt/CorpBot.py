import asyncio, discord, time, os
from   discord.ext import commands
from   datetime import datetime
from   operator import itemgetter
from   Cogs import Utils, Settings, ReadableTime, DisplayName

async def setup(bot):
	# Add the bot and deps
	settings = bot.get_cog("Settings")
	await bot.add_cog(Channel(bot, settings))

# This is the admin module.  It holds the admin-only commands
# Everything here *requires* that you're an admin

class Channel(commands.Cog):

	# Init with the bot reference, and a reference to the settings var
	def __init__(self, bot, settings):
		self.bot = bot
		self.settings = settings
		global Utils, DisplayName
		Utils = self.bot.get_cog("Utils")
		DisplayName = self.bot.get_cog("DisplayName")

	async def member_update(self, before, after):
		# Check if the member went offline and log the time
		if after.status == discord.Status.offline:
			currentTime = int(time.time())
			self.settings.setUserStat(after, after.guild, "LastOnline", currentTime)
		

	@commands.command()
	async def islocked(self, ctx):
		"""Says whether the bot only responds to admins."""
		isLocked = self.settings.getServerStat(ctx.message.guild, "AdminLock")
		await ctx.send("Admin lock is *On*." if isLocked else "Admin lock is *Off*.")
		
		
	@commands.command()
	async def rules(self, ctx):
		"""Display the server's rules."""
		rules = self.settings.getServerStat(ctx.guild, "Rules")
		msg = "***{}*** **Rules:**\n{}".format(ctx.guild.name, rules)
		await ctx.send(Utils.suppressed(ctx,msg))


	@commands.command()
	async def listmuted(self, ctx):
		"""Lists the names of those that are muted."""
		muteList = self.settings.getServerStat(ctx.guild, "MuteList")
		activeMutes = []
		for entry in muteList:
			member = DisplayName.memberForID(entry['ID'], ctx.guild)
			if member:
				# Found one!
				activeMutes.append(DisplayName.name(member))

		if not len(activeMutes):
			await ctx.send("No one is currently muted.")
			return

		# We have at least one member muted
		msg = 'Currently muted:\n\n'
		msg += ', '.join(activeMutes)

		await ctx.send(Utils.suppressed(ctx,msg))
		
		
	@commands.command()
	async def listadmin(self, ctx):
		"""Lists admin roles and id's."""
		promoArray = self.settings.getServerStat(ctx.message.guild, "AdminArray")		
		promoSorted = sorted(promoArray, key=itemgetter('Name'))

		if not len(promoSorted):
			roleText = "There are no admin roles set yet.  Use `{}addadmin [role]` to add some.".format(ctx.prefix)
			await ctx.send(roleText)
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

		await ctx.send(Utils.suppressed(ctx,roleText))


	@commands.command()
	async def log(self, ctx, messages : int = 25, *, chan : discord.TextChannel = None):
		"""Logs the passed number of messages from the given channel - 25 by default (admin only)."""
		if not await Utils.is_bot_admin_reply(ctx): return

		timeStamp = datetime.today().strftime("%Y-%m-%d %H.%M")
		logFile = 'Logs-{}.txt'.format(timeStamp)

		if not chan:
			chan = ctx

		# Remove original message
		await ctx.message.delete()

		mess = await ctx.send('Saving logs to *{}*...'.format(logFile))

		# Use logs_from instead of purge
		counter = 0
		msg = ''
		async for message in chan.history(limit=messages):
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
		await ctx.author.send(file=discord.File(fp=logFile))
		await mess.edit(content='Uploaded *{}!*'.format(logFile))
		os.remove(logFile)
