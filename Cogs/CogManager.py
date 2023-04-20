import discord, os, dis, subprocess
from discord.ext import commands
from Cogs import Settings, Message, PickList

def setup(bot):
	# Add the bot
	try:
		settings = bot.get_cog("Settings")
	except:
		settings = None
	bot.add_cog(CogManager(bot, settings))

class CogManager(commands.Cog):

	# Init with the bot reference, and a reference to the settings var
	def __init__(self, bot, settings):
		self.preloads = ("Cogs.Utils","Cogs.DisplayName","Cogs.Settings","Cogs.Mute")
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

	@commands.Cog.listener()
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
			if not instr.opname == "IMPORT_FROM":
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
		if extension is None:
			# Load them all!
			for x in self.preloads:
				if x in self.bot.extensions:
					self.bot.dispatch("unloaded_extension", self.bot.extensions.get(x))
					try: self.bot.unload_extension(x)
					except: print("{} failed to unload!".format(x))
				try:
					self.bot.load_extension(x)
					self.bot.dispatch("loaded_extension", self.bot.extensions.get(x))
				except: print("{} failed to load!".format(x))
			cog_count = len(self.preloads) # Assumes the prior 2 loaded correctly
			cog_loaded = len(self.preloads) # Again, assumes success above
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
		if extension is None:
			# NEED an extension to unload
			return ( 0, 1 )
		for cog in self.bot.cogs:
			if cog.lower() == extension.lower():
				try:
					self.bot.unload_extension("Cogs."+cog)
				except:
					return ( 0, 1 )
		return ( 0, 0 )
		
	# Proof of concept stuff for reloading cog/extension
	def _is_submodule(self, parent, child):
		return parent == child or child.startswith(parent + ".")
	
	@commands.command(pass_context=True)
	async def imports(self, ctx, *, extension = None):
		"""Outputs the extensions imported by the passed extension."""
		if extension is None:
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


	@commands.command(aliases=["extensions","ext"])
	async def extension(self, ctx, *, extension = None):
		"""Outputs the cogs and command count for the passed extension - or all extensions and their corresponding cogs if none passed."""

		# Build our extensions dictionary
		ext_dict = {}
		for e in self.bot.extensions:
			ext_name = str(e)[5:]
			cog_list = ext_dict.get(ext_name,[])
			b_ext = self.bot.extensions.get(e)
			for cog in self.bot.cogs:
				# Get the cog
				b_cog = self.bot.get_cog(cog)
				if self._is_submodule(b_ext.__name__, b_cog.__module__):
					# Submodule - add it to the list
					cog_list.append(str(cog))
			# Retain any cogs located for the extension here
			if cog_list:
				ext_dict[ext_name] = cog_list
			else:
				cogless = ext_dict.get("Cogless",[])
				cogless.append(ext_name)
				ext_dict["Cogless"] = cogless
		# Check if we got anything
		if not ext_dict:
			return await Message.Embed(
				title="No Extensions Found",
				color=ctx.author
			).send(ctx)
		# Check if we're searching - and retrieve the extension if so
		fields = []
		if extension:
			# Map the key to the first match - case-insensitive
			ext_name = next((x for x in ext_dict if x.lower() == extension.lower()),None)
			if not ext_name:
				return await Message.Embed(
					title="Extension Not Found",
					description="Could not find an extension by that name.",
					color=ctx.author
				).send(ctx)
			if ext_name == "Cogless":
				title = "Extensions Without Cogs ({:,} Total)".format(len(ext_dict[ext_name]))
				fields.append({
					"name":"Cogless - Each Has 0 Commands",
					"value":"\n".join(["`└─ {}`".format(x) for x in ext_dict[ext_name]]),
					"inline":True
				})
			else:
				title = "{} Extension ({:,} Total Cog{})".format(ext_name,len(ext_dict[ext_name]),"" if len(ext_dict[ext_name])==1 else "s")
				# Got the target extension - gather its info
				for cog in ext_dict[ext_name]:
					try: comms = len(self.bot.get_cog(cog).get_commands())
					except: comms = 0 # Zero it out if it's not a cog, or has none
					fields.append({
						"name":cog,
						"value":"`└─ {:,} command{}`".format(comms,"" if comms==1 else "s"),
						"inline":True
					})
		else:
			# We're listing them all
			title = "All Extensions ({:,} Total)".format(len(ext_dict))
			ext_list = [x for x in sorted(list(ext_dict),key=lambda x:x.lower()) if not x == "Cogless"]
			if "Cogless" in ext_dict: ext_list.append("Cogless") # Make sure this comes last
			for ext_name in ext_list:
				fields.append({
					"name":ext_name,
					"value":"\n".join(["`└─ {}`".format(x) for x in ext_dict[ext_name]]),
					"inline":True
				})
		return await PickList.PagePicker(
			title=title,
			list=fields,
			ctx=ctx,
			max=24
		).pick()
		
	
	@commands.command(pass_context=True)
	async def reload(self, ctx, *, extension = None):
		"""Reloads the passed extension - or all if none passed."""
		# Only allow owner
		isOwner = self.settings.isOwner(ctx.author)
		if isOwner is None:
			msg = 'I have not been claimed, *yet*.'
			await ctx.channel.send(msg)
			return
		elif isOwner == False:
			msg = 'You are not the *true* owner of me.  Only the rightful owner can use this command.'
			await ctx.channel.send(msg)
			return

		if extension is None:
			message = await ctx.send("Reloading all extensions...")
			result = self._load_extension()
			res_str = "*{}* of *{}* extensions reloaded successfully!".format(result[0], result[1])
			await message.edit(content=res_str)
			return

		message = await ctx.send("Reloading extensions related to `{}`...".format(extension.replace("`","").replace("\\","")))
		result = self._load_extension(extension)
		
		if result[1] == 0:
			await message.edit(content="I couldn't find that extension.")
		else:
			e_string = "extension" if result[1] == 1 else "extensions"
			await message.edit(content="{}/{} connected {} reloaded!".format(result[0], result[1], e_string))
				
	@commands.command(pass_context=True)
	async def update(self, ctx, reset=None):
		"""Updates from git, pass "reset" or "-reset" to this command to first run "git reset --hard" (owner only)."""
		isOwner = self.settings.isOwner(ctx.author)
		if isOwner is None: return await ctx.send("I have not been claimed, *yet*.")
		elif isOwner == False: return await ctx.send("You are not the *true* owner of me.  Only the rightful owner can use this command.")
		
		# Let's find out if we *have* git first
		command = "where" if os.name == "nt" else "which"
		try:
			p = subprocess.run(command + " git", shell=True, check=True, stderr=subprocess.DEVNULL, stdout=subprocess.PIPE)
			git_location = p.stdout.decode("utf-8").split("\n")[0].split("\r")[0]
		except:
			git_location = None
			
		if not git_location: return await ctx.send("It looks like my host environment doesn't have git in its path var :(")

		# Check if we first reset
		message = None
		reset = reset is not None and "reset" in reset.lower()
		if reset:
			message = await Message.EmbedText(title="Resetting...", description="```\ngit reset --hard\n```", color=ctx.author).send(ctx)
			try:
				u = subprocess.Popen([git_location, "reset", "--hard"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
				out, err = u.communicate()
			except:
				return await Message.EmbedText(title="Something went wrong!", description="Make sure you have `git` in your PATH var.", color=ctx.author).edit(ctx, message)
		# Try to update
		args = {"title":"Updating...","description":"```\ngit pull\n```","color":ctx.author}
		message = await Message.EmbedText(**args).edit(ctx, message) if message else await Message.EmbedText(**args).send(ctx)
		try:
			u = subprocess.Popen([git_location, 'pull'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
			out, err = u.communicate()
			msg = "```\n"
			if len(out.decode("utf-8")):
				msg += out.decode("utf-8").replace("`", "\`") + "\n"
			if len(err.decode("utf-8")):
				msg += err.decode("utf-8").replace("`", "\`") + "\n"
			msg += "```"
			await Message.EmbedText(title="{}Update Results:".format("Reset and " if reset else ""), description=msg, color=ctx.author).edit(ctx, message)
		except:
			await Message.EmbedText(title="Something went wrong!", description="Make sure you have `git` in your PATH var.", color=ctx.author).edit(ctx, message)
		
