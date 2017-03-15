import asyncio
import discord
import os
import time
from   datetime import datetime
from   discord.ext import commands

# This is the RateLimit module. It keeps users from being able to spam commands

class RateLimit:

	# Init with the bot reference, and a reference to the settings var
	def __init__(self, bot, settings):
		self.bot = bot
		self.settings = settings
		self.commandCooldown = 5 # 5 seconds between commands
		
	def canRun( self, firstTime, threshold ):
		# Check if enough time has passed since the last command to run another
		currentTime = int(time.time())
		if currentTime > (int(firstTime) + int(threshold)):
			return True
		else:
			return False

	async def message(self, message):
		# Check the message and see if we should allow it - always yes.
		# This module doesn't need to cancel messages - but may need to ignore
		ignore = False
		
		# Check if we can run commands
		lastTime = int(self.settings.getUserStat(message.author, message.server, "LastCommand"))
		if not self.canRun( lastTime, self.commandCooldown ):
			# We can't run commands yet - ignore
			ignore = True
		
		return { 'Ignore' : ignore, 'Delete' : False }
		
	async def oncommand(self, command, ctx):
		# Let's grab the user who had a completed command - and set the timestamp
		self.settings.setUserStat(ctx.message.author, ctx.message.server, "LastCommand", int(time.time()))
