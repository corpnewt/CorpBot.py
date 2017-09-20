import asyncio
import discord
import random
from   discord.ext import commands
from   Cogs import DisplayName
from   Cogs import Nullify

def setup(bot):
	# Add the bot
	bot.add_cog(Eat(bot))

class Eat:

	# Init with the bot reference, and a reference to the settings var
	def __init__(self, bot):
		self.bot = bot

	@commands.command(pass_context=True)
	async def eat(self, ctx, *, member : str = None):
		"""Eat like a boss."""

		authorName = DisplayName.name(ctx.message.author)

		# Check if we're eating nothing
		if member == None:
			nothingList = [ 'you sit quietly and eat *nothing*...',
							'you\'re *sure* there was something to eat, so you just chew on nothingness...',
							'there comes a time when you need to realize that you\'re just chewing nothing for the sake of chewing.  That time is now.']

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
				memberList = [  'you try to eat *me* - but unfortunately, I saw it coming - your jaw hangs open as I deftly sidestep.',
								'your mouth hangs open for a brief second before you realize that *I\'m* eating *you*.',
								'I\'m a bot.  You can\'t eat me.',
								'your jaw clamps down on... wait... on nothing, because I\'m *digital!*.',
								'what kind of bot would I be if I let you eat me?']
			elif memberCheck.id == ctx.message.author.id:
				# We're eating... ourselves?
				memberList = [  'you clamp down on your own forearm - not surprisingly, it hurts.',
								'you place a finger into your mouth, but *just can\'t* force yourself to bite down.',
								'you happily munch away, but can now only wave with your left hand.',
								'wait - you\'re not a sandwich!',
								'you might not be the smartest...']
			else:
				memName = DisplayName.name(memberCheck)
				memberList = [ 'you unhinge your jaw and consume *{}* in one bite.'.format(memName),
								'you try to eat *{}*, but you just can\'t quite do it - you spit them out, the taste of failure hanging in your mouth...'.format(memName),
								'you take a quick bite out of *{}*.  They probably didn\'t even notice.'.format(memName),
								'you sink your teeth into *{}\'s* shoulder - they turn to face you, eyes wide as you try your best to scurry away and hide.'.format(memName),
								'your jaw clamps down on *{}* - a satisfying *crunch* emanates as you finish your newest meal.'.format(memName)]
			randnum = random.randint(0, len(memberList)-1)
			msg = '*{}*, {}'.format(authorName, memberList[randnum])
			msg = Nullify.clean(msg)				
			await ctx.channel.send(msg)
			return

		# Assume we're eating something else
		itemList = [ 	'you take a big chunk out of *{}*. *Delicious.*'.format(member),
						'your teeth sink into *{}* - it tastes satisfying.'.format(member),
						'you rip hungrily into *{}*, tearing it to bits!'.format(member),
						'you just can\'t bring yourself to eat *{}* - so you just hold it for awhile...'.format(member),
						'you attempt to bite into *{}*, but you\'re clumsier than you remember - and fail...'.format(member),]

		randnum = random.randint(0, len(itemList)-1)
		msg = '*{}*, {}'.format(authorName, itemList[randnum])
		msg = Nullify.clean(msg)			
		await ctx.channel.send(msg)
		return				