import asyncio
import discord
import random
from   discord.ext import commands
from   Cogs import Settings

def setup(bot):
	# Add the bot and deps
	settings = bot.get_cog("Settings")
	bot.add_cog(DrBeer(bot, settings))

# This is the Uptime module. It keeps track of how long the bot's been up

class DrBeer:

	# Init with the bot reference, and a reference to the settings var
	def __init__(self, bot, settings):
		self.bot = bot
		self.settings = settings

	@commands.command(pass_context=True)
	async def drbeer(self, ctx):
		"""Put yourself in your place."""

		isAdmin = ctx.message.author.permissions_in(ctx.message.channel).administrator
		if not isAdmin:
			checkAdmin = self.settings.getServerStat(ctx.message.guild, "AdminArray")
			for role in ctx.message.author.roles:
				for aRole in checkAdmin:
					# Get the role that corresponds to the id
					if str(aRole['ID']) == str(role.id):
						isAdmin = True
		# Only allow admins
		if not isAdmin:
			return

		author  = ctx.message.author
		server  = ctx.message.guild
		channel = ctx.message.channel

		beerList = ["Hey, yall. Quit ya horsin' around now. Can't you see I'm busy tryin'a shoot'n all them summersquash?",
					"Now I don't know how to use all them 5-dollah words y'all sprayin' around, but sure seems to me like y'all need to mind your peas and queues.",
					"As long as I can keep practicin' and protectin' all my favorite amendments, like the second and thirty-first, I am all dandy.",
					"Woah there, buckaroo! That's a mighty harsh language from someone communicating through a tube in the ocean over the internets.",
					"Now, I don't mind y'all people, but you keep botherin' me when I'm tryin'a enjoy my cold Bud in this beautiful, patriotic sunset. Haven't yall folks got better things to do then keep arguing and snicker in' around when y'all should be worried about the government and the N, S & A listenin'?",
					"Well, my daddy always said a man is only as good as his words and the thrust and torque of his good ole John Deere."]
		randnum = random.randint(0, len(beerList)-1)
		msg = '{}'.format(beerList[randnum])
		# Remove original message
		await ctx.message.delete()
		# Say new message
		await ctx.channel.send(msg)