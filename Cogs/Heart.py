import re
from discord.ext import commands

def setup(bot):
	# Add the bot
	bot.add_cog(Heart(bot))

class Heart(commands.Cog):

	# Init with the bot reference, and a reference to the settings var
	def __init__(self, bot):
		self.bot = bot
		# compile regex to look for i + hug or hug + me
		self.hug_re = re.compile(r"(?i).*\b(i\b.*\bhug\b.*|hug\b.*\bme)\b.*")
		self.mention_re = re.compile(".*<@!?{}>.*".format(self.bot.user.id))

	async def message(self, message):
		# Check the message - and append a heart if a ping exists, but no command
		context = await self.bot.get_context(message)
		if context.command:
			return {}
		react_list = []
		# Get our hug phrases
		if self.hug_re.match(message.content):
			# We need a hug, stat!
			react_list.append("🤗")
		if self.mention_re.match(message.content):
			# We got a mention!
			react_list.append("❤")
		# Return our reactions - if any
		if len(react_list):
			return {"Reaction":react_list}
