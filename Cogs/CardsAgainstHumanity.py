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
from   Cogs import Nullify


class CardsAgainstHumanity:

    # Init with the bot reference, and a reference to the deck file
    def __init__(self, bot, file = None):
        self.bot = bot
        self.games = []
        self.maxBots = 5 # Max number of bots that can be added to a game - don't count toward max players
        self.maxPlayers = 10 # Max players for ranjom joins
        self.maxDeadTime = 3600 # Allow an hour of dead time before killing a game
        self.checkTime = 300 # 5 minutes between dead time checks
        self.winAfter = 10 # 10 wins for the game
        self.botWaitMin = 5 # Minimum number of seconds before the bot makes a decision
        self.botWaitMax = 30 # Max number of seconds before a bot makes a decision
        self.charset = "1234567890"
        self.botName = 'Rando Cardrissian'
        self.minMembers = 3
        self.loopsleep = 0.01
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
        self.bot.loop.create_task(self.checkDead())

    def cleanJson(self, json):
        json = html.unescape(json)
        # Clean out html formatting
        json = json.replace('_','[blank]')
        json = json.replace('<br>','\n')
        json = json.replace('<br/>','\n')
        json = json.replace('<i>', '*')
        json = json.replace('</i>', '*')
        return json


    async def checkDead(self):
        while not self.bot.is_closed:
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
                            continue
                        msg = "Game id: *{}* has been closed due to inactivity.".format(game['ID'])
                        await self.bot.send_message(member['User'], msg)
                    self.games.remove(game)

    async def checkPM(self, message):
        # Checks if we're talking in PM, and if not - outputs an error
        if message.channel.is_private:
            # PM
            return True
        else:
            # Not in PM
            await self.bot.send_message(message.channel, 'Cards Against Humanity commands must be run in PM.')
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
                if member['ID'] == newID:
                    exists = True
                    break
            if not exists:
                break
        return newID

    def userGame(self, user):
        # Returns the game the user is currently in
        if not type(user) is str:
            # Assume it's a discord.Member/User
            user = user.id

        for game in self.games:
            for member in game['Members']:
                if member['ID'] == user:
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
            # Assume it's a discord.Member/User
            user = user.id
        outcome  = False
        removed  = None
        if not game:
            game = self.userGame(user)
        if game:
            for member in game['Members']:
                if member['ID'] == user:
                    game['Members'].remove(member)
                    removed = member
                    outcome = True
                    if not member['IsBot']:
                        msg = 'You were removed from game id: *{}*.'.format(game['ID'])
                        await self.bot.send_message(member['User'], msg)
        if not outcome:
            return outcome
        # We removed someone - let's tell the world
        if removed['IsBot']:
            msg = '*{} ({})* left the game - reorganizing...'.format(self.botName, removed['ID'])
        else:
            msg = '*{}* left the game - reorganizing...'.format(DisplayName.name(removed['User']))
        for member in game['Members']:
            if member['IsBot']:
                continue
            await self.bot.send_message(member['User'], msg)
        return game
            

    def checkGame(self, game):
        for member in game['Members']:
            if not member['IsBot']:
                return True
        # If we got here - only bots, or empty game
        # Kill the game loop
        task = game['Task']
        task.cancel()
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
                await self.bot.send_typing(member['User'])
            await asyncio.sleep(typeTime)
        else:
            for member in game['Members']:
                if member['IsBot']:
                    continue
                # Show that we're typing
                await self.bot.send_typing(member['User'])
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
        if bot['Laid'] == False:
            newSubmission = { 'By': bot, 'Cards': cards }
            game['Submitted'].append(newSubmission)
            # Shuffle cards
            shuffle(game['Submitted'])
            bot['Laid'] = True
            game['Time'] = currentTime = int(time.time())
            await self.checkSubmissions(ctx, game)
    

    async def botPickWin(self, ctx, game):
        totalUsers = len(game['Members'])-1
        submitted  = len(game['Submitted'])
        if submitted >= totalUsers:
            # Judge is a bot - and all cards are in!
            await self.typing(game)
            # Pick a winner
            winner = random.randint(0, totalUsers-2)
            await self.winningCard(ctx, game, winner)


    async def checkSubmissions(self, ctx, game):
        totalUsers = len(game['Members'])-1
        submitted  = len(game['Submitted'])
        for member in game['Members']:
            if member['IsBot'] == True:
                continue
            if submitted < totalUsers:
                msg = '{}/{} cards submitted...'.format(submitted, totalUsers)
                await self.bot.send_message(member['User'], msg)
            else:
                msg = 'All cards have been submitted!'
                # if 
                await self.bot.send_message(member['User'], msg)
                await self.showOptions(ctx, member['User'])

                # Check if a bot is the judge
                judge = game['Members'][game['Judge']]
                if not judge['IsBot']:
                    continue
                task = self.bot.loop.create_task(self.botPickWin(ctx, game))
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
                msg = 'The **Winning** card was:\n\n{}'.format('{}'.format(' - '.join(winner['Cards'])))
            else:
                msg = 'The **Winning** cards were:\n\n{}'.format('{}'.format(' - '.join(winner['Cards'])))
            await self.bot.send_message(member['User'], embed=stat_embed)
            await self.bot.send_message(member['User'], msg)

            # await self.nextPlay(ctx, game)
            
        # Start the game loop
        event = game['NextHand']
        self.bot.loop.call_soon_threadsafe(event.set)
        game['Time'] = currentTime = int(time.time())

    async def gameCheckLoop(self, ctx, game):
        task = game['NextHand']
        while True:
            # Clear the pending task
            task.clear()
            # Wait for a second before continuing
            await asyncio.sleep(1)
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
                    await self.bot.send_message(member['User'], message)
            else:
                # Not the judge
                await self.bot.send_message(member['User'], message)

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

        msg = '{} the judge.\n\n'.format(judge)
        msg += '__Black Card:__\n\n**{}**\n\n'.format(blackCard)
        
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
                msg += '\n\nPick a card with `{}lay [card number]`'.format(ctx.prefix)
            elif blackNum > 1:
                # Plural
                msg += '\n\nPick **{} cards** with `{}lay [card numbers separated by commas (1,2,3)]`'.format(blackNum, ctx.prefix)
        
        stat_embed.set_author(name='Current Play')
        stat_embed.set_footer(text='Cards Against Humanity - id: {}'.format(game['ID']))
        await self.bot.send_message(user, embed=stat_embed)
        await self.bot.send_message(user, msg)
        
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
            if member['ID'] == user.id:
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
        stat_embed.set_author(name='Your Hand - {}'.format(points))
        stat_embed.set_footer(text='Cards Against Humanity - id: {}'.format(game['ID']))
        await self.bot.send_message(user, embed=stat_embed)
        await self.bot.send_message(user, msg)
                            
    async def showOptions(self, ctx, user):
        # Shows the judgement options
        stat_embed = discord.Embed(color=discord.Color.orange())
        game = self.userGame(user)
        if not game:
            return
        # Add title
        stat_embed.set_author(name='JUDGEMENT TIME!!')
        stat_embed.set_footer(text='Cards Against Humanity - id: {}'.format(game['ID']))
        await self.bot.send_message(user, embed=stat_embed)

        if game['Members'][game['Judge']]['User'] == user:
            judge = '**YOU** are'
        else:
            if game['Members'][game['Judge']]['IsBot']:
                # Bot
                judge = '*{} ({})* is'.format(self.botName, game['Members'][game['Judge']]['ID'])
            else:
                judge = '*{}* is'.format(DisplayName.name(game['Members'][game['Judge']]['User']))
        blackCard = game['BlackCard']['Text']

        msg = '{} judging.\n\n'.format(judge)
        msg += '__Black Card:__\n\n**{}**\n\n'.format(blackCard)
        msg += '__Submitted White Cards:__\n\n'

        i = 0
        for sub in game['Submitted']:
            i+=1
            msg += '{}. {}\n'.format(i, ' - '.join(sub['Cards']))
        if judge == '**YOU** are':
            msg += '\nPick a winner with `{}pick [submission number]`.'.format(ctx.prefix)
        await self.bot.send_message(user, msg)
        
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
                await self.bot.send_message(user, 'Shuffling white cards...')
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
            # Assume it's a discord.Member/User
            user = user.id
        # fills the user's hand up to number of cards
        game = self.userGame(user)
        for member in game['Members']:
            if member['ID'] == user:
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
                await self.bot.send_message(user, 'Shuffling black cards...')
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
                await self.bot.send_message(member['User'], embed=stat_embed)
            return

        # Find if we have a winner
        winner = False
        stat_embed = discord.Embed(color=discord.Color.lighter_grey())
        for member in game['Members']:
            if member['IsBot']:
                # Clear pending tasks and set to None
                if not member['Task'] == None:
                    task = member['Task']
                    task.cancel()
                    asyncio.sleep(1)
                    member['Task'] = None
            if member['Points'] >= self.winAfter:
                # We have a winner!
                winner = True
                stat_embed.set_author(name='{} is the WINNER!!'.format(DisplayName.name(member['User'])))
                break
        if winner:
            for member in game['Members']:
                if not member['IsBot']:
                    await self.bot.send_message(member['User'], embed=stat_embed)
                # Reset all users
                member['Hand']  = []
                member['Points'] = 0
                member['Won']   = []
                member['Laid']  = False

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

        # Have the bots lay their cards
        for member in game['Members']:
            if not member['IsBot']:
                continue
            if member['ID'] == game['Members'][game['Judge']]['ID']:
                continue
            # Not a human player, and not the judge
            task = self.bot.loop.create_task(self.botPick(ctx, member, game))
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
            await self.bot.send_message(ctx.message.author, msg)
            return
        await self.showPlay(ctx, ctx.message.author)


    @commands.command(pass_context=True)
    async def say(self, ctx, *, message = None):
        """Broadcasts a message to the other players in your game."""
        if not await self.checkPM(ctx.message):
            return
        userGame = self.userGame(ctx.message.author)
        if not userGame:
            msg = "You're not in a game - you can create one with `{}newcah` or join one with `{}joincah`.".format(ctx.prefix, ctx.prefix)
            await self.bot.send_message(ctx.message.author, msg)
            return
        userGame['Time'] = currentTime = int(time.time())
        if message == None:
            msg = "Ooookay, you say *nothing...*"
            await self.bot.send_message(ctx.message.author, msg)
            return
        msg = '*{}* says: {}'.format(ctx.message.author.name, message)
        for member in userGame['Members']:
            if member['IsBot']:
                continue
            # Tell them all!!
            if not member['User'] == ctx.message.author:
                # Don't tell yourself
                await self.bot.send_message(member['User'], msg)
        await self.bot.send_message(ctx.message.author, 'Message sent!')
            
                
    @commands.command(pass_context=True)
    async def lay(self, ctx, *, card = None):
        """Lays a card or cards from your hand.  If multiple cards are needed, separate them by a comma (1,2,3)."""
        if not await self.checkPM(ctx.message):
            return
        userGame = self.userGame(ctx.message.author)
        if not userGame:
            msg = "You're not in a game - you can create one with `{}newcah` or join one with `{}joincah`.".format(ctx.prefix, ctx.prefix)
            await self.bot.send_message(ctx.message.author, msg)
            return
        userGame['Time'] = currentTime = int(time.time())
        for member in userGame['Members']:
            if member['User'] == ctx.message.author:
                user = member
                index = userGame['Members'].index(member)
                if index == userGame['Judge']:
                    await self.bot.send_message(ctx.message.author, "You're the judge.  You don't get to lay cards this round.")
                    return
        for submit in userGame['Submitted']:
            if submit['By']['User'] == ctx.message.author:
                await self.bot.send_message(ctx.message.author, "You already made your submission this round.")
                return
        if card == None:
            await self.bot.send_message(ctx.message.author, 'You need you input *something.*')
            return
        card = card.strip()
        card = card.replace(" ", "")
        # Not the judge
        if len(userGame['Members']) < self.minMembers:
            stat_embed = discord.Embed(color=discord.Color.red())
            stat_embed.set_author(name='Not enough players to continue! ({}/{})'.format(len(userGame['Members']), self.minMembers))
            stat_embed.set_footer(text='Have other users join with: {}joincah {}'.format(ctx.prefix, userGame['ID']))
            for member in userGame['Members']:
                if member['IsBot']:
                    continue
                await self.bot.send_message(member['User'], embed=stat_embed)
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
                msg = 'You need to pick **{} cards** (no duplicates) with `{}lay [card numbers separated by commas (1,2,3)]`\n\nYour hand is:'.format(numberCards, ctx.prefix)
                await self.bot.send_message(ctx.message.author, msg)
                await self.showHand(ctx, ctx.message.author)
                return
            # Got something
            # Check for duplicates
            if not len(card) == len(set(card)):
                msg = 'You need to pick **{} cards** (no duplicates) with `{}lay [card numbers separated by commas (1,2,3)]`\n\nYour hand is:'.format(numberCards, ctx.prefix)
                await self.bot.send_message(ctx.message.author, msg)
                await self.showHand(ctx, ctx.message.author)
                return
            # Works
            for c in card:
                try:
                    c = int(c)
                except Exception:
                    msg = 'You need to pick **{} cards** (no duplicates) with `{}lay [card numbers separated by commas (1,2,3)]`\n\nYour hand is:'.format(numberCards, ctx.prefix)
                    await self.bot.send_message(ctx.message.author, msg)
                    await self.showHand(ctx, ctx.message.author)
                    return

                if c-1 < 0 or c-1 > len(user['Hand'])-1:
                    msg = 'Card numbers must be between 1 and {}.\n\nYour hand is:'.format(len(user['Hand']))
                    await self.bot.send_message(ctx.message.author, msg)
                    await self.showHand(ctx, ctx.message.author)
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
                msg = 'You need to pick a valid card with `{}lay [card number]`\n\nYour hand is:'.format(ctx.prefix)
                await self.bot.send_message(ctx.message.author, msg)
                await self.showHand(ctx, ctx.message.author)
                return
            # Valid card
            newSubmission = { 'By': user, 'Cards': [ user['Hand'].pop(card-1)['Text'] ] }
        userGame['Submitted'].append(newSubmission)
        
        # Shuffle cards
        shuffle(userGame['Submitted'])

        user['Laid'] = True
        await self.bot.send_message(ctx.message.author, 'You submitted your {}!'.format(cardSpeak))
        await self.checkSubmissions(ctx, userGame)
            

    @commands.command(pass_context=True)
    async def pick(self, ctx, *, card = None):
        """As the judge - pick the winning card(s)."""
        if not await self.checkPM(ctx.message):
            return
        # Check if the user is already in game
        userGame = self.userGame(ctx.message.author)
        if not userGame:
            # Not in a game
            msg = "You're not in a game - you can create one with `{}newcah` or join one with `{}joincah`.".format(ctx.prefix, ctx.prefix)
            await self.bot.send_message(ctx.message.author, msg)
            return
        userGame['Time'] = currentTime = int(time.time())
        isJudge = False
        for member in userGame['Members']:
            if member['User'] == ctx.message.author:
                user = member
                index = userGame['Members'].index(member)
                if index == userGame['Judge']:
                    isJudge = True
        if not isJudge:
            msg = "You're not the judge - I guess you'll have to wait your turn.".format(ctx.prefix, ctx.prefix)
            await self.bot.send_message(ctx.message.author, msg)
            return
        # Am judge
        totalUsers = len(userGame['Members'])-1
        submitted  = len(userGame['Submitted'])
        if submitted < totalUsers:
            if totalUsers - submitted == 1:
                msg = "Still waiting on 1 card..."
            else:
                msg = "Still waiting on {} cards...".format(totalUsers-submitted)
            await self.bot.send_message(ctx.message.author, msg)
            return
        try:
            card = int(card)-1
        except Exception:
            card = -1
        if card < 0 or card >= totalUsers:
            msg = "Your pick must be between 1 and {}.".format(totalUsers)
            await self.bot.send_message(ctx.message.author, msg)
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
            await self.bot.send_message(ctx.message.author, msg)
            return
        await self.showHand(ctx, ctx.message.author)
        userGame['Time'] = currentTime = int(time.time())


    @commands.command(pass_context=True)
    async def newcah(self, ctx):
        """Starts a new Cards Against Humanity game."""
        #if not await self.checkPM(ctx.message):
            #return
        # Check if the user is already in game
        userGame = self.userGame(ctx.message.author)
        if userGame:
            # Already in a game
            msg = "You're already in a game (id: *{}*)\nType `{}leavecah` to leave that game.".format(userGame['ID'], ctx.prefix)
            await self.bot.send_message(ctx.message.channel, msg)
            return

        # Not in a game - create a new one
        gameID = self.randomID()
        currentTime = int(time.time())
        newGame = { 'ID': gameID, 'Members': [], 'Discard': [], 'BDiscard': [], 'Judge': -1, 'Time': currentTime, 'BlackCard': None, 'Submitted': [], 'NextHand': asyncio.Event() }
        member = { 'ID': ctx.message.author.id, 'User': ctx.message.author, 'Points': 0, 'Won': [], 'Hand': [], 'Laid': False, 'IsBot': False, 'Creator': True, 'Task': None }
        newGame['Members'].append(member)
        task = self.bot.loop.create_task(self.gameCheckLoop(ctx, newGame))
        newGame['Task'] = task
        self.games.append(newGame)
        # Tell the user they created a new game and list its ID
        await self.bot.send_message(ctx.message.channel, 'You created game id: *{}*'.format(gameID))
        await self.drawCards(ctx.message.author)
        # await self.showHand(ctx, ctx.message.author)
        # await self.nextPlay(ctx, newGame)
    

    @commands.command(pass_context=True)
    async def leavecah(self, ctx):        
        """Leaves the current game you're in."""
        removeCheck = await self.removeMember(ctx.message.author)
        if not removeCheck:
            msg = 'You are not in a game.'
            await self.bot.send_message(ctx.message.channel, msg)
            return
        if self.checkGame(removeCheck):
            # await self.nextPlay(ctx, removeCheck)
            
            # Start the game loop
            event = removeCheck['NextHand']
            self.bot.loop.call_soon_threadsafe(event.set)


    @commands.command(pass_context=True)
    async def joincah(self, ctx, *, id = None):
        """Join a Cards Against Humanity game.  If no id or user is passed, joins a random game."""
        #if not await self.checkPM(ctx.message):
            #return
        # Check if the user is already in game
        userGame = self.userGame(ctx.message.author)
        isCreator = False
        if userGame:
            # Already in a game
            msg = "You're already in a game (id: *{}*)\nType `{}leavecah` to leave that game.".format(userGame['ID'], ctx.prefix)
            await self.bot.send_message(ctx.message.channel, msg)
            return
        if len(self.games):
            if id:
                game = self.gameForID(id)
                if game == None:
                    # That id doesn't exist - or is possibly a user
                    # If user, has to be joined from server chat
                    if not ctx.message.server:
                        msg = "I couldn't find a game attached to that id.  If you are trying to join a user - run the `{}joincah [user]` command in a channel on a server you share with that user.".format(ctx.prefix)
                        await self.bot.send_message(ctx.message.channel, msg)
                        return
                    else:
                        # We have a server - let's try for a user
                        member = DisplayName.memberForName(id, ctx.message.server)
                        if not member:
                            # Couldn't find user!
                            msg = "I couldn't find a game attached to that id.  If you are trying to join a user - run the `{}joincah [user]` command in a channel on a server you share with that user.".format(ctx.prefix)
                            await self.bot.send_message(ctx.message.channel, msg)
                            return
                        # Have a user - check if they're in a game
                        game = self.userGame(member)
                        if not game:
                            # That user is NOT in a game!
                            msg = "That user doesn't appear to be playing."
                            await self.bot.send_message(ctx.message.channel, msg)
                            return
                                
            else:
                game = random.choice(self.games)
        else:
            # No games - create a new one
            gameID = self.randomID()
            game = { 'ID': gameID, 'Members': [], 'Discard': [], 'BDiscard': [], 'Judge': -1, 'Time': 0, 'BlackCard': None, 'Submitted': [], 'NextHand': asyncio.Event() }
            task = self.bot.loop.create_task(self.gameCheckLoop(ctx, game))
            game['Task'] = task
            self.games.append(game)
            # Tell the user they created a new game and list its ID
            await self.bot.send_message(ctx.message.channel, 'You created game id: *{}*'.format(gameID))
            isCreator = True

        # Tell everyone else you joined
        for member in game['Members']:
            if member['IsBot']:
                continue
            await self.bot.send_message(member['User'], '*{}* joined the game! Reorganizing...'.format(DisplayName.name(ctx.message.author)))
            
        # We got a user!
        member = { 'ID': ctx.message.author.id, 'User': ctx.message.author, 'Points': 0, 'Won': [], 'Hand': [], 'Laid': False, 'IsBot': False, 'Creator': isCreator, 'Task': None }
        game['Members'].append(member)
        await self.drawCards(ctx.message.author)
        if len(game['Members'])==1:
            # Just created the game
            await self.drawCards(ctx.message.author)
            # await self.showHand(ctx, ctx.message.author)
            # await self.nextPlay(ctx, game)
        else:
            msg = "You've joined game id: *{}!*\n\nThere are *{} users* in this game.".format(game['ID'], len(game['Members']))
            await self.bot.send_message(ctx.message.channel, msg)
            # await self.nextPlay(ctx, game)
            # Start the game loop
            event = game['NextHand']
            self.bot.loop.call_soon_threadsafe(event.set)

        game['Time'] = currentTime = int(time.time())


    @commands.command(pass_context=True)
    async def addbot(self, ctx):
        """Adds a bot to the game.  Can only be done by the player who created the game."""
        if not await self.checkPM(ctx.message):
            return
        # Check if the user is already in game
        userGame = self.userGame(ctx.message.author)
        if not userGame:
            # Not in a game
            msg = "You're not in a game - you can create one with `{}newcah` or join one with `{}joincah`.".format(ctx.prefix, ctx.prefix)
            await self.bot.send_message(ctx.message.author, msg)
            return
        botCount = 0
        for member in userGame['Members']:
            if member['IsBot']:
                botCount += 1
                continue
            if member['User'] == ctx.message.author:
                if not member['Creator']:
                    # You didn't make this game
                    msg = 'Only the player that created the game can add bots.'
                    await self.bot.send_message(ctx.message.author, msg)
                    return
        # We are the creator - let's check the number of bots
        if botCount >= self.maxBots:
            # Too many bots!
            msg = 'You already have enough bots (max is {}).'.format(self.maxBots)
            await self.bot.send_message(ctx.message.author, msg)
            return
        # We can get another bot!
        botID = self.randomBotID(userGame)
        lobot = { 'ID': botID, 'User': None, 'Points': 0, 'Won': [], 'Hand': [], 'Laid': False, 'IsBot': True, 'Creator': False, 'Task': None }
        userGame['Members'].append(lobot)
        await self.drawCards(lobot['ID'])
        msg = '*{} ({})* joined the game! Reorganizing...'.format(self.botName, botID)
        for member in userGame['Members']:
            if member['IsBot']:
                continue
            await self.bot.send_message(member['User'], msg)
        # await self.nextPlay(ctx, userGame)

        # Start the game loop
        event = userGame['NextHand']
        self.bot.loop.call_soon_threadsafe(event.set)


    @commands.command(pass_context=True)
    async def addbots(self, ctx, number = None):
        """Adds bots to the game.  Can only be done by the player who created the game."""
        if not await self.checkPM(ctx.message):
            return
        # Check if the user is already in game
        userGame = self.userGame(ctx.message.author)
        if not userGame:
            # Not in a game
            msg = "You're not in a game - you can create one with `{}newcah` or join one with `{}joincah`.".format(ctx.prefix, ctx.prefix)
            await self.bot.send_message(ctx.message.author, msg)
            return
        botCount = 0
        for member in userGame['Members']:
            if member['IsBot']:
                botCount += 1
                continue
            if member['User'] == ctx.message.author:
                if not member['Creator']:
                    # You didn't make this game
                    msg = 'Only the player that created the game can add bots.'
                    await self.bot.send_message(ctx.message.author, msg)
                    return
        if number == None:
            # No number specified - let's add the max number of bots
            number = self.maxBots - botCount

        try:
            number = int(number)
        except Exception:
            msg = 'Number of bots to add must be an integer.'
            await self.bot.send_message(ctx.message.author, msg)
            return

        # We are the creator - let's check the number of bots
        if botCount >= self.maxBots:
            # Too many bots!
            msg = 'You already have enough bots (max is {}).'.format(self.maxBots)
            await self.bot.send_message(ctx.message.author, msg)
            return

        if number > (self.maxBots - botCount):
            number = self.maxBots - botCount
        
        if number == 1:
            msg = 'Adding {} bot:\n\n'.format(number)
        else:
            msg = 'Adding {} bots:\n\n'.format(number)

        for i in range(0, number):
            # We can get another bot!
            botID = self.randomBotID(userGame)
            lobot = { 'ID': botID, 'User': None, 'Points': 0, 'Won': [], 'Hand': [], 'Laid': False, 'IsBot': True, 'Creator': False, 'Task': None }
            userGame['Members'].append(lobot)
            await self.drawCards(lobot['ID'])
            msg += '*{} ({})* joined the game!\n'.format(self.botName, botID)
            # await self.nextPlay(ctx, userGame)
        msg += 'Reorganizing...'
        
        for member in userGame['Members']:
            if member['IsBot']:
                continue
            await self.bot.send_message(member['User'], msg)

        # Start the game loop
        event = userGame['NextHand']
        self.bot.loop.call_soon_threadsafe(event.set)


    @commands.command(pass_context=True)
    async def removebot(self, ctx, *, id = None):
        """Removes a bot from the game.  Can only be done by the player who created the game."""
        if not await self.checkPM(ctx.message):
            return
        # Check if the user is already in game
        userGame = self.userGame(ctx.message.author)
        if not userGame:
            # Not in a game
            msg = "You're not in a game - you can create one with `{}newcah` or join one with `{}joincah`.".format(ctx.prefix, ctx.prefix)
            await self.bot.send_message(ctx.message.author, msg)
            return
        botCount = 0
        for member in userGame['Members']:
            if member['IsBot']:
                botCount += 1
                continue
            if member['User'] == ctx.message.author:
                if not member['Creator']:
                    # You didn't make this game
                    msg = 'Only the player that created the game can add bots.'
                    await self.bot.send_message(ctx.message.author, msg)
                    return
        # We are the creator - let's check the number of bots
        if id == None:
            # Just remove the first bot we find
            for member in userGame['Members']:
                if member['IsBot']:
                    await self.removeMember(member['ID'])
                    # Start the game loop
                    event = userGame['NextHand']
                    self.bot.loop.call_soon_threadsafe(event.set)
                    return
            msg = 'No bots to remove!'
            await self.bot.send_message(ctx.message.author, msg)
            return
        else:
            # Remove a bot by id
            if not await self.removeMember(id):
                # not found
                msg = 'I couldn\'t locate that bot on this game.'
                await self.bot.send_message(ctx.message.author, msg)
                return
        # await self.nextPlay(ctx, userGame)

        # Start the game loop
        event = userGame['NextHand']
        self.bot.loop.call_soon_threadsafe(event.set)


    @commands.command(pass_context=True)
    async def cahgames(self, ctx):
        """Displays up to 10 CAH games in progress."""
        shuffledGames = list(self.games)
        random.shuffle(shuffledGames)
        if not len(shuffledGames):
            await self.bot.send_message(ctx.message.channel, 'No games being played currently.')
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

        await self.bot.send_message(ctx.message.channel, msg)

            

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
            await self.bot.send_message(ctx.message.author, msg)
            return
        stat_embed = discord.Embed(color=discord.Color.purple())
        stat_embed.set_author(name='Current Score')
        stat_embed.set_footer(text='Cards Against Humanity - id: {}'.format(userGame['ID']))
        await self.bot.send_message(ctx.message.author, embed=stat_embed)
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
        await self.bot.send_message(ctx.message.author, msg)
