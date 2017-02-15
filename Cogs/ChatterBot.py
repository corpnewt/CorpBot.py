import asyncio
import discord
from chatterbot import ChatBot
from discord.ext import commands

class ChatterBot:

	# Init with the bot reference, and a reference to the settings var
	def __init__(self, bot):
		self.bot = bot
		self.chatBot = ChatBot('Pooter', trainer='chatterbot.trainers.ChatterBotCorpusTrainer')
		self.chatBot.train('chatterbot.corpus.english')

	@commands.command(pass_context=True)
	async def chat(self, ctx, *, message = None):
		"""Chats with the bot."""
		if message == None:
			msg = 'You uh... you say nothing.'
		else:
			msg = self.chatBot.get_response(str(message))
		await self.bot.send_message(ctx.message.channel, msg)