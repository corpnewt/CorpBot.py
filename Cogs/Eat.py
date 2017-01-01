import asyncio
import discord
import random
from   discord.ext import commands
from   Cogs import DisplayName

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
			await self.bot.send_message(ctx.message.channel, msg)
			return
		
		# Check if we're eating a member
		memberCheck = DisplayName.memberForName(member, ctx.message.server)
		if memberCheck:
			memName = DisplayName.name(memberCheck)
			memberList = [ 'you uhninge your jaw and consume *{}* in one bite.'.format(memName),
							'you try to eat *{}*, but you just can\'t quite do it - you spit them out, the taste of failure hanging in your mouth...'.format(memName),
							'you take a quick bite out of *{}*.  They probably didn\'t even notice.'.format(memName),
							'you sink your teeth into *{}\'s* shoulder - they turn to face you, eyes wide as you try your best to scurry away and hide.'.format(memName),
							'your jaw crunches down on *{}* - a satisfying *crunch* emanates as you finish your newest meal.'.format(memName)]
			randnum = random.randint(0, len(memberList)-1)
			msg = '*{}*, {}'.format(authorName, memberList[randnum])				
			await self.bot.send_message(ctx.message.channel, msg)
			return

		# Assume we're eating something else
		itemList = [ 	'you take a big chunk out of *{}*. *Delicious.*'.format(member),
						'your teeth sink into *{}* - it tastes satisfying.'.format(member),
						'you attempt to bite into *{}*, but you\'re clumsier than you remember - and fail...'.format(member),]

		randnum = random.randint(0, len(itemList)-1)
		msg = '*{}*, {}'.format(authorName, itemList[randnum])				
		await self.bot.send_message(ctx.message.channel, msg)
		return				