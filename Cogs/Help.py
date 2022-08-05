import discord, os
from   datetime import datetime
from   discord.ext import commands
from   Cogs import ReadableTime, DisplayName, Message, FuzzySearch, PickList

def setup(bot):
	# Add the cog
	bot.remove_command("help")
	bot.add_cog(Help(bot))

# This is the Help module. It replaces the built-in help command

class Help(commands.Cog):

	# Init with the bot reference, and a reference to the settings var
	def __init__(self, bot):
		self.bot = bot
		global DisplayName
		DisplayName = self.bot.get_cog("DisplayName")
		
	def _get_prefix(self, ctx):
		# Helper method to get the simplified prefix
		# Setup a clean prefix
		bot_member = ctx.guild.get_member(self.bot.user.id) if ctx.guild else ctx.bot.user
		# Replace name and nickname mentions
		name = "@"+DisplayName.name(bot_member)
		return ctx.prefix.replace("<@{}>".format(bot_member.id),name).replace("<@!{}>".format(bot_member.id),name)

	def _is_submodule(self, parent, child):
		return parent == child or child.startswith(parent + ".")

	def _get_help(self, command, max_len = 0):
		# A helper method to return the command help - or a placeholder if none
		if max_len == 0:
			# Get the whole thing
			return command.help if command.help else "Help not available..."
		else:
			c_help = command.help.split("\n")[0] if command.help else "Help not available..."
			return (c_help[:max_len-3]+"...") if len(c_help) > max_len else c_help

	async def _get_info(self, ctx, com = None):
		# Helper method to return a list of embed content
		# or None if no results
		prefix = self._get_prefix(ctx)
		# Setup the footer
		footer = "\nType `{}help command` for more info on a command. \n".format(prefix)
		footer += "You can also type `{}help category` for more info on a category.".format(prefix)
		# Get settings - and check them if they exist
		settings = self.bot.get_cog("Settings")
		disabled_list = settings.getServerStat(ctx.guild, "DisabledCommands", []) if settings and ctx.guild else []
		if com:
			# We passed a command or cog - let's gather info
			embed_list = {"title":com,"fields":[]}
			the_cog = self.bot.get_cog(com)
			if the_cog:
				# Get the extension
				for e in self.bot.extensions:
					b_ext = self.bot.extensions.get(e)
					if not self._is_submodule(b_ext.__name__, the_cog.__module__): continue
					# It's a submodule
					embed_list = {"title" : "{} Cog - {}.py Extension". format(com, e[5:]), "fields" : [] }
					break
				for command in sorted(the_cog.get_commands(), key=lambda x:x.name):
					# Make sure there are only non-hidden commands here
					if command.hidden: continue
					command_help = self._get_help(command, 80)
					name = "{}{} {}{}".format(
						prefix,
						command.name,
						command.signature,
						"" if not len(command.aliases) else " (AKA: {})".format(", ".join(command.aliases))
					)
					if command.name in disabled_list: name = "~~" + name + "~~ (Disabled)"
					embed_list["fields"].append({ "name" : name, "value" : "`└─ " + command_help + "`", "inline" : False })
				# If all commands are hidden - pretend it doesn't exist
				if not len(embed_list["fields"]): return None
				return embed_list
			the_com = self.bot.get_command(com)
			if the_com:
				for e in self.bot.extensions:
					b_ext = self.bot.extensions.get(e)
					if self._is_submodule(b_ext.__name__, the_com.cog.__module__):
						# It's a submodule
						embed_list = {"title" : "{} Cog - {}.py Extension".format(the_com.cog_name, e[5:]), "fields" : [] }
						break
				name = "**{}{} {}{}**".format(
					prefix,
					the_com.name,
					the_com.signature,
					"" if not len(the_com.aliases) else " (AKA: {})".format(", ".join(the_com.aliases))
				)
				embed_list["com_name"] = "~~"+name+"~~ (Disabled)" if the_com.name in disabled_list else name
				embed_list["com_desc"] = the_com.help
				embed_list["description"] = "{}\n```\n{}\n```".format(
					embed_list["com_name"],
					embed_list["com_desc"]
				)
				return embed_list
			return None
		# No command or cog - let's send the coglist
		embed_list = { "title" : "Current Categories", "fields" : [] }
		command_list = {}
		for cog in sorted(self.bot.cogs):
			if not len(self.bot.get_cog(cog).get_commands()): continue
			comms = self.bot.get_cog(cog).get_commands()
			# Make sure there are non-hidden commands here
			visible = [x for x in comms if not x.hidden]
			disabled = len([x for x in visible if x.name in disabled_list])
			if not len(visible): continue
			# Add the name of each cog in the list
			embed_list["fields"].append({
				"name":cog if not disabled else "~~"+cog+"~~ (Disabled)" if len(visible)==disabled else "{} ({} Disabled)".format(cog,disabled),
				"value":"`└─ {:,} command{}`".format(len(visible),"" if len(visible)==1 else "s"),
				"inline":True
			})
		return embed_list

	@commands.command(pass_context=True)
	async def dumphelp(self, ctx, tab_indent_count = None):
		"""Dumps a timestamped, formatted list of commands and descriptions into the same directory as the bot."""
		try:
			tab_indent_count = int(tab_indent_count)
			assert tab_indent_count > 0
		except:
			tab_indent_count = 1

		timeStamp = datetime.today().strftime("%Y-%m-%d %H.%M")
		serverFile = 'HelpList-{}.txt'.format(timeStamp)
		message = await ctx.send('Saving help list to *{}*...'.format(serverFile))
		msg = ''
		prefix = self._get_prefix(ctx)

		msg = ""
		# Get and format the help
		for cog in sorted(self.bot.cogs):
			# Get the extension
			the_cog = self.bot.get_cog(cog)
			cog_commands = [c for c in sorted(the_cog.get_commands(), key=lambda x:x.name) if not c.hidden]
			if not len(cog_commands): continue
			cog_count = "{:,} command{}".format(len(cog_commands),"" if len(cog_commands)==1 else "s")
			cog_string = "{}{} Cog ({})".format(
				"	"*tab_indent_count,
				cog,
				cog_count,
			)
			for e in self.bot.extensions:
				b_ext = self.bot.extensions.get(e)
				if self._is_submodule(b_ext.__name__, the_cog.__module__):
					# It's a submodule
					cog_string += " - {}.py Extension".format(e[5:])
					break
			cog_string += ":\n"
			for command in cog_commands:
				cog_string += "{}  {}{}\n{}  {}└─ {}\n".format(
					"	"*tab_indent_count,
					prefix+command.name+" "+command.signature,
					"" if not len(command.aliases) else " (AKA: {})".format(", ".join(command.aliases)),
					"	"*tab_indent_count,
					" "*len(prefix),
					self._get_help(command, 80)
				)
			cog_string += "\n"
			msg += cog_string
		# Encode to binary
		# Trim the trailing newlines
		msg = msg.rstrip().encode("utf-8")
		with open(serverFile, "wb") as myfile:
			myfile.write(msg)
		await message.edit(content='Uploading *{}*...'.format(serverFile))
		await ctx.send(file=discord.File(serverFile))
		await message.edit(content='Uploaded *{}!*'.format(serverFile))
		os.remove(serverFile)

	@commands.command(pass_context=True)
	async def dumpmarkdown(self, ctx):
		"""Dumps a timestamped, markdown-formatted list of commands and descriptions into the same directory as the bot."""
		tab_indent_count = 1

		timeStamp = datetime.today().strftime("%Y-%m-%d %H.%M")
		serverFile = 'HelpMarkdown-{}.md'.format(timeStamp)
		message = await ctx.send('Saving help list to *{}*...'.format(serverFile))
		prefix = self._get_prefix(ctx)
		
		cog_list = []
		msg = ""
		# Get and format the help
		for cog in sorted(self.bot.cogs):
			# Get the extension
			the_cog = self.bot.get_cog(cog)
			cog_commands = [c for c in sorted(the_cog.get_commands(), key=lambda x:x.name) if not c.hidden]
			if not len(cog_commands): continue
			cog_list.append(cog)
			cog_count = "{:,} command{}".format(len(cog_commands),"" if len(cog_commands)==1 else "s")
			cog_string = "## {}\n####{}{} Cog ({})".format(
				cog,
				"	"*tab_indent_count,
				cog,
				cog_count,
			)
			for e in self.bot.extensions:
				b_ext = self.bot.extensions.get(e)
				if self._is_submodule(b_ext.__name__, the_cog.__module__):
					# It's a submodule
					cog_string += " - {}.py Extension".format(e[5:])
					break
			cog_string += ":\n"
			for command in cog_commands:
				cog_string += "{}  {}{}\n{}  {}└─ {}\n".format(
					"	"*tab_indent_count,
					prefix+command.name+" "+command.signature,
					"" if not len(command.aliases) else " (AKA: {})".format(", ".join(command.aliases)),
					"	"*tab_indent_count,
					" "*len(prefix),
					self._get_help(command, 80)
				)
			cog_string += "\n"
			msg += cog_string
		msg = ", ".join(["[{}](#{})".format(x,x.lower()) for x in sorted(cog_list)])+"\n\n"+msg
		# Encode to binary
		# Trim the trailing newlines
		msg = msg.rstrip().encode("utf-8")
		with open(serverFile, "wb") as myfile:
			myfile.write(msg)
		await message.edit(content='Uploading *{}*...'.format(serverFile))
		await ctx.send(file=discord.File(serverFile))
		await message.edit(content='Uploaded *{}!*'.format(serverFile))
		os.remove(serverFile)

	@commands.command(pass_context=True)
	async def help(self, ctx, *, command = None):
		"""Lists the bot's commands and cogs.
		You can pass a command or cog to this to get more info (case-sensitive)."""
		
		result = await self._get_info(ctx, command)

		if result == None:
			# Get a list of all commands and modules and server up the 3 closest
			cog_name_list = []
			com_name_list = []
			# ali_name_list = []
			
			for cog in self.bot.cogs:
				if cog in cog_name_list: continue
				if not len(self.bot.get_cog(cog).get_commands()):
					# Skip empty cogs
					continue
				cog_commands = self.bot.get_cog(cog).get_commands()
				hid = True
				for comm in cog_commands:
					if comm.hidden: continue
					hid = False
					if comm.name in com_name_list: continue
					com_name_list.extend([comm.name]+list(comm.aliases))
				if not hid:
					cog_name_list.append(cog)
			
			# Get cog list:
			cog_match = FuzzySearch.search(command, cog_name_list)
			com_match = FuzzySearch.search(command, com_name_list)
			# ali_match = FuzzySearch.search(command, ali_name_list)

			# Build the embed
			m = Message.Embed()
			if type(ctx.author) is discord.Member:
				m.color = ctx.author.color
			m.title = "Cog or command Not Found"
			m.description = "No exact Cog or command matches for \"{}\".".format(command)
			if len(cog_match):
				cog_mess = "\n".join(["`└─ {}`".format(x["Item"]) for x in cog_match])
				m.add_field(name="Close Cog Matches:", value=cog_mess)
			if len(com_match):
				com_mess = "\n".join(["`└─ {}`".format(x["Item"]) for x in com_match])
				m.add_field(name="Close Command Matches:", value=com_mess)
			'''if len(ali_match):
				ali_mess = "\n".join(["`└─ {}`".format(x["Item"]) for x in ali_match])
				m.add_field(name="Close Command Alias Matches:", value=ali_mess)'''
			m.footer = "Cog and command names are case-sensitive."
			return await m.send(ctx)
		result["color"] = ctx.author
		bot_user = ctx.guild.get_member(self.bot.user.id) if ctx.guild else self.bot.user
		desc = "Get more info with \"{}help Cog\" or \"{}help command\".\nCog and command names are case-sensitive.\n\n{}: {}".format(
			self._get_prefix(ctx),
			self._get_prefix(ctx),
			bot_user.display_name,
			self.bot.description
		)
		return await PickList.PagePicker(
			title=result["title"],
			list=result["fields"],
			ctx=ctx,
			description=result.get("com_desc",desc),
			d_header=result.get("com_name","")+"```\n",
			d_footer="```",
			footer=result.get("footer","" if len(result["fields"]) else desc.replace("```\n","").split("\n")[0])
		).pick()
