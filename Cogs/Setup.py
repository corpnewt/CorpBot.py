import asyncio
import discord
from   discord.ext import commands
from   Cogs import Settings

# This is the Uptime module. It keeps track of how long the bot's been up

class Setup:

	# Init with the bot reference, and a reference to the settings var
	def __init__(self, bot, settings):
		self.bot = bot
		self.settings = settings

	def message(self, message):
		# Check the message and see if we should allow it - always yes.
		# This module doesn't need to cancel messages.
		return { 'Ignore' : False, 'Delete' : False}

	@commands.command(pass_context=True)
	async def setup(self, ctx):
		"""Runs first-time setup."""
		# 1. Auto role? Yes/no
		#  a. If yes - ID or position
		#  b. get ID or position
		# 2. 