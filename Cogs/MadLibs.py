import discord, re, os, random, string
from   discord.ext import commands
from   Cogs import Settings, DisplayName, Nullify

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
	async def ml(self, ctx, word = None):
		"""Used to choose your words when in the middle of a madlibs."""
		pass

	@commands.command()
	async def madlibs(self, ctx):
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
			await ctx.send("I'm already playing MadLibs - use `{}{} [your word]` to submit answers.".format(ctx.prefix,self.prefix))
		
		self.playing_madlibs[str(ctx.guild.id)] = True

		# Get a random madlib from those available
		randLib = random.choice(choices)

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
				ctx.prefix,
				self.prefix
			))

			# Setup the check
			def check(msg):	
				return msg.content.startswith("{}{}".format(ctx.prefix, self.prefix)) and msg.channel == ctx.channel

			# Wait for a response
			try:
				talk = await self.bot.wait_for('message', check=check, timeout=60)
			except Exception:
				talk = None

			if not talk:
				# We timed out - leave the loop
				self.playing_madlibs.pop(str(ctx.guild.id),None)
				return await ctx.send("*{}*, I'm done waiting... we'll play another time.".format(DisplayName.name(ctx.author)))

			# Check if the message is to leave
			if talk.content.lower().startswith('{}{}'.format(ctx.prefix, self.leavePrefix.lower())):
				if talk.author is ctx.author:
					self.playing_madlibs.pop(str(ctx.guild.id),None)
					return await ctx.send("Alright, *{}*.  We'll play another time.".format(DisplayName.name(ctx.author)))
				else:
					# Not the originator
					await ctx.send("Only the originator (*{}*) can leave the MadLibs.".format(DisplayName.name(ctx.author)))
					continue

			# We got a relevant message
			val = talk.content
			# Let's remove the $ml prefix (with or without space)
			if val.startswith('{}{}'.format(ctx.prefix.lower(), self.prefix.lower())):
				val = val[len(ctx.prefix)+len(self.prefix):]
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
