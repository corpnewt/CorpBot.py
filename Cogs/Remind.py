import asyncio
import discord
import time
import parsedatetime
from   datetime import datetime
from   operator import itemgetter
from   discord.ext import commands
from   Cogs import ReadableTime
from   Cogs import DisplayName

# This is the Remind module. It sends a pm to a user after a specified amount of time

# Reminder = { "End" : timeToEnd, "Message" : whatToSay }

class Remind:

	# Init with the bot reference, and a reference to the settings var
	def __init__(self, bot, settings):
		self.bot = bot
		self.settings = settings

	async def onready(self):
		# Check all reminders - and start timers
		for server in self.bot.servers:
			for member in server.members:
				reminders = self.settings.getUserStat(member, server, "Reminders")
				if len(reminders):
					# We have a list
					for reminder in reminders:
						self.bot.loop.create_task(self.checkRemind(member, reminder))

	async def checkRemind(self, member, reminder):
		# Start our countdown
		countDown = int(reminder['End'])-int(time.time())
		if countDown > 0:
			# We have a positive countdown - let's wait
			await asyncio.sleep(countDown)
		
		# Check if member is online - if so - remind them
		if not str(member.status).lower() == "offline":
			# Well, they're not Offline...
			reminders = self.settings.getUserStat(member, member.server, "Reminders")
			server = reminder['Server']
			message = reminder['Message']

			if not message:
				message = 'You wanted me to remind you of something...'
			msg = 'In *{}*, you wanted me to remind you:\n\n{}'.format(server, message)
			await self.bot.send_message(member, msg)
			reminders.remove(reminder)
			self.settings.setUserStat(member, member.server, "Reminders", reminders)
					

	async def status(self, member):
		# Check the user's status - and if they have any reminders
		# If so - pm them - if not, ignore
		if not str(member.status).lower() == "offline":
			# They're not offline
			currentTime = int(time.time())
			reminders = self.settings.getUserStat(member, member.server, "Reminders")
			removeList = []
			if len(reminders):
				# We have a list
				for reminder in reminders:
					timeLeft = int(reminder['End'])-currentTime
					if timeLeft <= 0:
						# Out of time - PM
						message = reminder['Message']
						server  = reminder['Server']
						if not message:
							message = 'You wanted me to remind you of something...'
						msg = 'In *{}*, you wanted me to remind you:\n\n{}'.format(server, message)
						await self.bot.send_message(member, msg)
						removeList.append(reminder)
			if len(removeList):
				# We have spent reminders
				for reminder in removeList:
					reminders.remove(reminder)
				self.settings.setUserStat(member, member.server, "Reminders", reminders)


	@commands.command(pass_context=True)
	async def remindme(self, ctx, message : str = None, *, endtime : str = None):
		"""Set a reminder."""

		if not endtime or not message:
			msg = 'Usage: `$remindme "[message]" [endtime]`'
			await self.bot.send_message(ctx.message.channel, msg)
			return

		# Get current time - and end time
		currentTime = int(time.time())
		cal         = parsedatetime.Calendar()
		time_struct, parse_status = cal.parse(endtime)
		start       = datetime(*time_struct[:6])
		end         = time.mktime(start.timetuple())

		# Get the time from now to end time
		timeFromNow = end-currentTime

		# Get our readable time
		readableTime = ReadableTime.getReadableTimeBetween(int(currentTime), int(end))

		# Add reminder
		reminders = self.settings.getUserStat(ctx.message.author, ctx.message.server, "Reminders")
		reminder = { 'End' : end, 'Message' : message, 'Server' : ctx.message.server.name }
		reminders.append(reminder)
		self.settings.setUserStat(ctx.message.author, ctx.message.server, "Reminders", reminders)

		# Start timer for reminder
		self.bot.loop.create_task(self.checkRemind(ctx.message.author, reminder))
		
		# Confirm the reminder
		msg = 'Okay *{}*, I\'ll remind you in *{}*.'.format(DisplayName.name(ctx.message.author), readableTime)
		await self.bot.send_message(ctx.message.channel, msg)

	@commands.command(pass_context=True)
	async def clearmind(self, ctx):
		"""Clear all reminders."""
		member = ctx.message.author

		self.settings.setUserStat(member, member.server, "Reminders", [])

		msg = 'Alright *{}*, your calendar has been cleared of reminders!'.format(DisplayName.name(ctx.message.author))
		await self.bot.send_message(ctx.message.channel, msg)