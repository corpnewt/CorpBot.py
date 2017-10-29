import asyncio
import discord
import random
from   discord.ext import commands
from   Cogs import DisplayName
from   Cogs import Nullify

def setup(bot):
	# Add the bot
	bot.add_cog(HighFive(bot))

class HighFive:

	# Init with the bot reference
	def __init__(self, bot):
		self.bot = bot

	@commands.command(pass_context=True)
	async def highfive(self, ctx, *, member : str = None):
		"""It's like clapping with 2 people!"""

		authorName = DisplayName.name(ctx.message.author)

		# Check if we're eating nothing
		if member == None:
			nothingList = [ 'you stand alone for an eternity, hand raised up - desperate for any sort of recognition...',
							'with a wild swing you throw your hand forward - the momentum carries you to the ground and you just lay there - high fiveless...',
							'the only sound you hear as a soft *whoosh* as your hand connects with nothing...']

			randnum = random.randint(0, len(nothingList)-1)
			msg = '*{}*, {}'.format(authorName, nothingList[randnum])
			msg = Nullify.clean(msg)
			await ctx.channel.send(msg)
			return
		
		# Check if we're eating a member
		memberCheck = DisplayName.memberForName(member, ctx.message.guild)
		if memberCheck:
			# We're eating a member - let's do a bot-check
			if memberCheck.id == self.bot.user.id:
				# It's me!
				memberList = [  'the sky erupts with 1\'s and 0\'s as our hands meet in an epic high five of glory!',
								'you beam up to the cloud and receive a quick high five from me before downloading back to Earth.',
								'I unleash a fork-bomb of high five processes!',
								'01001000011010010110011101101000001000000100011001101001011101100110010100100001']
			elif memberCheck.id == ctx.message.author.id:
				# We're eating... ourselves?
				memberList = [  'ahh - high fiving yourself, classy...',
								'that\'s uh... that\'s just clapping...',
								'you run in a large circle - *totally* high fiving all your friends...',
								'now you\'re at both ends of a high five!']
			else:
				memName = DisplayName.name(memberCheck)
				memberList = [ 'you and *{}* jump up for an epic high five - freeze-framing as the credits roll and some wicked 80s synth plays out.'.format(memName),
								'you and *{}* elevate to a higher plane of existence in wake of that tremendous high five!'.format(memName),
								'a 2 hour, 3 episode anime-esque fight scene unfolds as you and *{}* engage in a world-ending high five!'.format(memName),
								'it *was* tomorrow - before you and *{}* high fived with enough force to spin the Earth in reverse!'.format(memName),
								'like two righteous torpedoes - you and *{}* connect palms, subsequently deafening everyone in a 300-mile radius!'.format(memName)]
			randnum = random.randint(0, len(memberList)-1)
			msg = '*{}*, {}'.format(authorName, memberList[randnum])
			msg = Nullify.clean(msg)				
			await ctx.channel.send(msg)
			return

		# Assume we're eating something else
		itemList = [ 	'neat... you just high fived *{}*.'.format(member),
						'your hand flops through the air - hitting *{}* with a soft thud.'.format(member),
						'you reach out a hand, gently pressing your palm to *{}*.  A soft *"high five"* escapes your lips as a tear runs down your cheek...'.format(member),
						'like an open-handed piston of ferocity - you drive your palm into *{}*.'.format(member)]

		randnum = random.randint(0, len(itemList)-1)
		msg = '*{}*, {}'.format(authorName, itemList[randnum])
		msg = Nullify.clean(msg)			
		await ctx.channel.send(msg)
		return
