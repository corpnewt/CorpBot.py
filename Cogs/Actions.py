import asyncio
import discord
import random
import datetime
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
		nothingList = [] # when you call without any arguments
		botList = [] # when the action is done at the bot
		selfList = [] # when the action is done at the user who called it
		memberList = [] # when the action is done toward another member
		itemList = [] # when the action is done on a string of text that is not a member

		def computeAction(self, bot, ctx, target):
			'''return a message based on the context and argument of the command'''
			mesg = ""

			if not target: # no arguments
				mesg = random.choice(self.nothingList)
			else:
				targetMember = DisplayName.memberForName(target, ctx.message.guild)

				if targetMember:
					if self.botList and targetMember.id == bot.user.id: # actioning the bot
						mesg = random.choice(self.botList) # if botList is empty we fail over to the member list
					elif self.selfList and targetMember.id == ctx.message.author.id: # actioning themselves
						mesg = random.choice(self.selfList)
					else: # actioning another user
						mesg = random.choice(self.memberList).replace("{}",DisplayName.name(targetMember))
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

	class booping(actionable):
		nothingList = [ 'you stretch out your hand in the air, but there\'s nothing there...',
						'you try and find someone to boop, but there\'s no one there.',
						'you look around the channel for someone to boop.',
						'you eye all the heads in the room, just waiting to be booped.',
						'are you sure you have someone to boop?',
						'I get it. You want to boop *someone*.']
		selfList = ['you boop yourself on the nose with your finger.',
					'you try to boop your head, but your hand gets lost along the way.',
					'you happily boop yourself, but you are now very giddy.',
					'wait - are you sure you want to boop yourself?',
					'you might not be the smartest...',
					'you might have some issues.',
					'you try to boop yourself.',
					'why would you boop yourself?']
		memberList = [  'you outstretch your lucky finger and boop *{}* in one go.',
						'you try to boop *{}*, but you just can\'t quite do it - you miss their head, the taste of failure hanging stuck to your hand...',
						'you sneak a boop onto *{}*.  They probably didn\'t even notice.',
						'you poke your hand onto *{}\'s* hand - You run away as they run after you.',
						'you happily drum your fingers away - *{}* starts to look annoyed.',
						'you\'re feeling boopy - *{}* sacrifices themself involuntarily.',
						'somehow you end up booping *{}*.',
						'you climb *{}*\'s head and  use it as a bouncy castle... they feel amused.']
		itemList = ['you put your hand onto *{}*\'s head. *Bliss.*',
					'your hand touches *{}*\'s snoot - it feels satisfying.',
					'you happily boop *{}*, it\'s lovely!',
					'you just can\'t bring yourself to boop *{}* - so you just let your hand linger...',
					'you attempt to boop *{}*, but you\'re clumsier than you remember - and fail...',
					'you boop *{}*.',
					'*{}* feels annoyed from your booping.',
					'*{}* starts resembling a happy pupper.']

	class spooky(actionable):
		nothingList = [ 'you spook no one but yourself',
						'you spook nothing, sp00py...',
						'sadly, no one got spooked',
						'it is sp00... you can\t spook air']
		botList = [ 'you scared the living pumpkin out of me!',
					'you spooked me so hard, I got the Heebie-jeebies...', # https://www.myenglishteacher.eu/blog/idioms-for-being-afraid/
					'you sp00p me? But I\'m a bot... I can\'t be spooked!',
					'sorry, but I cannot let you spook me; My digital emotions will get all messed up!'
					'aaaaaaaaaah! Don\t you scare me like that again!']
		selfList = ['go watch a scary movie to be absolutely sp00ped!',
					'boo! Did you scare you?',
					'you look yourself in the mirror and get a little scared...',
					'get spooked by... yourself?',
					'sp00py, but why spook yourself?']
		memberList = [  'you sp00p *{}* so hard that they start screaming!',
						'you tried to sneak up on *{}*, but they heard you sneakin\' and fail...',
						'it is sp00py time! Hey *{}*, boo!',
						'congrats, *{}* dun sp00ked.',
						'get spook3d *{}*!']
		itemList = ['you spook *{}* with no reaction, leaving you looking weird...',
					'*{}* got sp00p3d so hard, it ran away!',
					'you trick or treat *{}* without any reaction...',
					'you do your best to sp00p *{}*, but fail...',
					'sp00py time! *{}* gets sp00ped harder than you thought and starts crying!']

	class highfives(actionable):
		nothingList = [ 'you stand alone for an eternity, hand raised up - desperate for any sort of recognition...',
						'with a wild swing you throw your hand forward - the momentum carries you to the ground and you just lay there - high fiveless...',
						'the only sound you hear as a soft *whoosh* as your hand connects with nothing...']
		botList = [ 'the sky erupts with 1\'s and 0\'s as our hands meet in an epic high five of glory!',
					'you beam up to the cloud and receive a quick high five from me before downloading back to Earth.',
					'I unleash a fork-bomb of high five processes!',
					'01001000011010010110011101101000001000000100011001101001011101100110010100100001']
		selfList = ['ahh - high fiving yourself, classy...',
					'that\'s uh... that\'s just clapping...',
					'you run in a large circle - *totally* high fiving all your friends...',
					'now you\'re at both ends of a high five!']
		memberList = [  'you and *{}* jump up for an epic high five - freeze-framing as the credits roll and some wicked 80s synth plays out.',
						'you and *{}* elevate to a higher plane of existence in wake of that tremendous high five!',
						'a 2 hour, 3 episode anime-esque fight scene unfolds as you and *{}* engage in a world-ending high five!',
						'it *was* tomorrow - before you and *{}* high fived with enough force to spin the Earth in reverse!',
						'like two righteous torpedoes - you and *{}* connect palms, subsequently deafening everyone in a 300-mile radius!']
		itemList = ['neat... you just high fived *{}*.',
					'your hand flops through the air - hitting *{}* with a soft thud.',
					'you reach out a hand, gently pressing your palm to *{}*.  A soft *"high five"* escapes your lips as a tear runs down your cheek...',
					'like an open-handed piston of ferocity - you drive your palm into *{}*.']

	class petting(actionable): # meow
		nothingList = [ 'you absentmindedly wave your hand in the air.',
						'you could have sworn there was a cat there!',
						'you remember that there are no cats here.',
						'you try to pet the cat, but miss because the cat is gone.']
		botList = [ 'I may be electronic but I still appreciate pets.',
					'*purrrrrrrrrrrrrrr*.',
					'you electrocute yourself trying to pet a computer.']
		selfList = ['you give yourself a nice pat on the head.',
					'too bad there\'s no one else to pet you.',
					'in lieu of anything else to pet, you pet yourself.',
					'your hair is warm and soft.']
		memberList = [  'you give *{}* a pat on the head.',
						'you rub your hand through *{}\'s* hair.',
						'*{}* smiles from your petting.',
						'you try to pet *{}*, but miss because they hid under the bed.',
						'*{}* purrs from your petting.',
						'you pet *{}* but they bite your hand',
						'you try to pet *{}* but they hiss and run away.']
		itemList = ['you rub *{}* but it doesn\'t feel like a cat.',
					'you don\'t hear any purring from *{}*.',
					'you hurt your hand trying to pet *{}*.']

	# Init with the bot reference, and a reference to the settings var
	def __init__(self, bot):
		self.bot = bot
		global Utils, DisplayName
		Utils = self.bot.get_cog("Utils")
		DisplayName = self.bot.get_cog("DisplayName")

	@commands.command(pass_context=True)
	async def eat(self, ctx, *, member : str = None):
		"""Eat like a boss."""

		msg = self.eating.computeAction(self.eating, self.bot, ctx, member) #python is silly and makes me do this for uninitialized classes
		await ctx.channel.send(msg)
		return

	@commands.command(pass_context=True)
	async def drink(self, ctx, *, member : str = None):
		"""Drink like a boss."""

		msg = self.drinking.computeAction(self.drinking, self.bot, ctx, member)
		await ctx.channel.send(msg)
		return

	@commands.command(pass_context=True)
	async def boop(self, ctx, *, member : str = None):
		"""Boop da snoot."""

		msg = self.booping.computeAction(self.booping, self.bot, ctx, member)
		await ctx.channel.send(msg)
		return

	@commands.command(pass_context=True)
	async def spook(self, ctx, *, member : str = None):
		"""sp00ktober by camiel."""

		if datetime.date.today().month == 10:
			# make it extra sp00py because it is spooktober
			await ctx.message.add_reaction("🎃")
		msg = self.spooky.computeAction(self.spooky, self.bot, ctx, member)
		await ctx.channel.send(msg)
		return

	@commands.command(pass_context=True)
	async def highfive(self, ctx, *, member : str = None):
		"""High five like a boss."""

		msg = self.highfives.computeAction(self.highfives, self.bot, ctx, member)
		await ctx.channel.send(msg)
		return

	@commands.command(pass_context=True)
	async def pet(self, ctx, *, member : str = None):
		"""pet kitties."""

		msg = self.petting.computeAction(self.petting, self.bot, ctx, member)
		await ctx.channel.send(msg)
		return
