import asyncio, discord, time
from   discord.ext import commands
from   Cogs import DisplayName, ReadableTime, Nullify

def setup(bot):
	# Add the bot
	settings = bot.get_cog("Settings")
	bot.add_cog(Invite(bot, settings))

class Invite(commands.Cog):

	# Init with the bot reference, and a reference to the settings var
	def __init__(self, bot, settings):
		self.bot = bot
		self.settings = settings
		self.current_requests = []
		self.temp_allowed = []
		self.approval_time = 3600 # 1 hour for an approval to roll off
		self.request_time = 604800 # 7 x 24 x 3600 = 1 week for a request to roll off

	def _is_submodule(self, parent, child):
		return parent == child or child.startswith(parent + ".")

	async def onserverjoin(self, server):
		# First verify if we're joining servers
		if not self.settings.getGlobalStat("AllowServerJoin",True):
			# Not joining - see if we have temp access to a server
			temp = next((x for x in self.temp_allowed if x[0] == server.id),None)
			if temp:
				self.temp_allowed.remove(temp)
				# Add to our whitelist
				self._whitelist_server(temp[0])
				return False
			try:
				await server.leave()
			except:
				pass
			return True
		return False

	@commands.Cog.listener()
	async def on_guild_remove(self, server):
		# Remove from the whitelist if it exists
		self._unwhitelist_server(server.id)

	async def remove_request(self,user_server):
		# Wait for the allotted time and remove the request if it still exists
		await asyncio.sleep(self.request_time)
		try:
			self.current_requests.remove(user_server)
		except ValueError:
			pass

	async def remove_allow(self,server_id):
		# Wait for the allotted time and remove the temp_allowed value if it still exists
		await asyncio.sleep(self.approval_time)
		try:
			self.temp_allowed.remove(server_id)
		except ValueError:
			pass

	def _check_whitelist(self):
		# Helper method to whitelist all servers based on the "AllowServerJoin" setting - or else just revokes the whitelist entirely
		self.settings.setGlobalStat("ServerWhitelist",None if self.settings.getGlobalStat("AllowServerJoin",True) else [x.id for x in self.bot.guilds])

	def _whitelist_server(self, guild_id = None):
		# Takes a guild id and ensures it's whitelisted
		if not guild_id: return
		current_whitelist = self.settings.getGlobalStat("ServerWhitelist",[])
		current_whitelist = [] if not isinstance(current_whitelist,(list,tuple)) else current_whitelist
		current_whitelist.append(guild_id)
		self.settings.setGlobalStat("ServerWhitelist",current_whitelist)

	def _unwhitelist_server(self, guild_id = None):
		# Takes a guild id and removes it from the whitelist - if it finds it
		if not guild_id: return
		current_whitelist = self.settings.getGlobalStat("ServerWhitelist",[])
		current_whitelist = [] if not isinstance(current_whitelist,(list,tuple)) else [x for x in current_whitelist if not x == guild_id]
		self.settings.setGlobalStat("ServerWhitelist",current_whitelist if len(current_whitelist) else None)

	@commands.Cog.listener()
	async def on_loaded_extension(self, ext):
		# See if we were loaded
		if not self._is_submodule(ext.__name__, self.__module__):
			return
		await self.bot.wait_until_ready()
		# Check if we have the whitelist setup - and if not, auto-whitlelist all joined servers
		if self.settings.getGlobalStat("AllowServerJoin", True): return # No need to check - not restricting
		print("Verifying server whitelist...")
		current_whitelist = self.settings.getGlobalStat("ServerWhitelist",None)
		if not current_whitelist:
			print("No whitelist found - creating one with current servers.")
			return self._check_whitelist() # If we don't have one saved - save one and bail
		# Let's gather a list of any server we're on that's not in the whitelist
		server_list = [x.id for x in self.bot.guilds]
		bail_list = [x for x in server_list if not x in current_whitelist]
		# Leave the unwhitelisted servers
		t = time.time()
		for x in bail_list:
			server = self.bot.get_guild(x)
			print(" - {} not in whitelist - leaving...".format(x))
			try: 
				if server: await server.leave()
			except: print(" --> I couldn't leave {} :(".format(x))
		print("Whitelist verified - took {} seconds.".format(time.time() - t))

	@commands.command()
	async def invite(self, ctx, invite_url = None):
		"""Outputs a url you can use to invite me to your server."""
		if self.settings.getGlobalStat("AllowServerJoin", True):
			return await ctx.send('Invite me to *your* server with this link: \n<{}>'.format(
				discord.utils.oauth_url(self.bot.user.id, permissions=discord.Permissions(permissions=8))
			))
		# Check if we're temporarily allowing this server
		server = ctx.guild
		if invite_url:
			try:
				invite = await self.bot.fetch_invite(invite_url)
				server = invite.guild
			except:
				pass
		if server and any(x for x in self.temp_allowed if x[0] == server.id):
			# Got an invite
			return await ctx.send('Invite me to {} with this link: \n<{}>'.format(
				Nullify.clean(server.name),
				discord.utils.oauth_url(self.bot.user.id, permissions=discord.Permissions(permissions=8),guild=server)
			))
		return await ctx.send("You need approval from my owner{} to add me.  You can request it with `{}requestjoin guild_invite_url`.".format(
			"" if len(self.settings.getOwners()) == 1 else "s",
			ctx.prefix
		))

	@commands.command()
	async def requestjoin(self, ctx, invite_url = None):
		"""Forwards the invite url to the bot's owners for review."""
		if self.settings.getGlobalStat("AllowServerJoin", True):
			return await ctx.invoke(self.invite)
		# Get the list of owners - and account for any that have left
		owners = self.settings.getOwners()
		if not len(owners):
			return await ctx.send("I have not been claimed, *yet*.")
		if not invite_url:
			return await ctx.send("Usage: `{}requestjoin discord.gg_invite_url`".format(ctx.prefix))
		try:
			invite = await self.bot.fetch_invite(invite_url)
		except:
			return await ctx.send("That invite url was not valid or expired.")
		if invite.guild in self.bot.guilds:
			return await ctx.send("I'm already in that server.")
		temp = next((x for x in self.current_requests if x[1].id == invite.guild.id),None)
		if temp:
			return await ctx.send("I've already been requested for that server.  Request rolls off in {}, or when approved.".format(
				ReadableTime.getReadableTimeBetween(time.time(),temp[2])
			))
		temp = next((x for x in self.temp_allowed if x[0] == invite.guild.id),None)
		if temp:
			await ctx.invoke(self.invite,invite_url)
			return await ctx.send("Valid for {}.".format(ReadableTime.getReadableTimeBetween(time.time(),temp[1])))
		# Build a request to dm to up to the first 10 owners
		msg = "{} ({} - {}#{} - {})\nhas requested the bot for: {} ({})\nvia the following invite: {}".format(
			DisplayName.name(ctx.author),
			ctx.author.mention,
			Nullify.clean(ctx.author.name),
			ctx.author.discriminator,
			ctx.author.id,
			Nullify.clean(invite.guild.name),
			invite.guild.id,
			invite
		)
		owners = owners if len(owners) < 11 else owners[:10]
		for owner in owners:
			target = self.bot.get_user(int(owner))
			if not target:
				continue
			await target.send(msg)
		request = (ctx.author,invite.guild,time.time()+self.request_time,ctx)
		self.current_requests.append(request)
		self.bot.loop.create_task(self.remove_request(request))
		await ctx.send("I've forwarded the request to my owner{}.  The request is valid for {}.".format(
			"" if len(owners) == 1 else "s",
			ReadableTime.getReadableTimeBetween(0,self.request_time)))

	@commands.command()
	async def approvejoin(self, ctx, server_id = None):
		"""Temporarily allows the bot to join the passed server id or join url (owner-only)."""
		# Only allow owner
		isOwner = self.settings.isOwner(ctx.author)
		if isOwner == None:
			return await ctx.send('I have not been claimed, *yet*.')
		elif isOwner == False:
			return await ctx.send('You are not the *true* owner of me.  Only the rightful owner can use this command.')
		if server_id == None:
			return await ctx.send("Usage: `{}approvejoin server_id`".format(ctx.prefix))
		try:
			server_id = int(server_id)
		except:
			try:
				invite = await self.bot.fetch_invite(server_id)
				server_id = invite.guild.id
			except:
				return await ctx.send("Invalid server id passed.")
		guild_list = [x.id for x in self.bot.guilds]
		# Check if we're already on that server, or if it's already been approved
		if server_id in guild_list:
			return await ctx.send("I'm already in that server.")
		temp = next((x for x in self.temp_allowed if x[0] == server_id),None)
		if temp:
			# Let's remove the approval to allow it to re-add with a new time
			try:
				self.temp_allowed.remove(temp)
			except:
				pass
		# Allow the guild
		temp_allow = (server_id,time.time()+self.approval_time)
		self.temp_allowed.append(temp_allow)
		# Remove if it's been requested
		request = next((x for x in self.current_requests if x[1].id == invite.guild.id),None)
		if request:
			await request[3].send("{}, your request for me to join {} has been approved for the next {}.  You can invite me with this link:\n<{}>".format(
				request[0].mention,
				Nullify.clean(request[1].name),
				ReadableTime.getReadableTimeBetween(0,self.approval_time),
				discord.utils.oauth_url(self.bot.user.id, permissions=discord.Permissions(permissions=8),guild=request[1])
			))
			try:
				self.current_requests.remove(request)
			except:
				pass
		self.bot.loop.create_task(self.remove_allow(temp_allow))
		await ctx.send("I've been approved to join {} for the next {}.".format(
			server_id,
			ReadableTime.getReadableTimeBetween(0,self.approval_time)))

	@commands.command()
	async def revokejoin(self, ctx, server_id = None):
		"""Revokes a previously approved temporary join (owner-only)."""
		# Only allow owner
		isOwner = self.settings.isOwner(ctx.author)
		if isOwner == None:
			return await ctx.send('I have not been claimed, *yet*.')
		elif isOwner == False:
			return await ctx.send('You are not the *true* owner of me.  Only the rightful owner can use this command.')
		if server_id == None:
			return await ctx.send("Usage: `{}revokejoin server_id`".format(ctx.prefix))
		try:
			server_id = int(server_id)
		except:
			try:
				invite = await self.bot.fetch_invite(server_id)
				server_id = invite.guild.id
			except:
				return await ctx.send("Invalid server id passed.")
		guild_list = [x.id for x in self.bot.guilds]
		# Check if we're already on that server, or if it's already been approved
		if server_id in guild_list:
			return await ctx.send("I'm already in that server.")
		temp = next((x for x in self.temp_allowed if x[0] == server_id),None)
		if not temp:
			return await ctx.send("That server is not in my temp approved list.")
		self.temp_allowed.remove(temp)
		return await ctx.send("Approval to join guild id {} has been revoked.".format(server_id))

	@commands.command()
	async def canjoin(self, ctx, *, yes_no = None):
		"""Sets whether the bot is allowed to join new servers (owner-only and enabled by default)."""
		# Only allow owner
		isOwner = self.settings.isOwner(ctx.author)
		if isOwner == None:
			return await ctx.send('I have not been claimed, *yet*.')
		elif isOwner == False:
			return await ctx.send('You are not the *true* owner of me.  Only the rightful owner can use this command.')
		setting_name = "Allow new server joins"
		setting_val  = "AllowServerJoin"
		current = self.settings.getGlobalStat(setting_val, True)
		if yes_no == None:
			msg = "{} currently *{}.*".format(setting_name,"enabled" if current else "disabled")
		elif yes_no.lower() in [ "yes", "on", "true", "enabled", "enable" ]:
			yes_no = True
			msg = "{} {} *enabled*.".format(setting_name,"remains" if current else "is now")
		elif yes_no.lower() in [ "no", "off", "false", "disabled", "disable" ]:
			yes_no = False
			msg = "{} {} *disabled*.".format(setting_name,"remains" if not current else "is now")
		else:
			msg = "That's not a valid setting."
			yes_no = current
		if not yes_no == None and not yes_no == current:
			self.settings.setGlobalStat(setting_val, yes_no)
		# Force the whitelist update
		self._check_whitelist()
		await ctx.send(msg)

	@commands.command()
	async def block(self, ctx, *, server : str = None):
		"""Blocks the bot from joining a server - takes either a name or an id (owner-only).
		Can also take the id or case-sensitive name + descriminator of the owner (eg. Bob#1234)."""
		# Check if we're suppressing @here and @everyone mentions
		suppress = True if self.settings.getServerStat(ctx.guild,"SuppressMentions",True) else False
		# Only allow owner
		isOwner = self.settings.isOwner(ctx.author)
		if isOwner == None:
			return await ctx.send('I have not been claimed, *yet*.')
		elif isOwner == False:
			return await ctx.send('You are not the *true* owner of me.  Only the rightful owner can use this command.')
		if server == None:
			# No server provided
			return await ctx.send("Usage: `{}block [server name/id or owner name#desc/id]`".format(ctx.prefix))
		serverList = self.settings.getGlobalStat('BlockedServers',[])
		for serv in serverList:
			if str(serv).lower() == server.lower():
				# Found a match - already blocked.
				msg = "*{}* is already blocked!".format(serv)
				if suppress:
					msg = Nullify.clean(msg)
				return await ctx.send(msg)
		# Not blocked
		serverList.append(server)
		self.settings.setGlobalStat("BlockedServers",serverList)
		msg = "*{}* now blocked!".format(server)
		# Check for suppress
		if suppress:
			msg = Nullify.clean(msg)
		await ctx.send(msg)

	@commands.command()
	async def unblock(self, ctx, *, server : str = None):
		"""Unblocks a server or owner (owner-only)."""
		# Check if we're suppressing @here and @everyone mentions
		suppress = True if self.settings.getServerStat(ctx.guild,"SuppressMentions",True) else False
		# Only allow owner
		isOwner = self.settings.isOwner(ctx.author)
		if isOwner == None:
			return await ctx.send('I have not been claimed, *yet*.')
		elif isOwner == False:
			return await ctx.send('You are not the *true* owner of me.  Only the rightful owner can use this command.')
		if server == None:
			# No server provided
			return await ctx.send("Usage: `{}unblock [server name/id or owner name#desc/id]`".format(ctx.prefix))
		serverList = self.settings.getGlobalStat('BlockedServers',[])
		serverTest = [x for x in serverList if not str(x).lower() == server.lower()]
		if len(serverList) != len(serverTest):
			# Something changed
			self.settings.setGlobalStat("BlockedServers",serverTest)
			msg = "*{}* unblocked!".format(serv)
			if suppress:
				msg = Nullify.clean(msg)
			return await ctx.send(msg)
		# Not found
		msg = "I couldn't find *{}* in my blocked list.".format(server)
		# Check for suppress
		if suppress:
			msg = Nullify.clean(msg)
		await ctx.send(msg)

	@commands.command()
	async def unblockall(self, ctx):
		"""Unblocks all blocked servers and owners (owner-only)."""
		# Check if we're suppressing @here and @everyone mentions
		suppress = True if self.settings.getServerStat(ctx.guild,"SuppressMentions",True) else False
		# Only allow owner
		isOwner = self.settings.isOwner(ctx.author)
		if isOwner == None:
			return await ctx.send('I have not been claimed, *yet*.')
		elif isOwner == False:
			return await ctx.send('You are not the *true* owner of me.  Only the rightful owner can use this command.')
		self.settings.setGlobalStat('BlockedServers',[])
		await ctx.send("*All* servers and owners unblocked!")

	@commands.command()
	async def blocked(self, ctx):
		"""Lists all blocked servers and owners (owner-only)."""
		# Check if we're suppressing @here and @everyone mentions
		suppress = True if self.settings.getServerStat(ctx.guild,"SuppressMentions",True) else False
		# Only allow owner
		isOwner = self.settings.isOwner(ctx.author)
		if isOwner == None:
			return await ctx.send('I have not been claimed, *yet*.')
		elif isOwner == False:
			return await ctx.send('You are not the *true* owner of me.  Only the rightful owner can use this command.')
		serverList = self.settings.getGlobalStat('BlockedServers',[])
		if not len(serverList):
			msg = "There are no blocked servers or owners!"
		else:
			msg = "__Currently Blocked:__\n\n{}".format(', '.join(serverList))
		# Check for suppress
		if suppress:
			msg = Nullify.clean(msg)
		await ctx.send(msg)
