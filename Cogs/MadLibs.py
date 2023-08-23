import discord, re, os, random, string
from   discord.ext import commands
from   Cogs import Settings, DisplayName, Nullify, PickList

def setup(bot):
	# Add the bot and deps
	settings = bot.get_cog("Settings")
	bot.add_cog(MadLibs(bot, settings))

class MadLibs(commands.Cog):

	# Init with the bot reference, and a reference to the settings var
	def __init__(self, bot, settings):
		self.bot = bot
		self.settings = settings
		# Setup/compile our regex
		self.regex = re.compile(r"\[\[[^\[\]]+\]\]")
		self.prefix = "ml"
		self.leavePrefix = "mleave"
		self.playing_madlibs = {}
		global DisplayName
		DisplayName = self.bot.get_cog("DisplayName")

	@commands.command()
	async def ml(self, ctx, *, word = None):
		"""Used to choose your words when in the middle of a madlibs."""
		if not self.playing_madlibs.get(str(ctx.guild.id)):
			await ctx.invoke(self.madlibs,madlib=word)

	@commands.command()
	async def mleave(self, ctx):
		"""Used to leave a current MadLibs game."""
		pass

	@commands.command(aliases=["mlist","madlibslist","listmadlibs"])
	async def listml(self, ctx):
		"""List the available MadLibs"""

		# Check if our folder exists
		if not os.path.isdir("./Cogs/MadLibs"):
			return await ctx.send("I'm not configured for MadLibs yet...")
		# Folder exists - let's see if it has any files
		choices = ["{}. {}".format(i,x[:-4]) for i,x in enumerate(os.listdir("./Cogs/MadLibs"),start=1) if x.endswith(".txt")]
		return await PickList.PagePicker(
			title="Available MadLibs ({:,} total)".format(len(choices)),
			description="\n".join(choices),
			ctx=ctx
		).pick()

	@commands.command()
	async def madlibs(self, ctx, *, madlib = None):
		"""Let's play MadLibs!"""

		# Check if we have a MadLibs channel - and if so, restrict to that
		channel = self.settings.getServerStat(ctx.guild,"MadLibsChannel")
		if channel:
			# Resolve the id to the channel itself
			channel = self.bot.get_channel(int(channel))
			if channel and channel != ctx.channel:
				return await ctx.send("This isn't the channel for that.  Please take the MadLibs to {}.".format(channel.mention))

		# Check if our folder exists
		if not os.path.isdir("./Cogs/MadLibs"):
			return await ctx.send("I'm not configured for MadLibs yet...")

		# Folder exists - let's see if it has any files
		choices = [x for x in os.listdir("./Cogs/MadLibs") if x.endswith(".txt")]
		
		if not choices:
			# No madlibs...
			return await ctx.send("I'm not configured for MadLibs yet...")
		
		# Check if we're already in a game
		if self.playing_madlibs.get(str(ctx.guild.id)):
			return await ctx.send("I'm already playing MadLibs - use `{}{} [your word]` to submit answers.".format(Nullify.resolve_mentions(ctx.prefix,ctx=ctx,escape=False),self.prefix))

		# Check if we're taking a number - or the title of one of the MadLibs
		if madlib:
			randLib = None
			try:
				madloc = int(madlib)
				assert 0 < madloc <= len(choices)
				# Got an index
				randLib = choices[madloc-1]
			except:
				# Got a title
				randLib = next((x for x in choices if x[:-4].lower() == madlib.lower() or x.lower() == madlib.lower()),None)
			if not randLib:
				return await ctx.send("I couldn't find that MadLibs - you can use `{}listml` to see a list of available options.".format(Nullify.resolve_mentions(ctx.prefix,ctx=ctx,escape=False)))
		else: # Picking one at random
			randLib = random.choice(choices)
		
		self.playing_madlibs[str(ctx.guild.id)] = True

		# Let's load our text and get to work
		with open("./Cogs/MadLibs/{}".format(randLib), 'rb') as f:
			data = f.read().decode("utf-8")

		# Gather an array of words
		words = [x.group(0) for x in re.finditer(self.regex,data)]

		# At this point we need to scrape for words that end with _#
		reused_words = {}
		count_adjust = 0
		for word in words:
			try: int(word[2:-2].split("_")[-1])
			except: continue # Not formatted with _#
			if not word.lower() in reused_words:
				reused_words[word.lower()] = None
			else:
				count_adjust += 1 # Increment the amount we adjust by
		
		# Create empty substitution array
		subs = []

		# Iterate words and ask for input
		prompt_adjust = 0
		for i,word in enumerate(words,start=1):
			# First check if the word is in our reused_words list - and if
			# it's already received a value
			if reused_words.get(word.lower()):
				prompt_adjust += 1 # Adjust our prompt index
				# Got a value for it - just use that
				val = reused_words[word.lower()]
				# Append and capitalize if needed based on context
				subs.append(string.capwords(val) if word[2].isupper() else val)
				# No need to prompt - onto the next
				continue
			
			# Didn't match the reused_words list - or doesn't have an initial value set
			# Prompt the user for the word
			vowels = "aeiou"
			prompt = word[2:-2] # Strip [[ ]]
			# Check if it uses a number at the end
			try:
				int(prompt.split("_")[-1])
				# If we get here - it does, strip that from the prompt
				prompt = "_".join(prompt.split("_")[:-1])
			except: # It doesn't - leave it as-is
				pass
			await ctx.send("I need a{} **{}** (word *{:,}/{:,}*).  `{}{} [your word]`".format(
				"n" if prompt[0].lower() in vowels else "",
				prompt,
				i-prompt_adjust,
				len(words)-count_adjust,
				Nullify.resolve_mentions(ctx.prefix,ctx=ctx,escape=False),
				self.prefix
			))

			# Get the available prefixes
			prefixes      = await self.bot.get_prefix(ctx.message)
			allowed_ml    = tuple(["{}{}".format(x,self.prefix).lower() for x in prefixes])
			allowed_leave = tuple(["{}mleave".format(x,self.prefix).lower() for x in prefixes])

			# Setup the check
			def check(msg):
				# Check the channel
				if not msg.channel == ctx.channel: return False
				# Make sure it uses an allowed prefix
				prefix = next((x for x in allowed_ml if msg.content.lower().startswith(x)),None)
				if not prefix:
					# Check if it's a leave prefix
					prefix = next((x for x in allowed_leave if msg.content.lower().startswith(x)),None)
					if not prefix:
						# Didn't get a valid prefix - bail
						return False
				# Make sure we have something *after* the prefix as well
				if not msg.content[len(prefix):].strip(): return False
				# All checks passed
				return True

			# Wait for a response
			try:
				talk = await self.bot.wait_for('message', check=check, timeout=60)
			except:
				talk = None

			if not talk:
				# We timed out - leave the loop
				self.playing_madlibs.pop(str(ctx.guild.id),None)
				return await ctx.send("*{}*, I'm done waiting... we'll play another time.".format(DisplayName.name(ctx.author)))

			# Check if the message is to leave
			if talk.content.lower().startswith(allowed_leave):
				if talk.author == ctx.author:
					self.playing_madlibs.pop(str(ctx.guild.id),None)
					return await ctx.send("Alright, *{}*.  We'll play another time.".format(DisplayName.name(ctx.author)))
				else:
					# Not the originator
					await ctx.send("Only the originator (*{}*) can leave the MadLibs.".format(DisplayName.name(ctx.author)))
					continue

			# We got a relevant message
			val = talk.content
			# Let's remove the $ml prefix (with or without space)
			matched_prefix = next((x for x in allowed_ml if val.lower().startswith(x.lower())),None)
			if matched_prefix: # Strip the prefix
				val = val[len(matched_prefix):]
			# Strip any unnecessary whitespace
			val = val.strip()

			# Append and capitalize if needed based on context
			subs.append(string.capwords(val) if word[2].isupper() else val)
			
			# Check if we need to add to our reused_words
			if word.lower() in reused_words and not reused_words[word.lower()]:
				reused_words[word.lower()] = val

		# Let's replace
		for sub in subs:
			# Only replace the first occurence of each
			data = re.sub(self.regex, "**{}**".format(Nullify.escape_all(sub)), data, 1)

		self.playing_madlibs.pop(str(ctx.guild.id),None)
		
		# Message the output
		await ctx.send(data)
