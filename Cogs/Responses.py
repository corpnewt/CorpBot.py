import discord, re
from discord.ext import commands
from Cogs import Settings, DisplayName, Utils, Nullify, PickList

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
		self.regexUserName = re.compile(r"\[\[[user]+\]\]",     re.IGNORECASE)
		self.regexUserPing = re.compile(r"\[\[[atuser]+\]\]",   re.IGNORECASE)
		self.regexServer   = re.compile(r"\[\[[server]+\]\]",   re.IGNORECASE)
		self.regexHere     = re.compile(r"\[\[[here]+\]\]",     re.IGNORECASE)
		self.regexEveryone = re.compile(r"\[\[[everyone]+\]\]", re.IGNORECASE)

	@commands.Cog.listener()
	async def on_message(self, message):
		if message.author.bot: return
		if not message.guild: return
		message_responses = self.settings.getServerStat(message.guild, "MessageResponses", {})
		if not message_responses: return
		# We have something to check
		ctx = await self.bot.get_context(message)
		if ctx.command: return # Don't check if we're running a command
		# Check for matching response triggers here
		content = message.content.replace("\n"," ") # Remove newlines for better matching
		for trigger in message_responses:
			match = re.fullmatch(trigger, content)
			if not match: continue
			# Got a full match - build the message, send it and bail
			m = message_responses[trigger]
			m = re.sub(self.regexUserName, "{}".format(DisplayName.name(message.author)), m)
			m = re.sub(self.regexUserPing, "{}".format(message.author.mention), m)
			m = re.sub(self.regexServer,   "{}".format(Nullify.escape_all(ctx.guild.name)), m)
			m = re.sub(self.regexHere,     "@here", m)
			m = re.sub(self.regexEveryone, "@everyone", m)
			return await ctx.send(m)

	@commands.command()
	async def addresponse(self, ctx, regex_trigger = None, *, response = None):
		"""Adds a new response for the regex trigger.  If the trigger has spaces, it must be wrapped in quotes (bot-admin only).
		Available Options:
		
		[[user]]     = user name
		[[atuser]]   = user mention
		[[server]]   = server name
		[[here]]     = @​here ping
		[[everyone]] = @​everyone ping
		
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
			return await ctx.send("You need to pass a valid number from 1 to {:,}.\nYou can get a numbered list with `{}responses`".format(len(message_responses),ctx.prefix))
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
