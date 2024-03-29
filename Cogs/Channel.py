import asyncio, discord, time, os
from   discord.ext import commands
from   datetime import datetime
from   operator import itemgetter
from   Cogs import Utils, Settings, ReadableTime, DisplayName, PickList

def setup(bot):
	# Add the bot and deps
	settings = bot.get_cog("Settings")
	bot.add_cog(Channel(bot, settings))

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
		

	##
	## Not sure why I decided to put these commands in the Channel cog?  I'll likely move
	## them to more sane spots eventually...
	##
	@commands.command(pass_context=True)
	async def islocked(self, ctx):
		"""Says whether the bot only responds to admins."""
		isLocked = self.settings.getServerStat(ctx.message.guild, "AdminLock")
		await ctx.send("Admin lock is *On*." if isLocked else "Admin lock is *Off*.")
		
		
	@commands.command(pass_context=True)
	async def rules(self, ctx):
		"""Display the server's rules."""
		rules = self.settings.getServerStat(ctx.guild, "Rules")
		msg = "***{}*** **Rules:**\n{}".format(ctx.guild.name, rules)
		await ctx.send(Utils.suppressed(ctx,msg))
		
		
	@commands.command(pass_context=True)
	async def listadmin(self, ctx):
		"""Lists admin roles and id's."""
		promoArray = self.settings.getServerStat(ctx.message.guild, "AdminArray")		
		promoSorted = sorted(promoArray, key=itemgetter('Name'))

		if not len(promoSorted):
			roleText = "There are no admin roles set yet.  Use `{}addadmin [role]` to add some.".format(ctx.prefix)
			return await ctx.send(roleText)
		
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

	'''@commands.command(pass_context=True)
	async def rolecall(self, ctx, *, role = None):
		"""Lists the number of users in a current role."""
		if role == None:
			msg = 'Usage: `{}rolecall [role]`'.format(ctx.prefix)
			return await ctx.send(msg)
			
		if type(role) is str:
			roleName = role
			role = DisplayName.roleForName(roleName, ctx.guild)
			if not role:
				msg = 'I couldn\'t find *{}*...'.format(roleName)
				return await ctx.send(Utils.suppressed(ctx,msg))
		
		# Create blank embed
		role_embed = discord.Embed(color=role.color)
		role_embed.set_author(name='{}'.format(role.name))
		# We have a role
		members = [x for x in ctx.guild.members if role in x.roles]
		memberCount = len(members)
		memberOnline = len([x for x in members if x.status != discord.Status.offline])
		role_embed.add_field(name="Members", value='{:,} of {:,} online.'.format(memberOnline, memberCount), inline=True)
		await ctx.send(embed=role_embed)'''

	##
	## End of the odd commands
	##

	@commands.command(pass_context=True)
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
			msg += '----Sent-By: ' + str(message.author) + "\n"
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
