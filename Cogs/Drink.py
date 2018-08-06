import asyncio
import discord
import random
from   discord.ext import commands
from   Cogs import DisplayName
from   Cogs import Nullify

def setup(bot):
	# Add the bot
	bot.add_cog(Drink(bot))

class Drink:

	# Init with the bot reference, and a reference to the settings var
	def __init__(self, bot):
		self.bot = bot

	@commands.command(pass_context=True)
	async def drink(self, ctx, *, member : str = None):
		"""Drink like a boss."""

		authorName = DisplayName.name(ctx.message.author)

		# Check if we're drinking nothing
		if member == None:
			nothingList = [ 'you stare at your glass full of *nothing*...',
							'that cup must\'ve had something in it, so you drink *nothing*...',
							'you should probably just go get a drink.']

			randnum = random.randint(0, len(nothingList)-1)
			msg = '*{}*, {}'.format(authorName, nothingList[randnum])
			msg = Nullify.clean(msg)
			await ctx.channel.send(msg)
			return
		
		# Check if we're drinking a member
		memberCheck = DisplayName.memberForName(member, ctx.message.guild)
		if memberCheck:
			# We're drinking a member - let's do a bot-check
			if memberCheck.id == self.bot.user.id:
				# It's me!
				memberList = [  'you try to drink *me*, but I dodge your straw.',
								'You search for me, only to realise that *I* am already drinking you!',
								'I\'m a bot.  You can\'t drink me.',
								'you stick a straw in... wait... in nothing, because I\'m *digital!*.',
								'what do you think I am to let you drink me?']
			elif memberCheck.id == ctx.message.author.id:
				# We're drinking... ourselves?
				memberList = [  'you stab yourself with a straw - not surprisingly, it hurts.',
								'you fit yourself in to a cup, but you just can\'t do it.',
								'you happily drink away, but you are now very floppy.',
								'wait - you\'re not a drink!',
								'you might not be the smartest...']
			else:
				memName = DisplayName.name(memberCheck)
				memberList = [ 'you grab your lucky straw and empty *{}* in one sip.'.format(memName),
								'you try to drink *{}*, but you just can\'t quite do it - you spit them out, the taste of failure hanging in your mouth...'.format(memName),
								'you drink a small sip of *{}*.  They probably didn\'t even notice.'.format(memName),
								'you stab your straw into *{}\'s* shoulder - You run away as they run after you.'.format(memName),
								'you happily drink away - *{}* starts to look like an empty Capri Sun package.'.format(memName)]
			randnum = random.randint(0, len(memberList)-1)
			msg = '*{}*, {}'.format(authorName, memberList[randnum])
			msg = Nullify.clean(msg)				
			await ctx.channel.send(msg)
			return

		# Assume we're drinking something else
		itemList = [ 	'you take a big sip of *{}*. *Delicious.*'.format(member),
						'your straw sinks into *{}* - it tastes satisfying.'.format(member),
						'you thirstly guzzle *{}*, it\'s lovely!'.format(member),
						'you just can\'t bring yourself to drimk *{}* - so you just hold it for awhile...'.format(member),
						'you attempt to drain *{}*, but you\'re clumsier than you remember - and fail...'.format(member),]

		randnum = random.randint(0, len(itemList)-1)
		msg = '*{}*, {}'.format(authorName, itemList[randnum])
		msg = Nullify.clean(msg)			
		await ctx.channel.send(msg)
		return				