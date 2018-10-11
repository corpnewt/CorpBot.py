import asyncio
import discord
import random
from   discord.ext import commands
from   Cogs import DisplayName
from   Cogs import Nullify

def setup(bot):
	# Add the bot
	bot.add_cog(Boop(bot))

class Boop:

	# Init with the bot reference, and a reference to the settings var
	def __init__(self, bot):
		self.bot = bot

	@commands.command(pass_context=True)
	async def boop(self, ctx, *, member : str = None):
		"""Drink like a boss."""

		authorName = DisplayName.name(ctx.message.author)

		# Check if we're drinking nothing
		if member == None:
			nothingList = [ 'you stretch out your hand in the air, but there\'s nothing there...',
							'you try and find someone to boop, but there\'s no one there.',
							'you look around the channel for someone to boop.',
							'you eye all the heads in the room, just waiting to be booped.',
							'are you sure you have someone to boop?',
							'I get it. You want to boop *someone*.']

			randnum = random.randint(0, len(nothingList)-1)
			msg = '*{}*, {}'.format(authorName, nothingList[randnum])
			msg = Nullify.clean(msg)
			await ctx.channel.send(msg)
			return
		
		# Check if we're drinking a member
		memberCheck = DisplayName.memberForName(member, ctx.message.guild)
		if memberCheck:
			if memberCheck.id == ctx.message.author.id:
				# We're drinking... ourselves?
				memberList = [  'you boop yourself on the nose with your finger.',
								'you try to boop your head, but your hand gets lost along the way.',
								'you happily boop yourself, but you are now very giddy.',
								'wait - are you sure you want to boop yourself?',
								'you might not be the smartest...',
								'you might have some issues.',
								'you try to boop yourself.',
								'why would you boop yourself?']
			else:
				memName = DisplayName.name(memberCheck)
				memberList = [ 'you outstretch your lucky finger and boop *{}* in one go.'.format(memName),
								'you try to boop *{}*, but you just can\'t quite do it - you miss their head, the taste of failure hanging stuck to your hand...'.format(memName),
								'you sneak a boop onto *{}*.  They probably didn\'t even notice.'.format(memName),
								'you poke your hand onto *{}\'s* hand - You run away as they run after you.'.format(memName),
								'you happily drum your fingers away - *{}* starts to look annoyed.'.format(memName),
								'you\'re feeling boopy - *{}* sacrifices themself involuntarily.'.format(memName),
								'somehow you end up booping *{}*.'.format(memName),
								'you climb *{}*\'s head and  use it as a bouncy castle... they feel amused.'.format(memName)]
			randnum = random.randint(0, len(memberList)-1)
			msg = '*{}*, {}'.format(authorName, memberList[randnum])
			msg = Nullify.clean(msg)				
			await ctx.channel.send(msg)
			return

		# Assume we're drinking something else
		itemList = [ 	'you put your hand onto *{}*\'s head. *Bliss.*'.format(member),
						'your hand touches *{}*\'s snoot - it feels satisfying.'.format(member),
						'you happily boop *{}*, it\'s lovely!'.format(member),
						'you just can\'t bring yourself to boop *{}* - so you just let your hand linger...'.format(member),
						'you attempt to boop *{}*, but you\'re clumsier than you remember - and fail...'.format(member),
						'you boop *{}*.'.format(member),
						'*{}* feels annoyed from your booping.'.format(member),
						'*{}* starts resembling a happy pupper.'.format(member)]

		randnum = random.randint(0, len(itemList)-1)
		msg = '*{}*, {}'.format(authorName, itemList[randnum])
		msg = Nullify.clean(msg)			
		await ctx.channel.send(msg)
		return				