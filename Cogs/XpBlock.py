import asyncio
import discord
import time
import random
import re
from   operator import itemgetter
from   discord.ext import commands
from   Cogs import Message
from   Cogs import Nullify
from   Cogs import DisplayName

def setup(bot):
	# Add the bot and deps
	settings = bot.get_cog("Settings")
	bot.add_cog(XpBlock(bot, settings))

class XpBlock:

	# Init with the bot reference, and a reference to the settings var and xp var
	def __init__(self, bot, settings):
		self.bot = bot
		self.settings = settings
			

	@commands.command(pass_context=True)
	async def xpblock(self, ctx, *, user_or_role : str = None):
		"""Adds a new user or role to the xp block list (bot-admin only)."""

		usage = 'Usage: `{}xpblock [user_or_role]`'.format(ctx.prefix)

		# Check if we're suppressing @here and @everyone mentions
		if self.settings.getServerStat(ctx.message.guild, "SuppressMentions"):
			suppress = True
		else:
			suppress = False

		isAdmin = ctx.message.author.permissions_in(ctx.message.channel).administrator
		if not isAdmin:
			checkAdmin = self.settings.getServerStat(ctx.message.guild, "AdminArray")
			for role in ctx.message.author.roles:
				for aRole in checkAdmin:
					# Get the role that corresponds to the id
					if str(aRole['ID']) == str(role.id):
						isAdmin = True
		# Only allow admins to change server stats
		if not isAdmin:
			await ctx.channel.send('You do not have sufficient privileges to access this command.')
			return

		if user_or_role == None:
			await ctx.message.channel.send(usage)
			return

		roleName = user_or_role
		is_user = True
		if type(user_or_role) is str:
			# Check user first
			user_or_role = DisplayName.memberForName(roleName, ctx.guild)
			if not user_or_role:
				is_user = False
				# Check role
				if roleName.lower() == "everyone" or roleName.lower() == "@everyone":
					user_or_role = ctx.guild.default_role
				else:
					user_or_role = DisplayName.roleForName(roleName, ctx.guild)
					
			if not user_or_role:
				msg = 'I couldn\'t find *{}*...'.format(roleName)
				# Check for suppress
				if suppress:
					msg = Nullify.clean(msg)
				await ctx.message.channel.send(msg)
				return
		
		if is_user:
			# Check if they're admin or bot admin
			isAdmin = user_or_role.permissions_in(ctx.message.channel).administrator
			if not isAdmin:
				checkAdmin = self.settings.getServerStat(ctx.message.guild, "AdminArray")
				for role in user_or_role.roles:
					for aRole in checkAdmin:
						# Get the role that corresponds to the id
						if str(aRole['ID']) == str(role.id):
							isAdmin = True
			if isAdmin:
				msg = "You can't block other admins with this command."
				await ctx.send(msg)
				return
			ur_name = DisplayName.name(user_or_role)
		else:
			# Check if the role is admin or bot admin
			isAdmin = user_or_role.permissions.administrator
			if not isAdmin:
				checkAdmin = self.settings.getServerStat(ctx.message.guild, "AdminArray")
				for aRole in checkAdmin:
					# Get the role that corresponds to the id
					if str(aRole['ID']) == str(user_or_role.id):
						isAdmin = True
			if isAdmin:
				msg = "You can't block other admins with this command."
				await ctx.send(msg)
				return

			ur_name = user_or_role.name

		# Now we see if we already have that role in our list
		promoArray = self.settings.getServerStat(ctx.message.guild, "XpBlockArray")

		for aRole in promoArray:
			# Get the role that corresponds to the id
			if str(aRole) == str(user_or_role.id):
				# We found it - throw an error message and return
				msg = '**{}** is already in the list.'.format(ur_name)
				# Check for suppress
				if suppress:
					msg = Nullify.clean(msg)
				await ctx.message.channel.send(msg)
				return

		# If we made it this far - then we can add it
		promoArray.append(user_or_role.id)
		self.settings.setServerStat(ctx.message.guild, "XpBlockArray", promoArray)

		msg = '**{}** added to list.'.format(ur_name)
		# Check for suppress
		if suppress:
			msg = Nullify.clean(msg)
		await ctx.message.channel.send(msg)
		return
		
	
	@commands.command(pass_context=True)
	async def xpunblockall(self, ctx):
		"""Removes all users and roles from the xp block list (bot-admin only)."""

		# Check if we're suppressing @here and @everyone mentions
		if self.settings.getServerStat(ctx.message.guild, "SuppressMentions"):
			suppress = True
		else:
			suppress = False

		isAdmin = ctx.message.author.permissions_in(ctx.message.channel).administrator
		if not isAdmin:
			checkAdmin = self.settings.getServerStat(ctx.message.guild, "AdminArray")
			for role in ctx.message.author.roles:
				for aRole in checkAdmin:
					# Get the role that corresponds to the id
					if str(aRole['ID']) == str(role.id):
						isAdmin = True
		# Only allow admins to change server stats
		if not isAdmin:
			await ctx.channel.send('You do not have sufficient privileges to access this command.')
			return

		xparray = self.settings.getServerStat(ctx.message.guild, "XpBlockArray")
		self.settings.setServerStat(ctx.message.guild, "XpBlockArray", [])
		if len(xparray) == 1:
			await ctx.send("*1* user/role unblocked from the xp system.")
		else:
			await ctx.send("*{}* users/roles unblocked from the xp system.".format(len(xparray)))


	@commands.command(pass_context=True)
	async def xpunblock(self, ctx, *, user_or_role : str = None):
		"""Removes a user or role from the xp block list (bot-admin only)."""

		usage = 'Usage: `{}xpunblock [user_or_role]`'.format(ctx.prefix)

		# Check if we're suppressing @here and @everyone mentions
		if self.settings.getServerStat(ctx.message.guild, "SuppressMentions"):
			suppress = True
		else:
			suppress = False

		isAdmin = ctx.message.author.permissions_in(ctx.message.channel).administrator
		if not isAdmin:
			checkAdmin = self.settings.getServerStat(ctx.message.guild, "AdminArray")
			for role in ctx.message.author.roles:
				for aRole in checkAdmin:
					# Get the role that corresponds to the id
					if str(aRole['ID']) == str(role.id):
						isAdmin = True
		# Only allow admins to change server stats
		if not isAdmin:
			await ctx.channel.send('You do not have sufficient privileges to access this command.')
			return

		if user_or_role == None:
			await ctx.message.channel.send(usage)
			return

		roleName = user_or_role
		is_user = True
		if type(user_or_role) is str:
			# Check user first
			user_or_role = DisplayName.memberForName(roleName, ctx.guild)
			if not user_or_role:
				is_user = False
				# Check role
				if roleName.lower() == "everyone" or roleName.lower() == "@everyone":
					user_or_role = ctx.guild.default_role
				else:
					user_or_role = DisplayName.roleForName(roleName, ctx.guild)
					
			if not user_or_role:
				msg = 'I couldn\'t find *{}*...'.format(roleName)
				# Check for suppress
				if suppress:
					msg = Nullify.clean(msg)
				await ctx.message.channel.send(msg)
				return
		
		if is_user:
			ur_name = DisplayName.name(user_or_role)
		else:
			ur_name = user_or_role.name

		# If we're here - then the role is a real one
		promoArray = self.settings.getServerStat(ctx.message.guild, "XpBlockArray")

		for aRole in promoArray:
			# Check for Name
			if str(aRole) == str(user_or_role.id):
				# We found it - let's remove it
				promoArray.remove(aRole)
				self.settings.setServerStat(ctx.message.guild, "XpBlockArray", promoArray)
				msg = '**{}** removed successfully.'.format(ur_name)
				# Check for suppress
				if suppress:
					msg = Nullify.clean(msg)
				await ctx.message.channel.send(msg)
				return

		# If we made it this far - then we didn't find it
		msg = '**{}** not found in list.'.format(ur_name)
		# Check for suppress
		if suppress:
			msg = Nullify.clean(msg)
		await ctx.message.channel.send(msg)


	@commands.command(pass_context=True)
	async def listxpblock(self, ctx):
		"""Lists xp blocked users and roles."""

		# Check if we're suppressing @here and @everyone mentions
		if self.settings.getServerStat(ctx.message.guild, "SuppressMentions"):
			suppress = True
		else:
			suppress = False

		promoArray = self.settings.getServerStat(ctx.message.guild, "XpBlockArray")
		
		# rows_by_lfname = sorted(rows, key=itemgetter('lname','fname'))
		
		#promoSorted = sorted(promoArray, key=itemgetter('Name'))

		if not len(promoArray):
			roleText = "There are no users or roles xp blocked yet.  Use `{}xpblock [user_or_role]` to add some.".format(ctx.prefix)
			await ctx.channel.send(roleText)
			return
		
		roleText = "__**Current Xp Blocked Users and Roles:**__\n\n"
		
		for arole in promoArray:
			test = DisplayName.memberForID(arole, ctx.guild)
			if test:
				# It's a user
				roleText = roleText + "**{}**, ".format(DisplayName.name(test))
				continue
			test = DisplayName.roleForID(arole, ctx.guild)
			if test:
				# It's a role
				roleText = roleText + "**{}** (Role), ".format(test.name)
				continue
			# Didn't find a role or person
			roleText = roleText + "**{}** (removed from server), ".format(arole)

		roleText = roleText[:-2]
		# Check for suppress
		if suppress:
			roleText = Nullify.clean(roleText)

		await ctx.channel.send(roleText)