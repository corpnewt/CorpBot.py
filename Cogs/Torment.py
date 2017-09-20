import asyncio
import discord
import os
from   datetime import datetime
from   discord.ext import commands
from   Cogs import DisplayName

def setup(bot):
	# Add the bot and deps
	settings = bot.get_cog("Settings")
	bot.add_cog(Torment(bot, settings))

# This is the Torment module. It spams the target with pings for awhile

class Torment:

	# Init with the bot reference, and a reference to the settings var
	def __init__(self, bot, settings):
		self.bot = bot
		self.waitBetween = 1 # number of seconds to wait before sending another message
		self.settings = settings
		self.toTorment = False
		
	@commands.command(pass_context=True, hidden=True)
	async def tormentdelay(self, ctx, delay : int = None):
		"""Sets the delay in seconds between messages (owner only)."""
		
		channel = ctx.message.channel
		author  = ctx.message.author
		server  = ctx.message.guild

		# Only allow owner to change server stats
		isOwner = self.settings.isOwner(ctx.author)
		if isOwner == None:
			return
		elif isOwner == False:
			return
		
		if delay == None:
			if self.waitBetween == 1:
				await ctx.message.author.send('Current torment delay is *1 second.*')
			else:
				await ctx.message.author.send('Current torment delay is *{} seconds.*'.format(self.waitBetween))
			return
		
		try:
			delay = int(delay)
		except Exception:
			await ctx.message.author.send('Delay must be an int.')
			return
		
		if delay < 1:
			await ctx.message.author.send('Delay must be at least *1 second*.')
			return
		
		self.waitBetween = delay
		if self.waitBetween == 1:
			await ctx.message.author.send('Current torment delay is now *1 second.*')
		else:
			await ctx.message.author.send('Current torment delay is now *{} seconds.*'.format(self.waitBetween))
		
	
	@commands.command(pass_context=True, hidden=True)
	async def canceltorment(self, ctx):
		"""Cancels tormenting if it's in progress - must be false when next torment attempt starts to work (owner only)."""
		
		channel = ctx.message.channel
		author  = ctx.message.author
		server  = ctx.message.guild

		# Only allow owner to change server stats
		isOwner = self.settings.isOwner(ctx.author)
		if isOwner == None:
			return
		elif isOwner == False:
			return
			
		if not self.toTorment:
			await ctx.message.author.send('Not currently tormenting.')
			return
		# Cancel it!
		self.toTorment = False
		await ctx.message.author.send('Tormenting cancelled.')
		
		
	@commands.command(pass_context=True, hidden=True)
	async def torment(self, ctx, *, member = None, times : int = None):
		"""Deals some vigilante justice (owner only)."""

		channel = ctx.message.channel
		author  = ctx.message.author
		server  = ctx.message.guild
		message = ctx.message

		# Only allow owner to change server stats
		isOwner = self.settings.isOwner(ctx.author)
		if isOwner == None:
			return
		elif isOwner == False:
			return
				
		usage = 'Usage: `{}torment [role/member] [times]`'.format(ctx.prefix)

		isRole = False

		if member == None:
			await ctx.channel.send(usage)
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
						await ctx.channel.send(usage)
						return
					if not nameCheck["Member"]:
						msg = 'I couldn\'t find that user or role on the server.'.format(member)
						await ctx.channel.send(msg)
						return
					member   = nameCheck["Member"]
					times = nameCheck["Int"]
					
		# Set the torment flag
		self.toTorment = True

		if times == None:
			# Still no times - roll back to default
			times = 25
			
		if times > 100:
			times = 100
			
		if times == 0:
			await ctx.channel.send('Oooooh - I bet they feel *sooooo* tormented...')
			return
		
		if times < 0:
			await ctx.channel.send('I just uh... *un-tormented* them.  Yeah.')
			return
		
		# Delete original torment message
		await message.delete()

		for i in range(0, times):
			# Do this over time
			try:
				await channel.send('*{}*'.format(member.mention))
			except Exception:
				pass
			for j in range(0, self.waitBetween):
				# Wait for 1 second, then check if we should cancel - then wait some more
				await asyncio.sleep(1)
				if not self.toTorment:
					return


	@commands.command(pass_context=True, hidden=True)
	async def stealthtorment(self, ctx, *, member = None, times : int = None):
		"""Deals some sneaky vigilante justice (owner only)."""

		channel = ctx.message.channel
		author  = ctx.message.author
		server  = ctx.message.guild
		message = ctx.message

		# Only allow owner
		isOwner = self.settings.isOwner(ctx.author)
		if isOwner == None:
			return
		elif isOwner == False:
			return
				
		usage = 'Usage: `{}torment [role/member] [times]`'.format(ctx.prefix)

		isRole = False

		if member == None:
			await ctx.channel.send(usage)
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
						await ctx.channel.send(usage)
						return
					if not nameCheck["Member"]:
						msg = 'I couldn\'t find that user or role on the server.'.format(member)
						await ctx.channel.send(msg)
						return
					member   = nameCheck["Member"]
					times = nameCheck["Int"]
					
		# Set the torment flag
		self.toTorment = True

		if times == None:
			# Still no times - roll back to default
			times = 25
			
		if times > 100:
			times = 100
			
		if times == 0:
			await ctx.channel.send('Oooooh - I bet they feel *sooooo* tormented...')
			return
		
		if times < 0:
			await ctx.channel.send('I just uh... *un-tormented* them.  Yeah.')
			return

		# Delete original torment message
		await message.delete()
		
		for i in range(0, times):
			# Do this over time
			try:
				tmessage = await ctx.channel.send('*{}*'.format(member.mention))
				await tmessage.delete()
			except Exception:
				pass
			for j in range(0, self.waitBetween):
				# Wait for 1 second, then check if we should cancel - then wait some more
				await asyncio.sleep(1)
				if not self.toTorment:
					return


	@commands.command(pass_context=True, hidden=True)
	async def servertorment(self, ctx, *, member = None, times : int = None):
		"""Deals some vigilante justice in all channels (owner only)."""

		channel = ctx.message.channel
		author  = ctx.message.author
		server  = ctx.message.guild
		message = ctx.message

		# Only allow owner
		isOwner = self.settings.isOwner(ctx.author)
		if isOwner == None:
			return
		elif isOwner == False:
			return
				
		usage = 'Usage: `{}torment [role/member] [times]`'.format(ctx.prefix)

		isRole = False

		if member == None:
			await ctx.channel.send(usage)
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
						await ctx.channel.send(usage)
						return
					if not nameCheck["Member"]:
						msg = 'I couldn\'t find that user or role on the server.'.format(member)
						await ctx.channel.send(msg)
						return
					member   = nameCheck["Member"]
					times = nameCheck["Int"]
					
		# Set the torment flag
		self.toTorment = True

		if times == None:
			# Still no times - roll back to default
			times = 25
			
		if times > 100:
			times = 100
			
		if times == 0:
			await ctx.channel.send('Oooooh - I bet they feel *sooooo* tormented...')
			return
		
		if times < 0:
			await ctx.channel.send('I just uh... *un-tormented* them.  Yeah.')
			return

		# Delete original torment message
		await message.delete()
		
		for i in range(0, times):
			# Do this over time
			for channel in server.channels:
				# Get user's permissions
				if channel.permissions_for(member).read_messages and type(channel) is discord.TextChannel:
					# Only ping where they can read
					try:
						await channel.send('*{}*'.format(member.mention))
					except Exception:
						pass
			for j in range(0, self.waitBetween):
				# Wait for 1 second, then check if we should cancel - then wait some more
				await asyncio.sleep(1)
				if not self.toTorment:
					return


	@commands.command(pass_context=True, hidden=True)
	async def stealthservertorment(self, ctx, *, member = None, times : int = None):
		"""Deals some sneaky vigilante justice in all channels (owner only)."""

		channel = ctx.message.channel
		author  = ctx.message.author
		server  = ctx.message.guild
		message = ctx.message

		# Only allow owner
		isOwner = self.settings.isOwner(ctx.author)
		if isOwner == None:
			return
		elif isOwner == False:
			return
				
		usage = 'Usage: `{}torment [role/member] [times]`'.format(ctx.prefix)

		isRole = False

		if member == None:
			await ctx.channel.send(usage)
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
						await ctx.channel.send(usage)
						return
					if not nameCheck["Member"]:
						msg = 'I couldn\'t find that user or role on the server.'.format(member)
						await ctx.channel.send(msg)
						return
					member   = nameCheck["Member"]
					times = nameCheck["Int"]
					
		# Set the torment flag
		self.toTorment = True

		if times == None:
			# Still no times - roll back to default
			times = 25
			
		if times > 100:
			times = 100
			
		if times == 0:
			await ctx.channel.send('Oooooh - I bet they feel *sooooo* tormented...')
			return
		
		if times < 0:
			await ctx.channel.send('I just uh... *un-tormented* them.  Yeah.')
			return

		# Delete original torment message
		await message.delete()
		
		for i in range(0, times):
			# Do this over time
			for channel in server.channels:
				# Get user's permissions
				if channel.permissions_for(member).read_messages and type(channel) is discord.TextChannel:
					# Only ping where they can read
					try:
						tmessage = await channel.send('*{}*'.format(member.mention))
						await tmessage.delete()
					except Exception:
						pass
			for j in range(0, self.waitBetween):
				# Wait for 1 second, then check if we should cancel - then wait some more
				await asyncio.sleep(1)
				if not self.toTorment:
					return
