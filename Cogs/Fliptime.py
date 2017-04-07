import asyncio
import discord
import time
from   operator import itemgetter
from   discord.ext import commands
from   Cogs import ReadableTime
from   Cogs import DisplayName

# This is the Uptime module. It keeps track of how long the bot's been up

class Fliptime:

	# Init with the bot reference, and a reference to the settings var
	def __init__(self, bot, settings):
		self.bot = bot
		self.settings = settings

	async def message_edit(self, before_message, message):
		# Pipe the edit into our message func to respond if needed
		return await self.message(message)
		
	async def message(self, message):
		# Check the message and see if we should allow it - always yes.
		# This module doesn't need to cancel messages.

		# Check for admin status
		isAdmin = message.author.permissions_in(message.channel).administrator
		if not isAdmin:
			checkAdmin = self.settings.getServerStat(message.server, "AdminArray")
			for role in message.author.roles:
				for aRole in checkAdmin:
					# Get the role that corresponds to the id
					if aRole['ID'] == role.id:
						isAdmin = True

		# Check if the message contains the flip chars

		# if message.content.startswith('(') and message.content.endswith('┻'):
		conts = message.content
		face = table = False
		if '(' in conts:
			if ')' in conts or '）' in conts:
				face = True
		if '┻' in conts or '┻' in conts or '╙' in conts or '╨' in conts or '╜' in conts or 'ǝʃqɐʇ' in conts:
			table = True
		if face and table:
			# Contains all characters
			# Table flip - add time
			currentTime = int(time.time())
			cooldownFinal = currentTime+60
			alreadyMuted = self.settings.getUserStat(message.author, message.server, "Muted")
			if not isAdmin:
				# Check if we're muted already
				previousCooldown = self.settings.getUserStat(message.author, message.server, "Cooldown")
				if not previousCooldown:
					if alreadyMuted.lower() == "yes":
						# We're perma-muted - ignore
						return { 'Ignore' : False, 'Delete' : False}

					previousCooldown = 0
				if int(previousCooldown) > currentTime:
					# Already cooling down - add to it.
					cooldownFinal = previousCooldown+60
					coolText = ReadableTime.getReadableTimeBetween(currentTime, cooldownFinal)
					res = '┬─┬ ノ( ゜-゜ノ)  *{}*, I understand that you\'re frustrated, but we still don\'t flip tables here.  Why don\'t you cool down for *{}* instead.'.format(DisplayName.name(message.author), coolText)
				else:
					# Not cooling down - start it
					coolText = ReadableTime.getReadableTimeBetween(currentTime, cooldownFinal)
					res = '┬─┬ ノ( ゜-゜ノ)  *{}*, we don\'t flip tables here.  You should cool down for *{}*'.format(DisplayName.name(message.author), coolText)
				self.settings.setUserStat(message.author, message.server, "Cooldown", cooldownFinal)
				self.settings.setUserStat(message.author, message.server, "Muted", "Yes")
				await self.bot.send_message(message.channel, res)
				return { 'Ignore' : True, 'Delete' : True }		

		return { 'Ignore' : False, 'Delete' : False}
