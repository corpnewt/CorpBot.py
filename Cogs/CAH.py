import asyncio
import discord
import re
import os
import random
import string
import json
import time
import html
import codecs
from   random import shuffle
from   discord.ext import commands
from   Cogs import Settings
from   Cogs import DisplayName
from   Cogs import ReadableTime
from   Cogs import Nullify

def setup(bot):
    # Add the bot
    bot.add_cog(CAH(bot))

class CAH:

    # Init with the bot reference, and a reference to the deck file
    def __init__(self, bot, prefix = "$", file = None):
        self.prefix = prefix
        self.bot = bot
        self.games = []
        self.maxBots = 5 # Max number of bots that can be added to a game - don't count toward max players
        self.maxPlayers = 10 # Max players for ranjom joins
        self.maxDeadTime = 3600 # Allow an hour of dead time before killing a game
        self.checkTime = 300 # 5 minutes between dead time checks
        self.winAfter = 10 # 10 wins for the game
        self.botWaitMin = 5 # Minimum number of seconds before the bot makes a decision (default 5)
        self.botWaitMax = 30 # Max number of seconds before a bot makes a decision (default 30)
        self.userTimeout = 300 # 5 minutes to timeout
        self.utCheck = 30 # Check timeout every 30 seconds
        self.utWarn = 60 # Warn the user if they have 60 seconds or less before being kicked
        self.charset = "1234567890"
        self.botName = 'Rando Cardrissian'
        self.minMembers = 3
        self.loopsleep = 0.05
        self.loop_list = []
        if file == None:
            file = "deck.json"
        # Let's load our deck file
        # Can be found at http://www.crhallberg.com/cah/json
        if os.path.exists(file):
            f = open(file,'r')
            filedata = f.read()
            f.close()

            self.deck = json.loads(filedata)
        else:
            # File doesn't exist - create a placeholder
            self.deck = {}

    # Proof of concept stuff for reloading cog/extension
    def _is_submodule(self, parent, child):
        return parent == child or child.startswith(parent + ".")

    @asyncio.coroutine
    async def on_unloaded_extension(self, ext):
        # Called to shut things down
        if not self._is_submodule(ext.__name__, self.__module__):
            return
        for task in self.loop_list:
            task.cancel()

    @asyncio.coroutine
    async def on_loaded_extension(self, ext):
        # See if we were loaded
        if not self._is_submodule(ext.__name__, self.__module__):
            return
        self.loop_list.append(self.bot.loop.create_task(self.checkDead()))
        self.loop_list.append(self.bot.loop.create_task(self.checkUserTimeout()))

    def cleanJson(self, json):
        json = html.unescape(json)
        # Clean out html formatting
        json = json.replace('_','[blank]')
        json = json.replace('<br>','\n')
        json = json.replace('<br/>','\n')
        json = json.replace('<i>', '*')
        json = json.replace('</i>', '*')
        return json


    async def checkUserTimeout(self):
        await self.bot.wait_until_ready()
        while not self.bot.is_closed():
            # Wait first - then check
            await asyncio.sleep(self.utCheck)
            for game in self.games:
                if not game['Timeout']:
                    continue
                if len(game['Members']) >= self.minMembers:
                    # Game is started
                    for member in game['Members']:
                        if member['IsBot']:
                            continue
                        if game['Judging']:
                            if not member == game['Members'][game['Judge']]:
                                # Not the judge - don't hold against the user
                                member['Time'] = int(time.time())
                                continue
                        else:
                            # Not judging
                            if member == game['Members'][game['Judge']]:
                                # The judge - don't hold that against them
                                member['Time'] = int(time.time())
                                continue
                        currentTime = int(time.time())
                        userTime = member['Time']
                        downTime = currentTime - userTime
                        # Check if downTime results in a kick
                        if downTime >= self.userTimeout:
                            # You gettin kicked, son.
                            await self.removeMember(member['User'])
                            self.checkGame(game)
                            continue
                        # Check if downTime is in warning time
                        if downTime >= (self.userTimeout - self.utWarn):
                            # Check if we're at warning phase
                            if self.userTimeout - downTime >= (self.utWarn - self.utCheck):
                                kickTime = self.userTimeout - downTime
                                if kickTime % self.utCheck:
                                    # Kick time isn't exact time - round out to the next loop
                                    kickTime = kickTime-(kickTime % self.utCheck)+self.utCheck
                                # Warning time!
                                timeString = ReadableTime.getReadableTimeBetween(0, kickTime)
                                msg = '**WARNING** - You will be kicked from the game if you do not make a move in *{}!*'.format(timeString)
                                await member['User'].send(msg)
                else:
                    for member in game['Members']:
                        # Reset timer
                        member['Time'] = int(time.time())


    async def checkDead(self):
        await self.bot.wait_until_ready()
        while not self.bot.is_closed():
            # Wait first - then check
            await asyncio.sleep(self.checkTime)
            for game in self.games:
                gameTime = game['Time']
                currentTime = int(time.time())
                timeRemain  = currentTime - gameTime
                if timeRemain > self.maxDeadTime:
                    # Game is dead - quit it and alert members
                    for member in game['Members']:
                        if member['IsBot']:
                            # Clear pending tasks and set to None
                            if not member['Task'] == None:
                                task = member['Task']
                                if not task.done():
                                    task.cancel()
                                member['Task'] = None
                            continue
                        msg = "Game id: *{}* has been closed due to inactivity.".format(game['ID'])
                        await member['User'].send(msg)
                
                    # Set running to false
                    game['Running'] = False
                    self.games.remove(game)

    async def checkPM(self, message):
        # Checks if we're talking in PM, and if not - outputs an error
        if type(message.channel) is discord.DMChannel:
            # PM
            return True
        else:
            # Not in PM
            await message.channel.send('Cards Against Humanity commands must be run in PM.')
            return False


    def randomID(self, length = 8):
        # Create a random id that doesn't already exist
        while True:
            # Repeat until found
            newID = ''.join(random.choice(self.charset) for i in range(length))
            exists = False
            for game in self.games:
                if game['ID'] == newID:
                    exists = True
                    break
            if not exists:
                break
        return newID

    def randomBotID(self, game, length = 4):
        # Returns a random id for a bot that doesn't already exist
        while True:
            # Repeat until found
            newID = ''.join(random.choice(self.charset) for i in range(length))
            exists = False
            for member in game['Members']:
                if str(member['ID']) == str(newID):
                    exists = True
                    break
            if not exists:
                break
        return newID

    def userGame(self, user):
        # Returns the game the user is currently in
        if not type(user) is str:
            if type(user) is int:
                user = str(user)
            else:
                # Assume it's a discord.Member/User
                user = str(user.id)

        for game in self.games:
            for member in game['Members']:
                if str(member['ID']) == str(user):
                    # Found our user
                    return game
        return None

    def gameForID(self, id):
        # Returns the game with the passed id
        for game in self.games:
            if game['ID'] == id:
                return game
        return None

    async def removeMember(self, user, game = None):
        if not type(user) is str:
            if type(user) is int:
                user = str(user)
            else:
                # Assume it's a discord.Member/User
                user = str(user.id)
        outcome  = False
        removed  = None
        if not game:
            game = self.userGame(user)
        if game:
            for member in game['Members']:
                if str(member['ID']) == str(user):
                    removed = member
                    outcome = True
                    judgeChanged = False
                    # Reset judging flag to retrigger actions
                    game['Judging'] = False
                    # Get current Judge - only if game has started
                    if len(game['Members']) >= self.minMembers:
                        judge = game['Members'][game['Judge']]
                        game['Members'].remove(member)
                        # Check if we're removing the current judge                    
                        if judge == member:
                            # Judge will change
                            judgeChanged = True
                            # Find out if our member was the last in line
                            if game['Judge'] >= len(game['Members']):
                                game['Judge'] = 0
                            # Reset judge var
                            judge = game['Members'][game['Judge']]
                        else:
                            # Judge didn't change - so let's reset judge index
                            index = game['Members'].index(judge)
                            game['Judge'] = index
                    else:
                        judge = None
                        # Just remove the member
                        game['Members'].remove(member)
                        
                    if member['Creator']:
                        # We're losing the game creator - pick a new one
                        for newCreator in game['Members']:
                            if not newCreator['IsBot']:
                                newCreator['Creator'] = True
                                await newCreator['User'].send('The creator of this game left.  **YOU** are now the creator.')
                                break
                    
                    # Remove submissions
                    for sub in game['Submitted']:
                        # Remove deleted member and new judge's submissions
                        if sub['By'] == member or sub['By'] == judge:
                            # Found it!
                            game['Submitted'].remove(sub)
                            break
                    if member['IsBot']:
                        if not member['Task'] == None:
                            task = member['Task']
                            if not task.done():
                                task.cancel()
                            member['Task'] = None
                    else:
                        msg = '**You were removed from game id:** ***{}.***'.format(game['ID'])
                        await member['User'].send(msg)
                    # Removed, no need to finish the loop
                    break
        if not outcome:
            return outcome
        # We removed someone - let's tell the world
        for member in game['Members']:
            if member['IsBot']:
                continue
            if removed['IsBot']:
                msg = '***{} ({})*** **left the game - reorganizing...**'.format(self.botName, removed['ID'])
            else:
                msg = '***{}*** **left the game - reorganizing...**'.format(DisplayName.name(removed['User']))
            # Check if the judge changed
            if judgeChanged:
                # Judge changed
                newJudge = game['Members'][game['Judge']] 
                if newJudge['IsBot']:
                    msg += '\n\n***{} ({})*** **is now judging!**'.format(self.botName, newJudge['ID'])
                    # Schedule judging task
                else:
                    if newJudge == member:
                        msg += '\n\n***YOU*** **are now judging!**'
                    else:
                        msg += '\n\n***{}*** **is now judging!**'.format(DisplayName.name(newJudge['User']))
            await member['User'].send(msg)
        return game
            

    def checkGame(self, game):
        for member in game['Members']:
            if not member['IsBot']:
                return True
        # If we got here - only bots, or empty game
        # Kill all bots' loops
        for member in game['Members']:
            if member['IsBot']:
                # Clear pending tasks and set to None
                if not member['Task'] == None:
                    task = member['Task']
                    if not task.done():
                        task.cancel()
                    member['Task'] = None
        # Set running to false
        game['Running'] = False
        self.games.remove(game)
        return False

    async def typing(self, game, typeTime = 5):
        # Allows us to show the bot typing
        waitTime = random.randint(self.botWaitMin, self.botWaitMax)
        preType  = waitTime-typeTime
        if preType > 0:
            await asyncio.sleep(preType)
            for member in game['Members']:
                if member['IsBot']:
                    continue
                # Show that we're typing
                await member['User'].dm_channel.trigger_typing()
                await asyncio.sleep(self.loopsleep)
            await asyncio.sleep(typeTime)
        else:
            for member in game['Members']:
                if member['IsBot']:
                    continue
                # Show that we're typing
                await member['User'].dm_channel.trigger_typing()
                await asyncio.sleep(self.loopsleep)
            await asyncio.sleep(waitTime)

    async def botPick(self, ctx, bot, game):
        # Has the bot pick their card
        blackNum  = game['BlackCard']['Pick']
        if blackNum == 1:
            cardSpeak = 'card'
        else:
            cardSpeak = 'cards'
        i = 0
        cards = []
        while i < blackNum:
            randCard = random.randint(0, len(bot['Hand'])-1)
            cards.append(bot['Hand'].pop(randCard)['Text'])
            i += 1
        
        await self.typing(game)

        # Make sure we haven't laid any cards
        if bot['Laid'] == False and game['Judging'] == False:
            newSubmission = { 'By': bot, 'Cards': cards }
            game['Submitted'].append(newSubmission)
            # Shuffle cards
            shuffle(game['Submitted'])
            bot['Laid'] = True
            game['Time'] = currentTime = int(time.time())
            await self.checkSubmissions(ctx, game, bot)
    

    async def botPickWin(self, ctx, game):
        totalUsers = len(game['Members'])-1
        submitted  = len(game['Submitted'])
        if submitted >= totalUsers:
            # Judge is a bot - and all cards are in!
            await self.typing(game)
            # Pick a winner
            winner = random.randint(0, totalUsers-1)
            await self.winningCard(ctx, game, winner)


    async def checkSubmissions(self, ctx, game, user = None):        
        totalUsers = len(game['Members'])-1
        submitted  = len(game['Submitted'])
        for member in game['Members']:
            msg = ''
            # Is the game running?
            if len(game['Members']) < self.minMembers:
                if member['IsBot']:
                    # Clear pending tasks and set to None
                    if not member['Task'] == None:
                        task = member['Task']
                        if not task.done():
                            # Task isn't finished - we're on a new hand, cancel it
                            task.cancel()
                        member['Task'] = None
                    continue
                # not enough members - send the embed
                stat_embed = discord.Embed(color=discord.Color.red())
                stat_embed.set_author(name='Not enough players to continue! ({}/{})'.format(len(game['Members']), self.minMembers))
                stat_embed.set_footer(text='Have other users join with: {}joincah {}'.format(ctx.prefix, game['ID']))
                await member['User'].send(embed=stat_embed)
                continue
            if member['IsBot'] == True:
                continue
            # Check if we have a user
            if user:
                blackNum  = game['BlackCard']['Pick']
                if blackNum == 1:
                    card = 'card'
                else:
                    card = 'cards'
                if user['IsBot']:
                    msg = '*{} ({})* submitted their {}! '.format(self.botName, user['ID'], card)
                else:
                    if not member == user:
                        # Don't say this to the submitting user
                        msg = '*{}* submitted their {}! '.format(DisplayName.name(user['User']), card)
            if submitted < totalUsers:
                msg += '{}/{} cards submitted...'.format(submitted, totalUsers)
            if len(msg):
                # We have something to say
                await member['User'].send(msg)
                await asyncio.sleep(self.loopsleep)


    async def checkCards(self, ctx, game):
        while not self.bot.is_closed():
            if not game['Running']:
                break
            # wait for 1 second
            await asyncio.sleep(1)
            # Check for all cards
            if len(game['Members']) < self.minMembers:
                # Not enough members
                continue
            # Enough members - let's check if we're judging
            if game['Judging']:
                continue
            # Enough members, and not judging - let's check cards
            totalUsers = len(game['Members'])-1
            submitted  = len(game['Submitted'])
            if submitted >= totalUsers:
                game['Judging'] = True
                # We have enough cards
                for member in game['Members']:
                    if member['IsBot']:
                        continue
                    msg = 'All cards have been submitted!'
                    # if 
                    await member['User'].send(msg)
                    await self.showOptions(ctx, member['User'])
                    await asyncio.sleep(self.loopsleep)

                # Check if a bot is the judge
                judge = game['Members'][game['Judge']]
                if not judge['IsBot']:
                    continue
                # task = self.bot.loop.create_task(self.botPickWin(ctx, game))
                task = asyncio.ensure_future(self.botPickWin(ctx, game))
                judge['Task'] = task

        

    async def winningCard(self, ctx, game, card):
        # Let's pick our card and alert everyone
        winner = game['Submitted'][card]
        if winner['By']['IsBot']:
            winnerName = '{} ({})'.format(self.botName, winner['By']['ID'])
            winner['By']['Points'] += 1
            winner['By']['Won'].append(game['BlackCard']['Text'])
        else:
            winnerName = DisplayName.name(winner['By']['User'])
        for member in game['Members']:
            if member['IsBot']:
                continue
            stat_embed = discord.Embed(color=discord.Color.gold())
            stat_embed.set_footer(text='Cards Against Humanity - id: {}'.format(game['ID']))
            index = game['Members'].index(member)
            if index == game['Judge']:
                stat_embed.set_author(name='You picked {}\'s card!'.format(winnerName))
            elif member == winner['By']:
                stat_embed.set_author(name='YOU WON!!')
                member['Points'] += 1
                member['Won'].append(game['BlackCard']['Text'])
            else:
                stat_embed.set_author(name='{} won!'.format(winnerName))
            if len(winner['Cards']) == 1:
                stat_embed.add_field(name='The WINNING card was:', value='{}'.format(' - '.join(winner['Cards'])))
            else:
                stat_embed.add_field(name='The WINNING cards were:', value='{}'.format(' - '.join(winner['Cards'])))
            await member['User'].send(embed=stat_embed)
            # await member['User'].send(msg)
            await asyncio.sleep(self.loopsleep)

            # await self.nextPlay(ctx, game)
            
        # Start the game loop
        event = game['NextHand']
        self.bot.loop.call_soon_threadsafe(event.set)
        game['Time'] = currentTime = int(time.time())

    async def gameCheckLoop(self, ctx, game):
        task = game['NextHand']
        while True:
            if not game['Running']:
                break
            # Clear the pending task
            task.clear()
            # Queue up the next hand
            await self.nextPlay(ctx, game)
            # Wait until our next clear
            await task.wait()

    async def messagePlayers(self, ctx, message, game, judge = False):
        # Messages all the users on in a game
        for member in game['Members']:
            if member['IsBot']:
                continue
            # Not bots
            if member is game['Members'][game['Judge']]:
                # Is the judge
                if judge:
                    await member['User'].send(message)
            else:
                # Not the judge
                await member['User'].send(message)

    ################################################
    
    async def showPlay(self, ctx, user):
        # Creates an embed and displays the current game stats
        stat_embed = discord.Embed(color=discord.Color.blue())
        game = self.userGame(user)
        if not game:
            return
        # Get the judge's name
        if game['Members'][game['Judge']]['User'] == user:
            judge = '**YOU** are'
        else:
            if game['Members'][game['Judge']]['IsBot']:
                # Bot
                judge = '*{} ({})* is'.format(self.botName, game['Members'][game['Judge']]['ID'])
            else:
                judge = '*{}* is'.format(DisplayName.name(game['Members'][game['Judge']]['User']))
        
        # Get the Black Card
        try:
            blackCard = game['BlackCard']['Text']
            blackNum  = game['BlackCard']['Pick']
        except Exception:
            blackCard = 'None.'
            blackNum  = 0

        # msg = '{} the judge.\n\n'.format(judge)
        msg = '__Black Card:__\n\n**{}**\n\n'.format(blackCard)
        
        totalUsers = len(game['Members'])-1
        submitted  = len(game['Submitted'])
        if len(game['Members']) >= self.minMembers:
            if submitted < totalUsers:
                msg += '{}/{} cards submitted...'.format(submitted, totalUsers)
            else:
                msg += 'All cards have been submitted!'
                await self.showOptions(ctx, user)
                return
        if not judge == '**YOU** are':
            # Judge doesn't need to lay a card
            if blackNum == 1:
                # Singular
                msg += '\n\nLay a card with `{}lay [card number]`'.format(ctx.prefix)
            elif blackNum > 1:
                # Plural
                msg += '\n\nLay **{} cards** with `{}lay [card numbers separated by commas (1,2,3)]`'.format(blackNum, ctx.prefix)
        
        stat_embed.set_author(name='Current Play')
        stat_embed.set_footer(text='Cards Against Humanity - id: {}'.format(game['ID']))
        stat_embed.add_field(name="{} the judge.".format(judge), value=msg)
        await user.send(embed=stat_embed)
        #await user.send(msg)
        
    async def showHand(self, ctx, user):
        # Shows the user's hand in an embed
        stat_embed = discord.Embed(color=discord.Color.green())
        game = self.userGame(user)
        if not game:
            return
        i = 0
        msg = ''
        points = '? points'
        for member in game['Members']:
            if int(member['ID']) == user.id:
                # Got our user
                if member['Points']==1:
                    points = '1 point'
                else:
                    points = '{} points'.format(member['Points'])
                for card in member['Hand']:
                    i += 1
                    msg += '{}. {}\n'.format(i, card['Text'])

        try:
            blackCard = '**{}**'.format(game['BlackCard']['Text'])
        except Exception:
            blackCard = '**None.**'
        stat_embed.add_field(name="Your Hand - {}".format(points), value=msg)
        # stat_embed.set_author(name='Your Hand - {}'.format(points))
        stat_embed.set_footer(text='Cards Against Humanity - id: {}'.format(game['ID']))
        await user.send(embed=stat_embed)
        # await user.send(msg)
                            
    async def showOptions(self, ctx, user):
        # Shows the judgement options
        stat_embed = discord.Embed(color=discord.Color.orange())
        game = self.userGame(user)
        if not game:
            return
        # Add title
        stat_embed.set_author(name='JUDGEMENT TIME!!')
        stat_embed.set_footer(text='Cards Against Humanity - id: {}'.format(game['ID']))

        if game['Members'][game['Judge']]['User'] == user:
            judge = '**YOU** are'
        else:
            if game['Members'][game['Judge']]['IsBot']:
                # Bot
                judge = '*{} ({})* is'.format(self.botName, game['Members'][game['Judge']]['ID'])
            else:
                judge = '*{}* is'.format(DisplayName.name(game['Members'][game['Judge']]['User']))
        blackCard = game['BlackCard']['Text']

        msg = '__Black Card:__\n\n**{}**\n\n'.format(blackCard)
        msg += '__Submitted White Cards:__\n\n'

        i = 0
        for sub in game['Submitted']:
            i+=1
            msg += '{}. {}\n'.format(i, ' - '.join(sub['Cards']))
        if judge == '**YOU** are':
            msg += '\nPick a winner with `{}pick [submission number]`.'.format(ctx.prefix)

        stat_embed.add_field(name="{} judging.".format(judge), value=msg)
        await user.send(embed=stat_embed)
        # await user.send(msg)
        
    async def drawCard(self, game):
        # Draws a random unused card and shuffles the deck if needed
        totalDiscard = len(game['Discard'])
        for member in game['Members']:
            totalDiscard += len(member['Hand'])
        if totalDiscard >= len(self.deck['whiteCards']):
            # Tell everyone the cards were shuffled
            for member in game['Members']:
                if member['IsBot']:
                    continue
                user = member['User']
                await user.send('Shuffling white cards...')
            # Shuffle the cards
            self.shuffle(game)
        while True:
            # Random grab a unique card
            index = random.randint(0, len(self.deck['whiteCards'])-1)
            if not index in game['Discard']:
                game['Discard'].append(index)
                text = self.deck['whiteCards'][index]
                text = self.cleanJson(text)
                card = { 'Index': index, 'Text': text }
                return card


    def shuffle(self, game):
        # Adds discards back into the deck
        game['Discard'] = []
        for member in game['Members']:
            for card in member['Hand']:
                game['Discard'].append(card['Index'])


    async def drawCards(self, user, cards = 10):
        if not type(user) is str:
            if type(user) is int:
                user = str(user)
            else:
                # Assume it's a discord.Member/User
                user = str(user.id)
        # fills the user's hand up to number of cards
        game = self.userGame(user)
        for member in game['Members']:
            if str(member['ID']) == str(user):
                # Found our user - let's draw cards
                i = len(member['Hand'])
                while i < cards:
                    # Draw unique cards until we fill our hand
                    newCard = await self.drawCard(game)
                    member['Hand'].append(newCard)
                    i += 1


    async def drawBCard(self, game):
        # Draws a random black card
        totalDiscard = len(game['BDiscard'])
        if totalDiscard >= len(self.deck['blackCards']):
            # Tell everyone the cards were shuffled
            for member in game['Members']:
                if member['IsBot']:
                    continue
                user = member['User']
                await user.send('Shuffling black cards...')
            # Shuffle the cards
            game['BDiscard'] = []
        while True:
            # Random grab a unique card
            index = random.randint(0, len(self.deck['blackCards'])-1)
            if not index in game['BDiscard']:
                game['BDiscard'].append(index)
                text = self.deck['blackCards'][index]['text']
                text = self.cleanJson(text)
                game['BlackCard'] = { 'Text': text, 'Pick': self.deck['blackCards'][index]['pick'] }
                return game['BlackCard']


    async def nextPlay(self, ctx, game):
        # Advances the game
        if len(game['Members']) < self.minMembers:
            stat_embed = discord.Embed(color=discord.Color.red())
            stat_embed.set_author(name='Not enough players to continue! ({}/{})'.format(len(game['Members']), self.minMembers))
            stat_embed.set_footer(text='Have other users join with: {}joincah {}'.format(ctx.prefix, game['ID']))
            for member in game['Members']:
                if member['IsBot']:
                    continue
                await member['User'].send(embed=stat_embed)
            return

        # Find if we have a winner
        winner = False
        stat_embed = discord.Embed(color=discord.Color.lighter_grey())
        for member in game['Members']:
            if member['IsBot']:
                # Clear pending tasks and set to None
                if not member['Task'] == None:
                    task = member['Task']
                    if not task.done():
                        # Task isn't finished - we're on a new hand, cancel it
                        task.cancel()
                    member['Task'] = None
            if member['Points'] >= self.winAfter:
                # We have a winner!
                winner = True
                if member['IsBot']:
                    stat_embed.set_author(name='{} ({}) is the WINNER!!'.format(self.botName, member['ID']))
                else:
                    stat_embed.set_author(name='{} is the WINNER!!'.format(DisplayName.name(member['User'])))
                stat_embed.set_footer(text='Congratulations!'.format(game['ID']))
                break
        if winner:
            for member in game['Members']:
                if not member['IsBot']:
                    await member['User'].send(embed=stat_embed)
                # Reset all users
                member['Hand']  = []
                member['Points'] = 0
                member['Won']   = []
                member['Laid']  = False
                member['Refreshed'] = False
                await asyncio.sleep(self.loopsleep)

        game['Judging'] = False
        # Clear submitted cards
        game['Submitted'] = []
        # We have enough members
        if game['Judge'] == -1:
            # First game - randomize judge
            game['Judge'] = random.randint(0, len(game['Members'])-1)
        else:
            game['Judge']+=1
        # Reset the judge if out of bounds
        if game['Judge'] >= len(game['Members']):
            game['Judge'] = 0

        # Draw the next black card
        bCard = await self.drawBCard(game)

        # Draw cards
        for member in game['Members']:
            member['Laid'] = False
            await self.drawCards(member['ID'])

        # Show hands
        for member in game['Members']:
            if member['IsBot']:
                continue
            await self.showPlay(ctx, member['User'])
            index = game['Members'].index(member)
            if not index == game['Judge']:
                await self.showHand(ctx, member['User'])
            await asyncio.sleep(self.loopsleep)

        # Have the bots lay their cards
        for member in game['Members']:
            if not member['IsBot']:
                continue
            if str(member['ID']) == str(game['Members'][game['Judge']]['ID']):
                continue
            # Not a human player, and not the judge
            # task = self.bot.loop.create_task(self.botPick(ctx, member, game))\
            task = asyncio.ensure_future(self.botPick(ctx, member, game))
            member['Task'] = task
            # await self.botPick(ctx, member, game)


    @commands.command(pass_context=True)
    async def game(self, ctx, *, message = None):
        """Displays the game's current status."""
        if not await self.checkPM(ctx.message):
            return
        userGame = self.userGame(ctx.message.author)
        if not userGame:
            msg = "You're not in a game - you can create one with `{}newcah` or join one with `{}joincah`.".format(ctx.prefix, ctx.prefix)
            await ctx.author.send(msg)
            return
        await self.showPlay(ctx, ctx.message.author)


    @commands.command(pass_context=True)
    async def say(self, ctx, *, message = None):
        """Broadcasts a message to the other players in your game."""
        if not await self.checkPM(ctx.message):
            return
        # Get the user - for cross-server compatibility
        author = self.bot.get_user(ctx.message.author.id)
        userGame = self.userGame(ctx.message.author)
        if not userGame:
            msg = "You're not in a game - you can create one with `{}newcah` or join one with `{}joincah`.".format(ctx.prefix, ctx.prefix)
            await ctx.author.send(msg)
            return
        userGame['Time'] = int(time.time())
        
        stat_embed = discord.Embed(color=discord.Color.default())
        stat_embed.set_footer(text='Cards Against Humanity - id: {}'.format(userGame['ID']))
        
        if message == None:
            stat_embed.add_field(name="{} says:".format(ctx.author.name), value="Ooookay, you say *nothing...*")
            await ctx.author.send(embed=stat_embed)
            return
        stat_embed.add_field(name="{} says:".format(ctx.author.name), value=message)
        # msg = '*{}* says: {}'.format(ctx.message.author.name, message)
        member_count = 0
        for member in userGame['Members']:
            if member['IsBot']:
                continue
            # Tell them all!!
            if not member['User'] == author:
                # Don't tell yourself
                member_count += 1
                await member['User'].send(embed=stat_embed)
            else:
                # Update member's time
                member['Time'] = int(time.time())
        stat_embed.clear_fields()
        if member_count == 1:
            stat_embed.add_field(name="Message sent!", value="1 recipient")
        else:
            stat_embed.add_field(name="Message sent!", value="{} recipients".format(member_count))
        await ctx.author.send(embed=stat_embed)
            
                
    @commands.command(pass_context=True)
    async def lay(self, ctx, *, card = None):
        """Lays a card or cards from your hand.  If multiple cards are needed, separate them by a comma (1,2,3)."""
        if not await self.checkPM(ctx.message):
            return
        # Get the user - for cross-server compatibility
        author = self.bot.get_user(ctx.message.author.id)
        userGame = self.userGame(author)
        if not userGame:
            msg = "You're not in a game - you can create one with `{}newcah` or join one with `{}joincah`.".format(ctx.prefix, ctx.prefix)
            await ctx.author.send(msg)
            return
        userGame['Time'] = int(time.time())
        for member in userGame['Members']:
            if member['User'] == author:
                member['Time'] = int(time.time())
                user = member
                index = userGame['Members'].index(member)
                if index == userGame['Judge']:
                    await ctx.author.send("You're the judge.  You don't get to lay cards this round.")
                    return
        for submit in userGame['Submitted']:
            if submit['By']['User'] == author:
                await ctx.author.send("You already made your submission this round.")
                return
        if card == None:
            await ctx.author.send('You need you input *something.*')
            return
        card = card.strip()
        card = card.replace(" ", "")
        # Not the judge
        if len(userGame['Members']) < self.minMembers:
            stat_embed = discord.Embed(color=discord.Color.red())
            stat_embed.set_author(name='Not enough players to continue! ({}/{})'.format(len(userGame['Members']), self.minMembers))
            stat_embed.set_footer(text='Have other users join with: {}joincah {}'.format(ctx.prefix, userGame['ID']))
            await ctx.author.send(embed=stat_embed)
            return

        numberCards = userGame['BlackCard']['Pick']
        cards = []
        if numberCards > 1:
            cardSpeak = "cards"
            try:
                card = card.split(',')
            except Exception:
                card = []
            if not len(card) == numberCards:
                msg = 'You need to lay **{} cards** (no duplicates) with `{}lay [card numbers separated by commas (1,2,3)]`'.format(numberCards, ctx.prefix)
                await ctx.author.send(msg)
                await self.showHand(ctx, author)
                return
            # Got something
            # Check for duplicates
            if not len(card) == len(set(card)):
                msg = 'You need to lay **{} cards** (no duplicates) with `{}lay [card numbers separated by commas (1,2,3)]`'.format(numberCards, ctx.prefix)
                await ctx.author.send(msg)
                await self.showHand(ctx, author)
                return
            # Works
            for c in card:
                try:
                    c = int(c)
                except Exception:
                    msg = 'You need to lay **{} cards** (no duplicates) with `{}lay [card numbers separated by commas (1,2,3)]`'.format(numberCards, ctx.prefix)
                    await ctx.author.send(msg)
                    await self.showHand(ctx, author)
                    return

                if c < 1 or c > len(user['Hand']):
                    msg = 'Card numbers must be between 1 and {}.'.format(len(user['Hand']))
                    await ctx.author.send(msg)
                    await self.showHand(ctx, author)
                    return
                cards.append(user['Hand'][c-1]['Text'])
            # Remove from user's hand
            card = sorted(card, key=lambda card:int(card), reverse=True)
            for c in card:
                user['Hand'].pop(int(c)-1)
            # Valid cards
            
            newSubmission = { 'By': user, 'Cards': cards }
        else:
            cardSpeak = "card"
            try:
                card = int(card)
            except Exception:
                msg = 'You need to lay a valid card with `{}lay [card number]`'.format(ctx.prefix)
                await ctx.author.send(msg)
                await self.showHand(ctx, author)
                return
            if card < 1 or card > len(user['Hand']):
                msg = 'Card numbers must be between 1 and {}.'.format(len(user['Hand']))
                await ctx.author.send(msg)
                await self.showHand(ctx, author)
                return
            # Valid card
            newSubmission = { 'By': user, 'Cards': [ user['Hand'].pop(card-1)['Text'] ] }
        userGame['Submitted'].append(newSubmission)
        
        # Shuffle cards
        shuffle(userGame['Submitted'])

        user['Laid'] = True
        await ctx.author.send('You submitted your {}!'.format(cardSpeak))
        await self.checkSubmissions(ctx, userGame, user)
            

    @commands.command(pass_context=True)
    async def pick(self, ctx, *, card = None):
        """As the judge - pick the winning card(s)."""
        if not await self.checkPM(ctx.message):
            return
        # Get the user - for cross-server compatibility
        author = self.bot.get_user(ctx.message.author.id)
        # Check if the user is already in game
        userGame = self.userGame(ctx.message.author)
        if not userGame:
            # Not in a game
            msg = "You're not in a game - you can create one with `{}newcah` or join one with `{}joincah`.".format(ctx.prefix, ctx.prefix)
            await ctx.author.send(msg)
            return
        userGame['Time'] = int(time.time())
        isJudge = False
        for member in userGame['Members']:
            if member['User'] == author:
                member['Time'] = int(time.time())
                user = member
                index = userGame['Members'].index(member)
                if index == userGame['Judge']:
                    isJudge = True
        if not isJudge:
            msg = "You're not the judge - I guess you'll have to wait your turn."
            await ctx.author.send(msg)
            return
        # Am judge
        totalUsers = len(userGame['Members'])-1
        submitted  = len(userGame['Submitted'])
        if submitted < totalUsers:
            if totalUsers - submitted == 1:
                msg = "Still waiting on 1 card..."
            else:
                msg = "Still waiting on {} cards...".format(totalUsers-submitted)
            await ctx.author.send(msg)
            return
        try:
            card = int(card)-1
        except Exception:
            card = -1
        if card < 0 or card >= totalUsers:
            msg = "Your pick must be between 1 and {}.".format(totalUsers)
            await ctx.author.send(msg)
            return
        # Pick is good!
        await self.winningCard(ctx, userGame, card)


    @commands.command(pass_context=True)
    async def hand(self, ctx):
        """Shows your hand."""
        if not await self.checkPM(ctx.message):
            return
        # Check if the user is already in game
        userGame = self.userGame(ctx.message.author)
        if not userGame:
            # Not in a game
            msg = "You're not in a game - you can create one with `{}newcah` or join one with `{}joincah`.".format(ctx.prefix, ctx.prefix)
            await ctx.author.send(msg)
            return
        await self.showHand(ctx, ctx.message.author)
        userGame['Time'] = currentTime = int(time.time())


    @commands.command(pass_context=True)
    async def newcah(self, ctx):
        """Starts a new Cards Against Humanity game."""
        #if not await self.checkPM(ctx.message):
            #return
        # Get the user - for cross-server compatibility
        author = self.bot.get_user(ctx.message.author.id)
        # Check if the user is already in game
        userGame = self.userGame(ctx.message.author)
        if userGame:
            # Already in a game
            msg = "You're already in a game (id: *{}*)\nType `{}leavecah` to leave that game.".format(userGame['ID'], ctx.prefix)
            await ctx.channel.send(msg)
            return

        # Not in a game - create a new one
        gameID = self.randomID()
        currentTime = int(time.time())
        newGame = { 'ID': gameID, 'Members': [], 'Discard': [], 'BDiscard': [], 'Judge': -1, 'Time': currentTime, 'BlackCard': None, 'Submitted': [], 'NextHand': asyncio.Event(), 'Judging': False, 'Timeout': True }
        member = { 'ID': author.id, 'User': author, 'Points': 0, 'Won': [], 'Hand': [], 'Laid': False, 'Refreshed': False, 'IsBot': False, 'Creator': True, 'Task': None, 'Time': currentTime }
        newGame['Members'].append(member)
        newGame['Running'] = True
        self.loop_list.append(self.bot.loop.create_task(self.gameCheckLoop(ctx, newGame)))
        self.loop_list.append(self.bot.loop.create_task(self.checkCards(ctx, newGame)))
        self.games.append(newGame)
        # Tell the user they created a new game and list its ID
        await ctx.channel.send('**You created game id:** ***{}***'.format(gameID))
        await self.drawCards(ctx.message.author)
        # await self.showHand(ctx, ctx.message.author)
        # await self.nextPlay(ctx, newGame)
    

    @commands.command(pass_context=True)
    async def leavecah(self, ctx):        
        """Leaves the current game you're in."""
        removeCheck = await self.removeMember(ctx.message.author)
        if not removeCheck:
            msg = 'You are not in a game.'
            await ctx.channel.send(msg)
            return
        if self.checkGame(removeCheck):
            # await self.nextPlay(ctx, removeCheck)
            
            """# Start the game loop
            event = removeCheck['NextHand']
            self.bot.loop.call_soon_threadsafe(event.set)"""
            # Player was removed - try to handle it calmly...
            await self.checkSubmissions(ctx, removeCheck)


    @commands.command(pass_context=True)
    async def joincah(self, ctx, *, id = None):
        """Join a Cards Against Humanity game.  If no id or user is passed, joins a random game."""
        #if not await self.checkPM(ctx.message):
            #return
        # Get the user - for cross-server compatibility
        author = self.bot.get_user(ctx.message.author.id)
        # Check if the user is already in game
        userGame = self.userGame(ctx.message.author)
        isCreator = False
        if userGame:
            # Already in a game
            msg = "You're already in a game (id: *{}*)\nType `{}leavecah` to leave that game.".format(userGame['ID'], ctx.prefix)
            await ctx.channel.send(msg)
            return
        if len(self.games):
            if id:
                game = self.gameForID(id)
                if game == None:
                    # That id doesn't exist - or is possibly a user
                    # If user, has to be joined from server chat
                    if not ctx.message.guild:
                        msg = "I couldn't find a game attached to that id.  If you are trying to join a user - run the `{}joincah [user]` command in a channel on a server you share with that user.".format(ctx.prefix)
                        await ctx.channel.send(msg)
                        return
                    else:
                        # We have a server - let's try for a user
                        member = DisplayName.memberForName(id, ctx.message.guild)
                        if not member:
                            # Couldn't find user!
                            msg = "I couldn't find a game attached to that id.  If you are trying to join a user - run the `{}joincah [user]` command in a channel on a server you share with that user.".format(ctx.prefix)
                            await ctx.channel.send(msg)
                            return
                        # Have a user - check if they're in a game
                        game = self.userGame(member)
                        if not game:
                            # That user is NOT in a game!
                            msg = "That user doesn't appear to be playing."
                            await ctx.channel.send(msg)
                            return
                                
            else:
                # Let's order games by least number of people,
                # then randomly end up in one of the lower ones
                # Max number of people should be 10
                orderedGames = sorted(self.games, key=lambda x:len(x['Members']))
                lowestNumber = self.maxPlayers
                for game in orderedGames:
                    if len(game['Members']) < lowestNumber:
                        lowestNumber = len(game['Members'])
                
                if lowestNumber >= self.maxPlayers:
                    # We didn't find any games with fewer than 10 people
                    # Create a new one
                    # No games - create a new one
                    gameID = self.randomID()
                    currentTime = int(time.time())
                    game = { 'ID': gameID, 'Members': [], 'Discard': [], 'BDiscard': [], 'Judge': -1, 'Time': currentTime, 'BlackCard': None, 'Submitted': [], 'NextHand': asyncio.Event(), 'Judging': False, 'Timeout': True }
                    game['Running'] = True
                    self.loop_list.append(self.bot.loop.create_task(self.gameCheckLoop(ctx, game)))
                    self.loop_list.append(self.bot.loop.create_task(self.checkCards(ctx, game)))
                    self.games.append(game)
                    # Tell the user they created a new game and list its ID
                    await ctx.channel.send('**You created game id:** ***{}***'.format(gameID))
                    isCreator = True
                else:
                    # We found games with fewer than 10 members!
                    gameList = []
                    for game in orderedGames:
                        if len(game['Members']) <= lowestNumber:
                            gameList.append(game)
                    game = random.choice(gameList)
        else:
            # No games - create a new one
            gameID = self.randomID()
            currentTime = int(time.time())
            game = { 'ID': gameID, 'Members': [], 'Discard': [], 'BDiscard': [], 'Judge': -1, 'Time': currentTime, 'BlackCard': None, 'Submitted': [], 'NextHand': asyncio.Event(), 'Judging': False, 'Timeout': True }
            game['Running'] = True
            self.loop_list.append(self.bot.loop.create_task(self.gameCheckLoop(ctx, game)))
            self.loop_list.append(self.bot.loop.create_task(self.checkCards(ctx, game)))
            self.games.append(game)
            # Tell the user they created a new game and list its ID
            await ctx.channel.send('**You created game id:** ***{}***'.format(gameID))
            isCreator = True

        # Tell everyone else you joined
        for member in game['Members']:
            if member['IsBot']:
                continue
            await member['User'].send('***{}*** **joined the game!**'.format(DisplayName.name(ctx.message.author)))
            
        # We got a user!
        currentTime = int(time.time())
        member = { 'ID': author.id, 'User': author, 'Points': 0, 'Won': [], 'Hand': [], 'Laid': False, 'Refreshed': False, 'IsBot': False, 'Creator': isCreator, 'Task': None, 'Time': currentTime }
        game['Members'].append(member)
        await self.drawCards(ctx.message.author)
        if len(game['Members'])==1:
            # Just created the game
            await self.drawCards(ctx.message.author)
        else:
            msg = "**You've joined game id:** ***{}!***\n\nThere are *{} users* in this game.".format(game['ID'], len(game['Members']))
            await ctx.channel.send(msg)

        # Check if adding put us at minimum members
        if len(game['Members']) - 1 < self.minMembers:
            # It was - *actually* start a game
            event = game['NextHand']
            self.bot.loop.call_soon_threadsafe(event.set)
        else:
            # It was not - just incorporate new players
            await self.checkSubmissions(ctx, game)
            # Reset judging flag to retrigger actions
            game['Judging'] = False
            # Show the user the current card and their hand
            await self.showPlay(ctx, member['User'])
            await self.showHand(ctx, member['User'])
        event = game['NextHand']

        game['Time'] = int(time.time())


    @commands.command(pass_context=True)
    async def addbot(self, ctx):
        """Adds a bot to the game.  Can only be done by the player who created the game."""
        if not await self.checkPM(ctx.message):
            return
        # Get the user - for cross-server compatibility
        author = self.bot.get_user(ctx.message.author.id)
        # Check if the user is already in game
        userGame = self.userGame(ctx.message.author)
        if not userGame:
            # Not in a game
            msg = "You're not in a game - you can create one with `{}newcah` or join one with `{}joincah`.".format(ctx.prefix, ctx.prefix)
            await ctx.author.send(msg)
            return
        botCount = 0
        for member in userGame['Members']:
            if member['IsBot']:
                botCount += 1
                continue
            if member['User'] == author:
                if not member['Creator']:
                    # You didn't make this game
                    msg = 'Only the player that created the game can add bots.'
                    await ctx.author.send(msg)
                    return
                member['Time'] = int(time.time())
        # We are the creator - let's check the number of bots
        if botCount >= self.maxBots:
            # Too many bots!
            msg = 'You already have enough bots (max is {}).'.format(self.maxBots)
            await ctx.author.send(msg)
            return
        # We can get another bot!
        botID = self.randomBotID(userGame)
        lobot = { 'ID': botID, 'User': None, 'Points': 0, 'Won': [], 'Hand': [], 'Laid': False, 'Refreshed': False, 'IsBot': True, 'Creator': False, 'Task': None }
        userGame['Members'].append(lobot)
        await self.drawCards(lobot['ID'])
        msg = '***{} ({})*** **joined the game!**'.format(self.botName, botID)
        for member in userGame['Members']:
            if member['IsBot']:
                continue
            await member['User'].send(msg)
        # await self.nextPlay(ctx, userGame)

        # Check if adding put us at minimum members
        if len(userGame['Members']) - 1 < self.minMembers:
            # It was - *actually* start a game
            event = userGame['NextHand']
            self.bot.loop.call_soon_threadsafe(event.set)
        else:
            # It was not - just incorporate new players
            await self.checkSubmissions(ctx, userGame)
            # Reset judging flag to retrigger actions
            userGame['Judging'] = False
            # Schedule stuff
            task = asyncio.ensure_future(self.botPick(ctx, lobot, userGame))
            lobot['Task'] = task


    @commands.command(pass_context=True)
    async def addbots(self, ctx, number = None):
        """Adds bots to the game.  Can only be done by the player who created the game."""
        if not await self.checkPM(ctx.message):
            return
        # Get the user - for cross-server compatibility
        author = self.bot.get_user(ctx.message.author.id)
        # Check if the user is already in game
        userGame = self.userGame(ctx.message.author)
        if not userGame:
            # Not in a game
            msg = "You're not in a game - you can create one with `{}newcah` or join one with `{}joincah`.".format(ctx.prefix, ctx.prefix)
            await ctx.author.send(msg)
            return
        botCount = 0
        for member in userGame['Members']:
            if member['IsBot']:
                botCount += 1
                continue
            if member['User'] == author:
                if not member['Creator']:
                    # You didn't make this game
                    msg = 'Only the player that created the game can add bots.'
                    await ctx.author.send(msg)
                    return
                member['Time'] = int(time.time())
        if number == None:
            # No number specified - let's add the max number of bots
            number = self.maxBots - botCount

        try:
            number = int(number)
        except Exception:
            msg = 'Number of bots to add must be an integer.'
            await ctx.author.send(msg)
            return

        # We are the creator - let's check the number of bots
        if botCount >= self.maxBots:
            # Too many bots!
            msg = 'You already have enough bots (max is {}).'.format(self.maxBots)
            await ctx.author.send(msg)
            return

        if number > (self.maxBots - botCount):
            number = self.maxBots - botCount
        
        if number == 1:
            msg = '**Adding {} bot:**\n\n'.format(number)
        else:
            msg = '**Adding {} bots:**\n\n'.format(number)

        newBots = []
        for i in range(0, number):
            # We can get another bot!
            botID = self.randomBotID(userGame)
            lobot = { 'ID': botID, 'User': None, 'Points': 0, 'Won': [], 'Hand': [], 'Laid': False, 'Refreshed': False, 'IsBot': True, 'Creator': False, 'Task': None }
            userGame['Members'].append(lobot)
            newBots.append(lobot)
            await self.drawCards(lobot['ID'])
            msg += '***{} ({})*** **joined the game!**\n'.format(self.botName, botID)
            # await self.nextPlay(ctx, userGame)
        
        for member in userGame['Members']:
            if member['IsBot']:
                continue
            await member['User'].send(msg)

        # Check if adding put us at minimum members
        if len(userGame['Members']) - number < self.minMembers:
            # It was - *actually* start a game
            event = userGame['NextHand']
            self.bot.loop.call_soon_threadsafe(event.set)
        else:
            # It was not - just incorporate new players
            await self.checkSubmissions(ctx, userGame)
            # Reset judging flag to retrigger actions
            game['Judging'] = False
            for bot in newBots:
                # Schedule stuff
                task = asyncio.ensure_future(self.botPick(ctx, bot, userGame))
                bot['Task'] = task

    @commands.command(pass_context=True)
    async def removebot(self, ctx, *, id = None):
        """Removes a bot from the game.  Can only be done by the player who created the game."""
        if not await self.checkPM(ctx.message):
            return
        # Get the user - for cross-server compatibility
        author = self.bot.get_user(ctx.message.author.id)
        # Check if the user is already in game
        userGame = self.userGame(ctx.message.author)
        if not userGame:
            # Not in a game
            msg = "You're not in a game - you can create one with `{}newcah` or join one with `{}joincah`.".format(ctx.prefix, ctx.prefix)
            await ctx.author.send(msg)
            return
        botCount = 0
        for member in userGame['Members']:
            if member['IsBot']:
                botCount += 1
                continue
            if member['User'] == author:
                if not member['Creator']:
                    # You didn't make this game
                    msg = 'Only the player that created the game can remove bots.'
                    await ctx.author.send(msg)
                    return
                member['Time'] = int(time.time())
        # We are the creator - let's check the number of bots
        if id == None:
            # Just remove the first bot we find
            for member in userGame['Members']:
                if member['IsBot']:
                    await self.removeMember(member['ID'])
                    """# Start the game loop
                    event = userGame['NextHand']
                    self.bot.loop.call_soon_threadsafe(event.set)"""
                    # Bot was removed - try to handle it calmly...
                    await self.checkSubmissions(ctx, userGame)
                    return
            msg = 'No bots to remove!'
            await ctx.author.send(msg)
            return
        else:
            # Remove a bot by id
            if not await self.removeMember(id):
                # not found
                msg = 'I couldn\'t locate that bot on this game.  If you\'re trying to remove a player, try the `{}removeplayer [name]` command.'.format(ctx.prefix)
                await ctx.author.send(msg)
                return
        # await self.nextPlay(ctx, userGame)

        """# Start the game loop
        event = userGame['NextHand']
        self.bot.loop.call_soon_threadsafe(event.set)"""
        # Bot was removed - let's try to handle it calmly...
        await self.checkSubmissions(ctx, userGame)


    @commands.command(pass_context=True)
    async def cahgames(self, ctx):
        """Displays up to 10 CAH games in progress."""
        shuffledGames = list(self.games)
        random.shuffle(shuffledGames)
        if not len(shuffledGames):
            await ctx.channel.send('No games being played currently.')
            return
        
        max = 10
        if len(shuffledGames) < 10:
            max = len(shuffledGames)
        msg = '__Current CAH Games__:\n\n'

        for i in range(0, max):
            playerCount = 0
            botCount    = 0
            gameID      = shuffledGames[i]['ID']
            for j in shuffledGames[i]['Members']:
                if j['IsBot']:
                    botCount += 1
                else:
                    playerCount += 1
            botText = '{} bot'.format(botCount)
            if not botCount == 1:
                botText += 's'
            playerText = '{} player'.format(playerCount)
            if not playerCount == 1:
                playerText += 's'

            msg += '{}. {} - {} | {}\n'.format(i+1, gameID, playerText, botText)

        await ctx.channel.send(msg)

            

    @commands.command(pass_context=True)
    async def score(self, ctx):
        """Display the score of the current game."""
        if not await self.checkPM(ctx.message):
            return
        # Check if the user is already in game
        userGame = self.userGame(ctx.message.author)
        if not userGame:
            # Not in a game
            msg = "You're not in a game - you can create one with `{}newcah` or join one with `{}joincah`.".format(ctx.prefix, ctx.prefix)
            await ctx.author.send(msg)
            return
        stat_embed = discord.Embed(color=discord.Color.purple())
        # stat_embed.set_author(name='Current Score')
        stat_embed.set_footer(text='Cards Against Humanity - id: {}'.format(userGame['ID']))
        users = sorted(userGame['Members'], key=lambda card:int(card['Points']), reverse=True)
        msg = ''
        i = 0
        if len(users) > 10:
            msg += '__10 of {} Players:__\n\n'.format(len(users))
        else:
            msg += '__Players:__\n\n'
        for user in users:
            i += 1
            if i > 10:
                break
            if user['Points'] == 1:
                if user['User']:
                    # Person
                    msg += '{}. *{}* - 1 point\n'.format(i, DisplayName.name(user['User']))
                else:
                    # Bot
                    msg += '{}. *{} ({})* - 1 point\n'.format(i, self.botName, user['ID'])
            else:
                if user['User']:
                    # Person
                    msg += '{}. *{}* - {} points\n'.format(i, DisplayName.name(user['User']), user['Points'])
                else:
                    # Bot
                    msg += '{}. *{} ({})* - {} points\n'.format(i, self.botName, user['ID'], user['Points'])
        stat_embed.add_field(name="Current Score", value=msg)
        await ctx.author.send(embed=stat_embed)
        # await ctx.author.send(msg)

    @commands.command(pass_context=True)
    async def laid(self, ctx):
        """Shows who laid their cards and who hasn't."""
        if not await self.checkPM(ctx.message):
            return
        # Check if the user is already in game
        userGame = self.userGame(ctx.message.author)
        if not userGame:
            # Not in a game
            msg = "You're not in a game - you can create one with `{}newcah` or join one with `{}joincah`.".format(ctx.prefix, ctx.prefix)
            await ctx.author.send(msg)
            return
        stat_embed = discord.Embed(color=discord.Color.purple())
        stat_embed.set_author(name='Card Check')
        stat_embed.set_footer(text='Cards Against Humanity - id: {}'.format(userGame['ID']))
        await ctx.author.send(embed=stat_embed)
        users = sorted(userGame['Members'], key=lambda card:int(card['Laid']))
        msg = ''
        i = 0
        if len(users) > 10:
            msg += '__10 of {} Players:__\n\n'.format(len(users))
        else:
            msg += '__Players:__\n\n'
        for user in users:
            if len(userGame['Members']) >= self.minMembers:
                if user == userGame['Members'][userGame['Judge']]:
                    continue
            i += 1
            if i > 10:
                break

            if user['Laid']:
                if user['User']:
                    # Person
                    msg += '{}. *{}* - Cards are in.\n'.format(i, DisplayName.name(user['User']))
                else:
                    # Bot
                    msg += '{}. *{} ({})* - Cards are in.\n'.format(i, self.botName, user['ID'])
            else:
                if user['User']:
                    # Person
                    msg += '{}. *{}* - Waiting for cards...\n'.format(i, DisplayName.name(user['User']))
                else:
                    # Bot
                    msg += '{}. *{} ({})* - Waiting for cards...\n'.format(i, self.botName, user['ID'])
        await ctx.author.send(msg)

    @commands.command(pass_context=True)
    async def removeplayer(self, ctx, *, name = None):
        """Removes a player from the game.  Can only be done by the player who created the game."""
        if not await self.checkPM(ctx.message):
            return
        # Get the user - for cross-server compatibility
        author = self.bot.get_user(ctx.message.author.id)
        # Check if the user is already in game
        userGame = self.userGame(ctx.message.author)
        if not userGame:
            # Not in a game
            msg = "You're not in a game - you can create one with `{}newcah` or join one with `{}joincah`.".format(ctx.prefix, ctx.prefix)
            await ctx.author.send(msg)
            return
        botCount = 0
        for member in userGame['Members']:
            if member['IsBot']:
                botCount += 1
                continue
            if member['User'] == author:
                if not member['Creator']:
                    # You didn't make this game
                    msg = 'Only the player that created the game can remove players.'
                    await ctx.author.send(msg)
                    return
                member['Time'] = int(time.time())
        # We are the creator - let's check the number of bots
        if name == None:
            # Nobody named!
            msg = 'Okay, I removed... no one from the game...'
            await ctx.author.send(msg)
            return

        # Let's get the person either by name, or by id
        nameID = ''.join(list(filter(str.isdigit, name)))
        for member in userGame['Members']:
            toRemove = False
            if member['IsBot']:
                continue
            if name.lower() == DisplayName.name(member['User']).lower():
                # Got em!
                toRemove = True
            elif nameID == member['ID']:
                # Got em!
                toRemove = True
            if toRemove:
                await self.removeMember(member['ID'])
                break
        # await self.nextPlay(ctx, userGame)

        if toRemove:
            """# Start the game loop
            event = userGame['NextHand']
            self.bot.loop.call_soon_threadsafe(event.set)"""
            # Player was removed - try to handle it calmly...
            await self.checkSubmissions(ctx, userGame)
        else:
            msg = 'I couldn\'t locate that player on this game.  If you\'re trying to remove a bot, try the `{}removebot [id]` command.'.format(ctx.prefix)
            await ctx.author.send(msg)
            return

    @commands.command(pass_context=True)
    async def flushhand(self, ctx):
        """Flushes the cards in your hand - can only be done once per game."""
        if not await self.checkPM(ctx.message):
            return
        # Get the user - for cross-server compatibility
        author = self.bot.get_user(ctx.message.author.id)
        # Check if the user is already in game
        userGame = self.userGame(ctx.message.author)
        if not userGame:
            # Not in a game
            msg = "You're not in a game - you can create one with `{}newcah` or join one with `{}joincah`.".format(ctx.prefix, ctx.prefix)
            await ctx.author.send(msg)
            return
        if userGame['Judge'] == -1:
            msg = "The game hasn't started yet.  Probably not worth it to flush your hand before you get it..."
            await ctx.author.send(msg)
            return
        for member in userGame['Members']:
            if member['IsBot']:
                continue
            if member['User'] == author:
                member['Time'] = int(time.time())
                # Found us!
                if member['Refreshed']:
                    # Already flushed their hand
                    msg = 'You have already flushed your hand this game.'
                    await ctx.author.send(msg)
                    return
                else:
                    member['Hand'] = []
                    await self.drawCards(member['ID'])
                    member['Refreshed'] = True
                    msg = 'Flushing your hand!'
                    await ctx.author.send(msg)
                    await self.showHand(ctx, ctx.message.author)
                    return

    @commands.command(pass_context=True)
    async def idlekick(self, ctx, *, setting = None):
        """Sets whether or not to kick members if idle for 5 minutes or more.  Can only be done by the player who created the game."""
        if not await self.checkPM(ctx.message):
            return
        # Get the user - for cross-server compatibility
        author = self.bot.get_user(ctx.message.author.id)
        # Check if the user is already in game
        userGame = self.userGame(ctx.message.author)
        if not userGame:
            # Not in a game
            msg = "You're not in a game - you can create one with `{}newcah` or join one with `{}joincah`.".format(ctx.prefix, ctx.prefix)
            await ctx.author.send(msg)
            return
        botCount = 0
        for member in userGame['Members']:
            if member['IsBot']:
                botCount += 1
                continue
            if member['User'] == author:
                if not member['Creator']:
                    # You didn't make this game
                    msg = 'Only the player that created the game can remove bots.'
                    await ctx.author.send(msg)
                    return
        # We are the creator - let's check the number of bots
        if setting == None:
            # Output idle kick status
            if userGame['Timeout']:
                await ctx.channel.send('Idle kick is enabled.')
            else:
                await ctx.channel.send('Idle kick is disabled.')
            return
        elif setting.lower() in [ "yes", "on", "true", "enabled", "enable" ]:
            setting = True
        elif setting.lower() in [ "no", "off", "false", "disabled", "disable" ]:
            setting = False
        else:
            setting = None

        if setting == True:
            if userGame['Timeout'] == True:
                msg = 'Idle kick remains enabled.'
            else:
                msg = 'Idle kick now enabled.'
                for member in userGame['Members']:
                    member['Time'] = int(time.time())
        else:
            if userGame['Timeout'] == False:
                msg = 'Idle kick remains disabled.'
            else:
                msg = 'Idle kick now disabled.'
        userGame['Timeout'] = setting
        
        await ctx.channel.send(msg)
