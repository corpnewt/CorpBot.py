import asyncio
import discord
import time
import parsedatetime
from   datetime import datetime
from   discord.ext import commands
from   Cogs import ReadableTime, DisplayName, Utils, Nullify, Message, PickList

def setup(bot):
	# Add the bot and deps
	settings = bot.get_cog("Settings")
	bot.add_cog(Remind(bot, settings))

# This is the Remind module. It sends a pm to a user after a specified amount of time

# Reminder = { "End" : timeToEnd, "Message" : whatToSay }

class Remind(commands.Cog):

	# Init with the bot reference, and a reference to the settings var
	def __init__(self, bot, settings):
		self.bot = bot
		self.settings = settings
		self.loop_list = []
		global Utils, DisplayName
		Utils = self.bot.get_cog("Utils")
		DisplayName = self.bot.get_cog("DisplayName")

	# Proof of concept stuff for reloading cog/extension
	def _is_submodule(self, parent, child):
		return parent == child or child.startswith(parent + ".")

	@commands.Cog.listener()
	async def on_unloaded_extension(self, ext):
		# Called to shut things down
		if not self._is_submodule(ext.__name__, self.__module__):
			return
		for task in self.loop_list:
			task.cancel()

	@commands.Cog.listener()
	async def on_loaded_extension(self, ext):
		# See if we were loaded
		if not self._is_submodule(ext.__name__, self.__module__):
			return
		self.bot.loop.create_task(self.start_loading())

	async def start_loading(self):
		await self.bot.wait_until_ready()
		# await self.bot.loop.run_in_executor(None, self.check_reminders)
		await self.check_reminders()

	async def check_reminders(self):
		# Check all reminders - and start timers
		print("Checking reminders...")
		t = time.time()
		for user in self.bot.users:
			reminders = await self.bot.loop.run_in_executor(
				None,
				self.settings.getGlobalUserStat,
				user,
				"Reminders",
				[]
			)
			if reminders:
				for reminder in reminders:
					if reminder.get("bot_id") is None or reminder["bot_id"] == self.bot.user.id:
						self.loop_list.append(self.bot.loop.create_task(self.check_remind(user,reminder)))
		for server in self.bot.guilds:
			for member in server.members:
				# reminders = self.settings.getUserStat(member, server, "Reminders", [])
				reminders = await self.bot.loop.run_in_executor(
					None,
					self.settings.getUserStat,
					member,
					server,
					"Reminders",
					[]
				)
				if reminders:
					# We have a list
					for reminder in reminders:
						if reminder.get("bot_id") is None or reminder["bot_id"] == self.bot.user.id:
							self.loop_list.append(self.bot.loop.create_task(self.check_remind(member,reminder)))
		print("Reminders checked - took {} seconds.".format(time.time() - t))

	async def check_remind(self, member, reminder):
		# Get our current task
		try:
			task = asyncio.Task.current_task()
		except AttributeError:
			task = asyncio.current_task()
		# Start our countdown
		countDown = int(reminder['End'])-int(time.time())
		if countDown > 0:
			# We have a positive countdown - let's wait
			await asyncio.sleep(countDown)

		guild_reminders = await self.bot.loop.run_in_executor(None,self.settings.getUserStat,member,getattr(member,"guild",None),"Reminders",[])
		global_reminders = await self.bot.loop.run_in_executor(None,self.settings.getGlobalUserStat,member,"Reminders",[])

		# Verify reminder is still valid
		if not any((reminder in x for x in (guild_reminders,global_reminders))):
			return

		server  = reminder.get("Server")
		message = reminder.get("Message","I know it was something, but I forgot...")
		link    = reminder.get("Link")

		title = "Reminder in {}:".format(server) if server else "Private Reminder:"
		desc = ("[You asked me to remind you:]({})\n\n".format(link) if link else "")+message

		# Attempt to send the reminder to the user
		try: await Message.Embed(title=title,description=desc,color=member).send(member)
		except: pass # No perms :(

		# Recheck reminders after sending the message
		guild_reminders = await self.bot.loop.run_in_executor(None,self.settings.getUserStat,member,getattr(member,"guild",None),"Reminders",[])
		global_reminders = await self.bot.loop.run_in_executor(None,self.settings.getGlobalUserStat,member,"Reminders",[])

		# Remove the reminder from either list if it exists - and save the updated lists
		if reminder in global_reminders:
			global_reminders.remove(reminder)
			await self.bot.loop.run_in_executor(None,self.settings.setGlobalUserStat,member,"Reminders",global_reminders)
		if reminder in guild_reminders:
			guild_reminders.remove(reminder)
			await self.bot.loop.run_in_executor(None,self.settings.setUserStat,member,getattr(member,"guild",None),"Reminders",guild_reminders)
		
		# Remove the task from the loop list
		if task in self.loop_list: self.loop_list.remove(task)

	@commands.command(pass_context=True)
	async def remindme(self, ctx, message : str = None, *, endtime : str = None):
		"""Set a reminder.  If the message contains spaces, it must be wrapped in quotes."""

		if not endtime or not message:
			return await ctx.send("Usage: `{}remindme \"[message]\" [endtime]`".format(ctx.prefix))

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
		readableTime = ReadableTime.getReadableTimeBetween(int(currentTime),int(end))

		# Add reminder - make sure we retain guild/global context
		reminder = {
			"bot_id":self.bot.user.id,
			"End":end,
			"Message":message,
			"Server":Nullify.escape_all(ctx.guild.name) if ctx.guild else None,
			"Link":"https://discord.com/channels/{}/{}/{}".format(
				ctx.guild.id if ctx.guild else "@me",
				ctx.channel.id,
				ctx.message.id
			)
		}
		if ctx.guild:
			reminders = self.settings.getUserStat(ctx.author,ctx.guild,"Reminders",[])
			reminders.append(reminder)
			self.settings.setUserStat(ctx.author,ctx.guild,"Reminders",reminders)
		else:
			reminders = self.settings.getGlobalUserStat(ctx.author,"Reminders",[])
			reminders.append(reminder)
			self.settings.setGlobalUserStat(ctx.author,"Reminders",reminders)

		# Start timer for reminder
		self.loop_list.append(self.bot.loop.create_task(self.check_remind(ctx.author,reminder)))
		
		# Confirm the reminder
		await ctx.send("Okay *{}*, I'll remind you in *{}*.".format(DisplayName.name(ctx.author),readableTime))

	@commands.command(pass_context=True)
	async def reminders(self, ctx, *, member = None):
		"""List pending reminders - pass a member to see their reminders in the current guild."""

		if not ctx.guild: member = None # Don't allow passing members in dm
		if type(member) is str:
			memberName = member
			member = DisplayName.memberForName(memberName,ctx.guild)
			if not member:
				return await ctx.send("I couldn't find *{}*...".format(Utils.suppressed(ctx,memberName)))
		if not member: member = ctx.author
		if ctx.guild:
			reminders = self.settings.getUserStat(member,ctx.guild,"Reminders",[])
		else:
			reminders = self.settings.getGlobalUserStat(member,"Reminders",[])
		# Gather a list of reminders sorted by remaining time
		# Make sure we only include reminders that this instance of the bot has set
		reminders_sorted = [x for x in sorted(reminders,key=lambda y:int(y["End"])) if x.get("bot_id") is None or x["bot_id"] == self.bot.user.id]
		if not reminders_sorted:
			# No reminders
			return await ctx.send("{} currently have any {}reminders set.  {} can add some with the `{}remindme \"[message]\" [time]` command.".format(
				"You don't" if member==ctx.author else "*{}* doesn't".format(DisplayName.name(member)),
				"" if ctx.guild else "private ",
				"You" if member==ctx.author else "They",
				ctx.prefix
			))
		c_time = int(time.time())
		entries = [{
			"name":"{}. {}".format(i,ReadableTime.getReadableTimeBetween(c_time,int(x["End"]))),
			"value":("[Link:]({})\n".format(x["Link"]) if "Link" in x else "")+x["Message"]
		} for i,x in enumerate(reminders_sorted,start=1)]
		title = "{}'{} Remaining {}Reminders ({:,} total)".format(
			DisplayName.name(member),
			"" if DisplayName.name(member).lower()[-1]=="s" else "s",
			"" if ctx.guild else "Private ",
			len(reminders_sorted)
		)
		# Show our list
		return await PickList.PagePicker(title=title,list=entries,ctx=ctx).pick()

	@commands.command(pass_context=True)
	async def clearmind(self, ctx, *, index = None):
		"""Clear the reminder index passed - or all if none passed."""
		if ctx.guild:
			reminders = self.settings.getUserStat(ctx.author,ctx.guild,"Reminders",[])
		else:
			reminders = self.settings.getGlobalUserStat(ctx.author,"Reminders",[])
		# Get all the reminders if using the "all" keyword
		if index and index.lower() == "all":
			index = None # reset index
			reminders_sorted = reminders
			reminders_left = []
		else:
			# Not getting all - just get our reminders
			reminders_sorted = [x for x in sorted(reminders, key=lambda x:int(x["End"])) if x.get("bot_id") is None or x["bot_id"] == self.bot.user.id]
			reminders_left   = [x for x in reminders if not x in reminders_sorted]
		if not reminders_sorted:
			# No reminders
			return await ctx.send("Oooh, look at you, *so much to be reminded about*... Just kidding.  You don't have any {}reminders to clear.".format(
				"" if ctx.guild else "private "
			))
		if index is None:
			if ctx.guild:
				self.settings.setUserStat(ctx.author,ctx.guild,"Reminders",[]+reminders_left)
			else:
				self.settings.setGlobalUserStat(ctx.author,"Reminders",[]+reminders_left)
			return await ctx.send("Alright *{}*, your {}calendar has been cleared of reminders!".format(DisplayName.name(ctx.author),"" if ctx.guild else "private "))
		# We have something for our index
		try:
			index = int(index)
		except Exception:
			return await ctx.send("Usage: `{}clearmind [index]`".format(ctx.prefix))
		# We have an int
		if index < 1 or index > len(reminders_sorted):
			# Out of bounds!
			return await ctx.send("You'll have to pick an index between 1 and {:,}.".format(len(reminders_sorted)))
		# We made it!  Valid index and all sorts of stuff
		removed = reminders_sorted.pop(index-1)
		if ctx.guild:
			self.settings.setUserStat(ctx.author,ctx.guild,"Reminders",reminders_sorted+reminders_left)
		else:
			self.settings.setGlobalUserStat(ctx.author,"Reminders",reminders_sorted+reminders_left)
		title = "{}Reminder Cleared!".format("" if ctx.guild else "Private ")
		desc = ("[You asked me to remind you:]({})\n\n".format(removed["Link"]) if "Link" in removed else "")+removed["Message"]
		await Message.Embed(title=title,description=desc,color=ctx.author).send(ctx)
