import asyncio
import discord
import os
import random
import math
import subprocess
from   discord.ext import commands
from   Cogs import DisplayName
from   Cogs import Settings

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
	async def extensions(self, ctx):
		"""Lists all extensions and their corresponding cogs."""
		# Build the embed
		if type(ctx.author) is discord.Member:
			help_embed = discord.Embed(color=ctx.author.color)
		else:
			help_embed = discord.Embed(color=random.choice(self.colors))
			
		# Setup blank dict
		ext_list = {}
		for extension in self.bot.extensions:
			if not extension in ext_list:
				ext_list[extension] = []
			# Get the extension
			b_ext = self.bot.extensions.get(extension)
			for cog in self.bot.cogs:
				# Get the cog
				b_cog = self.bot.get_cog(cog)
				if self._is_submodule(extension, cog):
					# Submodule - add it to the list
					ext_list[extension].append(cog)
		
		if not len(ext_list):
			# no extensions - somehow... just return
			return
		
		to_pm = len(ext_list) > 10
		page_count = 1
		page_total = math.ceil(len(ext_list)/25)
		if page_total > 1:
			help_embed.title = "Extensions (Page {:,} of {:,})".format(page_count, page_total)
		else:
			help_embed.title = "Extensions"
		for embed in ext_list:
			help_embed.add_field(name=embed, value=", ".join(ext_list[embed]), inline=embed["inline"])
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
		
