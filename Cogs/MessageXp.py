import asyncio
import discord
from   discord.ext import commands
from   Cogs import Settings
from   Cogs import CheckRoles

# This is the message xp module.  It's also likely to be retarded.

class MessageXp:

	# Init with the bot reference, and a reference to the settings var
	def __init__(self, bot, settings):
		self.bot = bot
		self.settings = settings
		
	async def message(self, message):
		# Check the message and see if we should allow it - always yes.
		# This module doesn't need to cancel messages.

		server = message.server
		xpAmount   = int(self.settings.getServerStat(server, "XPPerMessage"))
		xpRAmount  = int(self.settings.getServerStat(server, "XPRPerMessage"))
		
		if xpRAmount > 0:
			# Bump xp
			self.settings.incrementStat(message.author, server, "XPReserve", xpAmount)
		
		if xpAmount > 0:
			# Bump xp
			self.settings.incrementStat(message.author, server, "XP", xpAmount)
			# Check for promotion/demotion
			await CheckRoles.checkroles(message.author, message.channel, self.settings, self.bot)
			
		return { 'Ignore' : False, 'Delete' : False}