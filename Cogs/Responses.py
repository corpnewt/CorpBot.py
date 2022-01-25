import discord, re, time
from discord.ext import commands
from Cogs import Settings, DisplayName, Utils, Nullify, PickList, Message

def setup(bot):
	# Add the bot and deps
	settings = bot.get_cog("Settings")
	bot.add_cog(Responses(bot, settings))

class Responses(commands.Cog):

	# Init with the bot reference, and a reference to the settings var
	def __init__(self, bot, settings):
		self.bot = bot
		self.settings = settings
		global Utils, DisplayName
		Utils = self.bot.get_cog("Utils")
		DisplayName = self.bot.get_cog("DisplayName")
		# Regex values
		self.regexUserName = re.compile(r"\[\[user\]\]",      re.IGNORECASE)
		self.regexUserPing = re.compile(r"\[\[atuser\]\]",    re.IGNORECASE)
		self.regexServer   = re.compile(r"\[\[server\]\]",    re.IGNORECASE)
		self.regexHere     = re.compile(r"\[\[here\]\]",      re.IGNORECASE)
		self.regexEveryone = re.compile(r"\[\[everyone\]\]",  re.IGNORECASE)
		self.regexDelete   = re.compile(r"\[\[delete\]\]",    re.IGNORECASE)
		self.regexMute     = re.compile(r"\[\[mute:?\d*\]\]", re.IGNORECASE)
		self.regexRoleMent = re.compile(r"\[\[(m_role|role_m):\d+\]\]",re.IGNORECASE)
		self.regexUserMent = re.compile(r"\[\[(m_user|user_m):\d+\]\]",re.IGNORECASE)
		self.regexKick     = re.compile(r"\[\[kick\]\]",      re.IGNORECASE)
		self.regexBan      = re.compile(r"\[\[ban\]\]",       re.IGNORECASE)
		self.regexSuppress = re.compile(r"\[\[suppress\]\]",  re.IGNORECASE)

	async def _get_response(self, ctx, message):
		message_responses = self.settings.getServerStat(ctx.guild, "MessageResponses", {})
		if not message_responses: return {}
		# Check for matching response triggers here
		content = message.replace("\n"," ") # Remove newlines for better matching
		for trigger in message_responses:
			check_time = time.perf_counter_ns()
			if not re.fullmatch(trigger, content): continue
			match_time = time.perf_counter_ns()-check_time
			response = {"matched":trigger,"match_time_ms":match_time/1000000}
			# Got a full match - build the message, send it and bail
			m = message_responses[trigger]
			if self.regexDelete.search(m): response["delete"] = True
			if self.regexSuppress.search(m): response["suppress"] = True
			action = "ban" if self.regexBan.search(m) else "kick" if self.regexKick.search(m) else "mute" if self.regexMute.search(m) else None
			if action:
				response["action"] = action
				if action == "mute":
					# Let's get the mute time - if any
					try: response["mute_time"] = int(self.regexMute.search(m).group(0).replace("]]","").split(":")[-1])
					except: pass
			m = re.sub(self.regexUserName, "{}".format(DisplayName.name(ctx.author)), m)
			m = re.sub(self.regexUserPing, "{}".format(ctx.author.mention), m)
			m = re.sub(self.regexServer,   "{}".format(Nullify.escape_all(ctx.guild.name)), m)
			m = re.sub(self.regexHere,     "@here", m)
			m = re.sub(self.regexEveryone, "@everyone", m)
			d = re.compile("\\d+")
			mentions = {
				"user": {
					"list":self.regexUserMent.finditer(m),
					"func":ctx.guild.get_member
				},
				"role": {
					"list":self.regexRoleMent.finditer(m),
					"func":ctx.guild.get_role
				}
			}
			for type in mentions:
				if not "func" in mentions[type]: continue # borken
				func = mentions[type]["func"]
				for mention in mentions[type].get("list",[]):
					# Convert the id to a member - make sure that resolves, then replace
					try:
						check_id = int(d.search(mention.group(0)).group(0))
						resolved = func(check_id)
						assert resolved
					except:
						continue # Broken, or didn't resolve
					m = m.replace(mention.group(0),resolved.mention)

			# Strip out leftovers from delete, ban, kick, mute, and suppress
			for sub in (self.regexDelete,self.regexBan,self.regexKick,self.regexMute,self.regexSuppress):
				m = re.sub(sub,"",m)
			response["message"] = m
			return response
		return {}

	@commands.Cog.listener()
	async def on_message(self, message):
		# Gather exclusions - no bots, no dms, and don't check if running a command
		if message.author.bot: return
		if not message.guild: return
		ctx = await self.bot.get_context(message)
		if ctx.command: return
		# Gather the response info - if any
		response = await self._get_response(ctx,message.content)
		if not response: return
		# See if we're admin/bot-admin - and bail if suppressed
		if Utils.is_bot_admin(ctx) and response.get("suppress"): return
		# Walk punishments first in order of severity (ban -> kick -> mute)
		if response.get("action") in ("ban","kick"):
			action = ctx.guild.ban if response["action"] == "ban" else ctx.guild.kick
			await action(ctx.author,reason="Response trigger matched")
		elif response.get("action") == "mute":
			mute = self.bot.get_cog("Mute")
			mute_time = None if not response.get("mute_time") else int(time.time())+response["mute_time"]
			if mute: await mute._mute(ctx.author,ctx.guild,cooldown=mute_time)
		# Check if we need to delete the message
		if response.get("delete"):
			try: await message.delete()
			except: pass # RIP - couldn't delete that one, I guess
		if response.get("message","").strip(): # Don't send an empty message, or one with just whitespace
			return await ctx.send(response["message"],allowed_mentions=discord.AllowedMentions.all())

	@commands.command()
	async def addresponse(self, ctx, regex_trigger = None, *, response = None):
		"""Adds a new response for the regex trigger - or updates the response if the trigger exists already.  If the trigger has spaces, it must be wrapped in quotes (bot-admin only).
		
		Value substitutions:
		
		[[user]]      = sender's name
		[[server]]    = server name

		Mention options:

		[[atuser]]    = sender mention
		[[m_role:id]] = role mention where id is the role id
		[[m_user:id]] = user mention where id is the user id
		[[here]]      = @here ping
		[[everyone]]  = @everyone ping

		Standard user behavioral flags (do not apply to admin/bot-admin):

		[[delete]]   = delete the original message
		[[ban]]      = bans the message author
		[[kick]]     = kicks the message author
		[[mute]]     = mutes the author indefinitely
		[[mute:#]]   = mutes the message author for # seconds

		Admin/bot-admin behavioral flags:

		[[suppress]] = suppresses output for admin/bot-admin author matches
		
		Example:  $addresponse "(?i)(hello there|\\btest\\b).*" [[atuser]], this is a test!
		
		This would look for a message starting with the whole word "test" or "hello there" (case-insensitive) and respond by pinging the user and saying "this is a test!"
		"""

		if not await Utils.is_bot_admin_reply(ctx): return
		if not regex_trigger or not response: return await ctx.send("Usage: `{}addresponse regex_trigger response`".format(ctx.prefix))
		# Ensure the regex is valid
		try: re.compile(regex_trigger)
		except Exception as e: return await ctx.send(Nullify.escape_all(str(e)))
		# Save the trigger and response
		message_responses = self.settings.getServerStat(ctx.guild, "MessageResponses", {})
		context = "Updated" if regex_trigger in message_responses else "Added new"
		message_responses[regex_trigger] = response
		self.settings.setServerStat(ctx.guild, "MessageResponses", message_responses)
		return await ctx.send("{} response trigger!".format(context))

	@commands.command()
	async def edittrigger(self, ctx, response_index = None, *, regex_trigger = None):
		"""Edits the regex trigger for the passed index.  The triggers passed here do not require quotes if there are spaces (bot-admin only)."""

		if not await Utils.is_bot_admin_reply(ctx): return
		if not regex_trigger or not response_index: return await ctx.send("Usage: `{}edittrigger response_index regex_trigger`".format(ctx.prefix))
		message_responses = self.settings.getServerStat(ctx.guild, "MessageResponses", {})
		if not message_responses: return await ctx.send("No responses setup!  You can use the `{}addresponse` command to add some.".format(ctx.prefix))
		# Ensure the passed index is valid
		try:
			response_index = int(response_index)
			assert 0 < response_index <= len(message_responses)
		except:
			return await ctx.send("You need to pass a valid integer from 1 to {:,}.\nYou can get a numbered list with `{}responses`".format(len(message_responses),ctx.prefix))
		# Ensure the regex is valid
		try: re.compile(regex_trigger)
		except Exception as e: return await ctx.send(Nullify.escape_all(str(e)))
		# Update the response
		ordered_responses = {}
		for index,key in enumerate(message_responses,start=1):
			ordered_responses[regex_trigger if index==response_index else key] = message_responses[key]
		self.settings.setServerStat(ctx.guild,"MessageResponses",ordered_responses)
		return await ctx.send("Updated response trigger at index {:,}!".format(response_index))

	@commands.command()
	async def editresponse(self, ctx, response_index = None, *, response = None):
		"""Edits the response for the passed index.  The response passed here does not require quotes if there are spaces (bot-admin only).
		
		Value substitutions:
		
		[[user]]     = user name
		[[atuser]]   = user mention
		[[server]]   = server name
		[[here]]     = @​here ping
		[[everyone]] = @​everyone ping

		Standard user behavioral flags (do not apply to admin/bot-admin):

		[[delete]]   = delete the original message
		[[ban]]      = bans the message author
		[[kick]]     = kicks the message author
		[[mute]]     = mutes the author indefinitely
		[[mute:#]]   = mutes the message author for # seconds

		Admin/bot-admin behavioral flags:

		[[suppress]] = suppresses output for admin/bot-admin author matches
		
		Example:  $editresponse 1 [[atuser]], this is a test!
		
		This would edit the first response trigger to respond by pinging the user and saying "this is a test!"""

		if not await Utils.is_bot_admin_reply(ctx): return
		if not response or not response_index: return await ctx.send("Usage: `{}editresponse response_index response`".format(ctx.prefix))
		message_responses = self.settings.getServerStat(ctx.guild, "MessageResponses", {})
		if not message_responses: return await ctx.send("No responses setup!  You can use the `{}addresponse` command to add some.".format(ctx.prefix))
		# Ensure the passed index is valid
		try:
			response_index = int(response_index)
			assert 0 < response_index <= len(message_responses)
		except:
			return await ctx.send("You need to pass a valid integer from 1 to {:,}.\nYou can get a numbered list with `{}responses`".format(len(message_responses),ctx.prefix))
		# Update the response
		message_responses[list(message_responses)[response_index-1]] = response
		self.settings.setServerStat(ctx.guild,"MessageResponses",message_responses)
		return await ctx.send("Updated response at index {:,}!".format(response_index))

	@commands.command()
	async def responses(self, ctx):
		"""Lists the response triggers and their responses (bot-admin only)."""
		
		if not await Utils.is_bot_admin_reply(ctx): return
		message_responses = self.settings.getServerStat(ctx.guild, "MessageResponses", {})
		if not message_responses: return await ctx.send("No responses setup!  You can use the `{}addresponse` command to add some.".format(ctx.prefix))
		entries = [{"name":"{}. ".format(i)+Nullify.escape_all(x),"value":Nullify.escape_all(message_responses[x])} for i,x in enumerate(message_responses,start=1)]
		return await PickList.PagePicker(title="Current Responses",list=entries,ctx=ctx).pick()

	@commands.command()
	async def remresponse(self, ctx, *, regex_trigger_number = None):
		"""Removes the passed response trigger (bot-admin only)."""
		
		if not await Utils.is_bot_admin_reply(ctx): return
		if not regex_trigger_number: return await ctx.send("Usage: `{}remresponse regex_trigger_number`\nYou can get a numbered list with `{}responses`".format(ctx.prefix,ctx.prefix))
		message_responses = self.settings.getServerStat(ctx.guild, "MessageResponses", {})
		if not message_responses: return await ctx.send("No responses setup!  You can use the `{}addresponse` command to add some.".format(ctx.prefix))
		# Make sure we got a number, and it's within our list range
		try:
			regex_trigger_number = int(regex_trigger_number)
			assert 0 < regex_trigger_number <= len(message_responses)
		except:
			return await ctx.send("You need to pass a valid integer from 1 to {:,}.\nYou can get a numbered list with `{}responses`".format(len(message_responses),ctx.prefix))
		# Remove it, save, and report
		message_responses.pop(list(message_responses)[regex_trigger_number-1],None)
		self.settings.setServerStat(ctx.guild, "MessageResponses", message_responses)
		return await ctx.send("Response trigger removed!")

	@commands.command()
	async def clearresponses(self, ctx):
		"""Removes all response triggers (bot-admin only)."""

		if not await Utils.is_bot_admin_reply(ctx): return
		self.settings.setServerStat(ctx.guild, "MessageResponses", {})
		return await ctx.send("All response triggers removed!")

	@commands.command()
	async def mvresponse(self, ctx, response_index = None, target_index = None):
		"""Moves the passed response index to the target index (bot-admin only)."""

		if not await Utils.is_bot_admin_reply(ctx): return
		if response_index == None or target_index == None:
			return await ctx.send("Usage: `{}mvresponse [response_index] [target_index]`\nYou can get a numbered list with `{}responses`".format(ctx.prefix,ctx.prefix))
		message_responses = self.settings.getServerStat(ctx.guild, "MessageResponses", {})
		if not message_responses: return await ctx.send("No responses setup!  You can use the `{}addresponse` command to add some.".format(ctx.prefix))
		# Make sure our indices are within the proper range
		try:
			response_index = int(response_index)
			target_index = int(target_index)
			assert all((0 < x <= len(message_responses) for x in (response_index,target_index)))
		except:
			return await ctx.send("Both `response_index` and `target_index` must be valid intergers from 1 to {:,}.\nYou can get a numbered list with `{}responses`".format(len(message_responses),ctx.prefix))
		if response_index == target_index: return await ctx.send("Both indices are the same - nothing to move!")
		# Let's get the keys in a list - remove the target, add it to the desired index, then build a new dict with the elements
		keys = list(message_responses)
		keys.insert(target_index-1,keys.pop(response_index-1))
		ordered_responses = {}
		for key in keys: ordered_responses[key] = message_responses[key]
		self.settings.setServerStat(ctx.guild,"MessageResponses",ordered_responses)
		return await ctx.send("Moved response from {:,} to {:,}!".format(response_index,target_index))

	@commands.command()
	async def chkresponse(self, ctx, *, check_string = None):
		"""Reports a breakdown of the first match (if any) in the responses for the passed check string (bot-admin only)."""

		if not await Utils.is_bot_admin_reply(ctx): return
		if check_string == None: return await ctx.send("Usage: `{}checkresponse [check_string]`\nYou can get a numbered list with `{}responses`".format(ctx.prefix,ctx.prefix))
		message_responses = self.settings.getServerStat(ctx.guild, "MessageResponses", {})
		if not message_responses: return await ctx.send("No responses setup!  You can use the `{}addresponse` command to add some.".format(ctx.prefix))
		response = await self._get_response(ctx,check_string)
		if not response: return await ctx.send("No matches!")
		# Got a match - let's print out what it will do
		description = Nullify.escape_all(response.get("matched","Unknown match"))
		entries = []
		# Let's walk the reponse and add values
		entries.append({"name":"Output Suppressed for Admin/Bot-Admin:","value":"Yes" if response.get("suppress") else "No"})
		if response.get("action") == "mute":
			mute_time = "indefinitely" if not response.get("mute_time") else "for {:,} second{}".format(response["mute_time"],"" if response["mute_time"]==1 else "s")
			entries.append({"name":"Action:","value":"Mute {}".format(mute_time)})
		else:
			entries.append({"name":"Action:","value":str(response.get("action")).capitalize()})
		entries.append({"name":"Delete:","value":"Yes" if response.get("delete") else "No"})
		entries.append({"name":"Output Message:","value":"None" if not response.get("message","").strip() else response["message"]})
		return await PickList.PagePicker(title="Matched Response",description=description,list=entries,ctx=ctx,footer="Matched in {:,} ms".format(response["match_time_ms"])).pick()

	@commands.command()
	async def viewresponse(self, ctx, response_index = None):
		"""Displays the response in full which corresponds to the target index (bot-admin only)."""

		if not await Utils.is_bot_admin_reply(ctx): return
		if response_index == None: return await ctx.send("Usage: `{}viewresponse [response_index]`\nYou can get a numbered list with `{}responses`".format(ctx.prefix,ctx.prefix))
		message_responses = self.settings.getServerStat(ctx.guild, "MessageResponses", {})
		if not message_responses: return await ctx.send("No responses setup!  You can use the `{}addresponse` command to add some.".format(ctx.prefix))
		# Make sure we got a number, and it's within our list range
		try:
			response_index = int(response_index)
			assert 0 < response_index <= len(message_responses)
		except:
			return await ctx.send("You need to pass a valid integer from 1 to {:,}.\nYou can get a numbered list with `{}responses`".format(len(message_responses),ctx.prefix))
		return await Message.EmbedText(
			title="Response at index {:,}".format(response_index),
			description=Nullify.escape_all(message_responses[list(message_responses)[response_index-1]]),
			color=ctx.author
		).send(ctx)

	@commands.command()
	async def viewtrigger(self, ctx, response_index = None):
		"""Displays the regex trigger in full which corresponds to the target index (bot-admin only)."""

		if not await Utils.is_bot_admin_reply(ctx): return
		if response_index == None: return await ctx.send("Usage: `{}viewtrigger [response_index]`\nYou can get a numbered list with `{}responses`".format(ctx.prefix,ctx.prefix))
		message_responses = self.settings.getServerStat(ctx.guild, "MessageResponses", {})
		if not message_responses: return await ctx.send("No responses setup!  You can use the `{}addresponse` command to add some.".format(ctx.prefix))
		# Make sure we got a number, and it's within our list range
		try:
			response_index = int(response_index)
			assert 0 < response_index <= len(message_responses)
		except:
			return await ctx.send("You need to pass a valid integer from 1 to {:,}.\nYou can get a numbered list with `{}responses`".format(len(message_responses),ctx.prefix))
		return await Message.EmbedText(
			title="Trigger at index {:,}".format(response_index),
			description=Nullify.escape_all(list(message_responses)[response_index-1]),
			color=ctx.author
		).send(ctx)
