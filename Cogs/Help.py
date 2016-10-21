import asyncio
import discord
import inspect
from   discord.ext import commands
from   Cogs import *

# This module is for random funny things I guess...

class Help:

	def __init__(self, bot, cogs):
		# cogs = an array of the cogs used to start the bot
		self.bot = bot
		self.cogs = cogs
		
	def message(self, message):
		# Check the message and see if we should allow it - always yes.
		# This module doesn't need to cancel messages.
		return { 'Ignore' : False, 'Delete' : False}
	