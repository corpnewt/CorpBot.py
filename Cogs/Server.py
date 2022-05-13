import discord, os, re
from   datetime import datetime
from   discord.ext import commands
from   Cogs import Utils, Message, PCPP

def setup(bot):
	# Add the bot and deps
	settings = bot.get_cog("Settings")
	bot.add_cog(Server(bot, settings))

# This module sets/gets some server info

class Server(commands.Cog):

	# Init with the bot reference, and a reference to the settings var and xp var
	def __init__(self, bot, settings):
		self.bot = bot
		self.settings = settings
		# Regex for extracting urls from strings
		self.regex = re.compile(r"(http|ftp|https)://([\w_-]+(?:(?:\.[\w_-]+)+))([\w.,@?^=%&:/~+#-]*[\w@?^=%&/~+#-])?")
		global Utils, DisplayName
		Utils = self.bot.get_cog("Utils")
		DisplayName = self.bot.get_cog("DisplayName")

	async def message(self, message):
		if not type(message.channel) is discord.TextChannel:
			return { "Ignore" : False, "Delete" : False }
		# Make sure we're not already in a parts transaction
		if self.settings.getGlobalUserStat(message.author, 'HWActive'):
			return { "Ignore" : False, "Delete" : False }
		# Check if we're attempting to run the pcpp command
		the_prefix = await self.bot.command_prefix(self.bot, message)
		if message.content.startswith(the_prefix):
			# Running a command - return
			return { "Ignore" : False, "Delete" : False }
		# Check if we have a pcpartpicker link
		matches = re.finditer(self.regex, message.content)
		pcpplink = None
		for match in matches:
			if 'pcpartpicker.com' in match.group(0).lower():
				pcpplink = match.group(0)
		if not pcpplink:
			# Didn't find any
			return { "Ignore" : False, "Delete" : False }
		autopcpp = self.settings.getServerStat(message.guild, "AutoPCPP")
		if autopcpp == None:
			return { "Ignore" : False, "Delete" : False }
		ret = await PCPP.getMarkdown(pcpplink, autopcpp)
		return { "Ignore" : False, "Delete" : False, "Respond" : ret }

	@commands.command()
	async def poll(self, ctx, *, poll_options = None):
		"""Starts a poll - which can take a custom title/question, as well as one or up to 10 options.

		You can provide an optional poll prompt as your first option by ending it with a colon (:).

		Poll options are separated by commas - if only one option is present, the poll will use thumbs up/down reactions.
		If 2-10 options are present, the poll will use numbered reactions for each.

		If you need to use commas or a colon in your prompt or options, you can use a backslash to escape them.
		
		Examples:
		- Thumbs up/down poll:
		    $poll Who likes pizza?
		- Multi-option poll:
		    $poll macOS, Windows, Linux
		- Thumbs up/down poll with a prompt:
		    $poll Days of the week:  Wednesday is the best
		- Multi-option poll with a prompt:
		    $poll Favorite day of the weekend?: Saturday, Sunday
		- Thumbs up/down poll using escaped comma:
		    $poll April\, May\, and June are the best months
		- Multi-option poll with prompt with escaped colon:
		    $poll Escaped\: Rest of Prompt: option 1, option 2, option 3
		"""

		if not poll_options: return await ctx.send("Usage: `{}poll (prompt:)[option 1(, option 2, option 3...)]`".format(ctx.prefix))
		
		# Helper to replace escaped characters
		def replace_escaped(val,esc = ",:"):
			for e in esc: val = val.replace("\\"+e,e)
			return val

		poll_options = poll_options.replace("\n"," ")
		desc = "**__New Poll by {}__**\n\n".format(ctx.author.mention)
		# First we check for a title
		title_check = [x for x in re.split(r"(?<!\\):",poll_options) if x]
		if len(title_check) > 1: # We have a valid title
			p_check = poll_options[len(title_check[0])+1:].strip()
			if p_check: # We have something left - parse
				# Add the title to our desc with escaped vars replaced
				desc += "{}:\n\n".format(replace_escaped(title_check[0]))
				# Update our poll options to skip the title
				poll_options = p_check
		# Let's see how many poll_options we have
		options = [replace_escaped(option.strip()) for option in re.split(r"(?<!\\),",poll_options) if option.strip()]
		if len(options) == 1: # Use thumbsup/thumbsdown
			desc += poll_options
			reactions = ("👍","👎")
		elif len(options) <= 10: # Have the right amount
			reactions = []
			for i,x in enumerate(options):
				reactions.append("{}\N{COMBINING ENCLOSING KEYCAP}".format(i+1) if i < 9 else "🔟")
				desc += "{} - {}\n".format(reactions[i],x.strip())
		else:
			return await ctx.send("Polls max out at 10 options.")
		# Remove the original message first
		try: await ctx.message.delete()
		except: pass # Maybe we don't have perms?  Ignore and continue
		message = await Message.Embed(
			description=desc,
			color=ctx.author,
			thumbnail=Utils.get_avatar(ctx.author)
		).send(ctx)
		# Add our poll reactions
		for r in reactions:
			await message.add_reaction(r)

	@commands.command(pass_context=True)
	async def setprefix(self, ctx, *, prefix : str = None):
		"""Sets the bot's prefix (bot-admin only)."""
		if not await Utils.is_bot_admin_reply(ctx): return
		# We're admin
		if not prefix:
			self.settings.setServerStat(ctx.guild, "Prefix", None)
			msg = 'Custom server prefix *removed*.'
		elif prefix in ['@everyone','@here']:
			return await ctx.send("Yeah, that'd get annoying *reaaaal* fast.  Try another prefix.")
		else:
			self.settings.setServerStat(ctx.guild, "Prefix", prefix)
			msg = 'Custom server prefix is now: {}'.format(prefix)
		await ctx.send(msg)

	@commands.command(pass_context=True)
	async def getprefix(self, ctx):
		"""Output's the server's prefix - custom or otherwise."""
		# Get the current prefix
		prefix = await self.bot.command_prefix(self.bot, ctx.message)
		prefixlist = ", ".join([x for x in prefix if not x == "<@!{}> ".format(self.bot.user.id)])
		msg = 'Prefix{}: {}'.format("es are" if len(prefix) > 1 else " is",prefixlist)
		await ctx.send(msg)
	
	@commands.command(pass_context=True)
	async def autopcpp(self, ctx, *, setting : str = None):
		"""Sets the bot's auto-pcpartpicker markdown if found in messages (admin-only). Setting can be normal, md, mdblock, bold, bolditalic, or nothing."""
		if not await Utils.is_admin_reply(ctx): return
		if setting == None:
			# Disabled
			self.settings.setServerStat(ctx.guild, "AutoPCPP", None)
			msg = 'Auto pcpartpicker *disabled*.'
		elif setting.lower() == "normal":
			self.settings.setServerStat(ctx.guild, "AutoPCPP", "normal")
			msg = 'Auto pcpartpicker set to *Normal*.'
		elif setting.lower() == "md":
			self.settings.setServerStat(ctx.guild, "AutoPCPP", "md")
			msg = 'Auto pcpartpicker set to *Markdown*.'
		elif setting.lower() == "mdblock":
			self.settings.setServerStat(ctx.guild, "AutoPCPP", "mdblock")
			msg = 'Auto pcpartpicker set to *Markdown Block*.'
		elif setting.lower() == "bold":
			self.settings.setServerStat(ctx.guild, "AutoPCPP", "bold")
			msg = 'Auto pcpartpicker set to *Bold*.'
		elif setting.lower() == "bolditalic":
			self.settings.setServerStat(ctx.guild, "AutoPCPP", "bolditalic")
			msg = 'Auto pcpartpicker set to *Bold Italics*.'
		else:
			msg = "That's not one of the options."
		await ctx.send(msg)

	@commands.command(pass_context=True)
	async def setinfo(self, ctx, *, word : str = None):
		"""Sets the server info (bot-admin only)."""
		if not await Utils.is_bot_admin_reply(ctx): return
		# We're admin
		word = None if not word else word
		self.settings.setServerStat(ctx.guild,"Info",word)
		msg = "Server info *{}*.".format("updated" if word else "removed")
		await ctx.send(msg)

	@commands.command(pass_context=True)
	async def info(self, ctx):
		"""Displays the server info if any."""
		serverInfo = self.settings.getServerStat(ctx.guild, "Info")
		msg = 'I have no info on *{}* yet.'.format(ctx.guild.name)
		if serverInfo:
			msg = '*{}*:\n\n{}'.format(ctx.guild.name, serverInfo)
		await ctx.send(Utils.suppressed(ctx,msg))

	@commands.command(pass_context=True)
	async def dumpservers(self, ctx):
		"""Dumps a timpestamped list of servers into the same directory as the bot (owner only)."""
		if not await Utils.is_owner_reply(ctx): return
		timeStamp = datetime.today().strftime("%Y-%m-%d %H.%M")
		serverFile = 'ServerList-{}.txt'.format(timeStamp)
		message = await ctx.author.send('Saving server list to *{}*...'.format(serverFile))
		msg = ''
		for server in self.bot.guilds:
			msg += server.name + "\n"
			msg += str(server.id) + "\n"
			msg += server.owner.name + "#" + str(server.owner.discriminator) + "\n\n"
			msg += str(len(server.members)) + "\n\n"
		# Trim the last 2 newlines
		msg = msg[:-2].encode("utf-8")
		with open(serverFile, "wb") as myfile:
			myfile.write(msg)
		await message.edit(content='Uploading *{}*...'.format(serverFile))
		await ctx.author.send(file=discord.File(serverFile))
		await message.edit(content='Uploaded *{}!*'.format(serverFile))
		os.remove(serverFile)

	@commands.command(pass_context=True)
	async def leaveserver(self, ctx, *, targetServer = None):
		"""Leaves a server - can take a name or id (owner only)."""
		if not await Utils.is_owner_reply(ctx): return
		if targetServer == None:
			# No server passed
			msg = 'Usage: `{}leaveserver [id/name]`'.format(ctx.prefix)
			return await ctx.send(msg)
		# Check id first, then name
		guild = next((x for x in self.bot.guilds if str(x.id) == str(targetServer)),None)
		if not guild:
			guild = next((x for x in self.bot.guilds if x.name.lower() == targetServer.lower()),None)
		if guild:
			await guild.leave()
			try:
				await ctx.send("Alright - I left that server.")
			except:
				pass
			return
		await ctx.send("I couldn't find that server.")
