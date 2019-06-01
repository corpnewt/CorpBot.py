import asyncio
import discord
import random
from   discord.ext import commands
from   Cogs import DisplayName
from   Cogs import Nullify

def setup(bot):
	# Add the bot
	bot.add_cog(Actions(bot))

class Actions(commands.Cog):
	## class that handles storing and computing action messages
	class actionable:
		## these should be filled in the override class. any {} are replaced with target member's name
		nothinglist = [] # when you call without any arguments
		botList = [] # when the action is done at the bot
		selfList = [] # when the action is done at the user who called it
		memberList = [] # when the action is done toward another member
		itemList = [] # when the action is done on a string of text that is not a member

		def computeAction(self, ctx, target):
			'''return a message based on the context and argument of the command'''
			mesg = None

			if not target: # no arguments
				mesg = random.choice(self.nothingList)

			targetMember = DisplayName.memberForName(target, ctx.message.guild)

			if targetMember:
				if targetMember.id == self.bot.user.id: # actioning the bot
					mesg = random.choice(self.botList)
				elif targetmember.id == ctx.message.author.id: # actioning themselves
					mesg = random.choice(self.selfList)
				else: # actioning another user
					mesg = random.choice(self.memberList)
					if '{}' in mesg:
						mesg = mesg.format(DisplayName.name(memberCheck))
			else: # actioning an item
				mesg = random.choice(self.itemList)
				if '{}' in mesg:
					mesg = mesg.format(target)

			mesgFull = '*{}*, {}'.format(DisplayName.name(ctx.message.author), mesg)
			mesgFull = Nullify.clean(mesgFull)
			return mesgFull

	## static definitions of all the action messages
	class eating(actionable):
		nothingList = [ 'you sit quietly and eat *nothing*...',
						'you\'re *sure* there was something to eat, so you just chew on nothingness...',
						'there comes a time when you need to realize that you\'re just chewing nothing for the sake of chewing.  That time is now.']
		botList = [ 'you try to eat *me* - but unfortunately, I saw it coming - your jaw hangs open as I deftly sidestep.',
					'your mouth hangs open for a brief second before you realize that *I\'m* eating *you*.',
					'I\'m a bot.  You can\'t eat me.',
					'your jaw clamps down on... wait... on nothing, because I\'m *digital!*.',
					'what kind of bot would I be if I let you eat me?']
		selfList = ['you clamp down on your own forearm - not surprisingly, it hurts.',
					'you place a finger into your mouth, but *just can\'t* force yourself to bite down.',
					'you happily munch away, but can now only wave with your left hand.',
					'wait - you\'re not a sandwich!',
					'you might not be the smartest...']
		memberList = [  'you unhinge your jaw and consume *{}* in one bite.',
						'you try to eat *{}*, but you just can\'t quite do it - you spit them out, the taste of failure hanging in your mouth...',
						'you take a quick bite out of *{}*.  They probably didn\'t even notice.',
						'you sink your teeth into *{}\'s* shoulder - they turn to face you, eyes wide as you try your best to scurry away and hide.',
						'your jaw clamps down on *{}* - a satisfying *crunch* emanates as you finish your newest meal.']
		itemList = [ 	'you take a big chunk out of *{}*. *Delicious.*',
						'your teeth sink into *{}* - it tastes satisfying.',
						'you rip hungrily into *{}*, tearing it to bits!',
						'you just can\'t bring yourself to eat *{}* - so you just hold it for awhile...',
						'you attempt to bite into *{}*, but you\'re clumsier than you remember - and fail...']
	class drinking(actionable):
		nothingList = [ 'you stare at your glass full of *nothing*...',
						'that cup must\'ve had something in it, so you drink *nothing*...',
						'you should probably just go get a drink.',
						'that desk looks pretty empty',
						'are you sure you know what drinking is?',
						'you desperatly search for something to drink']
		botList = [ 'you try to drink *me*, but I dodge your straw.',
					'You search for me, only to realise that *I* am already drinking you!',
					'I\'m a bot.  You can\'t drink me.',
					'you stick a straw in... wait... in nothing, because I\'m *digital!*.',
					'what do you think I am to let you drink me?',
					'I don\'t think you would like the taste of me.',
					'you can\'t drink me, I\'m a machine!']
		selfList = ['you stab yourself with a straw - not surprisingly, it hurts.',
					'you fit yourself in to a cup, but you just can\'t do it.',
					'you happily drink away, but you are now very floppy.',
					'wait - you\'re not a drink!',
					'you might not be the smartest...',
					'you might have some issues.',
					'you try to drink yourself.',
					'why would you drink yourself?']
		memberList = [  'you grab your lucky straw and empty *{}* in one sip.',
						'you try to drink *{}*, but you just can\'t quite do it - you spit them out, the taste of failure hanging in your mouth...',
						'you drink a small sip of *{}*.  They probably didn\'t even notice.',
						'you stab your straw into *{}\'s* shoulder - You run away as they run after you.',
						'you happily drink away - *{}* starts to look like an empty Capri Sun package.',
						'you are thirsty - *{}* sacrifices themself involuntarily.',
						'somehow you end up emptying *{}*.']
		itemList = ['you take a big sip of *{}*. *Delicious.*',
					'your straw sinks into *{}* - it tastes satisfying.',
					'you thirstly guzzle *{}*, it\'s lovely!',
					'you just can\'t bring yourself to drink *{}* - so you just hold it for awhile...',
					'you attempt to drain *{}*, but you\'re clumsier than you remember - and fail...',
					'you drink *{}*.',
					'*{}* dries up from your drinking.',
					'*{}* starts resembling the Aral Sea.']
	# Init with the bot reference, and a reference to the settings var
	def __init__(self, bot):
		self.bot = bot

	@commands.command(pass_context=True)
	async def eat(self, ctx, *, member : str = None):
		"""Eat like a boss."""

		msg = eating.computeAction(ctx, member)
		await ctx.channel.send(msg)
		return




	@commands.command(pass_context=True)
	async def drink(self, ctx, *, member : str = None):
		"""Drink like a boss."""

		
		await ctx.channel.send(msg)
		return