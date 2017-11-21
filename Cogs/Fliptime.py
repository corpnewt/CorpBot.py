import asyncio
import discord
import time
from   operator import itemgetter
from   discord.ext import commands
from   Cogs import ReadableTime
from   Cogs import DisplayName
from   Cogs import Mute

def setup(bot):
	# Add the bot and deps
	settings = bot.get_cog("Settings")
	mute     = bot.get_cog("Mute")
	bot.add_cog(Fliptime(bot, settings, mute))

# This is the Uptime module. It keeps track of how long the bot's been up

class Fliptime:

	# Init with the bot reference, and a reference to the settings var
	def __init__(self, bot, settings, mute):
		self.bot = bot
		self.settings = settings
		self.mute = mute

	async def message_edit(self, before_message, message):
		# Pipe the edit into our message func to respond if needed
		return await self.message(message)

	async def test_message(self, message):
		# Implemented to bypass having this called twice
		return { "Ignore" : False, "Delete" : False }

	async def message(self, message):
		# Check the message and see if we should allow it - always yes.
		# This module doesn't need to cancel messages.
		# Check if our server supports it
		table = self.settings.getServerStat(message.guild, "TableFlipMute")

		if not table:
			return { 'Ignore' : False, 'Delete' : False}

		# Check for admin status
		isAdmin = message.author.permissions_in(message.channel).administrator
		if not isAdmin:
			checkAdmin = self.settings.getServerStat(message.guild, "AdminArray")
			for role in message.author.roles:
				for aRole in checkAdmin:
					# Get the role that corresponds to the id
					if str(aRole['ID']) == str(role.id):
						isAdmin = True

		# Check if the message contains the flip chars
		conts = message.content
		face = table = False
		table_list  = [ '┻', '╙', '╨', '╜', 'ǝʃqɐʇ', '┺' ]
		front_list = [ '(' ]
		back_list  = [ ')', '）' ]
		if any(ext in conts for ext in front_list) and any(ext in conts for ext in back_list):
			face = True
		if any(ext in conts for ext in table_list):
			table = True
		if face and table:	
			# Contains all characters
			# Table flip - add time
			currentTime = int(time.time())
			cooldownFinal = currentTime+60
			alreadyMuted = self.settings.getUserStat(message.author, message.guild, "Muted")
			if not isAdmin:
				# Check if we're muted already
				previousCooldown = self.settings.getUserStat(message.author, message.guild, "Cooldown")
				if not previousCooldown:
					if alreadyMuted:
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
				# Do the actual muting
				await self.mute.mute(message.author, message.guild, cooldownFinal)

				await message.channel.send(res)
				return { 'Ignore' : True, 'Delete' : True }		

		return { 'Ignore' : False, 'Delete' : False}

	@commands.command(pass_context=True)
	async def tableflip(self, ctx, *, yes_no = None):
		"""Turns on/off table flip muting (bot-admin only; always off by default)."""

		# Check for admin status
		isAdmin = ctx.author.permissions_in(ctx.channel).administrator
		if not isAdmin:
			checkAdmin = self.settings.getServerStat(ctx.guild, "AdminArray")
			for role in ctx.author.roles:
				for aRole in checkAdmin:
					# Get the role that corresponds to the id
					if str(aRole['ID']) == str(role.id):
						isAdmin = True
		if not isAdmin:
			await ctx.send("You do not have permission to use this command.")
			return

		setting_name = "Table flip muting"
		setting_val  = "TableFlipMute"

		current = self.settings.getServerStat(ctx.guild, setting_val)
		if yes_no == None:
			if current:
				msg = "{} currently *enabled.*".format(setting_name)
			else:
				msg = "{} currently *disabled.*".format(setting_name)
		elif yes_no.lower() in [ "yes", "on", "true", "enabled", "enable" ]:
			yes_no = True
			if current == True:
				msg = '{} remains *enabled*.'.format(setting_name)
			else:
				msg = '{} is now *enabled*.'.format(setting_name)
		elif yes_no.lower() in [ "no", "off", "false", "disabled", "disable" ]:
			yes_no = False
			if current == False:
				msg = '{} remains *disabled*.'.format(setting_name)
			else:
				msg = '{} is now *disabled*.'.format(setting_name)
		else:
			msg = "That's not a valid setting."
			yes_no = current
		if not yes_no == None and not yes_no == current:
			self.settings.setServerStat(ctx.guild, setting_val, yes_no)
		await ctx.send(msg)
