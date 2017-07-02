import asyncio
import discord
import re
import os
import random
import string
from   discord.ext import commands
from   Cogs import Settings
from   Cogs import DisplayName
from   Cogs import Nullify
from   Cogs import FuzzySearch

class Telephone:

	# Init with the bot reference, and a reference to the settings var
	def __init__(self, bot, settings):
		self.bot = bot
		self.settings = settings
		self.switchboard = []

	async def onready(self):
		# Clear any previous games
		for guild in self.bot.guilds:
			self.settings.setServerStat(guild, "TeleConnected", False)

	async def ontyping(self, channel, user, when):
		# Check if the channel is typing, and send typing to receiving
		# channels if in call
		# Don't listen to bots
		if user.bot:
			return
		call = self._incall(channel.guild)
		if not call:
			return
		for caller in call['Members']:
			if caller is channel.guild:
				continue
			# Get the tele channel
			call_channel = self._gettelechannel(caller)
			if not call_channel:
				continue
			await call_channel.trigger_typing()

	def _gettelechannel(self, server):
		teleChannel = self.settings.getServerStat(server, "TeleChannel")
		if teleChannel:
			teleChannel = DisplayName.channelForName(str(teleChannel), server, "text")
		if teleChannel == "":
			return None
		return teleChannel

	def _getsafenumber(self, number, server):
		numeric = "0123456789"
		found = False
		for guild in self.bot.guilds:
			if guild.id == server.id:
				continue
			teleNum = self.settings.getServerStat(guild, "TeleNumber")
			if teleNum == number:
				found = True
				break
		if not found:
			return number
		while True:
			found = False
			newNum = "".join(random.choice(numeric) for i in range(7))
			for guild in self.bot.guilds:
				teleNum = self.settings.getServerStat(guild, "TeleNumber")
				if teleNum == newNum:
					found = True
					break
			if not found:
				return newNum

	def _incall(self, server):
		for call in self.switchboard:
			if server in call["Members"]:
				return call
		return None	

	def _getothernumber(self, call, server):
		# Returns the other caller's number
		if not server in call["Members"]:
			# We're uh.. not in this call
			return None
		for member in call["Members"]:
			if not member is server:
				# HA! GOTEM
				return self.settings.getServerStat(member, "TeleNumber")

	def _hangup(self, caller):
		# Hangs up all calls the caller is in
		for call in self.switchboard:
			if caller in call["Members"]:
				self.switchboard.remove(call)

	@commands.command(pass_context=True)
	async def phonebook(self, ctx, *, look_up = None):
		"""Displays up to 20 entries in the phone book - or optionally lets you search for a server name or number."""
		# Build our phone list
		entries = []
		for guild in self.bot.guilds:
			teleNum = self.settings.getServerStat(guild, "TeleNumber")
			if teleNum:
				entries.append({ "Name": guild.name, "Number": teleNum })

		if not len(entries):
			await ctx.send(":telephone: The phonebook is *empty!*")
			return
		
		max_entries = 20
		if look_up == None:
			if len(entries) > 20:
				title = ":telephone: __First 20 of {} Phonebook Entries:__\n\n".format(len(entries))
			else:
				max_entries = len(entries)
				title = ":telephone: __Phonebook:__\n\n"
			count = 0
			for i in entries:
				count += 1
				num = i['Number']
				i_form = num[:3] + "-" + num[3:]
				title += "{}. {} - *{}*\n".format(count, i["Name"], i_form)
			await ctx.send(title)
			return

		# Search time!
		look_up_num = re.sub(r'\W+', '', look_up)
		id_ratio = 0
		if len(look_up_num):
			idMatch = FuzzySearch.search(look_up_num, entries, 'Number', 3)
			id_ratio = idMatch[0]['Ratio']
			if id_ratio == 1:
				# Found it!
				num = idMatch[0]['Item']['Number']
				i_form = num[:3] + "-" + num[3:]
				msg = ":telephone: __Phonebook:__\n\n{} - *{}*".format(idMatch[0]['Item']['Name'], i_form)
				await ctx.send(msg)
				return
		# Look up by name now
		nameMatch = FuzzySearch.search(look_up, entries, 'Name', 3)
		if nameMatch[0]['Ratio'] == 1:
			# Exact name
			# Found it!
			num = nameMatch[0]['Item']['Number']
			i_form = num[:3] + "-" + num[3:]
			msg = ":telephone: __Phonebook:__\n\n{} - *{}*".format(nameMatch[0]['Item']['Name'], i_form)
			await ctx.send(msg)
			return
		# now we need to find which is better
		matchCheck = []
		if nameMatch[0]['Ratio'] > id_ratio:
			matchCheck = nameMatch
		else:
			matchCheck = idMatch

		msg = ":telephone: __Phonebook - Closest Matches:__\n\n"
		count = 0
		for m in matchCheck:
			count += 1
			num = m['Item']['Number']
			i_form = num[:3] + "-" + num[3:]
			msg += "{}. {} - *{}*\n".format(count, m['Item']['Name'], i_form)

		await ctx.send(msg)

	@commands.command(pass_context=True)
	async def telenumber(self, ctx):
		"""Prints your telephone number."""
		teleNum = self.settings.getServerStat(ctx.guild, "TeleNumber")
		if not teleNum:
			await ctx.send(":telephone: is currently *disabled*.")
			return
		teleNumFormat = teleNum[:3] + "-" + teleNum[3:]
		await ctx.send("Your :telephone: number is: *{}*".format(teleNumFormat))

	@commands.command(pass_context=True)
	async def settelechannel(self, ctx, *, channel = None):
		"""Sets the channel for telephone commands - or disables that if nothing is passed (admin only)."""
		isAdmin = ctx.message.author.permissions_in(ctx.message.channel).administrator
		# Only allow admins to change server stats
		if not isAdmin:
			await ctx.channel.send('You do not have sufficient privileges to access this command.')
			return
		if channel == None:
			self.settings.setServerStat(ctx.message.guild, "TeleChannel", "")
			msg = ':telephone: *disabled*.'
			await ctx.channel.send(msg)
			return
		channel = DisplayName.channelForName(channel, ctx.guild, "text")
		if channel == None:
			await ctx.send("I couldn't find that channel :(")
			return
		self.settings.setServerStat(ctx.message.guild, "TeleChannel", channel.id)
		teleNumber = self._getsafenumber(str(channel.id)[len(str(channel.id))-7:], ctx.guild)
		self.settings.setServerStat(ctx.guild, "TeleNumber", teleNumber)
		
		msg = ':telephone: channel set to **{}**.'.format(channel.name)
		await ctx.channel.send(msg)

	@commands.command(pass_context=True)
	async def telechannel(self, ctx):
		"""Prints the current channel for telephone commands."""
		teleChan = self.settings.getServerStat(ctx.guild, "TeleChannel")
		if not teleChan:
			await ctx.send(":telephone: is currently *disabled*.")
			return
		channel = DisplayName.channelForName(str(teleChan), ctx.guild, "text")
		if channel:
			await ctx.send("The current :telephone: channel is **{}**.".format(channel.name))
			return
		await ctx.send("Channel id: *{}* no longer exists on this server.  Consider updating this setting!".format(teleChan))

	@commands.command(pass_context=True)
	async def call(self, ctx, *, number = None):
		"""Calls the passed number.  Can use *67 to hide your identity - or *69 to connect to the last incoming call (ignored if another number is present)."""
		teleChan = self._gettelechannel(ctx.guild)
		if not teleChan:
			await ctx.send(":telephone: is currently *disabled*.  You can set it up with `{}settelechannel [channel]`".format(ctx.prefix))
			return
		
		# Check if we're already in a call
		incall = self._incall(ctx.guild)
		if incall:
			if incall["Hidden"]:
				call_with = "UNKOWN CALLER"
			else:
				teleNum = self._getothernumber(incall, ctx.guild)
				call_with = teleNum[:3] + "-" + teleNum[3:]
			# Busy :(
			caller = self._gettelechannel(ctx.guild)
			if caller:
				await caller.send(":telephone: You're already in a call with: *{}*".format(call_with))
				return

		hidden = False
		target = None
		dial_hide = False
		if not number == None:
			if "*67" in number:
				hidden = True
			if "*69" in number:
				target = self.settings.getServerStat(ctx.guild, "LastCall")
				if self.settings.getServerStat(ctx.guild, "LastCallHidden").lower() == "yes":
					dial_hide = True
			number = number.replace("*67", "").replace("*69", "")
			number = re.sub(r'\W+', '', number)
			if len(number):
				dial_hide = False
				target = number
		await self._dial(ctx.guild, target, hidden, dial_hide)

	async def _dial(self, caller, target, hidden, dial_hide):
		if target == None:
			# Need a random number
			numbers = []
			for guild in self.bot.guilds:
				if guild.id == caller.id:
					continue
				teleNum = self.settings.getServerStat(guild, "TeleNumber")
				if teleNum:
					numbers.append(guild)
			if len(numbers):
				target = random.choice(numbers)
		else:
			found = False
			for guild in self.bot.guilds:
				teleNum = self.settings.getServerStat(guild, "TeleNumber")
				if teleNum == target:
					if guild.id == caller.id:
						# We're uh... calling ourselves.
						caller = self._gettelechannel(caller)
						if caller:
							await caller.send(":telephone: ***Beep beep beep beep!*** *Busy signal...*")
							return
					found = True
					target = guild
					break
			if not found:
				target = None
		if target == None:
			# We didn't find a server to connect to
			caller = self._gettelechannel(caller)
			if caller:
				await caller.send(":telephone: ***Beep beep beep!***  *We're sorry, the number you've dialed is not in service at this time.*")
				return

		target_channel = self._gettelechannel(target)
		if target_channel == None:
			# We found a server - but they have no telechannel
			caller = self._gettelechannel(caller)
			if caller:
				await caller.send(":telephone: ***Beep beep beep!***  *We're sorry, the number you've dialed is not in service at this time.*")
				return

		# Check if the caller is in a call currently
		if self._incall(target):
			# Busy :(
			caller = self._gettelechannel(caller)
			if caller:
				await caller.send(":telephone: ***Beep beep beep beep!*** *Busy signal...*")
				return
		
		# Ring!
		await self._ring(caller, target, hidden, dial_hide)

	async def _ring(self, caller, receiver, hidden, dial_hide):
		# This should be called when he have a valid caller, receiver, and no one is busy
		receiver_chan = self._gettelechannel(receiver)
		caller_chan   = self._gettelechannel(caller)

		if receiver_chan == None or caller_chan == None:
			# No dice
			return

		# Add both to the call list
		self.switchboard.append({ "Members": [caller, receiver], "Hidden": hidden })

		# Let the caller know we're dialing
		msg = ":telephone: Dialing..."
		teleNum = self.settings.getServerStat(receiver, "TeleNumber")
		msg_add = []
		if hidden:
			msg_add.append("*67 ")
		if dial_hide:
			msg_add.append("###-")
			msg_add.append("####")
		else:
			msg_add.append(teleNum[:3]+"-")
			msg_add.append(teleNum[3:])
		
		# Send dialing
		message = await caller_chan.send(msg)
		# Dialing edits
		for i in msg_add:
			msg += i
			await message.edit(content=msg)
			await asyncio.sleep(0.5)
		
		# Here - we should have "dialed"
		# Send a message to the other channel that there's a call incoming
		# Save last call
		self.settings.setServerStat(receiver, "LastCall", self.settings.getServerStat(caller, "TeleNumber"))
		if hidden:
			caller_number = "UNKNOWN CALLER"
			self.settings.setServerStat(receiver, "LastCallHidden", "Yes")
		else:
			self.settings.setServerStat(receiver, "LastCallHidden", "No")
			caller_number = self.settings.getServerStat(caller, "TeleNumber")
			caller_number = caller_number[:3] + "-" + caller_number[3:]
		await receiver_chan.send(":telephone: Incoming call from: *{}*\nType *pickup* to answer.".format(caller_number))

		# Ring for 30 seconds - then report no answer
		# Setup the check
		def check(msg):
			if msg.author.bot:
				return False
			m_cont = msg.content.lower()
			if msg.channel == receiver_chan and m_cont == "pickup":
				return True
			if msg.channel == caller_chan and m_cont == "hangup":
				return True
			return False
		# Wait for a response
		try:
			talk = await self.bot.wait_for('message', check=check, timeout=30)
		except Exception:
			talk = None

		if talk == None:
			# No answer - hangup
			self._hangup(caller)
			await caller_chan.send(":telephone: No answer...")
			await receiver_chan.send(":telephone: Ringing stops.")
			return
		elif talk.content.lower() == "hangup":
			# You hung up the call
			self._hangup(caller)
			await caller_chan.send(":telephone: You have hung up.")
			await receiver_chan.send(":telephone: Ringing stops.")
			return
		
		# They answered!
		await caller_chan.send(":telephone_receiver: Connected.\nType *hangup* to end the call.")
		await receiver_chan.send(":telephone_receiver: Connected.\nType *hangup* to end the call.")
		# Wait on the call
		while True:
			# Setup the check
			def check_in_call(msg):	
				if msg.author.bot:
					return False
				if msg.channel == receiver_chan or msg.channel == caller_chan:
					return True
			try:
				# 1 minute timeout
				talk = await self.bot.wait_for('message', check=check_in_call, timeout=60)
			except Exception:
				talk = None
			if talk == None:
				# Timed out
				self._hangup(caller)
				self._hangup(receiver)
				await caller_chan.send(":telephone: Disconnected.")
				await receiver_chan.send(":telephone: Disconnected.")
				return
			elif talk.content.lower() == "hangup":
				# One side hung up
				self._hangup(caller)
				self._hangup(receiver)
				if talk.channel == caller_chan:
					# The caller disconnected
					await receiver_chan.send(":telephone: The other phone was hung up.")
					await caller_chan.send(":telephone: You have hung up.")
				else:
					# The receiver disconnected
					await caller_chan.send(":telephone: The other phone was hung up.")
					await receiver_chan.send(":telephone: You have hung up.")
				return
			else:
				talk_msg = Nullify.clean(talk.content)
				# Must be conversation
				if talk.channel == caller_chan:
					# Coming from the talking channel
					if hidden:
						await receiver_chan.send(":telephone_receiver: " + talk_msg)
					else:
						user = DisplayName.name(talk.author)
						await receiver_chan.send(":telephone_receiver: *{}:* {}".format(user, talk_msg))
				else:
					user = DisplayName.name(talk.author)
					await caller_chan.send(":telephone_receiver: *{}:* {}".format(user, talk_msg))