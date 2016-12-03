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

	def message(self, message):
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
		if message.content.startswith('(') and message.content.endswith('┻'):
			# Table flip - add time
			currentTime = int(time.time())
			cooldownFinal = currentTime+60
			coolText = ReadableTime.getReadableTimeBetween(currentTime, cooldownFinal)
			alreadyMuted = self.settings.getUserStat(message.author, message.server, "Muted")
			if not isAdmin and alreadyMuted.lower() == "no":
				self.settings.setUserStat(message.author, message.server, "Muted", "Yes")
				self.settings.setUserStat(message.author, message.server, "Cooldown", cooldownFinal)
				res = '┬─┬ ノ( ゜-゜ノ)  *{}*, we don\'t flip tables here.  You should cool down for *{}*'.format(DisplayName.name(message.author), coolText)
				return { 'Ignore' : True, 'Delete' : True, 'Respond' : res }		

		return { 'Ignore' : False, 'Delete' : False}