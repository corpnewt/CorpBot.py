import asyncio, discord, os, textwrap, time
from   datetime import datetime
from   operator import itemgetter
from   discord.ext import commands
from   Cogs import Utils, DisplayName, Message, ReadableTime

def setup(bot):
	# Add the bot and deps
	settings = bot.get_cog("Settings")
	bot.add_cog(Debugging(bot, settings))

# This is the Debugging module. It keeps track of how long the bot's been up

class Debugging(commands.Cog):

	# Init with the bot reference, and a reference to the settings var
	def __init__(self, bot, settings, debug = False):
		self.bot = bot
		self.wrap = False
		self.settings = settings
		self.debug = debug
		self.logvars = [ 'invite.create', 'invite.delete', 'user.ban', 'user.unban', 'user.mute', 'user.unmute', 'user.join', 'user.leave', 'user.status',
				'user.game.name', 'user.game.url', 'user.game.type', 'user.avatar',
				'user.nick', 'user.name', 'message.send', 'message.delete',
				'message.edit', "xp" ]
		self.quiet = [ 'user.ban', 'user.unban', 'user.mute', 'user.unmute', 'user.join', 'user.leave' ]
		self.normal = [ 'invite.create', 'invite.delete', 'user.ban', 'user.unban', 'user.mute', 'user.unmute', 'user.join', 'user.leave', 'user.avatar', 'user.nick', 'user.name',
				'message.edit', 'message.delete', "xp" ]
		self.verbose = [ x for x in self.logvars ] # Enable all of them
		self.cleanChannels = []
		self.invite_list = {}
		global Utils, DisplayName
		Utils = self.bot.get_cog("Utils")
		DisplayName = self.bot.get_cog("DisplayName")

	def _is_submodule(self, parent, child):
		return parent == child or child.startswith(parent + ".")

	@commands.Cog.listener()
	async def on_loaded_extension(self, ext):
		# See if we were loaded
		if not self._is_submodule(ext.__name__, self.__module__):
			return
		await self.bot.wait_until_ready()
		print("Gathering invites...")
		t = time.time()
		for guild in self.bot.guilds:
			try:
				self.invite_list[str(guild.id)] = await guild.invites()
			except:
				pass
		print("Invites gathered - took {} seconds.".format(time.time() - t))

	async def oncommand(self, ctx):
		if self.debug:
			# We're Debugging
			timeStamp = datetime.today().strftime("%Y-%m-%d %H.%M")
			msg = '{}{}:\n"{}"\nRun at {}\nBy {}\nOn {}'.format(ctx.prefix, ctx.command, ctx.message.content, timeStamp, ctx.author.name, ctx.guild.name)
			if os.path.exists('debug.txt'):
				# Exists - let's append
				msg = "\n\n" + msg
				msg = msg.encode("utf-8")
				with open("debug.txt", "ab") as myfile:
					myfile.write(msg)
			else:
				msg = msg.encode("utf-8")
				with open("debug.txt", "wb") as myfile:
					myfile.write(msg)

	async def oncommandcompletion(self, ctx):
		if self.debug:
			# We're Debugging
			timeStamp = datetime.today().strftime("%Y-%m-%d %H.%M")
			msg = '{}{}:\n"{}"\nCompleted at {}\nBy {}\nOn {}'.format(ctx.prefix, ctx.command, ctx.message.content, timeStamp, ctx.author.name, ctx.guild.name)
			if os.path.exists('debug.txt'):
				# Exists - let's append
				msg = "\n\n" + msg
				msg = msg.encode("utf-8")
				with open("debug.txt", "ab") as myfile:
					myfile.write(msg)
			else:
				msg = msg.encode("utf-8")
				with open("debug.txt", "wb") as myfile:
					myfile.write(msg)

	def shouldLog(self, logVar, guild):
		serverLogVars = self.settings.getServerStat(guild, "LogVars")
		checks = logVar.split('.')
		check = ''
		for item in checks:
			if len(check):
				check += '.' + item
			else:
				check = item
			if check.lower() in serverLogVars:
				return True
		return False

	def format_invite(self, invite):
		# Gather prelim info
		guild = self.bot.get_guild(int(invite.guild.id))
		channel = None if guild == None else guild.get_channel(invite.channel.id)
		url = invite.url if invite.url else "https://discord.gg/{}".format(invite.code)
		expires_after = None if invite.max_age == None else "Never" if invite.max_age == 0 else "In "+ReadableTime.getReadableTimeBetween(0, invite.max_age)
		max_uses = None if invite.max_uses == None else "Unlimited" if invite.max_uses == 0 else "{:,}".format(invite.max_uses)
		uses = None if invite.uses == None else "{:,}".format(invite.uses)
		created_by = None if invite.inviter == None else "{}#{} ({})".format(invite.inviter.name, invite.inviter.discriminator, invite.inviter.id)
		created_at = None if invite.created_at == None else invite.created_at.strftime("%b %d %Y - %I:%M %p") + " UTC"
		temp = None if invite.temporary == None else invite.temporary
		# Build the description
		desc = "Invite URL:      {}".format(url)
		if created_by != None:    desc += "\nCreated By:      {}".format(created_by)
		if created_at != None:    desc += "\nCreated At:      {}".format(created_at)
		if channel != None:       desc += "\nFor Channel:     #{} ({})".format(channel.name, channel.id)
		if expires_after != None: desc += "\nExpires:         {}".format(expires_after)
		if temp != None:          desc += "\nTemporary:       {}".format(temp)
		if uses != None:          desc += "\nUses:            {}".format(uses)
		if max_uses != None:      desc += "\nMax Uses:        {}".format(max_uses)
		return desc

	# Catch custom xp event
	@commands.Cog.listener()
	async def on_xp(self, to_user, from_user, amount):
		guild = from_user.guild
		if not self.shouldLog('xp', guild):
			return
		if type(to_user) is discord.Role:
			msg = "🌟 {}#{} ({}) gave {} xp to the {} role.".format(from_user.name, from_user.discriminator, from_user.id, amount, to_user.name)
		else:
			msg = "🌟 {}#{} ({}) gave {} xp to {}#{} ({}).".format(from_user.name, from_user.discriminator, from_user.id, amount, to_user.name, to_user.discriminator, to_user.id)
		await self._logEvent(guild, "", title=msg, color=discord.Color.blue())

	@commands.Cog.listener()
	async def on_member_ban(self, guild, member):
		if not self.shouldLog('user.ban', guild):
			return
		# A member was banned
		msg = '🚫 {}#{} ({}) was banned from {}.'.format(member.name, member.discriminator, member.id, Utils.suppressed(guild, guild.name))
		await self._logEvent(guild, "", title=msg, color=discord.Color.red())

	@commands.Cog.listener()
	async def on_member_unban(self, guild, member):
		if not self.shouldLog('user.unban', guild):
			return
		# A member was unbanned
		msg = '🔵 {}#{} ({}) was unbanned from {}.'.format(member.name, member.discriminator, member.id, Utils.suppressed(guild, guild.name))
		await self._logEvent(guild, "", title=msg, color=discord.Color.green())

	@commands.Cog.listener()
	async def on_mute(self, member, guild, cooldown, muted_by):
		if not self.shouldLog('user.mute', guild): return
		# A memeber was muted
		msg = "🔇 {}#{} ({}) was muted.".format(member.name, member.discriminator, member.id)
		message = "Muted by {}.\nMuted {}.".format(
			"Auto-Muted" if not muted_by else "{}#{} ({})".format(muted_by.name, muted_by.discriminator, muted_by.id),
			"for "+ReadableTime.getReadableTimeBetween(time.time(), cooldown) if cooldown else "until further notice"
		)
		await self._logEvent(guild, message, title=msg, color=discord.Color.red())

	@commands.Cog.listener()
	async def on_unmute(self, member, guild):
		if not self.shouldLog('user.unmute', guild): return
		# A memeber was muted
		msg = "🔊 {}#{} ({}) was unmuted.".format(member.name, member.discriminator, member.id)
		await self._logEvent(guild, "", title=msg, color=discord.Color.green())

	@commands.Cog.listener()
	async def on_invite_create(self, invite):
		# Add the invite to our list
		if invite.guild == None: return # Nothing to do here
		guild = self.bot.get_guild(int(invite.guild.id))
		if not guild: return # Didn't find it
		# Store the invite in our working list
		self.invite_list[str(guild.id)] = self.invite_list.get(str(guild.id),[])+[invite]
		if not self.shouldLog('invite.create', invite.guild): return
		# An invite was created
		msg = "📥 Invite created."
		log_msg = self.format_invite(invite)
		await self._logEvent(self.bot.get_guild(int(invite.guild.id)),log_msg,title=msg,color=discord.Color.teal())

	@commands.Cog.listener()
	async def on_invite_delete(self, invite):
		if invite.guild == None: return # Nothing to do here
		guild = self.bot.get_guild(int(invite.guild.id))
		if not guild: return # Didn't find it
		# Refresh the list omitting the deleted invite
		self.invite_list[str(guild.id)] = [x for x in self.invite_list.get(str(guild.id),[]) if x.code != invite.code]
		if not self.shouldLog('invite.delete', guild): return
		msg = "📤 Invite deleted."
		log_msg = self.format_invite(invite)
		await self._logEvent(guild,log_msg,title=msg,color=discord.Color.teal())

	@commands.Cog.listener()	
	async def on_member_join(self, member):
		guild = member.guild
		# Try and determine which invite was used
		invite = None
		invite_list = self.invite_list.get(str(guild.id),[])
		try: new_invites = await guild.invites()
		except: new_invites = []
		changed = [x for x in invite_list for y in new_invites if x.code == y.code and x.uses != y.uses]
		if len(changed) == 1:
			# We have only one changed invite - this is the one!
			invite = changed[0]
		self.invite_list[str(guild.id)] = new_invites
		if not self.shouldLog('user.join', guild):
			return
		# A new member joined
		msg = '👐 {}#{} ({}) joined {}.'.format(member.name, member.discriminator, member.id, Utils.suppressed(guild, guild.name))
		log_msg = "Account Created: {}".format("Unknown" if member.created_at == None else member.created_at.strftime("%b %d %Y - %I:%M %p") + " UTC")
		if invite: log_msg += "\n"+self.format_invite(invite)
		await self._logEvent(guild, log_msg, title=msg, color=discord.Color.teal())
		
	@commands.Cog.listener()
	async def on_member_remove(self, member):
		guild = member.guild
		if not self.shouldLog('user.leave', guild):
			return
		# A member left
		msg = '👋 {}#{} ({}) left {}.'.format(member.name, member.discriminator, member.id, Utils.suppressed(guild, guild.name))
		await self._logEvent(guild, "", title=msg, color=discord.Color.light_grey())

	def type_to_string(self, activity_type):
		# Returns the string associated with the passed activity type
		if activity_type is discord.ActivityType.unknown:
			return "None"
		if activity_type is discord.ActivityType.playing:
			return "Playing"
		if activity_type is discord.ActivityType.streaming:
			return "Streaming"
		if activity_type is discord.ActivityType.listening:
			return "Listening"
		if activity_type is discord.ActivityType.watching:
			return "Watching"
		return "None"

	def activity_to_dict(self, activity):
		# Only gathers name, url, and type
		d = {}
		try:
			d["name"] = activity.name
		except:
			d["name"] = None
		try:
			d["url"] = activity.url
		except:
			d["url"] = None
		try:
			d["type"] = self.type_to_string(activity.type)
		except:
			d["type"] = "Unknown"
		return d

	@commands.Cog.listener()
	async def on_member_update(self, before, after):
		if before.bot:
			return
		# A member changed something about their user-profile
		server = before.guild
		if not before.status == after.status and self.shouldLog('user.status', server):
			msg = 'Changed Status:\n\n{}\n   --->\n{}'.format(str(before.status).lower(), str(after.status).lower())
			await self._logEvent(server, msg, title="👤 {}#{} ({}) Updated.".format(before.name, before.discriminator, before.id), color=discord.Color.gold())
		if not before.activities == after.activities:
			# Something changed
			msg = ''
			# We need to explore the activities and see if any changed
			# we plan to ignore Spotify song changes though - as those don't matter.
			# 
			# First let's gather a list of activity changes, then find out which changed
			bact = [x for x in list(before.activities) if not x in list(after.activities)]
			aact = [x for x in list(after.activities) if not x in list(before.activities)]
			# Now we format
			changes = {}
			for x in bact:
				# Get the type, check if it exists already,
				# and update if need be - or add it if it doesn't
				t = self.type_to_string(x.type)
				# Verify that it has name, url, and type
				changes[t] = {"before":x}
			for y in aact:
				# Same as above, but from the after standpoint
				t = self.type_to_string(y.type)
				changes[t] = {"after":y}
			# Format the data
			for k in changes:
				# We need to gather our changed values and print the changes if logging
				b = self.activity_to_dict(changes[k].get("before",discord.Activity(name=None,url=None,type=None)))
				a = self.activity_to_dict(changes[k].get("after",discord.Activity(name=None,url=None,type=None)))
				# Check the name, url, and type
				if not b["name"] == a["name"] and self.shouldLog('user.game.name', server):
					# Name change
					msg += 'Name:\n   {}\n   --->\n   {}\n'.format(b["name"], a["name"])
				if not b["url"] == a["url"] and self.shouldLog('user.game.url', server):
					# URL changed
					msg += 'URL:\n   {}\n   --->\n   {}\n'.format(b["url"], a["url"])
				if not b["type"] == a["type"] and self.shouldLog('user.game.type', server):
					# URL changed
					msg += 'Type:\n   {}\n   --->\n   {}\n'.format(b["type"], a["type"])

			if len(msg):
				# We saw something tangible change
				msg = 'Changed Playing Status: \n\n{}'.format(msg)
				if self.shouldLog('user.game.name', server) or self.shouldLog('user.game.url', server) or self.shouldLog('user.game.type', server):
					await self._logEvent(server, msg, title="👤 {}#{} ({}) Updated.".format(before.name, before.discriminator, before.id), color=discord.Color.gold())
		if not str(before.avatar_url) == str(after.avatar_url) and self.shouldLog('user.avatar', server):
			# Avatar changed
			msg = 'Changed Avatars: \n\n{}\n   --->\n{}'.format(before.avatar_url, after.avatar_url)
			await self._logEvent(server, msg, title="👤 {}#{} ({}) Updated.".format(before.name, before.discriminator, before.id), color=discord.Color.gold())
		if not before.nick == after.nick and self.shouldLog('user.nick', server):
			# Nickname changed
			msg = 'Changed Nickname: \n\n{}\n   --->\n{}'.format(before.nick, after.nick)
			await self._logEvent(server, msg, title="👤 {}#{} ({}) Updated.".format(before.name, before.discriminator, before.id), color=discord.Color.gold())
		if not before.name == after.name and self.shouldLog('user.name', server):
			# Name changed
			msg = 'Changed Name: \n\n{}\n   --->\n{}'.format(before.name, after.name)
			await self._logEvent(server, msg, title="👤 {}#{} ({}) Updated.".format(before.name, before.discriminator, before.id), color=discord.Color.gold())
		
	@commands.Cog.listener()
	async def on_message(self, message):
		# context = await self.bot.get_context(message)
		# print(context)
		# print(context.command)

		if not message.guild:
			return
		
		if message.author.bot:
			return
		if not self.shouldLog('message.send', message.guild):
			return
		# A message was sent
		title = '📧 {}#{} ({}), in #{}, sent:'.format(message.author.name, message.author.discriminator, message.author.id, message.channel.name)
		msg = message.content
		if len(message.attachments):
			msg += "\n\n--- Attachments ---\n\n"
			for a in message.attachments:
				msg += a.url + "\n"
		
		await self._logEvent(message.guild, msg, title=title, color=discord.Color.dark_grey())
		return
		
	@commands.Cog.listener()
	async def on_message_edit(self, before, after):

		if not before.guild:
			return

		if before.author.bot:
			return
		if not self.shouldLog('message.edit', before.guild):
			return
		if before.content == after.content:
			# Edit was likely a preview happening
			return
		# A message was edited
		title = '✏️ {}#{} ({}), in #{}, edited:'.format(before.author.name, before.author.discriminator, before.author.id, before.channel.name)
		msg = before.content
		if len(before.attachments):
			msg += "\n\n--- Attachments ---\n\n"
			for a in before.attachments:
				msg += a.url + "\n"
		msg += '\n\n--- To ---\n\n{}\n'.format(after.content)
		if len(after.attachments):
			msg += "\n--- Attachments ---\n\n"
			for a in after.attachments:
				msg += a.url + "\n"
		
		await self._logEvent(before.guild, msg, title=title, color=discord.Color.purple())
		return
		
	@commands.Cog.listener()
	async def on_message_delete(self, message):

		if not message.guild:
			return

		if message.author.bot:
			return
		if not self.shouldLog('message.delete', message.guild):
			return
		# Check if we're cleaning from said channel
		if message.channel in self.cleanChannels:
			# Don't log these - as they'll spit out a text file later
			return
		# A message was deleted
		title = '❌ {}#{} ({}), in #{}, deleted:'.format(message.author.name, message.author.discriminator, message.author.id, message.channel.name)
		msg = message.content
		if len(message.attachments):
			msg += "\n\n--- Attachments ---\n\n"
			for a in message.attachments:
				msg += a.url + "\n"
		await self._logEvent(message.guild, msg, title=title, color=discord.Color.orange())
	
	async def _logEvent(self, server, log_message, *, filename = None, color = None, title = None):
		# Here's where we log our info
		# Check if we're suppressing @here and @everyone mentions
		if color == None:
			color = discord.Color.default()
		if self.settings.getServerStat(server, "SuppressMentions"):
			suppress = True
		else:
			suppress = False
		# Get log channel
		logChanID = self.settings.getServerStat(server, "LogChannel")
		if not logChanID:
			return
		logChan = self.bot.get_channel(int(logChanID))
		if not logChan:
			return
		# At this point - we log the message
		try:
			if filename:
				await logChan.send(log_message, file=discord.File(filename))
			else:
				# Check for suppress
				if suppress:
					log_message = Utils.suppressed(server,log_message)
				# Remove triple backticks and replace any single backticks with single quotes
				log_back  = log_message.replace("`", "'")
				if log_back == log_message:
					# Nothing changed
					footer = datetime.utcnow().strftime("%b %d %Y - %I:%M %p") + " UTC"
				else:
					# We nullified some backticks - make a note of it
					log_message = log_back
					footer = datetime.utcnow().strftime("%b %d %Y - %I:%M %p") + " UTC - Note: Backticks --> Single Quotes"
				if self.wrap:
					# Wraps the message to lines no longer than 70 chars
					log_message = textwrap.fill(log_message, replace_whitespace=False)
				await Message.EmbedText(
					title=title,
					description=log_message,
					color=color,
					desc_head="```\n",
					desc_foot="```",
					footer=footer
				).send(logChan)
				# await logChan.send(log_message)
		except:
			# We don't have perms in this channel or something - silently cry
			pass

	@commands.command(pass_context=True)
	async def clean(self, ctx, messages = None, *, chan : discord.TextChannel = None):
		"""Cleans the passed number of messages from the given channel (admin only)."""
		if not await Utils.is_bot_admin_reply(ctx): return

		if not chan:
			chan = ctx.channel

		if chan in self.cleanChannels:
			# Don't clean messages from a channel that's being cleaned
			return
		
		# Try to get the number of messages to clean so you don't "accidentally" clean
		# any...
		try:
			messages = int(messages)
		except:
			return await ctx.send("You need to specify how many messages to clean!")
		# Make sure we're actually trying to clean something
		if messages < 1:
			return await ctx.send("Can't clean less than 1 message!")

		# Add channel to list
		self.cleanChannels.append(chan)

		# Remove original message
		await ctx.message.delete()
		
		if messages > 1000:
			messages = 1000

		# Use history instead of purge
		counter = 0

		# I tried bulk deleting - but it doesn't work on messages over 14 days
		# old - so we're doing them individually I guess.

		# Setup deleted message logging
		# Log the user who called for the clean
		msg = ''
		totalMess = messages
		while totalMess > 0:
			gotMessage = False
			if totalMess > 100:
				tempNum = 100
			else:
				tempNum = totalMess
			try:
				async for message in chan.history(limit=tempNum):
					# Save to a text file
					new_msg = '{}#{}:\n    {}\n'.format(message.author.name, message.author.discriminator, message.content)
					if len(message.attachments):
						new_msg += "\n    --- Attachments ---\n\n"
						for a in message.attachments:
							new_msg += "    " + a.url + "\n"
					new_msg += "\n"
					msg = new_msg + msg
					await message.delete()
					gotMessage = True
					counter += 1
					totalMess -= 1
			except Exception:
				pass
			if not gotMessage:
				# No more messages - exit
				break

		# Remove channel from list
		self.cleanChannels.remove(chan)

		msg = 'Messages cleaned by {}#{} in {} - #{}\n\n'.format(ctx.message.author.name, ctx.message.author.discriminator, Utils.suppressed(ctx, ctx.guild.name), ctx.channel.name) + msg

		# Timestamp and save to file
		timeStamp = datetime.today().strftime("%Y-%m-%d %H.%M")
		filename = "cleaned-{}.txt".format(timeStamp)
		msg = msg.encode('utf-8')
		with open(filename, "wb") as myfile:
			myfile.write(msg)

		# Send the cleaner a pm letting them know we're done
		await ctx.author.send('*{}* message{} removed from *#{}* in *{}!*'.format(counter, "" if counter == 1 else "s", chan.name, Utils.suppressed(ctx, ctx.guild.name)))
		# PM the file
		await ctx.author.send(file=discord.File(filename))
		if self.shouldLog('message.delete', ctx.guild):
			# We're logging
			logmess = '{}#{} cleaned in #{}'.format(ctx.author.name, ctx.author.discriminator, chan.name)
			await self._logEvent(ctx.guild, logmess, filename=filename)
		# Delete the remaining file
		os.remove(filename)
	
	
	@commands.command(pass_context=True)
	async def logpreset(self, ctx, *, preset = None):
		"""Can select one of 4 available presets - off, quiet, normal, verbose (bot-admin only)."""
		if not await Utils.is_bot_admin_reply(ctx): return
		
		if preset == None:
			return await ctx.send('Usage: `{}logpreset [off/quiet/normal/verbose]`'.format(ctx.prefix))
		if preset.lower() in ["0", "off"]:
			currentVars = []
			msg = 'Removed *all* logging options.'
		elif preset.lower() in ['quiet', '1']:
			currentVars = self.quiet
			msg = 'Logging with *quiet* preset.'
		elif preset.lower() in ['normal', '2']:
			currentVars = self.normal
			msg = 'Logging with *normal* preset.'
		elif preset.lower() in ['verbose', '3']:
			currentVars = self.verbose
			msg = 'Logging with *verbose* preset.'
		else:
			return await ctx.send('Usage: `{}logpreset [off/quiet/normal/verbose]`'.format(ctx.prefix))
		self.settings.setServerStat(ctx.guild, "LogVars", currentVars)
		await ctx.send(msg)
		
	
	@commands.command(pass_context=True)
	async def logging(self, ctx):
		"""Outputs whether or not we're logging is enabled (bot-admin only)."""
		if not await Utils.is_bot_admin_reply(ctx): return
		
		logChannel = self.settings.getServerStat(ctx.guild, "LogChannel")
		if logChannel:
			channel = self.bot.get_channel(int(logChannel))
			if channel:
				logVars = self.settings.getServerStat(ctx.guild, "LogVars")
				logText = ", ".join(logVars) if len(logVars) else "*Nothing*"
				return await ctx.send('Logging is *enabled* in *{}*.\nCurrently logging: {}'.format(channel.mention, logText))
		await ctx.send('Logging is currently *disabled*.')
		
		
	@commands.command(pass_context=True)
	async def logenable(self, ctx, *, options = None):
		"""Enables the passed, comma-delimited log vars (bot-admin only)."""
		if not await Utils.is_bot_admin_reply(ctx): return
		
		if options == None:
			msg = 'Usage: `{}logenable option1, option2, option3...`\nAvailable options:\n{}'.format(ctx.prefix, ', '.join(self.logvars))
			return await ctx.send(msg)
		
		serverOptions = self.settings.getServerStat(ctx.guild, "LogVars")
		optionList = "".join(options.split()).split(",")
		addedOptions = []
		for option in optionList:
			for varoption in self.logvars:
				if varoption.startswith(option.lower()) and not varoption in serverOptions:
					# Only add if valid and not already added
					addedOptions.append(varoption)
		if not len(addedOptions):
			return await ctx.send('No valid or disabled options were passed.')
		
		serverOptions.extend(addedOptions)
		
		# Save the updated options
		self.settings.setServerStat(ctx.guild, "LogVars", serverOptions)

		await ctx.send("*{}* logging option{} enabled.".format(len(addedOptions),"" if len(addedOptions) == 1 else "s"))
		
				
	@commands.command(pass_context=True)
	async def logdisable(self, ctx, *, options = None):
		"""Disables the passed, comma-delimited log vars.  If run with no arguments, disables all current logging options (bot-admin only)."""
		if not await Utils.is_bot_admin_reply(ctx): return
		
		if options == None:
			msg = 'Cleared all logging options.'
			self.settings.setServerStat(ctx.guild, "LogVars", [])
			return await ctx.send(msg)
		
		serverOptions = self.settings.getServerStat(ctx.guild, "LogVars")
		optionList = "".join(options.split()).split(",")
		addedOptions = []
		for option in optionList:
			for varoption in self.logvars:
				if varoption.startswith(option.lower()) and varoption in serverOptions:
					# Only remove if valid and in list
					addedOptions.append(varoption)
					serverOptions.remove(varoption)
		if not len(addedOptions):
			return await ctx.send('No valid or enabled options were passed.  Nothing to disable.')

		# Save the updated options
		self.settings.setServerStat(ctx.guild, "LogVars", serverOptions)

		await ctx.send("*{}* logging option{} disabled.".format(len(addedOptions),"" if len(addedOptions) == 1 else "s"))		
			
			
	@commands.command(pass_context=True)
	async def setlogchannel(self, ctx, *, channel : discord.TextChannel = None):
		"""Sets the channel for Logging (bot-admin only)."""
		if not await Utils.is_bot_admin_reply(ctx): return

		if channel == None:
			self.settings.setServerStat(ctx.guild, "LogChannel", "")
			return await ctx.send('Logging is now *disabled*.')

		# If we made it this far - then we can add it
		self.settings.setServerStat(ctx.guild, "LogChannel", channel.id)

		await ctx.send('Logging is now *enabled* in **{}**.'.format(channel.mention))
		
	
	@setlogchannel.error
	async def setlogchannel_error(self, ctx, error):
		# do stuff
		msg = 'setlogchannel Error: {}'.format(ctx)
		await error.channel.send(msg)


	@commands.command(pass_context=True)
	async def setdebug(self, ctx, *, debug = None):
		"""Turns on/off debugging (owner only - always off by default)."""
		# Only allow owner
		isOwner = self.settings.isOwner(ctx.author)
		if isOwner == None:
			return await ctx.send('I have not been claimed, *yet*.')
		elif isOwner == False:
			return await ctx.send('You are not the *true* owner of me.  Only the rightful owner can use this command.')

		if debug == None:
			# Output debug status
			return await ctx.send("Debugging is {}.".format("enabled" if self.debug else "disabled"))
		elif debug.lower() in [ "yes", "on", "true", "enabled", "enable" ]:
			debug = True
		elif debug.lower() in [ "no", "off", "false", "disabled", "disable" ]:
			debug = False
		else:
			debug = None

		if debug == True:
			msg = 'Debugging remains enabled.' if self.debug == True else 'Debugging now enabled.'
		else:
			msg = 'Debugging remains disabled.' if self.debug == False else 'Debugging now disabled.'
		self.debug = debug
		
		await ctx.send(msg)
		
		
	@commands.command(pass_context=True)
	async def cleardebug(self, ctx):
		"""Deletes the debug.txt file (owner only)."""
		# Only allow owner
		isOwner = self.settings.isOwner(ctx.author)
		if isOwner == None:
			return await ctx.send('I have not been claimed, *yet*.')
		elif isOwner == False:
			return await ctx.send('You are not the *true* owner of me.  Only the rightful owner can use this command.')
		
		if not os.path.exists('debug.txt'):
			return await ctx.send("No *debug.txt* found.")
		# Exists - remove it
		os.remove('debug.txt')
		await ctx.send('*debug.txt* removed!')


	@commands.command(pass_context=True)
	async def heartbeat(self, ctx):
		"""Write to the console and attempt to send a message (owner only)."""
		# Only allow owner
		isOwner = self.settings.isOwner(ctx.author)
		if isOwner == None:
			return await ctx.send('I have not been claimed, *yet*.')
		elif isOwner == False:
			return await ctx.send('You are not the *true* owner of me.  Only the rightful owner can use this command.')

		timeStamp = datetime.today().strftime("%Y-%m-%d %H.%M")
		print('Heartbeat tested at {}.'.format(timeStamp))
		# Message send
		message = await ctx.send('Heartbeat tested at {}.'.format(timeStamp))
		print("Message:\n{}".format(message) if message else "No message returned.")
