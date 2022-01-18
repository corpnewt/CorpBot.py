import asyncio, discord
from   discord.ext import commands
from   Cogs import Utils, ReadableTime, Message

def setup(bot):
	# Add the bot and deps
	settings = bot.get_cog("Settings")
	bot.add_cog(DisableCommand(bot, settings))

# This is the DisableCommand module. It allows servers to enable/disable specific commands

class DisableCommand(commands.Cog):

	# Init with the bot reference, and a reference to the settings var
	def __init__(self, bot, settings):
		self.bot = bot
		self.settings = settings
		self.exceptions = [ # Can be a cog or command
			"Settings",
			"CogManager",
			"Help"
		]
		global Utils, DisplayName
		Utils = self.bot.get_cog("Utils")
		DisplayName = self.bot.get_cog("DisplayName")

	async def message(self, message):
		# Check the message and see if we should allow it
		ctx = await self.bot.get_context(message)
		if not ctx.guild:
			# Don't restrict in pm
			return
		if not ctx.command:
			# No command - no need to check
			return
		# Get the list of blocked commands
		dis_com = self.settings.getServerStat(ctx.guild, "DisabledCommands")
		if ctx.command.name in dis_com:
			# Check if we're going to override
			admin_allow  = self.settings.getServerStat(ctx.guild, "AdminDisabledAccess")
			badmin_allow = self.settings.getServerStat(ctx.guild, "BAdminDisabledAccess")
			# Check if we're admin and bot admin
			is_admin  = Utils.is_admin(ctx)
			is_badmin = Utils.is_bot_admin_only(ctx)
			# Check if we override
			if (is_admin and admin_allow) or (is_badmin and badmin_allow):
				return
			# React if needed
			to_react = self.settings.getServerStat(ctx.guild, "DisabledReactions")
			if to_react:
				await message.add_reaction("🚫")
			# We have a disabled command - ignore it
			return { 'Ignore' : True, 'Delete' : False }

	def _get_our_comms(self):
		# Get our cog
		our_cog = self.__module__.split(".")[1]
		# Build a list of commands
		our_comm_list = [c.name for c in self.bot.get_cog(our_cog).get_commands()]
		# Add our cog name to the list
		our_comm_list.append(our_cog)
		return our_comm_list

	def _get_commands(self, check):
		# Check Cogs first
		cog = self._get_cog_commands(check)
		if cog: return cog
		# Check for commands
		return self._get_command(check)

	def _get_command(self, command):
		# Returns the command in a list if it exists
		# excludes hidden commands
		for cog in self.bot.cogs:
			if cog in self.exceptions: continue
			for c in self.bot.get_cog(cog).get_commands():
				if any((x == command for x in [c.name]+list(c.aliases))):
					if c.hidden or c in self.exceptions: return None
					return [c.name]
		return None

	def _get_cog_commands(self, cog):
		# Returns a list of commands associated with the passed cog
		# excludes hidden commands
		if not cog in self.bot.cogs:
			return None
		if cog in self.exceptions:
			return None
		command_list = []
		for c in self.bot.get_cog(cog).get_commands():
			if not c.hidden and not c in self.exceptions:
				command_list.append(c.name)
		return command_list

	def _get_all_commands(self):
		# Returns a list of all commands - excludes hidden commands
		command_list = []
		for cog in self.bot.cogs:
			if cog in self.exceptions:
				continue
			for c in self.bot.get_cog(cog).get_commands():
				if not c.hidden and not c in self.exceptions:
					command_list.append(c.name)
		return command_list

	@commands.command(pass_context=True)
	async def disabledreact(self, ctx, *, yes_no = None):
		"""Sets whether the bot reacts to disabled commands when attempted (admin-only)."""
		if not await Utils.is_admin_reply(ctx): return
		await ctx.send(Utils.yes_no_setting(ctx,"Disabled command reactions","DisabledReactions",yes_no))

	@commands.command(pass_context=True)
	async def adminallow(self, ctx, *, yes_no = None):
		"""Sets whether admins can access disabled commands (admin-only)."""
		if not await Utils.is_admin_reply(ctx): return
		await ctx.send(Utils.yes_no_setting(ctx,"Admin disabled command access","AdminDisabledAccess",yes_no))

	@commands.command(pass_context=True)
	async def badminallow(self, ctx, *, yes_no = None):
		"""Sets whether bot-admins can access disabled commands (admin-only)."""
		if not await Utils.is_admin_reply(ctx): return
		await ctx.send(Utils.yes_no_setting(ctx,"Bot-admin disabled command access","BAdminDisabledAccess",yes_no))

	@commands.command(pass_context=True)
	async def disable(self, ctx, *, command_or_cog_name = None):
		"""Disables the passed command or all commands in the passed cog (admin-only).  Command and cog names are case-sensitive."""
		if not await Utils.is_admin_reply(ctx): return
		if command_or_cog_name == None:
			return await ctx.send("Usage: `{}disable [command_or_cog_name]`".format(ctx.prefix))
		# Make sure we're not trying to block anything in this cog
		if command_or_cog_name in self._get_our_comms():
			msg = "You can't disable any commands from this cog."
			return await Message.EmbedText(desc_head="```\n", desc_foot="```", color=ctx.author, description=msg, title="Disable Commands").send(ctx)
		# At this point - we should check if we have a command
		comm = self._get_commands(command_or_cog_name)
		if comm == None:
			msg = "\"{}\" is not a cog or command name that is eligible for this system.".format(command_or_cog_name)
			return await Message.EmbedText(desc_head="```\n", desc_foot="```", color=ctx.author, description=msg, title="Disable Commands").send(ctx)
		# Build a list of the commands we disable
		disabled = []
		dis_com = self.settings.getServerStat(ctx.guild, "DisabledCommands")
		for c in comm:
			if not c in dis_com:
				dis_com.append(c)
				disabled.append(c)
		if len(disabled):
			# We actually made changes - update the setting
			self.settings.setServerStat(ctx.guild, "DisabledCommands", dis_com)
		# Now we give some output
		msg = "All eligible passed commands are already disabled." if len(disabled) == 0 else ", ".join(sorted(disabled))
		title = "Disabled 1 Command" if len(disabled) == 1 else "Disabled {} Commands".format(len(disabled))
		await Message.EmbedText(desc_head="```\n", desc_foot="```", color=ctx.author, description=msg, title=title).send(ctx)

	@commands.command(pass_context=True)
	async def enable(self, ctx, *, command_or_cog_name = None):
		"""Enables the passed command or all commands in the passed cog (admin-only).  Command and cog names are case-sensitive."""
		if not await Utils.is_admin_reply(ctx): return
		if command_or_cog_name == None:
			return await ctx.send("Usage: `{}enable [command_or_cog_name]`".format(ctx.prefix))
		# We should check if we have a command
		comm = self._get_commands(command_or_cog_name)
		if comm == None:
			msg = "\"{}\" is not a cog or command name that is eligible for this system.".format(command_or_cog_name)
			return await Message.EmbedText(desc_head="```\n", desc_foot="```", color=ctx.author, description=msg, title="Enable Commands").send(ctx)
		# Build a list of the commands we disable
		enabled = []
		dis_com = self.settings.getServerStat(ctx.guild, "DisabledCommands")
		dis_copy = []
		for c in dis_com:
			if not c in comm:
				# Not in our list - keep it disabled
				dis_copy.append(c)
			else:
				# In our list - add it to the enabled list
				enabled.append(c)
		if len(enabled):
			# We actually made changes - update the setting
			self.settings.setServerStat(ctx.guild, "DisabledCommands", dis_copy)
		# Now we give some output
		msg = "All eligible passed commands are already enabled." if len(enabled) == 0 else ", ".join(sorted(enabled))
		title = "Enabled 1 Command" if len(enabled) == 1 else "Enabled {} Commands".format(len(enabled))
		await Message.EmbedText(desc_head="```\n", desc_foot="```", color=ctx.author, description=msg, title=title).send(ctx)

	@commands.command(pass_context=True)
	async def listdisabled(self, ctx):
		"""Lists all disabled commands (admin-only)."""
		if not await Utils.is_admin_reply(ctx): return
		dis_com = self.settings.getServerStat(ctx.guild, "DisabledCommands")
		msg = "No commands have been disabled." if len(dis_com) == 0 else ", ".join(sorted(dis_com))
		title = "1 Disabled Command" if len(dis_com) == 1 else "{} Disabled Commands".format(len(dis_com))
		await Message.EmbedText(desc_head="```\n", desc_foot="```", color=ctx.author, description=msg, title=title).send(ctx)

	@commands.command(pass_context=True)
	async def isdisabled(self, ctx, *, command_or_cog_name = None):
		"""Outputs whether the passed command - or all commands in a passed cog are disabled (admin-only)."""
		if not await Utils.is_admin_reply(ctx): return
		# Get our commands or whatever
		dis_com = self.settings.getServerStat(ctx.guild, "DisabledCommands")
		comm = self._get_commands(command_or_cog_name)
		if comm == None:
			msg = "\"{}\" is not a cog or command name that is eligible for this system.".format(command_or_cog_name)
			return await Message.EmbedText(desc_head="```\n", desc_foot="```", color=ctx.author, description=msg, title="Disabled Commands").send(ctx)
		is_cog = True if self.bot.get_cog(command_or_cog_name) else False
		# Now we check if they're all disabled
		disabled = []
		for c in dis_com:
			if c in comm:
				disabled.append(c)
		if is_cog:
			title = "1 Command Disabled in {}".format(command_or_cog_name) if len(disabled) == 1 else "{} Commands Disabled in {}".format(len(disabled), command_or_cog_name)
			if len(disabled) == 0:
				msg = "None"
				footer = "0% disabled"
			else:
				msg = ", ".join(disabled)
				footer = "{:,g}% disabled".format(round(len(disabled)/len(comm)*100, 2))
		else:
			title = "{} Command Status".format(command_or_cog_name)
			footer = None
			msg = "Disabled" if len(disabled) else "Enabled"
		await Message.EmbedText(desc_head="```\n", desc_foot="```", color=ctx.author, description=msg, title=title, footer=footer).send(ctx)

	@commands.command(pass_context=True)
	async def disableall(self, ctx):
		"""Disables all enabled commands outside this module (admin-only)."""
		if not await Utils.is_admin_reply(ctx): return
		# Setup our lists
		comm_list = self._get_all_commands()
		our_comm_list = self._get_our_comms()
		dis_com = self.settings.getServerStat(ctx.guild, "DisabledCommands")
		disabled = []

		# Iterate and disable
		for c in comm_list:
			if not c in our_comm_list and not c in dis_com:
				disabled.append(c)
				dis_com.append(c)
		if len(disabled):
			# We actually made changes - update the setting
			self.settings.setServerStat(ctx.guild, "DisabledCommands", dis_com)
			
		# Give some output
		msg = "All eligible commands are already disabled." if len(disabled) == 0 else ", ".join(sorted(disabled))
		title = "Disabled 1 Command" if len(disabled) == 1 else "Disabled {} Commands".format(len(disabled))
		await Message.EmbedText(desc_head="```\n", desc_foot="```", color=ctx.author, description=msg, title=title).send(ctx)

	@commands.command(pass_context=True)
	async def enableall(self, ctx):
		"""Enables all disabled commands (admin-only)."""
		if not await Utils.is_admin_reply(ctx): return
		# Setup our lists
		dis_com = self.settings.getServerStat(ctx.guild, "DisabledCommands")

		if len(dis_com):
			# We actually made changes - update the setting
			self.settings.setServerStat(ctx.guild, "DisabledCommands", [])
			
		# Give some output
		msg = "All eligible commands are already enabled." if len(dis_com) == 0 else ", ".join(sorted(dis_com))
		title = "Enabled 1 Command" if len(dis_com) == 1 else "Enabled {} Commands".format(len(dis_com))
		await Message.EmbedText(desc_head="```\n", desc_foot="```", color=ctx.author, description=msg, title=title).send(ctx)
