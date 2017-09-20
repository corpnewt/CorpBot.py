import asyncio
import discord
from   discord.ext import commands

def setup(bot):
	# Disabled for now
	return
	# Add the bot and deps
	settings = bot.get_cog("Settings")
	bot.add_cog(Monitor(bot, settings))

# This is the Monitor module. It keeps track of how many messages fail

class Monitor:

	# Init with the bot reference
	def __init__(self, bot, settings):
		self.bot = bot
		self.settings = settings
		self.commands = []
		self.commandCount = 25 # Keep 25 commands in the list max
		self.threshold = 0.9 # If we fall below 90% success - reboot the bot

	async def oncommand(self, command, ctx):
		# Check previous commands and see if we need to reboot
		passed = 0
		checked = 0
		for command in self.commands:
			checked += 1
			if command['Success'] == True:
				passed += 1
		
		if checked > 1 and float(passed/checked) < self.threshold:
			# We checked at least one command - and are below threshold
			print('Command success below threshold - rebooting...')
			self.settings.flushSettings()
			# Logout, stop the event loop, close the loop, quit
			for task in asyncio.Task.all_tasks():
				try:
					task.cancel()
				except Exception:
					continue
			try:
				await self.bot.logout()
				self.bot.loop.stop()
				self.bot.loop.close()
			except Exception:
				pass
			try:
				await exit(0)
			except Exception:
				pass
	
		# Once we're here - we add our new command
		# Save the command to a list with the message
		newCommand = { 'Message': ctx.message, 'Success': False }
		self.commands.append(newCommand)
		
		while len(self.commands) > self.commandCount:
			# Remove the first item in the array until we're at our limit
			self.commands.pop(0)	
		

	async def oncommandcompletion(self, command, ctx):
		for command in self.commands:
			# command passed
			if command['Message'] == ctx.message:
				command['Success'] = True
