import asyncio
import discord
import os
from   datetime import datetime
from   discord.ext import commands
from   Cogs import DisplayName

# This is the Torment module. It spams the target with pings for awhile

class RateLimit:

	# Init with the bot reference, and a reference to the settings var
	def __init__(self, bot, settings):
		self.bot = bot
		self.waitBetween = 1 # number of seconds to wait before sending another message

	@commands.command(pass_context=True)
	async def torment(self, ctx, *, member = None, times : int = None):
		"""Deals some vigilante justice (owner only)."""

		channel = ctx.message.channel
		author  = ctx.message.author
		server  = ctx.message.server

		# Only allow owner to change server stats
		serverDict = self.settings.serverDict

		try:
			owner = serverDict['Owner']
		except KeyError:
			owner = None

		if owner == None:
			# No owner set
			msg = 'I have not been claimed, *yet*.'
			await self.bot.send_message(channel, msg)
			return
		else:
			if not author.id == owner:
				msg = 'You are not the *true* owner of me.  Only the rightful owner can use this command.'
				await self.bot.send_message(channel, msg)
				return
				
		usage = 'Usage: `{}torment [role/member] [times]`'.format(ctx.prefix)

		isRole = False

		if member == None:
			await self.bot.send_message(ctx.message.channel, usage)
			return
				
		# Check for formatting issues
		if times == None:
			# Either xp wasn't set - or it's the last section
			if type(member) is str:
				# It' a string - the hope continues
				roleCheck = DisplayName.checkRoleForInt(member, server)
				if roleCheck and roleCheck["Role"]:
					isRole = True
					member   = roleCheck["Role"]
					times = roleCheck["Int"]
				else:
					# Role is invalid - check for member instead
					nameCheck = DisplayName.checkNameForInt(member, server)
					if not nameCheck:
						await self.bot.send_message(ctx.message.channel, usage)
						return
					if not nameCheck["Member"]:
						msg = 'I couldn\'t find that user or role on the server.'.format(member)
						await self.bot.send_message(ctx.message.channel, msg)
						return
					member   = nameCheck["Member"]
					times = nameCheck["Int"]

		if times == None:
			# Still no times - roll back to default
			times = 25
		
		for i in range(0, times):
			# Do this over time
			await self.bot.send_message(ctx.message.channel, '*{}*'.format(member.mention))
			await asyncio.sleep(self.waitBetween)
		