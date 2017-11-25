import asyncio
import discord
import os
import dis
import random
import math
import subprocess
from   discord.ext import commands
from   Cogs import DisplayName
from   Cogs import Settings
from   Cogs import Message

def setup(bot):
	# Add the bot
	try:
		settings = bot.get_cog("Settings")
	except:
		settings = None
	bot.add_cog(CogManager(bot, settings))

class CogManager:

	# Init with the bot reference, and a reference to the settings var
	def __init__(self, bot, settings):
		self.bot = bot
		self.settings = settings
		self.colors = [ 
				discord.Color.teal(),
				discord.Color.dark_teal(),
				discord.Color.green(),
				discord.Color.dark_green(),
				discord.Color.blue(),
				discord.Color.dark_blue(),
				discord.Color.purple(),
				discord.Color.dark_purple(),
				discord.Color.magenta(),
				discord.Color.dark_magenta(),
				discord.Color.gold(),
				discord.Color.dark_gold(),
				discord.Color.orange(),
				discord.Color.dark_orange(),
				discord.Color.red(),
				discord.Color.dark_red(),
				discord.Color.lighter_grey(),
				discord.Color.dark_grey(),
				discord.Color.light_grey(),
				discord.Color.darker_grey(),
				discord.Color.blurple(),
				discord.Color.greyple()
				]

	@asyncio.coroutine
	async def on_ready(self):
		# Load cogs when bot is ready
		return

	def _get_imports(self, file_name):
		if not os.path.exists("Cogs/" + file_name):
			return []
		file_string = open("Cogs/" + file_name, "rb").read().decode("utf-8")
		instructions = dis.get_instructions(file_string)
		imports = [__ for __ in instructions if 'IMPORT' in __.opname]
		i = []
		for instr in imports:
			if not instr.opname is "IMPORT_FROM":
				continue
			i.append(instr.argval)
		cog_imports = []
		for f in i:
			if os.path.exists("Cogs/" + f + ".py"):
				cog_imports.append(f)
		return cog_imports

	def _get_imported_by(self, file_name):
		ext_list = []
		for ext in os.listdir("Cogs"):
			# Avoid reloading Settings and Mute
			if not ext.lower().endswith(".py") or ext == file_name:
				continue
			if file_name[:-3] in self._get_imports(ext):
				ext_list.append(ext)
		return ext_list

	def _load_extension(self, extension = None):
		# Loads extensions - if no extension passed, loads all
		# starts with Settings, then Mute
		if extension == None:
			# Load them all!
			self.bot.load_extension("Cogs.Settings")
			self.bot.dispatch("loaded_extension", self.bot.extensions.get("Cogs.Settings"))
			self.bot.load_extension("Cogs.Mute")
			self.bot.dispatch("loaded_extension", self.bot.extensions.get("Cogs.Mute"))
			cog_count = 2 # Assumes the prior 2 loaded correctly
			cog_loaded = 2 # Again, assumes success above
			# Load the rest of the cogs
			for ext in os.listdir("Cogs"):
				# Avoid reloading Settings and Mute
				if ext.lower().endswith(".py") and not (ext.lower() in ["settings.py", "mute.py"]):
					# Valid cog - load it
					cog_count += 1
					# Try unloading
					try:
						# Only unload if loaded
						if "Cogs."+ext[:-3] in self.bot.extensions:
							self.bot.dispatch("unloaded_extension", self.bot.extensions.get("Cogs."+ext[:-3]))
							self.bot.unload_extension("Cogs."+ext[:-3])
					except Exception as e:
						print("{} failed to unload!".format(ext[:-3]))
						print("    {}".format(e))
						pass
					# Try to load
					try:
						self.bot.load_extension("Cogs." + ext[:-3])
						self.bot.dispatch("loaded_extension", self.bot.extensions.get("Cogs."+ext[:-3]))
						cog_loaded += 1
					except Exception as e:
						print("{} failed to load!".format(ext[:-3]))
						print("    {}".format(e))
						pass
			return ( cog_loaded, cog_count )
		else:
			for ext in os.listdir("Cogs"):
				if ext[:-3].lower() == extension.lower():
					# First - let's get a list of extensions
					# that imported this one
					to_reload = self._get_imported_by(ext)
					# Add our extension first
					to_reload.insert(0, ext)
					total = len(to_reload)
					success = 0
					# Iterate and reload
					for e in to_reload:
						# Try unloading
						try:
							# Only unload if loaded
							if "Cogs."+e[:-3] in self.bot.extensions:
								self.bot.dispatch("unloaded_extension", self.bot.extensions.get("Cogs."+e[:-3]))
								self.bot.unload_extension("Cogs."+e[:-3])
						except Exception as er:
							print("{} failed to unload!".format(e[:-3]))
							print("    {}".format(er))
							pass
						# Try to load
						try:
							self.bot.load_extension("Cogs."+e[:-3])
							self.bot.dispatch("loaded_extension", self.bot.extensions.get("Cogs."+e[:-3]))
							success += 1
						except Exception as er:
							print("{} failed to load!".format(e[:-3]))
							print("    {}".format(er))
					return ( success, total )
			# Not found
			return ( 0, 0 )

	def _unload_extension(self, extension = None):
		if extension == None:
			# NEED an extension to unload
			return ( 0, 1 )
		for cog in self.bot.cogs:
			if cog.lower() == extension.lower():
				try:
					self.bot.unload_extension("Cogs."+cog)
				except:
					return ( 0, 1 )
		return ( 0, 0 )
	
	async def _send_embed(self, ctx, embed, pm = False):
		# Helper method to send embeds to their proper location
		if pm == True and not ctx.channel == ctx.author.dm_channel:
			# More than 2 pages, try to dm
			try:
				await ctx.author.send(embed=embed)
				await ctx.message.add_reaction("📬")
			except discord.Forbidden:
				await ctx.send(embed=embed)
			return
		await ctx.send(embed=embed)
		
	# Proof of concept stuff for reloading cog/extension
	def _is_submodule(self, parent, child):
		return parent == child or child.startswith(parent + ".")
	
	@commands.command(pass_context=True)
	async def imports(self, ctx, *, extension = None):
		"""Outputs the extensions imported by the passed extension."""
		if extension == None:
			# run the extensions command
			await ctx.invoke(self.extensions)
			return
		for ext in os.listdir("Cogs"):
			# Avoid reloading Settings and Mute
			if not ext.lower().endswith(".py"):
				continue
			if ext[:-3].lower() == extension.lower():
				# Found it
				import_list = self._get_imports(ext)
				if not len(import_list):
					await ctx.send("That extension has no local extensions imported.")
				else:
					await ctx.send("Imports:\n\n{}".format(", ".join(import_list)))
				return
		await cxt.send("I couldn't find that extension...")


	@commands.command(pass_context=True)
	async def extension(self, ctx, *, extension = None):
		"""Outputs the cogs attatched to the passed extension."""
		if extension == None:
			# run the extensions command
			await ctx.invoke(self.extensions)
			return

		cog_list = []
		for e in self.bot.extensions:
			if not str(e[5:]).lower() == extension.lower():
				continue
			# At this point - we should've found it
			# Get the extension
			b_ext = self.bot.extensions.get(e)
			for cog in self.bot.cogs:
				# Get the cog
				b_cog = self.bot.get_cog(cog)
				if self._is_submodule(b_ext.__name__, b_cog.__module__):
					# Submodule - add it to the list
					cog_list.append(str(cog))
			# build the embed
			if type(ctx.author) is discord.Member:
				help_embed = discord.Embed(color=ctx.author.color)
			else:
				help_embed = discord.Embed(color=random.choice(self.colors))
			help_embed.title = str(e[5:]) + " Extension"
			if len(cog_list):
				total_commands = 0
				for cog in cog_list:
					total_commands += len(self.bot.get_cog_commands(cog))
				if len(cog_list) > 1:
					comm = "total command"
				else:
					comm = "command"
				if total_commands == 1:
					comm = "└─ 1 " + comm
				else:
					comm = "└─ {:,} {}s".format(total_commands, comm)
				help_embed.add_field(name=", ".join(cog_list), value=comm, inline=True)
			else:
				help_embed.add_field(name="No Cogs", value="└─ 0 commands", inline=True)
			await ctx.send(embed=help_embed)
			return
		await ctx.send("I couldn't find that extension.")


	@commands.command(pass_context=True)
	async def extensions(self, ctx):
		"""Lists all extensions and their corresponding cogs."""
		# Build the embed
		if type(ctx.author) is discord.Member:
			help_embed = discord.Embed(color=ctx.author.color)
		else:
			help_embed = discord.Embed(color=random.choice(self.colors))
			
		# Setup blank dict
		ext_list = {}
		cog_less = []
		for extension in self.bot.extensions:
			if not str(extension)[5:] in ext_list:
				ext_list[str(extension)[5:]] = []
			# Get the extension
			b_ext = self.bot.extensions.get(extension)
			for cog in self.bot.cogs:
				# Get the cog
				b_cog = self.bot.get_cog(cog)
				if self._is_submodule(b_ext.__name__, b_cog.__module__):
					# Submodule - add it to the list
					ext_list[str(extension)[5:]].append(str(cog))
			if not len(ext_list[str(extension)[5:]]):
				ext_list.pop(str(extension)[5:])
				cog_less.append(str(extension)[5:])
		
		if not len(ext_list) and not len(cog_less):
			# no extensions - somehow... just return
			return
		
		# Get all keys and sort them
		key_list = list(ext_list.keys())
		key_list = sorted(key_list)
		
		if len(cog_less):
			ext_list["Cogless"] = cog_less
			# add the cogless extensions at the end
			key_list.append("Cogless")
		
		to_pm = len(ext_list) > 25
		page_count = 1
		page_total = math.ceil(len(ext_list)/25)
		if page_total > 1:
			help_embed.title = "Extensions (Page {:,} of {:,})".format(page_count, page_total)
		else:
			help_embed.title = "Extensions"
		for embed in key_list:
			if len(ext_list[embed]):
				help_embed.add_field(name=embed, value="└─ " + ", ".join(ext_list[embed]), inline=True)
			else:
				help_embed.add_field(name=embed, value="└─ None", inline=True)
			# 25 field max - send the embed if we get there
			if len(help_embed.fields) >= 25:
				if page_total == page_count:
					if len(ext_list) == 1:
						help_embed.set_footer(text="1 Extension Total")
					else:
						help_embed.set_footer(text="{} Extensions Total".format(len(ext_list)))
				await self._send_embed(ctx, help_embed, to_pm)
				help_embed.clear_fields()
				page_count += 1
				if page_total > 1:
					help_embed.title = "Extensions (Page {:,} of {:,})".format(page_count, page_total)
		
		if len(help_embed.fields):
			if len(ext_list) == 1:
				help_embed.set_footer(text="1 Extension Total")
			else:
				help_embed.set_footer(text="{} Extensions Total".format(len(ext_list)))
			await self._send_embed(ctx, help_embed, to_pm)
		
	
	@commands.command(pass_context=True)
	async def reload(self, ctx, *, extension = None):
		"""Reloads the passed extension - or all if none passed."""
		# Only allow owner
		isOwner = self.settings.isOwner(ctx.author)
		if isOwner == None:
			msg = 'I have not been claimed, *yet*.'
			await ctx.channel.send(msg)
			return
		elif isOwner == False:
			msg = 'You are not the *true* owner of me.  Only the rightful owner can use this command.'
			await ctx.channel.send(msg)
			return

		if extension == None:
			message = await ctx.send("Reloading all extensions...")
			result = self._load_extension()
			res_str = "*{}* of *{}* extensions reloaded successfully!".format(result[0], result[1])
			await message.edit(content=res_str)
			return

		result = self._load_extension(extension)
		if result[1] == 0:
			await ctx.send("I couldn't find that extension.")
		else:
			e_string = "extension" if result[1] == 1 else "extensions"
			await ctx.send("{}/{} connected {} reloaded!".format(result[0], result[1], e_string))
				
	@commands.command(pass_context=True)
	async def update(self, ctx):
		"""Updates from git."""
		isOwner = self.settings.isOwner(ctx.author)
		if isOwner == None:
			msg = 'I have not been claimed, *yet*.'
			await ctx.channel.send(msg)
			return
		elif isOwner == False:
			msg = 'You are not the *true* owner of me.  Only the rightful owner can use this command.'
			await ctx.channel.send(msg)
			return
		
		# Let's find out if we *have* git first
		if os.name == 'nt':
			# Check for git
			command = "where"
		else:
			command = "which"
		try:
			p = subprocess.run(command + " git", shell=True, check=True, stderr=subprocess.DEVNULL, stdout=subprocess.PIPE)
			git_location = p.stdout.decode("utf-8").split("\n")[0].split("\r")[0]
		except:
			git_location = None
			
		if not git_location:
			await ctx.send("It looks like my host environment doesn't have git in its path var :(")
			return
		# Try to update
		message = await Message.EmbedText(title="Updating...", description="git pull", color=ctx.author).send(ctx)
		try:
			u = subprocess.Popen([git_location, 'pull'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
			out, err = u.communicate()
			msg = "```\n"
			if len(out.decode("utf-8")):
				msg += out.decode("utf-8").replace("`", "\`") + "\n"
			if len(err.decode("utf-8")):
				msg += err.decode("utf-8").replace("`", "\`") + "\n"
			msg += "```"
			await Message.EmbedText(title="Update Results:", description=msg, color=ctx.author).edit(ctx, message)
		except:
			await ctx.send("Something went wrong!  Make sure you have git installed and in your path var!")
			return
		
