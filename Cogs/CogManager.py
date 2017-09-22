import asyncio
import discord
import os
import subprocess
from   discord.ext import commands
from   Cogs import DisplayName

def setup(bot):
	# Add the bot
	bot.add_cog(CogManager(bot))

class CogManager:

	# Init with the bot reference, and a reference to the settings var
	def __init__(self, bot):
		self.bot = bot
		self.settings = None

	@asyncio.coroutine
	async def on_ready(self):
		# Load cogs when bot is ready
		return

	def _load_extension(self, extension = None):
		# Loads extensions - if no extension passed, loads all
		# starts with Settings, then Mute
		if extension == None:
			# Load them all!
			self.bot.load_extension("Cogs.Settings")
			self.bot.dispatch("loaded_extension", self.bot.extensions.get("Cogs.Settings"))
			self.settings = self.bot.get_cog("Settings")
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
					except:
						pass
					# Try to load
					try:
						self.bot.load_extension("Cogs." + ext[:-3])
						self.bot.dispatch("loaded_extension", self.bot.extensions.get("Cogs."+ext[:-3]))
						cog_loaded += 1
					except:
						print("{} not loaded!".format(ext[:-3]))
						pass
			return ( cog_loaded, cog_count )
		else:
			for ext in os.listdir("Cogs"):
				if ext[:-3].lower() == extension.lower():
					# Found it - check if loaded
					# Try unloading
					try:
						# Only unload if loaded
						if "Cogs."+ext[:-3] in self.bot.extensions:
							self.bot.dispatch("unloaded_extension", self.bot.extensions.get("Cogs."+ext[:-3]))
							self.bot.unload_extension("Cogs."+ext[:-3])
					except:
						pass
					# Try to load
					try:
						self.bot.load_extension("Cogs."+ext[:-3])
						self.bot.dispatch("loaded_extension", self.bot.extensions.get("Cogs."+ext[:-3]))
					except:
						print("{} failed to load!".format(ext[:-3]))
						return ( 0, 1 )
					return ( 1, 1 )
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

	@commands.command(pass_context=True)
	async def reload(self, ctx, *, extension = None):
		"""Reloads the passed extension."""
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
			await ctx.send("Usage `{}reload [extension]`".format(ctx.prefix))
			return

		result = self._load_extension(extension)
		if result[1] == 0:
			await ctx.send("I couldn't find that extension.")
		else:
			if result[0] == 0:
				await ctx.send("Extension failed to load...")
			else:
				await ctx.send("Extension reloaded!")
				
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
		try:
			u = subprocess.Popen([git_location, 'pull'])
			u.wait()
			out, err = u.communicate()
		except:
			await ctx.send("Something went wrong!  Make sure you have git installed and in your path var!")
			return
		await ctx.send("Updated!")
		
