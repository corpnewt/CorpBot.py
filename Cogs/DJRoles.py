import asyncio
import discord
from   operator import itemgetter
from   discord.ext import commands
from   Cogs import Nullify
from   Cogs import DisplayName

def setup(bot):
	# Add the bot and deps
	settings = bot.get_cog("Settings")
	bot.add_cog(DJRoles(bot, settings))

class DJRoles:

	# Init with the bot reference, and a reference to the settings var and xp var
	def __init__(self, bot, settings):
		self.bot = bot
		self.settings = settings
			
	@commands.command(pass_context=True)
	async def ytlist(self, ctx, yes_no = None):
		"""Gets or sets whether or not the server will show a list of options when searching with the play command - or if it'll just pick the first (admin only)."""
		
		setting_name = "Youtube search list"
		setting_val  = "YTMultiple"

		isAdmin = ctx.author.permissions_in(ctx.channel).administrator
		if not isAdmin:
			await ctx.send('You do not have sufficient privileges to access this command.')
			return
		current = self.settings.getServerStat(ctx.guild, setting_val)
		if yes_no == None:
			# Output what we have
			if current:
				msg = "{} currently *enabled.*".format(setting_name)
			else:
				msg = "{} currently *disabled.*".format(setting_name)
		elif yes_no.lower() in [ "yes", "on", "true", "enabled", "enable" ]:
			yes_no = True
			if current == True:
				msg = '{} remains *enabled*.'.format(setting_name)
			else:
				msg = '{} is now *enabled*.'.format(setting_name)
		elif yes_no.lower() in [ "no", "off", "false", "disabled", "disable" ]:
			yes_no = False
			if current == False:
				msg = '{} remains *disabled*.'.format(setting_name)
			else:
				msg = '{} is now *disabled*.'.format(setting_name)
		else:
			msg = "That's not a valid setting."
			yes_no = current
		if not yes_no == None and not yes_no == current:
			self.settings.setServerStat(ctx.guild, setting_val, yes_no)
		await ctx.send(msg)

	@commands.command(pass_context=True)
	async def adddj(self, ctx, *, role : str = None):
		"""Adds a new role to the dj list (bot-admin only)."""

		usage = 'Usage: `{}adddj [role]`'.format(ctx.prefix)

		# Check if we're suppressing @here and @everyone mentions
		if self.settings.getServerStat(ctx.message.guild, "SuppressMentions"):
			suppress = True
		else:
			suppress = False

		isAdmin = ctx.message.author.permissions_in(ctx.message.channel).administrator
		if not isAdmin:
			checkAdmin = self.settings.getServerStat(ctx.message.guild, "AdminArray")
			for trole in ctx.message.author.roles:
				for aRole in checkAdmin:
					# Get the role that corresponds to the id
					if str(aRole['ID']) == str(trole.id):
						isAdmin = True
		# Only allow admins to change server stats
		if not isAdmin:
			await ctx.channel.send('You do not have sufficient privileges to access this command.')
			return

		if role == None:
			await ctx.message.channel.send(usage)
			return

		roleName = role
		if type(role) is str:
			if role.lower() == "everyone" or role.lower() == "@everyone":
				role = ctx.guild.default_role
			else:
				role = DisplayName.roleForName(roleName, ctx.guild)
			if not role:
				msg = 'I couldn\'t find *{}*...'.format(roleName)
				# Check for suppress
				if suppress:
					msg = Nullify.clean(msg)
				await ctx.message.channel.send(msg)
				return

		# Now we see if we already have that role in our list
		promoArray = self.settings.getServerStat(ctx.message.guild, "DJArray")

		for aRole in promoArray:
			# Get the role that corresponds to the id
			if str(aRole['ID']) == str(role.id):
				# We found it - throw an error message and return
				msg = '**{}** is already in the list.'.format(role.name)
				# Check for suppress
				if suppress:
					msg = Nullify.clean(msg)
				await ctx.message.channel.send(msg)
				return

		# If we made it this far - then we can add it
		promoArray.append({ 'ID' : role.id, 'Name' : role.name })
		self.settings.setServerStat(ctx.message.guild, "DJArray", promoArray)

		msg = '**{}** added to list.'.format(role.name)
		# Check for suppress
		if suppress:
			msg = Nullify.clean(msg)
		await ctx.message.channel.send(msg)
		return
		
		
	@commands.command(pass_context=True)
	async def removedj(self, ctx, *, role : str = None):
		"""Removes a role from the dj list (bot-admin only)."""

		usage = 'Usage: `{}removedj [role]`'.format(ctx.prefix)

		# Check if we're suppressing @here and @everyone mentions
		if self.settings.getServerStat(ctx.message.guild, "SuppressMentions"):
			suppress = True
		else:
			suppress = False

		isAdmin = ctx.message.author.permissions_in(ctx.message.channel).administrator
		if not isAdmin:
			checkAdmin = self.settings.getServerStat(ctx.message.guild, "AdminArray")
			for trole in ctx.message.author.roles:
				for aRole in checkAdmin:
					# Get the role that corresponds to the id
					if str(aRole['ID']) == str(trole.id):
						isAdmin = True
		# Only allow admins to change server stats
		if not isAdmin:
			await ctx.channel.send('You do not have sufficient privileges to access this command.')
			return

		if role == None:
			await ctx.message.channel.send(usage)
			return

		# Name placeholder
		roleName = role
		if type(role) is str:
			if role.lower() == "everyone" or role.lower() == "@everyone":
				role = ctx.guild.default_role
			else:
				role = DisplayName.roleForName(role, ctx.guild)

		# If we're here - then the role is a real one
		promoArray = self.settings.getServerStat(ctx.message.guild, "DJArray")

		for aRole in promoArray:
			# Check for Name
			if aRole['Name'].lower() == roleName.lower():
				# We found it - let's remove it
				promoArray.remove(aRole)
				self.settings.setServerStat(ctx.message.guild, "DJArray", promoArray)
				msg = '**{}** removed successfully.'.format(aRole['Name'])
				# Check for suppress
				if suppress:
					msg = Nullify.clean(msg)
				await ctx.message.channel.send(msg)
				return

			# Get the role that corresponds to the id
			if role and (str(aRole['ID']) == str(role.id)):
				# We found it - let's remove it
				promoArray.remove(aRole)
				self.settings.setServerStat(ctx.message.guild, "DJArray", promoArray)
				msg = '**{}** removed successfully.'.format(role.name)
				# Check for suppress
				if suppress:
					msg = Nullify.clean(msg)
				await ctx.message.channel.send(msg)
				return

		# If we made it this far - then we didn't find it
		msg = '**{}** not found in list.'.format(aRole['Name'])
		# Check for suppress
		if suppress:
			msg = Nullify.clean(msg)
		await ctx.message.channel.send(msg)


	@commands.command(pass_context=True)
	async def listdj(self, ctx):
		"""Lists dj roles and id's."""

		# Check if we're suppressing @here and @everyone mentions
		if self.settings.getServerStat(ctx.message.guild, "SuppressMentions"):
			suppress = True
		else:
			suppress = False

		promoArray = self.settings.getServerStat(ctx.message.guild, "DJArray")
		
		# rows_by_lfname = sorted(rows, key=itemgetter('lname','fname'))
		
		promoSorted = sorted(promoArray, key=itemgetter('Name'))

		if not len(promoSorted):
			roleText = "There are no dj roles set yet.  Use `{}adddj [role]` to add some.".format(ctx.prefix)
			await ctx.channel.send(roleText)
			return
		
		roleText = "__**Current DJ Roles:**__\n\n"

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