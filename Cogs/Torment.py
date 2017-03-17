import asyncio
import discord
import os
from   datetime import datetime
from   discord.ext import commands
from   Cogs import DisplayName

# This is the Torment module. It spams the target with pings for awhile

class Torment:

	# Init with the bot reference, and a reference to the settings var
	def __init__(self, bot, settings):
		self.bot = bot
		self.waitBetween = 1 # number of seconds to wait before sending another message
		self.settings = settings
		self.torment = False
		
	@commands.command(pass_context=True, hidden=True)
	async def tormentdelay(self, ctx, delay : int = None):
		"""Sets the delay in seconds between messages (owner only)."""
		
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
		
		if delay == None:
			if self.waitBetween == 1:
				await self.bot.send_message(ctx.message.author, 'Current torment delay is *1 second.*')
			else:
				await self.bot.send_message(ctx.message.author, 'Current torment delay is *{} seconds.*'.format(self.waitBetween))
			return
		
		try:
			delay = int(delay)
		except Exception:
			await self.bot.send_message(ctx.message.author, 'Delay must be an int.')
			return
		
		if delay < 1:
			await self.bot.send_message(ctx.message.author, 'Delay must be at least 1 second.')
			return
		
		self.waitBetween = delay
		if self.waitBetween == 1:
			await self.bot.send_message(ctx.message.author, 'Current torment delay is now *1 second.*')
		else:
			await self.bot.send_message(ctx.message.author, 'Current torment delay is now *{} seconds.*'.format(self.waitBetween))
		
	
	@commands.command(pass_context=True, hidden=True)
	async def canceltorment(self, ctx):
		"""Cancels tormenting if it's in progress - must be false when next torment attempt starts to work (owner only)."""
		
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
			
		if not self.torment:
			await self.bot.send_message(ctx.message.author, 'Not currently tormenting.')
			return
		# Cancel it!
		self.torment = False
		await self.bot.send_message(ctx.message.author, 'Tormenting cancelled.')
		
		
	@commands.command(pass_context=True, hidden=True)
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
					
		# Set the torment flag
		self.torment = True

		if times == None:
			# Still no times - roll back to default
			times = 25
			
		if times > 100:
			times = 100
			
		if times == 0:
			await self.bot.send_message(ctx.message.channel, 'Oooooh - I bet they feel *sooooo* tormented...')
			return
		
		if times < 0:
			await self.bot.send_message(ctx.message.channel, 'I just uh... *un-tormented* them.  Yeah.')
			return
		
		for i in range(0, times):
			if not self.torment:
				break
			# Do this over time
			await self.bot.send_message(ctx.message.channel, '*{}*'.format(member.mention))
			await asyncio.sleep(self.waitBetween)
		
