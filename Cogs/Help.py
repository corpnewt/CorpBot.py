import discord, os
from   datetime import datetime
from   discord.ext import commands
from   Cogs import ReadableTime, Message, FuzzySearch, PickList, Nullify

def setup(bot):
	# Add the cog
	bot.remove_command("help")
	bot.add_cog(Help(bot))

# This is the Help module. It replaces the built-in help command

class Help(commands.Cog):

	# Init with the bot reference, and a reference to the settings var
	def __init__(self, bot):
		self.bot = bot
		
	def _get_prefix(self, ctx):
		# Helper method to get the simplified prefix
		return Nullify.resolve_mentions(ctx.prefix,ctx=ctx,escape=False)

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

	def _dict_add_cog(self, current_dict, cog, prefix, command_named=None, show_hidden=False):
		the_cog = self.bot.get_cog(cog)
		if not the_cog:
			return current_dict # Didn't find it
		# Resolve the extension
		extension = "Unknown"
		for e in self.bot.extensions:
			b_ext = self.bot.extensions.get(e)
			if self._is_submodule(b_ext.__name__, the_cog.__module__):
				# It's a submodule
				extension = "{}.py".format(e[5:])
				break
		commands = sorted(the_cog.get_commands(),key=lambda x:x.name)
		if not show_hidden:
			commands = [c for c in commands if not c.hidden]
		if not commands:
			return current_dict
		# Build our info
		current_dict[cog] = {
			"command_count":len(commands),
			"extension":extension,
			"commands":{},
			"formatted":"	{} Cog ({:,} command{}){}:".format(
				cog,
				len(commands),
				"" if len(commands)==1 else "s",
				" - {} Extension".format(extension) if extension else ""
			),
		}
		# Add the markdown variant
		current_dict[cog]["markdown"] = "## {}\n####{}".format(cog,current_dict[cog]["formatted"])
		# Walk the commands
		for comm in sorted(commands,key=lambda x:x.name):
			if command_named and not command_named == comm.name:
				continue # Skip, as it doesn't match what we're looking for
			# Add the info
			current_dict[cog]["commands"][comm.name] = {
				"signature":comm.signature,
				"prefix":prefix,
				"aliases":comm.aliases,
				"help":self._get_help(comm,80),
				"formatted":"	  {}{}\n	  {}└─ {}".format(
					prefix+comm.name+" "+comm.signature,
					" (AKA: {})".format(", ".join(comm.aliases)) if comm.aliases else "",
					" "*len(prefix),
					self._get_help(comm,80)
				)
			}
		return current_dict

	def _dump_help(self, ctx, file_name=None, cog_or_command=None, markdown=False, show_hidden=False):
		if file_name is None:
			file_name = "{}HelpList-{}.txt".format(
				"" if cog_or_command is None else "{}-".format(cog_or_command),
				datetime.today().strftime("%Y-%m-%d %H.%M")
			)
		prefix = self._get_prefix(ctx)
		if cog_or_command:
			cog_dict = self._dict_add_cog({},cog_or_command,prefix,show_hidden=show_hidden)
			if not cog_dict:
				# Wasn't found - let's try to locate the command if possible
				for cog in self.bot.cogs:
					comm = next((c for c in self.bot.get_cog(cog).get_commands() if cog_or_command in (c.name,*c.aliases)),None)
					if comm:
						cog_dict = self._dict_add_cog({},cog,prefix,command_named=comm.name,show_hidden=show_hidden)
						break
		else:
			# Add them all
			cog_dict = {}
			for cog in sorted(self.bot.cogs):
				cog_dict = self._dict_add_cog(cog_dict,cog,prefix,show_hidden=show_hidden)
		# Walk our list and build the output text if any
		if not cog_dict:
			return None
		output = []
		for cog in cog_dict:
			cog_text = cog_dict[cog]["markdown" if markdown else "formatted"]
			for comm in cog_dict[cog]["commands"]:
				cog_text += "\n"+cog_dict[cog]["commands"][comm]["formatted"]
			output.append(cog_text)
		# Join all the elements with two newlines
		final_output = "\n\n".join(output)
		# Check if we need the markdown index
		if markdown:
			final_output = "{}\n\n{}".format(
				", ".join(["[{}](#{})".format(x,x.lower()) for x in cog_dict]),
				final_output
			)
		return final_output

	@commands.command()
	async def dumphelp(self, ctx, cog_or_command = None):
		"""Dumps and uploads a timestamped, formatted list of commands and descriptions.  Can optionally take a specific Cog or command name to dump help for."""

		file_name = "{}HelpList-{}.txt".format(
			"" if cog_or_command is None else "{}-".format(cog_or_command),
			datetime.today().strftime("%Y-%m-%d %H.%M")
		)
		prefix = self._get_prefix(ctx)
		output = self._dump_help(ctx,file_name,cog_or_command)
		if not output:
			return await ctx.send("I couldn't find that Cog or command.  Cog and command names are case-sensitive.")
		
		# Got something!
		message = await ctx.send('Saving help list to *{}*...'.format(file_name))
		# Encode to binary
		# Trim the trailing newlines
		output = output.rstrip().encode("utf-8")
		with open(file_name, "wb") as myfile:
			myfile.write(output)
		# Upload the resulting file and clean up
		await message.edit(content='Uploading *{}*...'.format(file_name))
		await ctx.send(file=discord.File(file_name))
		await message.edit(content='Uploaded *{}!*'.format(file_name))
		os.remove(file_name)

	@commands.command(aliases=["dumpmd"])
	async def dumpmarkdown(self, ctx, cog_or_command = None):
		"""Dumps and uploads a timestamped, markdown-formatted list of commands and descriptions.  Can optionally take a specific Cog or command name to dump help for."""
		
		file_name = "{}HelpMarkdown-{}.md".format(
			"" if cog_or_command is None else "{}-".format(cog_or_command),
			datetime.today().strftime("%Y-%m-%d %H.%M")
		)
		prefix = self._get_prefix(ctx)
		output = self._dump_help(ctx,file_name,cog_or_command,markdown=True)
		if not output:
			return await ctx.send("I couldn't find that Cog or command.  Cog and command names are case-sensitive.")
		
		# Got something!
		message = await ctx.send('Saving help list to *{}*...'.format(file_name))
		# Encode to binary
		# Trim the trailing newlines
		output = output.rstrip().encode("utf-8")
		with open(file_name, "wb") as myfile:
			myfile.write(output)
		# Upload the resulting file and clean up
		await message.edit(content='Uploading *{}*...'.format(file_name))
		await ctx.send(file=discord.File(file_name))
		await message.edit(content='Uploaded *{}!*'.format(file_name))
		os.remove(file_name)

	@commands.command()
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
			max=12 if result["fields"] else 100, # 12 fields or 100 lines of desc text
			d_header=result.get("com_name","")+"```\n",
			d_footer="```",
			footer=result.get("footer","" if len(result["fields"]) else desc.replace("```\n","").split("\n")[0])
		).pick()
