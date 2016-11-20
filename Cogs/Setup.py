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
		#############################
		# Role Management:
		#############################
		# 1. Auto role? Yes/no
		#  a. If yes - get role ID (let's move away from position)
		# 2. Use XP? Yes/no
		#  a. If yes:
		#    * how much reserve per hour
		#    * how much xp/reserve to start