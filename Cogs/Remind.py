import asyncio
import discord
import time
import parsedatetime
from   datetime import datetime
from   operator import itemgetter
from   discord.ext import commands
from   Cogs import ReadableTime
from   Cogs import DisplayName
from   Cogs import Nullify

def setup(bot):
	# Add the bot and deps
	settings = bot.get_cog("Settings")
	bot.add_cog(Remind(bot, settings))

# This is the Remind module. It sends a pm to a user after a specified amount of time

# Reminder = { "End" : timeToEnd, "Message" : whatToSay }

class Remind:

	# Init with the bot reference, and a reference to the settings var
	def __init__(self, bot, settings):
		self.bot = bot
		self.settings = settings
		self.loop_list = []

	def suppressed(self, guild, msg):
		# Check if we're suppressing @here and @everyone mentions
		if self.settings.getServerStat(guild, "SuppressMentions"):
			return Nullify.clean(msg)
		else:
			return msg

	# Proof of concept stuff for reloading cog/extension
	def _is_submodule(self, parent, child):
		return parent == child or child.startswith(parent + ".")

	@asyncio.coroutine
	async def on_unloaded_extension(self, ext):
		# Called to shut things down
		if not self._is_submodule(ext.__name__, self.__module__):
			return
		for task in self.loop_list:
			task.cancel()

	@asyncio.coroutine
	async def on_loaded_extension(self, ext):
		# See if we were loaded
		if not self._is_submodule(ext.__name__, self.__module__):
			return
		# Check all reminders - and start timers
		for server in self.bot.guilds:
			for member in server.members:
				reminders = self.settings.getUserStat(member, server, "Reminders")
				if len(reminders):
					# We have a list
					for reminder in reminders:
						self.loop_list.append(self.bot.loop.create_task(self.checkRemind(member, reminder)))

	'''async def onready(self):
		# Check all reminders - and start timers
		for server in self.bot.guilds:
			for member in server.members:
				reminders = self.settings.getUserStat(member, server, "Reminders")
				if len(reminders):
					# We have a list
					for reminder in reminders:
						self.bot.loop.create_task(self.checkRemind(member, reminder))'''


	async def checkRemind(self, member, reminder):
		# Get our current task
		task = asyncio.Task.current_task()
		# Start our countdown
		countDown = int(reminder['End'])-int(time.time())
		if countDown > 0:
			# We have a positive countdown - let's wait
			await asyncio.sleep(countDown)
		
		# Check if member is online - if so - remind them
		if not member.status == discord.Status.offline:
			# Well, they're not Offline...
			reminders = self.settings.getUserStat(member, member.guild, "Reminders")
			# Verify reminder is still valid
			if not reminder in reminders:
				return
			server = reminder['Server']
			message = reminder['Message']

			if not message:
				message = 'You wanted me to remind you of something...'
			msg = 'In *{}*, you wanted me to remind you:\n\n{}'.format(server, message)
			try:
				await member.send(msg)
			except:
				pass
			reminders.remove(reminder)
			self.settings.setUserStat(member, member.guild, "Reminders", reminders)
		self._remove_task(task)
					
	async def member_update(self, before, member):
		# Not sure why I was using this "status" method before... seems to only show up here
		# and not used in the Main.py - probably some serious brain-thought.
		#### async def status(self, member): ####
		# Check the user's status - and if they have any reminders
		# If so - pm them - if not, ignore
		if not member.status == discord.Status.offline:
			# They're not offline
			currentTime = int(time.time())
			reminders = self.settings.getUserStat(member, member.guild, "Reminders")
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
						await member.send(msg)
						removeList.append(reminder)
			if len(removeList):
				# We have spent reminders
				for reminder in removeList:
					reminders.remove(reminder)
				self.settings.setUserStat(member, member.guild, "Reminders", reminders)


	@commands.command(pass_context=True)
	async def remindme(self, ctx, message : str = None, *, endtime : str = None):
		"""Set a reminder."""

		if not endtime or not message:
			msg = 'Usage: `{}remindme "[message]" [endtime]`'.format(ctx.prefix)
			await ctx.channel.send(msg)
			return

		# Get current time - and end time
		currentTime = int(time.time())
		cal         = parsedatetime.Calendar()
		time_struct, parse_status = cal.parse(endtime)
		start       = datetime(*time_struct[:6])
		end         = time.mktime(start.timetuple())

		# Get the time from now to end time
		timeFromNow = end-currentTime

		if timeFromNow < 1:
			# Less than a second - set it to 1 second
			end = currentTime+1
			timeFromNow = 1

		# Get our readable time
		readableTime = ReadableTime.getReadableTimeBetween(int(currentTime), int(end))

		# Add reminder
		reminders = self.settings.getUserStat(ctx.message.author, ctx.message.guild, "Reminders")
		reminder = { 'End' : end, 'Message' : message, 'Server' : self.suppressed(ctx.guild, ctx.guild.name) }
		reminders.append(reminder)
		self.settings.setUserStat(ctx.message.author, ctx.message.guild, "Reminders", reminders)

		# Start timer for reminder
		self.loop_list.append(self.bot.loop.create_task(self.checkRemind(ctx.message.author, reminder)))
		
		# Confirm the reminder
		msg = 'Okay *{}*, I\'ll remind you in *{}*.'.format(DisplayName.name(ctx.message.author), readableTime)
		await ctx.channel.send(msg)

	@commands.command(pass_context=True)
	async def reminders(self, ctx, *, member = None):
		"""List up to 10 pending reminders - pass a user to see their reminders."""

		# Check if we're suppressing @here and @everyone mentions
		if self.settings.getServerStat(ctx.message.guild, "SuppressMentions"):
			suppress = True
		else:
			suppress = False

		if type(member) is str:
			memberName = member
			member = DisplayName.memberForName(memberName, ctx.message.guild)
			if not member:
				msg = 'I couldn\'t find *{}*...'.format(memberName)
				# Check for suppress
				if suppress:
					msg = Nullify.clean(msg)
				await ctx.message.channel.send(msg)
				return

		if not member:
			member = ctx.message.author
		
		myReminders = self.settings.getUserStat(member, member.guild, "Reminders")
		if member == ctx.message.author:
			msg = 'You don\'t currently have any reminders set.  You can add some with the `{}remindme "[message]" [time]` command.'.format(ctx.prefix)
		else:
			msg = '*{}* doesn\'t currently have any reminders set.  They can add some with the `{}remindme "[message]" [time]` command.'.format(DisplayName.name(member), ctx.prefix)

		if not len(myReminders):
			# No reminders
			await ctx.channel.send(msg)
			return
		
		mySorted = sorted(myReminders, key=lambda x:int(x['End']))
		currentTime = int(time.time())
		total  = 10 # Max number to list
		remain = 0

		if len(mySorted) < 10:
			# Less than 10 - set the total
			total = len(mySorted)
		else:
			# More than 10 - let's find out how many remain after
			remain = len(mySorted)-10

		if len(mySorted):
			# We have at least 1 item
			msg = '***{}\'s*** **Remaining Reminders:**\n'.format(DisplayName.name(member))

		for i in range(0, total):
			endTime = int(mySorted[i]['End'])
			# Get our readable time
			readableTime = ReadableTime.getReadableTimeBetween(currentTime, endTime)
			msg = '{}\n{}. {} - in *{}*'.format(msg, i+1, mySorted[i]['Message'], readableTime)
		
		if remain == 1:
			msg = '{}\n\nYou have *{}* additional reminder.'.format(msg, remain)
		elif remain > 1:
			msg = '{}\n\nYou have *{}* additional reminders.'.format(msg, remain)

		# Check for suppress
		if suppress:
			msg = Nullify.clean(msg)

		await ctx.channel.send(msg)


	@commands.command(pass_context=True)
	async def clearmind(self, ctx, *, index = None):
		"""Clear the reminder index passed - or all if none passed."""
		member = ctx.message.author
		
		# Check if we're suppressing @here and @everyone mentions
		if self.settings.getServerStat(ctx.message.guild, "SuppressMentions"):
			suppress = True
		else:
			suppress = False
			
		reminders = self.settings.getUserStat(member, member.guild, "Reminders")
		reminders = sorted(reminders, key=lambda x:int(x['End']))
		if not len(reminders):
			# No reminders
			msg = "Oooh, look at you, *so much to be reminded about*... Just kidding.  You don't have any reminders to clear."
			await ctx.channel.send(msg)
			return
		
		if index == None:
			self.settings.setUserStat(member, member.guild, "Reminders", [])
			msg = 'Alright *{}*, your calendar has been cleared of reminders!'.format(DisplayName.name(ctx.message.author))
			await ctx.channel.send(msg)
			return
		
		# We have something for our index
		try:
			index = int(index)
		except Exception:
			msg = 'Usage: `{}clearmind [index]`'.format(ctx.prefix)
			await ctx.channel.send(msg)
			return
		
		# We have an int
		if index < 1 or index > len(reminders):
			# Out of bounds!
			msg = "You'll have to pick an index between 1 and {}.".format(len(reminders))
			await ctx.channel.send(msg)
			return
		
		# We made it!  Valid index and all sorts of stuff
		removed = reminders.pop(index-1)
		self.settings.setUserStat(member, member.guild, "Reminders", reminders)
		msg = "I will no longer remind you: {}".format(removed["Message"])
		# Check for suppress
		if suppress:
			msg = Nullify.clean(msg)
		await ctx.channel.send(msg)
