import asyncio
import discord
from chatterbot import ChatBot
from discord.ext import commands
from Cogs import Nullify

class ChatterBot:

	# Init with the bot reference, and a reference to the settings var
	def __init__(self, bot, settings):
		self.bot = bot
		self.settings = settings
		self.chatBot = ChatBot('Pooter', trainer='chatterbot.trainers.ChatterBotCorpusTrainer')
		self.chatBot.train('chatterbot.corpus.english')

	@commands.command(pass_context=True)
	async def chat(self, ctx, *, message = None):
		"""Chats with the bot."""
		# Check if we're suppressing @here and @everyone mentions
		if self.settings.getServerStat(ctx.message.server, "SuppressMentions").lower() == "yes":
			suppress = True
		else:
			suppress = False
		if message == None:
			return
		msg = str(self.chatBot.get_response(str(message)))
		# Check for suppress
		if suppress:
			msg = Nullify.clean(msg)
		await self.bot.send_message(ctx.message.channel, msg)