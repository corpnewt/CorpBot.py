import asyncio
import discord
from   operator import itemgetter
from   discord.ext import commands
from   Cogs import ReadableTime
from   Cogs import Message

def setup(bot):
	# Add the bot and deps
	settings = bot.get_cog("Settings")
	bot.add_cog(DisableCommand(bot, settings))

# This is the DisableCommand module. It allows servers to enable/disable specific commands

class DisableCommand:

	# Init with the bot reference, and a reference to the settings var
	def __init__(self, bot, settings):
		self.bot = bot
		self.settings = settings
		self.exceptions = [ # Can be a cog or command
			"Settings",
			"CogManager",
			"Help"
		]

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
			# Check if we're admin
			is_admin  = ctx.message.author.permissions_in(ctx.channel).administrator
			is_badmin = False
			# Check if we're bot-admin
			checkAdmin = self.settings.getServerStat(ctx.message.guild, "AdminArray")
			for role in ctx.author.roles:
				for aRole in checkAdmin:
					# Get the role that corresponds to the id
					if str(aRole['ID']) == str(role.id):
						isBadmin = True
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
		our_comm_list = [c.name for c in self.bot.get_cog_commands(our_cog)]
		# Add our cog name to the list
		our_comm_list.append(our_cog)
		return our_comm_list

	def _get_commands(self, check):
		# Check Cogs first
		cog = self._get_cog_commands(check)
		if cog:
			return cog
		# Check for commands
		return self._get_command(check)

	def _get_command(self, command):
		# Returns the command in a list if it exists
		# excludes hidden commands
		for cog in self.bot.cogs:
			if cog in self.exceptions:
				# Skip exceptions
				continue
			for c in self.bot.get_cog_commands(cog):
				if c.name == command:
					if c.hidden or c in self.exceptions:
						return None
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
		for c in self.bot.get_cog_commands(cog):
			if not c.hidden and not c in self.exceptions:
				command_list.append(c.name)
		return command_list

	def _get_all_commands(self):
		# Returns a list of all commands - excludes hidden commands
		command_list = []
		for cog in self.bot.cogs:
			if cog in self.exceptions:
				continue
			for c in self.bot.get_cog_commands(cog):
				if not c.hidden and not c in self.exceptions:
					command_list.append(c.name)
		return command_list

	@commands.command(pass_context=True)
	async def disabledreact(self, ctx, *, yes_no = None):
		"""Sets whether the bot reacts to disabled commands when attempted (admin-only)."""

		# Check for admin status
		isAdmin = ctx.author.permissions_in(ctx.channel).administrator
		if not isAdmin:
			await ctx.send("You do not have permission to use this command.")
			return

		setting_name = "Disabled command reactions"
		setting_val  = "DisabledReactions"

		current = self.settings.getServerStat(ctx.guild, setting_val)
		if yes_no == None:
			if current:
				msg = "{} currently *enabled.*".format(setting_name)
			else:
				msg = "{} currently *disabled.*".format(setting_name)
		elif yes_no.lower() in [ "yes", "on", "true", "enabled", "enable" ]:
			yes_no = True
			if current == True:
				msg = '{} remains *enabled*.'.format(setting_name)
			else:
				msg = '{} is now *enabled*.'.format(setting_name)
		elif yes_no.lower() in [ "no", "off", "false", "disabled", "disable" ]:
			yes_no = False
			if current == False:
				msg = '{} remains *disabled*.'.format(setting_name)
			else:
				msg = '{} is now *disabled*.'.format(setting_name)
		else:
			msg = "That's not a valid setting."
			yes_no = current
		if not yes_no == None and not yes_no == current:
			self.settings.setServerStat(ctx.guild, setting_val, yes_no)
		await ctx.send(msg)

	@commands.command(pass_context=True)
	async def adminallow(self, ctx, *, yes_no = None):
		"""Sets whether admins can access disabled commands (admin-only)."""

		# Check for admin status
		isAdmin = ctx.author.permissions_in(ctx.channel).administrator
		if not isAdmin:
			await ctx.send("You do not have permission to use this command.")
			return

		setting_name = "Admin disabled command access"
		setting_val  = "AdminDisabledAccess"

		current = self.settings.getServerStat(ctx.guild, setting_val)
		if yes_no == None:
			if current:
				msg = "{} currently *enabled.*".format(setting_name)
			else:
				msg = "{} currently *disabled.*".format(setting_name)
		elif yes_no.lower() in [ "yes", "on", "true", "enabled", "enable" ]:
			yes_no = True
			if current == True:
				msg = '{} remains *enabled*.'.format(setting_name)
			else:
				msg = '{} is now *enabled*.'.format(setting_name)
		elif yes_no.lower() in [ "no", "off", "false", "disabled", "disable" ]:
			yes_no = False
			if current == False:
				msg = '{} remains *disabled*.'.format(setting_name)
			else:
				msg = '{} is now *disabled*.'.format(setting_name)
		else:
			msg = "That's not a valid setting."
			yes_no = current
		if not yes_no == None and not yes_no == current:
			self.settings.setServerStat(ctx.guild, setting_val, yes_no)
		await ctx.send(msg)

	@commands.command(pass_context=True)
	async def badminallow(self, ctx, *, yes_no = None):
		"""Sets whether bot-admins can access disabled commands (admin-only)."""

		# Check for admin status
		isAdmin = ctx.author.permissions_in(ctx.channel).administrator
		if not isAdmin:
			await ctx.send("You do not have permission to use this command.")
			return

		setting_name = "Bot-admin disabled command access"
		setting_val  = "BAdminDisabledAccess"

		current = self.settings.getServerStat(ctx.guild, setting_val)
		if yes_no == None:
			if current:
				msg = "{} currently *enabled.*".format(setting_name)
			else:
				msg = "{} currently *disabled.*".format(setting_name)
		elif yes_no.lower() in [ "yes", "on", "true", "enabled", "enable" ]:
			yes_no = True
			if current == True:
				msg = '{} remains *enabled*.'.format(setting_name)
			else:
				msg = '{} is now *enabled*.'.format(setting_name)
		elif yes_no.lower() in [ "no", "off", "false", "disabled", "disable" ]:
			yes_no = False
			if current == False:
				msg = '{} remains *disabled*.'.format(setting_name)
			else:
				msg = '{} is now *disabled*.'.format(setting_name)
		else:
			msg = "That's not a valid setting."
			yes_no = current
		if not yes_no == None and not yes_no == current:
			self.settings.setServerStat(ctx.guild, setting_val, yes_no)
		await ctx.send(msg)

	@commands.command(pass_context=True)
	async def disable(self, ctx, *, command_or_cog_name = None):
		"""Disables the passed command or all commands in the passed cog (admin-only).  Command and cog names are case-sensitive."""
		# Check for admin status
		isAdmin = ctx.author.permissions_in(ctx.channel).administrator
		if not isAdmin:
			await ctx.send("You do not have permission to use this command.")
			return
		if command_or_cog_name == None:
			await ctx.send("Usage: `{}disable [command_or_cog_name]`".format(ctx.prefix))
			return
		# Make sure we're not trying to block anything in this cog
		if command_or_cog_name in self._get_our_comms():
			msg = "You can't disable any commands from this cog."
			await Message.EmbedText(desc_head="```\n", desc_foot="```", color=ctx.author, description=msg, title="Disable Commands").send(ctx)
			return
		# At this point - we should check if we have a command
		comm = self._get_commands(command_or_cog_name)
		if comm == None:
			msg = "\"{}\" is not a cog or command name that is eligible for this system.".format(command_or_cog_name)
			await Message.EmbedText(desc_head="```\n", desc_foot="```", color=ctx.author, description=msg, title="Disable Commands").send(ctx)
			return
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
		# Check for admin status
		isAdmin = ctx.author.permissions_in(ctx.channel).administrator
		if not isAdmin:
			await ctx.send("You do not have permission to use this command.")
			return
		if command_or_cog_name == None:
			await ctx.send("Usage: `{}enable [command_or_cog_name]`".format(ctx.prefix))
			return
		# We should check if we have a command
		comm = self._get_commands(command_or_cog_name)
		if comm == None:
			msg = "\"{}\" is not a cog or command name that is eligible for this system.".format(command_or_cog_name)
			await Message.EmbedText(desc_head="```\n", desc_foot="```", color=ctx.author, description=msg, title="Enable Commands").send(ctx)
			return
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
		# Check for admin status
		isAdmin = ctx.author.permissions_in(ctx.channel).administrator
		if not isAdmin:
			await ctx.send("You do not have permission to use this command.")
			return
		dis_com = self.settings.getServerStat(ctx.guild, "DisabledCommands")
		if not len(dis_com):
			msg = "No commands have been disabled."
		else:
			msg = ", ".join(sorted(dis_com))
		title = "1 Disabled Command" if len(dis_com) == 1 else "{} Disabled Commands".format(len(dis_com))
		await Message.EmbedText(desc_head="```\n", desc_foot="```", color=ctx.author, description=msg, title=title).send(ctx)

	@commands.command(pass_context=True)
	async def isdisabled(self, ctx, *, command_or_cog_name = None):
		"""Outputs whether the passed command - or all commands in a passed cog are disabled (admin-only)."""
		# Check for admin status
		isAdmin = ctx.author.permissions_in(ctx.channel).administrator
		if not isAdmin:
			await ctx.send("You do not have permission to use this command.")
			return
		# Get our commands or whatever
		dis_com = self.settings.getServerStat(ctx.guild, "DisabledCommands")
		comm = self._get_commands(command_or_cog_name)
		if comm == None:
			msg = "\"{}\" is not a cog or command name that is eligible for this system.".format(command_or_cog_name)
			await Message.EmbedText(desc_head="```\n", desc_foot="```", color=ctx.author, description=msg, title="Disabled Commands").send(ctx)
			return
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
		# Check for admin status
		isAdmin = ctx.author.permissions_in(ctx.channel).administrator
		if not isAdmin:
			await ctx.send("You do not have permission to use this command.")
			return

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
		# Check for admin status
		isAdmin = ctx.author.permissions_in(ctx.channel).administrator
		if not isAdmin:
			await ctx.send("You do not have permission to use this command.")
			return

		# Setup our lists
		dis_com = self.settings.getServerStat(ctx.guild, "DisabledCommands")

		if len(dis_com):
			# We actually made changes - update the setting
			self.settings.setServerStat(ctx.guild, "DisabledCommands", [])
			
		# Give some output
		msg = "All eligible commands are already enabled." if len(dis_com) == 0 else ", ".join(sorted(dis_com))
		title = "Enabled 1 Command" if len(dis_com) == 1 else "Enabled {} Commands".format(len(dis_com))
		await Message.EmbedText(desc_head="```\n", desc_foot="```", color=ctx.author, description=msg, title=title).send(ctx)