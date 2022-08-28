import discord, os, textwrap, time, re, shutil, tempfile
from   datetime import datetime, timezone
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
		self.logvars = [ 'invite.create', 'invite.delete', 'invite.send', 'user.ban', 'user.unban', 'user.mute', 'user.unmute', 'user.join', 'user.leave', 'user.status',
				'user.game.name', 'user.game.url', 'user.game.type', 'user.avatar', 'user.spotify',
				'user.nick', 'user.name', 'message.send', 'message.delete',
				'message.edit', "xp" ]
		self.quiet = [ 'user.ban', 'user.unban', 'user.mute', 'user.unmute', 'user.join', 'user.leave' ]
		self.normal = [ 'invite.create', 'invite.delete', 'invite.send', 'user.ban', 'user.unban', 'user.mute', 'user.unmute', 'user.join', 'user.leave', 'user.avatar', 'user.nick', 'user.name',
				'message.edit', 'message.delete', "xp" ]
		self.verbose = [ x for x in self.logvars ] # Enable all of them
		self.cleanChannels = []
		self.invite_list = {}
		self.audit_log_threshold = 30 # Try to get logs within 30 seconds of happening
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

	def _t(self,value,ago=False):
		return "Time Unknown" if value is None else "<t:{}>{}".format(
			int(value.timestamp())," (<t:{}:R>)".format(int(value.timestamp())) if ago else ""
		)

	def _f(self,name,value,ts=False,ago=False,wrap=True):
		if ts: # Create the timestamp
			value = self._t(value,ago=ago)
		elif wrap: # Only wrap if not ts, and wrap
			value = "```\n{}```".format(value)
		return {"name":"{}".format(name),"value":value}

	def format_invite_fields(self, invite, sent = False):
		# Gather prelim info
		guild = invite.guild
		channel = None if guild is None else invite.channel
		url = invite.url if invite.url else "https://discord.gg/{}".format(invite.code)
		expires_after = None if invite.max_age is None else "Never" if invite.max_age == 0 else "In "+ReadableTime.getReadableTimeBetween(0, invite.max_age)
		max_uses = None if invite.max_uses is None else "Unlimited" if invite.max_uses == 0 else "{:,}".format(invite.max_uses)
		uses = None if invite.uses is None else "{:,}".format(invite.uses)
		created_by = None if invite.inviter is None else "{}#{} ({})".format(invite.inviter.name, invite.inviter.discriminator, invite.inviter.id)
		temp = False if invite.temporary is None else invite.temporary
		# Setup the fields
		fields = []
		if invite.created_at:
			fields.append(self._f("Invite Created",invite.created_at,ts=True,ago=True))
		# Build the description
		desc = "Invite URL:      {}".format(url)
		if sent == True:
			if guild:	  desc += "\nName:            {}".format(guild.name)
			if invite.approximate_member_count:		  desc += "\nMembers:         {:,}/{:,}".format(invite.approximate_presence_count,invite.approximate_member_count)
		if created_by:    desc += "\nCreated By:      {}".format(created_by)
		# if created_at:    desc += "\nCreated At:      {}".format(created_at)
		if channel:       desc += "\nFor Channel:     #{} ({})".format(channel.name, channel.id)
		if expires_after: desc += "\nExpires:         {}".format(expires_after)
		if temp:          desc += "\nTemporary:       {}".format(temp)
		if uses:          desc += "\nUses:            {}".format(uses)
		if max_uses:      desc += "\nMax Uses:        {}".format(max_uses)
		fields.append(self._f("Invite Information",desc))
		return fields

	async def get_latest_log(self, guild, member, types=None):
		if not types or not isinstance(types,(list,tuple)): return
		now = datetime.now(timezone.utc)
		try:
			actions = []
			for t in types:
				actions.extend([x for x in await guild.audit_logs(limit=1,action=t).flatten() if x.target == member])
			if not actions: return # Nothing to report
			# We got something - let's get the latest
			recent = max(actions,key=lambda x:x.created_at)
			difference = now-recent.created_at
			if difference.total_seconds() <= self.audit_log_threshold:
				# Within the threshold - return it
				return recent
		except: pass

	# Catch custom xp event
	@commands.Cog.listener()
	async def on_xp(self, to_user, from_user, amount):
		guild = from_user.guild
		pfpurl = Utils.get_avatar(from_user)
		if not self.shouldLog('xp', guild):
			return
		if type(to_user) is discord.Role:
			msg = "🌟 {}#{} ({}) gave {} xp to the {} role.".format(from_user.name, from_user.discriminator, from_user.id, amount, to_user.name)
		else:
			msg = "🌟 {}#{} ({}) gave {} xp to {}#{} ({}).".format(from_user.name, from_user.discriminator, from_user.id, amount, to_user.name, to_user.discriminator, to_user.id)
		await self._logEvent(guild, "", title=msg, color=discord.Color.blue(),thumbnail=pfpurl)

	@commands.Cog.listener()
	async def on_member_ban(self, guild, member):
		if not self.shouldLog('user.ban', guild):
			return
		last = await self.get_latest_log(guild, member, (discord.AuditLogAction.ban,))
		log_msg = ""
		if last:
			log_msg = "By:  {}#{} ({})\nFor: {}".format(
				last.user.name,last.user.discriminator,last.user.id,
				last.reason if last.reason else "No reason provided."
			)
		# A member was banned
		pfpurl = Utils.get_avatar(member)
		msg = '🚫 {}#{} ({}) was banned from {}.'.format(member.name, member.discriminator, member.id, guild.name)
		await self._logEvent(guild, log_msg, title=msg, color=discord.Color.red(),thumbnail=pfpurl)

	@commands.Cog.listener()
	async def on_member_unban(self, guild, member):
		if not self.shouldLog('user.unban', guild):
			return
		last = await self.get_latest_log(guild, member, (discord.AuditLogAction.unban,))
		log_msg = ""
		if last:
			log_msg = "By:  {}#{} ({})\nFor: {}".format(
				last.user.name,last.user.discriminator,last.user.id,
				last.reason if last.reason else "No reason provided."
			)
		# A member was unbanned
		pfpurl = Utils.get_avatar(member)
		msg = '🔵 {}#{} ({}) was unbanned from {}.'.format(member.name, member.discriminator, member.id, guild.name)
		await self._logEvent(guild, log_msg, title=msg, color=discord.Color.green(),thumbnail=pfpurl)

	@commands.Cog.listener()
	async def on_mute(self, member, guild, cooldown, muted_by):
		if not self.shouldLog('user.mute', guild): return
		# A memeber was muted
		pfpurl = Utils.get_avatar(member)
		msg = "🔇 {}#{} ({}) was muted.".format(member.name, member.discriminator, member.id)
		message = "Muted by {}.\nMuted {}.".format(
			"Auto-Muted" if not muted_by else "{}#{} ({})".format(muted_by.name, muted_by.discriminator, muted_by.id),
			"for "+ReadableTime.getReadableTimeBetween(time.time(), cooldown) if cooldown else "until further notice"
		)
		await self._logEvent(guild, message, title=msg, color=discord.Color.red(),thumbnail=pfpurl)

	@commands.Cog.listener()
	async def on_unmute(self, member, guild):
		if not self.shouldLog('user.unmute', guild): return
		# A memeber was muted
		pfpurl = Utils.get_avatar(member)
		msg = "🔊 {}#{} ({}) was unmuted.".format(member.name, member.discriminator, member.id)
		await self._logEvent(guild, "", title=msg, color=discord.Color.green(),thumbnail=pfpurl)

	@commands.Cog.listener()
	async def on_invite_create(self, invite):
		# Add the invite to our list
		if invite.guild is None: return # Nothing to do here
		guild = self.bot.get_guild(int(invite.guild.id))
		if not guild: return # Didn't find it
		pfpurl = Utils.get_avatar(self.bot.user)
		if invite.inviter: pfpurl = Utils.get_avatar(invite.inviter)
		# Store the invite in our working list
		self.invite_list[str(guild.id)] = self.invite_list.get(str(guild.id),[])+[invite]
		if not self.shouldLog('invite.create', invite.guild): return
		# An invite was created
		msg = "📥 Invite created."
		fields = self.format_invite_fields(invite)
		await self._logEvent(self.bot.get_guild(int(invite.guild.id)),"",fields=fields,title=msg,color=discord.Color.teal(),thumbnail=pfpurl)

	@commands.Cog.listener()
	async def on_invite_delete(self, invite):
		if invite.guild is None: return # Nothing to do here
		guild = self.bot.get_guild(int(invite.guild.id))
		if not guild: return # Didn't find it
		pfpurl = Utils.get_guild_icon(guild)
		# Refresh the list omitting the deleted invite
		self.invite_list[str(guild.id)] = [x for x in self.invite_list.get(str(guild.id),[]) if x.code != invite.code]
		if not self.shouldLog('invite.delete', guild): return
		msg = "📤 Invite deleted."
		fields = self.format_invite_fields(invite)
		await self._logEvent(guild,"",fields=fields,title=msg,color=discord.Color.teal(),thumbnail=pfpurl)

	@commands.Cog.listener()	
	async def on_member_join(self, member):
		guild = member.guild
		pfpurl = Utils.get_avatar(member)
		# Try and determine which invite was used
		invite = None
		invite_list = self.invite_list.get(str(guild.id),[])
		try: new_invites = await guild.invites()
		except: new_invites = []
		changed = [x for x in new_invites for y in invite_list if x.code == y.code and x.uses != y.uses]
		if len(changed) == 1:
			# We have only one changed invite - this is the one!
			invite = changed[0]
		self.invite_list[str(guild.id)] = new_invites
		if not self.shouldLog('user.join', guild):
			return
		# A new member joined
		msg = '👐 {}#{} ({}) joined {}.'.format(member.name, member.discriminator, member.id, guild.name)
		fields = [self._f("Account Created",member.created_at,ts=True,ago=True)]
		if invite: fields.extend(self.format_invite_fields(invite))
		await self._logEvent(guild, "", fields=fields, title=msg, color=discord.Color.teal(), thumbnail=pfpurl)
		
	@commands.Cog.listener()
	async def on_member_remove(self, member):
		guild = member.guild
		pfpurl = Utils.get_avatar(member)
		if not self.shouldLog('user.leave', guild):
			return
		# A member left - get the last ban/kick audit log entry
		msg = '👋 {}#{} ({}) left {}.'.format(member.name, member.discriminator, member.id, guild.name)
		fields = [self._f("Joined",member.joined_at,ts=True,ago=True)]
		last = await self.get_latest_log(guild,member,(discord.AuditLogAction.kick,discord.AuditLogAction.ban))
		if last:
			fields.append({
				"name":"Member was **{}**".format("banned" if last.action==discord.AuditLogAction.ban else "kicked"),
				"value":"{}\n```\nBy:  {}#{} ({})\nFor: {}```".format(
					self._t(last.created_at,ago=True),
					last.user.name,last.user.discriminator,last.user.id,
					last.reason or "No reason provided."
				)
			})
		roles = ["{} ({})".format(x.name,x.id) for x in member.roles if x != guild.default_role]
		log_msg = "{}".format("\n".join(roles) if roles else "None")
		await self._logEvent(guild, log_msg, header="**Had Roles**",fields=fields, title=msg, color=discord.Color.light_grey(), thumbnail=pfpurl)

	def type_to_string(self, activity_type):
		# Returns the string associated with the passed activity type
		return {
			discord.ActivityType.playing:"Playing",
			discord.ActivityType.streaming:"Streaming",
			discord.ActivityType.listening:"Listening",
			discord.ActivityType.watching:"Watching",
			discord.ActivityType.custom:"Custom",
			discord.ActivityType.competing:"Competing"
		}.get(activity_type,"None")

	def activity_to_dict(self, activity):
		# Only gathers name, url, and type
		return {
			"name":str(getattr(activity,"name",None)),
			"url":str(getattr(activity,"url",None)),
			"title":str(getattr(activity,"title",None)),
			"type":self.type_to_string(getattr(activity,"type",None))
		}

	@commands.Cog.listener()
	async def on_presence_update(self, before, after):
		# Workaround to keep all member/presence updates in the on_member_update() check
		await self.on_member_update(before,after)

	def sanitize_activity(self, activity):
		# If our activity has _timestamps, make sure we have *something* for "start" and "end"
		if hasattr(activity,"_timestamps"):
			t = int(time.time())
			for key in ("start","end"):
				if not key in activity._timestamps:
					activity._timestamps[key] = t
		return activity

	@commands.Cog.listener()
	async def on_member_update(self, before, after):
		if not before or before.bot: return
		# A member changed something about their user-profile
		server = before.guild
		pfpurl = Utils.get_avatar(before)
		if before.status != after.status and self.shouldLog('user.status', server):
			msg = 'Changed Status:\n\n{}\n   --->\n{}'.format(str(before.status).lower(), str(after.status).lower())
			await self._logEvent(server, msg, title="👤 {}#{} ({}) Updated.".format(before.name, before.discriminator, before.id), color=discord.Color.gold(), thumbnail=pfpurl)
		# Sanitize activities - fixes an issue where the "start" and "end" keys may not be visible
		before.activities = [self.sanitize_activity(x) for x in before.activities]
		after.activities = [self.sanitize_activity(x) for x in after.activities]
		if before.activities != after.activities and not discord.Status.offline in (before.status,after.status):
			# Something changed - and it wasn't just us going on/offline
			msg = ''
			# We need to explore the activities and see if any changed
			# we plan to ignore Spotify song changes though - as those don't matter.
			# 
			# First let's gather a list of activity changes, then find out which changed
			bact = [x for x in list(before.activities) if not x in after.activities]
			aact = [x for x in list(after.activities) if not x in before.activities]
			# Now we format
			changes = {}
			for x in bact:
				# Get the type, check if it exists already,
				# and update if need be - or add it if it doesn't
				t = self.type_to_string(x.type)
				# Verify that it has name, url, and type
				if not t in changes: changes[t] = {}
				changes[t]["before"] = x
			for y in aact:
				# Same as above, but from the after standpoint
				t = self.type_to_string(y.type)
				if not t in changes: changes[t] = {}
				changes[t]["after"] = y
			# Format the data
			for k in changes:
				# We need to gather our changed values and print the changes if logging
				b = self.activity_to_dict(changes[k].get("before",discord.Activity(name=None,url=None,type=None)))
				a = self.activity_to_dict(changes[k].get("after",discord.Activity(name=None,url=None,type=None)))
				if "spotify" in (a["name"].lower(),b["name"].lower()) and "listening" in (a["type"].lower(),b["type"].lower()) and not self.shouldLog("user.spotify",server):
					# Skip spotify changes as they're spammy
					continue
				# Check the name, url, and type
				for x,y in (("name","Name"),("url","URL"),("type","Type")):
					if b[x]!=a[x] and self.shouldLog("user.game.{}".format(x),server):
						msg += "{}:\n   {}\n   --->\n   {}\n".format(y,b[x],a[x])
				# Check for spotify title logging
				if b["title"]!=a["title"] and self.shouldLog("user.spotify",server):
					msg += "Title:\n   {}\n   --->\n   {}\n".format(b["title"],a["title"])
			if len(msg):
				# We saw something tangible change
				msg = 'Changed Playing Status: \n\n{}'.format(msg)
				if self.shouldLog('user.game.name', server) or self.shouldLog('user.game.url', server) or self.shouldLog('user.game.type', server):
					await self._logEvent(server, msg, title="👤 {}#{} ({}) Updated.".format(before.name, before.discriminator, before.id), color=discord.Color.gold(), thumbnail=pfpurl)
		if Utils.get_avatar(before) != Utils.get_avatar(after) and self.shouldLog('user.avatar', server):
			# Avatar changed
			msg = 'Changed Avatars: \n\n{}\n   --->\n{}'.format(Utils.get_avatar(before), Utils.get_avatar(after))
			await self._logEvent(server, msg, title="👤 {}#{} ({}) Updated.".format(before.name, before.discriminator, before.id), color=discord.Color.gold(), thumbnail=pfpurl)
		if before.nick != after.nick and self.shouldLog('user.nick', server):
			# Nickname changed
			msg = 'Changed Nickname: \n\n{}\n   --->\n{}'.format(before.nick, after.nick)
			await self._logEvent(server, msg, title="👤 {}#{} ({}) Updated.".format(before.name, before.discriminator, before.id), color=discord.Color.gold(), thumbnail=pfpurl)
		if before.name != after.name and self.shouldLog('user.name', server):
			# Name changed
			msg = 'Changed Name: \n\n{}\n   --->\n{}'.format(before.name, after.name)
			await self._logEvent(server, msg, title="👤 {}#{} ({}) Updated.".format(before.name, before.discriminator, before.id), color=discord.Color.gold(), thumbnail=pfpurl)
		
	@commands.Cog.listener()
	async def on_message(self, message):
		if not message.guild or message.author.bot:
			return
		message_url = "https://discord.com/channels/{}/{}/{}".format(
			message.guild.id,
			message.channel.id,
			message.id
		)
		if self.shouldLog('message.send', message.guild):
			# A message was sent
			title = '📧 {}#{} ({}), in #{}, sent:'.format(message.author.name, message.author.discriminator, message.author.id, message.channel.name)
			msg = message.content
			if len(message.attachments):
				msg += "\n\n--- Attachments ---\n\n"
				for a in message.attachments:
					msg += a.url + "\n"
			pfpurl = Utils.get_avatar(message.author)
			await self._logEvent(message.guild, msg, title=title, color=discord.Color.dark_grey(), thumbnail = pfpurl, message_url=message_url)
		if self.shouldLog('invite.send', message.guild):
			# A message was sent
			matches = re.finditer(r"(?i)((discord\.gg|discordapp\.com\/invite)\/\S+)",message.content)
			invites = []
			for match in matches:
				invite = match.group(0).split("/")[-1]
				if not invite in invites: invites.append(invite)
			if invites:
				title = '🎫 {}#{} ({}), in #{}, sent invite:'.format(message.author.name, message.author.discriminator, message.author.id, message.channel.name)
				fields = []
				for invite in invites:
					fields.extend(self.format_invite_fields(await self.bot.fetch_invite(invite,with_counts=True),sent=True))
				pfpurl = Utils.get_avatar(message.author)
				await self._logEvent(message.guild, "", fields=fields, title=title, color=discord.Color.dark_grey(), thumbnail = pfpurl, message_url=message_url)

	@commands.Cog.listener()
	async def on_raw_message_edit(self, payload):
		# Let's get all message edits - regardless of whether or not they're in the cache
		guild = self.bot.get_guild(payload.guild_id)
		if not guild: return # Not in a guild
		try: author = guild.get_member(int(payload.data["author"]["id"]))
		except:
			try: author = await self.bot.fetch_user(int(payload.data.get("author",{}).get("id","0")))
			except: author = None
		if not author or author.bot: return # Author doesn't exist - or is a bot
		if not self.shouldLog("message.edit",guild): return # We're not logging edits
		channel = guild.get_channel(payload.channel_id)
		title = '✏️ {}#{} ({}), in {}, edited:'.format(
			author.name,
			author.discriminator,
			author.id,
			"#"+channel.name if channel else payload.channel_id
		)
		before = payload.cached_message
		if before:
			msg = before.content
			if before.attachments:
				msg += "\n\n--- Attachments ---\n\n"
				for a in before.attachments:
					msg += a.url + "\n"
		else:
			msg = "[ Message ID {} Not Found In Cache ]".format(payload.message_id)
		msg += "\n\n--- To ---\n\n{}\n".format(payload.data.get("content",""))
		if payload.data.get("attachments"):
			msg += "\n--- Attachments ---\n\n"
			for a in payload.data["attachments"]:
				msg += a.get("url","Unknown URL") + "\n"
		pfpurl = Utils.get_avatar(author)
		message_url = "https://discord.com/channels/{}/{}/{}".format(
				payload.guild_id,
				payload.channel_id,
				payload.message_id
			)
		await self._logEvent(guild, msg, title=title, color=discord.Color.purple(), thumbnail=pfpurl, message_url=message_url)

	@commands.Cog.listener()
	async def on_raw_message_delete(self, payload):
		guild = self.bot.get_guild(payload.guild_id)
		if not guild: return # Not in a guild
		if not self.shouldLog("message.delete",guild): return # Not logging deletes
		if not payload.cached_message:
			channel = guild.get_channel(payload.channel_id)
			title = '❌ Message in {} deleted.'.format(
				"#"+channel.name if channel else payload.channel_id
			)
			msg = "[ Message ID {} Not Found In Cache ]".format(payload.message_id)
			pfpurl = Utils.get_guild_icon(guild)
		else:
			message = payload.cached_message
			if message.author.bot:
				return # Don't log bots
			title = '❌ {}#{} ({}), in #{}, deleted:'.format(
				message.author.name,
				message.author.discriminator,
				message.author.id,
				message.channel.name
			)
			msg = message.content
			if len(message.attachments):
				msg += "\n\n--- Attachments ---\n\n"
				for a in message.attachments:
					msg += a.url + "\n"
			pfpurl = Utils.get_avatar(message.author)
		await self._logEvent(guild, msg, title=title, color=discord.Color.orange(), thumbnail=pfpurl)

	@commands.Cog.listener()
	async def on_raw_bulk_message_delete(self, payload):
		guild = self.bot.get_guild(payload.guild_id)
		if not guild: return # Not in a guild
		if not self.shouldLog("message.delete",guild): return # Not logging deletes
		# Generate a timestamp for the delete event
		name = "Bulk-Delete-{}.txt".format(datetime.utcnow().strftime("%Y-%m-%d %H.%M"))
		channel = guild.get_channel(payload.channel_id)
		cached_ids = [x.id for x in payload.cached_messages] if payload.cached_messages else []
		missing_ids = [x for x in payload.message_ids if not x in cached_ids]
		msg = "Bulk Delete in {} -> {}:\n\n".format(
			guild.name,
			"#"+channel.name if channel else payload.channel_id
		)
		if cached_ids:
			msg += "--- Cached Messages ---\n\n"
			for message in payload.cached_messages:
				msg += "Sent By: {}#{} ({}) at {}{}:{}{}\n\n".format(
					message.author.name,
					message.author.discriminator,
					message.author.id,
					message.created_at.strftime("%b %d %Y - %I:%M %p")+" UTC",
					"(edited at {} UTC)".format(message.edited_at.strftime("%b %d %Y - %I:%M %p")) if message.edited_at else "",
					"\n"+message.content if message.content else "",
					"\n--- Attachments ---\n{}".format("\n".join([x.url for x in message.attachments])) if message.attachments else ""
				)
		if missing_ids:
			msg += "--- Message IDs Not Found In Cache ---\n\n"+"\n".join([str(x) for x in missing_ids])
		# Log the event
		title = '❌ Bulk Message Deletion in {}:'.format(
			"#"+channel.name if channel else payload.channel_id
		)
		event_msg = "{:,}/{:,} bulk deleted message{} were found in cache.\n\nSaved to {}".format(
			len(payload.cached_messages),
			len(payload.message_ids),
			"" if len(payload.message_ids)==1 else "s",
			name
		)
		# Save to a local file
		temp = tempfile.mkdtemp()
		temp_file = os.path.join(temp,name)
		with open(temp_file,"wb") as f:
			f.write(msg.encode("utf-8"))
		await self._logEvent(guild,event_msg,filename=temp_file,color=discord.Color.orange(),title=title,thumbnail=Utils.get_guild_icon(guild))
		shutil.rmtree(temp,ignore_errors=True)
	
	async def _logEvent(self, server, log_message, *, header = None, fields = None, filename = None, color = None, title = None, thumbnail = None, message_url = None):
		# Here's where we log our info
		# Check if we're suppressing @here and @everyone mentions
		if color is None:
			color = discord.Color.default()
		# Get log channel
		logChanID = self.settings.getServerStat(server, "LogChannel")
		if not logChanID:
			return
		logChan = self.bot.get_channel(int(logChanID))
		if not logChan:
			return
		# At this point - we log the message
		try:
			# Remove triple backticks and replace any single backticks with single quotes
			log_back  = log_message.replace("`", "'")
			footer = None
			if log_back != log_message:
				# We nullified some backticks - make a note of it
				log_message = log_back
				footer = "Note: Backticks --> Single Quotes"
			if self.wrap:
				# Wraps the message to lines no longer than 70 chars
				log_message = textwrap.fill(log_message, replace_whitespace=False)
			# Save our current and UTC time for the logged event
			d_header = "`Event Logged:` <t:{}>{}\n{}```\n".format(
				int(datetime.now().timestamp()),
				"\n[Message Link]({})".format(message_url) if message_url else "",
				"\n"+header+"\n" if header else ""
			)
			d_footer = "\n```"
			# Make sure we timestamp - even if there's no description
			if not log_message:
				log_message = d_header[:-4] if d_header.endswith("```\n") else d_header
				d_header = d_footer = ""
			# Send the embed
			message = await Message.Embed(
				title=title,
				description=log_message,
				color=color,
				thumbnail=thumbnail,
				d_header=d_header,
				d_footer=d_footer,
				footer=footer,
				fields=fields
			).send(logChan)
			if filename: await message.edit(file=discord.File(filename))
		except Exception as e:
			print(e)
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

		msg = 'Messages cleaned by {}#{} in {} - #{}\n\n'.format(ctx.message.author.name, ctx.message.author.discriminator, ctx.guild.name, ctx.channel.name) + msg

		# Timestamp and save to file
		timeStamp = datetime.today().strftime("%Y-%m-%d %H.%M")
		filename = "cleaned-{}.txt".format(timeStamp)
		msg = msg.encode('utf-8')
		with open(filename, "wb") as myfile:
			myfile.write(msg)

		# Send the cleaner a pm letting them know we're done
		try:
			await ctx.author.send('*{}* message{} removed from *#{}* in *{}!*'.format(counter, "" if counter == 1 else "s", chan.name, ctx.guild.name))
			# PM the file
			await ctx.author.send(file=discord.File(filename))
		except:
			# Assume the author doesn't accept pms - just silently fail
			pass
		if self.shouldLog('message.delete', ctx.guild):
			# We're logging
			logmess = '{}#{} cleaned in #{}'.format(ctx.author.name, ctx.author.discriminator, chan.name)
			pfpurl = Utils.get_avatar(ctx.author)
			await self._logEvent(ctx.guild, "{:,} message{} removed.".format(counter, "" if counter == 1 else "s"), title=logmess, filename=filename, thumbnail=pfpurl)
		# Delete the remaining file
		os.remove(filename)
	
	
	@commands.command(pass_context=True)
	async def logpreset(self, ctx, *, preset = None):
		"""Can select one of 4 available presets - off, quiet, normal, verbose (bot-admin only)."""
		if not await Utils.is_bot_admin_reply(ctx): return
		
		if preset is None:
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
		"""Outputs whether or not we're logging is enabled, the log channel, and any set logging options (bot-admin only)."""
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
		
		if options is None:
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
		
		if options is None:
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

		if channel is None:
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
		if not await Utils.is_owner_reply(ctx): return

		if debug is None:
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
		if not await Utils.is_owner_reply(ctx): return

		if not os.path.exists('debug.txt'):
			return await ctx.send("No *debug.txt* found.")
		# Exists - remove it
		os.remove('debug.txt')
		await ctx.send('*debug.txt* removed!')


	@commands.command(pass_context=True)
	async def heartbeat(self, ctx):
		"""Write to the console and attempt to send a message (owner only)."""
		# Only allow owner
		if not await Utils.is_owner_reply(ctx): return
		
		timeStamp = datetime.today().strftime("%Y-%m-%d %H.%M")
		print('Heartbeat tested at {}.'.format(timeStamp))
		# Message send
		message = await ctx.send('Heartbeat tested at {}.'.format(timeStamp))
		print("Message:\n{}".format(message) if message else "No message returned.")
