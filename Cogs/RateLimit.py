import asyncio
import discord
import os
import time
from   datetime import datetime
from   discord.ext import commands

def setup(bot):
	# Add the bot and deps
	settings = bot.get_cog("Settings")
	bot.add_cog(RateLimit(bot, settings))

# This is the RateLimit module. It keeps users from being able to spam commands

class RateLimit:

	# Init with the bot reference, and a reference to the settings var
	def __init__(self, bot, settings):
		self.bot = bot
		self.settings = settings
		self.commandCooldown = 5 # 5 seconds between commands - placeholder, overridden by settings
		self.maxCooldown = 10 # 10 seconds MAX between commands for cooldown
		
	def canRun( self, firstTime, threshold ):
		# Check if enough time has passed since the last command to run another
		currentTime = int(time.time())
		if currentTime > (int(firstTime) + int(threshold)):
			return True
		else:
			return False
		
	async def test_message(self, message):
		# Implemented to bypass having this called twice
		return { "Ignore" : False, "Delete" : False }

	async def message(self, message):
		# Check the message and see if we should allow it - always yes.
		# This module doesn't need to cancel messages - but may need to ignore
		ignore = False

		# Get current delay
		try:
			currDelay = self.settings.serverDict['CommandCooldown']
		except KeyError:
			currDelay = self.commandCooldown
		
		# Check if we can run commands
		try:
			lastTime = int(self.settings.getUserStat(message.author, message.guild, "LastCommand"))
		except:
			# Not set - or incorrectly set - default to 0
			lastTime = 0
		# None fix
		if lastTime == None:
			lastTime = 0
		if not self.canRun( lastTime, currDelay ):
			# We can't run commands yet - ignore
			ignore = True
		
		return { 'Ignore' : ignore, 'Delete' : False }
		
	async def oncommand(self, ctx):
		# Let's grab the user who had a completed command - and set the timestamp
		self.settings.setUserStat(ctx.message.author, ctx.message.guild, "LastCommand", int(time.time()))


	@commands.command(pass_context=True)
	async def ccooldown(self, ctx, delay : int = None):
		"""Sets the cooldown in seconds between each command (owner only)."""
		
		channel = ctx.message.channel
		author  = ctx.message.author
		server  = ctx.message.guild

		# Only allow owner
		isOwner = self.settings.isOwner(ctx.author)
		if isOwner == None:
			msg = 'I have not been claimed, *yet*.'
			await ctx.channel.send(msg)
			return
		elif isOwner == False:
			msg = 'You are not the *true* owner of me.  Only the rightful owner can use this command.'
			await ctx.channel.send(msg)
			return

		# Get current delay
		try:
			currDelay = self.settings.serverDict['CommandCooldown']
		except KeyError:
			currDelay = self.commandCooldown
		
		if delay == None:
			if currDelay == 1:
				await ctx.channel.send('Current command cooldown is *1 second.*')
			else:
				await ctx.channel.send('Current command cooldown is *{} seconds.*'.format(currDelay))
			return
		
		try:
			delay = int(delay)
		except Exception:
			await ctx.channel.send('Cooldown must be an int.')
			return
		
		if delay < 0:
			await ctx.channel.send('Cooldown must be at least *0 seconds*.')
			return

		if delay > self.maxCooldown:
			if self.maxCooldown == 1:
				await ctx.channel.send('Cooldown cannot be more than *1 second*.')
			else:
				await ctx.channel.send('Cooldown cannot be more than *{} seconds*.'.format(self.maxCooldown))
			return
		
		self.settings.serverDict['CommandCooldown'] = delay
		if delay == 1:
			await ctx.channel.send('Current command cooldown is now *1 second.*')
		else:
			await ctx.channel.send('Current command cooldown is now *{} seconds.*'.format(delay))
