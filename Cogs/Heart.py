import asyncio
import discord
import re
from   discord.ext import commands
from   Cogs import DisplayName

def setup(bot):
	# Add the bot
	bot.add_cog(Heart(bot))

class Heart:

	# Init with the bot reference, and a reference to the settings var
	def __init__(self, bot):
		self.bot = bot
		# compile regex to look for i + hug or hug + me
		self.regex = re.compile(r"((.*?)\bi\b(.*?)\bhug\b(.*?))|((.*?)\bhug\b(.*?)\bme\b(.*?))")

	async def message(self, message):
		# Check the message - and append a heart if a ping exists, but no command
		context = await self.bot.get_context(message)
		if context.command:
			return {}
		# Check for a mention
		bot_mentions = ["<@!{}>".format(self.bot.user.id), "<@{}>".format(self.bot.user.id)]
		react_list = []
		# Get our hug phrases
		matches = re.finditer(self.regex, message.content.lower())
		if len(list(matches)):
			# We need a hug, stat!
			react_list.append("🤗")
		for x in bot_mentions:
			if x in message.content:
				# We got a mention!
				react_list.append("❤")
		# Return our reactions - if any
		if len(react_list):
			return { "Reaction" : react_list }
