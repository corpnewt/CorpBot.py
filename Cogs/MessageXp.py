import asyncio
import discord
from   discord.ext import commands
from   Cogs import Settings
from   Cogs import CheckRoles

def setup(bot):
	# Add the bot and deps
	settings = bot.get_cog("Settings")
	bot.add_cog(MessageXp(bot, settings))

# This is the message xp module.  It's also likely to be retarded.

class MessageXp:

	# Init with the bot reference, and a reference to the settings var
	def __init__(self, bot, settings):
		self.bot = bot
		self.settings = settings
		
	async def message(self, message):
		# Check the message and see if we should allow it - always yes.
		# This module doesn't need to cancel messages.

		server = message.guild

		# Check if we're blocked
		xpblock = self.settings.getServerStat(server, "XpBlockArray")
		if message.author.id in xpblock:
			# No xp for you
			return { 'Ignore' : False, 'Delete' : False}
		for role in message.author.roles:
			if role.id in xpblock:
				return { 'Ignore' : False, 'Delete' : False}

		xpAmount   = int(self.settings.getServerStat(server, "XPPerMessage"))
		xpRAmount  = int(self.settings.getServerStat(server, "XPRPerMessage"))

		xpLimit    = self.settings.getServerStat(server, "XPLimit")
		xprLimit   = self.settings.getServerStat(server, "XPReserveLimit")
		
		if xpRAmount > 0:
			# First we check if we'll hit our limit
			skip = False
			if not xprLimit == None:
				# Get the current values
				newxp = self.settings.getUserStat(message.author, server, "XPReserve")
				# Make sure it's this xpr boost that's pushing us over
				# This would only push us up to the max, but not remove
				# any we've already gotten
				if newxp + xpRAmount > xprLimit:
					skip = True
					if newxp < xprLimit:
						self.settings.setUserStat(message.author, server, "XPReserve", xprLimit)
			if not skip:
				# Bump xp reserve
				self.settings.incrementStat(message.author, server, "XPReserve", xpRAmount)
		
		if xpAmount > 0:
			# First we check if we'll hit our limit
			skip = False
			if not xpLimit == None:
				# Get the current values
				newxp = self.settings.getUserStat(message.author, server, "XP")
				# Make sure it's this xpr boost that's pushing us over
				# This would only push us up to the max, but not remove
				# any we've already gotten
				if newxp + xpAmount > xpLimit:
					skip = True
					if newxp < xpLimit:
						self.settings.setUserStat(message.author, server, "XP", xpLimit)
			if not skip:
				# Bump xp
				self.settings.incrementStat(message.author, server, "XP", xpAmount)
				# Check for promotion/demotion
			await CheckRoles.checkroles(message.author, message.channel, self.settings, self.bot)
			
		return { 'Ignore' : False, 'Delete' : False}
