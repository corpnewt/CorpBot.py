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
        self.maxDeadTime = 3600 # Allow an hour of dead time before killing a game
        self.checkTime = 300 # 5 minutes between dead time checks
        self.winAfter = 10 # 10 wins for the game
        self.charset = "1234567890"
        if file == None:
            file = "deck.json"
        # Let's load our deck file
        # Can be found at http://www.crhallberg.com/cah/json
        if os.path.exists(file):
            f = open(file,'r')
            filedata = f.read()
            f.close()
            """#filedata = filedata.encode()
            filedata = self.cleanJson(filedata)
            f = open(file,'w', encoding='utf-16')
            f.write(filedata)
            f.close()"""

            self.deck = json.loads(filedata)
        else:
            # File doesn't exist - create a placeholder
            self.deck = {}
        self.bot.loop.create_task(self.checkDead())

    def cleanJson(self, json):
        json = html.unescape(json)
        #json = json.encode('utf-8', 'replace')
        json = json.replace('_','[blank]')
        json = json.replace('<br>','\n')
        json = json.replace('<i>', '*')
        json = json.replace('</i>', '*')
        return json


    async def checkDead(self):
        # Wait first - then check
        await asyncio.sleep(self.checkTime)
        for game in self.games:
            gameTime = game['Time']
            currentTime = int(time.time())
            timeRemain  = currentTime - gameTime
            if timeRemain > self.maxDeadTime:
                # Game is dead - quit it and alert members
                for member in game['Members']:
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

    def userGame(self, user):
        # Returns the game the user is currently in
        for game in self.games:
            for member in game['Members']:
                if member['User'] == user:
                    # Found our user
                    return game
        return None

    def gameForID(self, id):
        # Returns the game with the passed id
        for game in self.games:
            if game['ID'] == id:
                return game
        return None

    def removeMember(self, user, game = None):
        if game:
            for member in game['Members']:
                if member['User'] == user:
                    game['Members'].remove(member)
                    self.checkGame(game)
                    return game
            return None
        game = self.userGame(user)
        if game:
            for member in game['Members']:
                if member['User'] == user:
                    game['Members'].remove(member)
                    self.checkGame(game)
                    return game
        return None

    def checkGame(self, game):
        if not len(game['Members']):
            # Game is empty - remove it
            self.games.remove(game)

    ################################################
    
    async def showPlay(self, user):
        # Creates an embed and displays the current game stats
        stat_embed = discord.Embed(color=discord.Color.teal())
        game = self.userGame(user)
        if not game:
            return
        # add the game id
        stat_embed.set_author(name='Cards Against Humanity - id: {}'.format(game['ID']))
        # Get the judge's name
        if game['Members'][game['Judge']]['User'] == user:
            judge = '**YOU**'
        else:
            judge = DisplayName.name(game['Members'][game['Judge']]['User'])
        stat_embed.add_field(name="Judge", value=judge, inline=True)
        # Get the Black Card
        try:
            blackCard = '**{}**'.format(game['BlackCard']['Text'])
        except Exception:
            blackCard = 'None.'
        stat_embed.add_field(name="Black Card", value=blackCard, inline=True)
        await self.bot.send_message(user, embed=stat_embed)
        
    async def showHand(self, user):
        # Shows the user's hand in an embed
        stat_embed = discord.Embed(color=discord.Color.teal())
        game = self.userGame(user)
        if not game:
            return
        msg = ''
        stat_embed.set_author(name='{} - Hand'.format(DisplayName.name(user)))
        i = 0
        for member in game['Members']:
            if member['ID'] == user.id:
                # Got our user
                for card in member['Hand']:
                    i += 1
                    msg += '{}. {}\n'.format(i, card['Text'])
        stat_embed.add_field(name="Cards", value=msg, inline=True)
        await self.bot.send_message(user, embed=stat_embed)
                              
    async def showOptions(self, ctx, user):
        # Shows the judgement options
        stat_embed = discord.Embed(color=discord.Color.teal())
        game = self.userGame(user)
        if not game:
            return
        # Add title
        stat_embed.set_author(name='JUDGEMENT TIME!')
        if game['Members'][game['Judge']]['User'] == user:
            judge = '**YOU**'
        else:
            judge = DisplayName.name(game['Members'][game['Judge']]['User'])
        # Add Judge
        stat_embed.add_field(name="Judge", value=judge, inline=True)
        # Add black card
        stat_embed.add_field(name="Black Card", value='**{}**'.format(game['BlackCard']['Text']), inline=True)
        i = 0
        msg = ''
        for sub in game['Submitted']:
            i+=1
            msg += '{}. {}\n'.format(i, ' - '.join(sub['Cards']))
        stat_embed.add_field(name="Cards Submitted", value=msg, inline=True)
        await self.bot.send_message(user, embed=stat_embed)
        
    async def drawCard(self, game):
        # Draws a random unused card and shuffles the deck if needed
        totalDiscard = len(game['Discard'])
        for member in game['Members']:
            totalDiscard += len(member['Hand'])
        if totalDiscard >= len(self.deck['whiteCards']):
            # Tell everyone the cards were shuffled
            for member in game['Members']:
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
        # fills the user's hand up to number of cards
        game = self.userGame(user)
        for member in game['Members']:
            if member['ID'] == user.id:
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

    async def showHands(self, user):
        # Shows the user's hand
        game = self.userGame(user)
        msg = ''
        i = 0
        for member in game['Members']:
            if member['ID'] == user.id:
                for card in member['Hand']:
                    i += 1
                    msg += '{}. {}\n'.format(i, card['Text'])
        await self.bot.send_message(user, msg)


    async def showOption(self, ctx, user, isJudge = True):
        # Shows the judgement options
        game = self.userGame(user)
        msg = '**{}**\n\n'.format(game['BlackCard']['Text'])
        i = 0
        for sub in game['Submitted']:
            i+=1
            msg += '{}. {}\n'.format(i, ' - '.join(sub['Cards']))
        if isJudge:
            msg += '\nPick a winner with `{}pick [submission number]`.'.format(ctx.prefix)
        await self.bot.send_message(user, msg)

    async def nextPlay(self, ctx, game):
        # Advances the game
        if len(game['Members']) < 2:
            for member in game['Members']:
                await self.bot.send_message(member['User'], '**Not enough players to continue!**\n\nTo get other users into this game, have them PM me and type `{}joincah {}`'.format(ctx.prefix, game['ID']))
            return

        # Find if we have a winner
        msg = ''
        for member in game['Members']:
            if member['Points'] >= self.winAfter:
                # We have a winner!
                msg = "__***{}*** **is the WINNER!!__**".format(DisplayName.name(member['User']))
                break
        if not msg == '':
            for member in game['Members']:
                await self.bot.send_message(member['User'], msg)
                # Reset all users
                member['Hand']  = []
                member['Points'] = 0
                member['Won']   = []
                member['Laid']  = False

        # Clear submitted cards
        game['Submitted'] = []
        # We have enough members
        game['Judge']+=1
        # Reset the judge if out of bounds
        if game['Judge'] >= len(game['Members']):
            game['Judge'] = 0

        # Draw the next black card
        bCard = await self.drawBCard(game)

        # Find the judge
        for member in game['Members']:
            await self.drawCards(member['User'])
            index = game['Members'].index(member)
            if index == game['Judge']:
                thejudge = game['Members'][index]['User']

        # PM the new judge - that they're the judge
        # PM everyone else their name - and that they need to pick their cards
        for member in game['Members']:
            member['Laid'] = False
            index = game['Members'].index(member)
            if index == game['Judge']:
                msg = '**YOU** are the judge this round!\n\nWaiting for *{}/{}* cards...\n\n'.format(len(game['Members'])-1, len(game['Members'])-1)
                msg += 'Your black card is:\n\n**{}**\n\n'.format(bCard['Text'])
                await self.bot.send_message(member['User'], msg)
            else:
                if bCard['Pick'] == 1:
                    pickText = 'card'
                else:
                    pickText = 'cards'
                msg = '*{}* is the judge this round!\n\n'.format(DisplayName.name(thejudge))
                msg += 'Waiting for *{}/{}* cards...'.format(len(game['Members'])-1, len(game['Members'])-1)
                msg += 'The black card is:\n\n**{}**\n\n'.format(bCard['Text'])
                if bCard['Pick'] == 1:
                    msg += 'Pick a card with `{}lay [card number]`.\n\nYour hand is:'.format(ctx.prefix)
                else:
                    msg += 'Pick **{} cards** with `{}lay [card numbers separated by commas (1,2,3)]`\n\nYour hand is:'.format(bCard['Pick'], ctx.prefix)
                await self.bot.send_message(member['User'], msg)
                await self.showHand(member['User'])

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
        await self.showPlay(ctx.message.author)
                
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
            if submit['By'] == ctx.message.author:
                await self.bot.send_message(ctx.message.author, "You already made your submission this round.")
                return
        if card == None:
            await self.bot.send_message(ctx.message.author, 'You need you input *something.*')
            return
        card = card.strip()
        card = card.replace(" ", "")
        # Not the judge
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
                await self.showHand(ctx.message.author)
                return
            # Got something
            # Check for duplicates
            if not len(card) == len(set(card)):
                msg = 'You need to pick **{} cards** (no duplicates) with `{}lay [card numbers separated by commas (1,2,3)]`\n\nYour hand is:'.format(numberCards, ctx.prefix)
                await self.bot.send_message(ctx.message.author, msg)
                await self.showHand(ctx.message.author)
                return
            # Works
            for c in card:
                try:
                    c = int(c)
                except Exception:
                    msg = 'You need to pick **{} cards** (no duplicates) with `{}lay [card numbers separated by commas (1,2,3)]`\n\nYour hand is:'.format(numberCards, ctx.prefix)
                    await self.bot.send_message(ctx.message.author, msg)
                    await self.showHand(ctx.message.author)
                    return

                if c-1 < 0 or c-1 > len(user['Hand'])-1:
                    msg = 'Card numbers must be between 1 and {}.\n\nYour hand is:'.format(len(user['Hand']))
                    await self.bot.send_message(ctx.message.author, msg)
                    await self.showHand(ctx.message.author)
                    return
                cards.append(user['Hand'][c-1]['Text'])
            # Remove from user's hand
            card = sorted(card, key=lambda card:int(card), reverse=True)
            for c in card:
                user['Hand'].pop(int(c)-1)
            # Valid cards
            
            newSubmission = { 'By': ctx.message.author, 'Cards': cards }
        else:
            cardSpeak = "card"
            try:
                card = int(card)
            except Exception:
                msg = 'You need to pick a valid card with `{}lay [card number]`\n\nYour hand is:'.format(ctx.prefix)
                await self.bot.send_message(ctx.message.author, msg)
                await self.showHand(ctx.message.author)
                return
            # Valid card
            newSubmission = { 'By': ctx.message.author, 'Cards': [ user['Hand'].pop(card-1)['Text'] ] }
        userGame['Submitted'].append(newSubmission)
        
        # Shuffle cards
        shuffle(userGame['Submitted'])

        user['Laid'] = True
        
        for member in userGame['Members']:
            if member['User'] == ctx.message.author:
                await self.bot.send_message(ctx.message.author, 'You submitted your {}!'.format(cardSpeak))
            totalUsers = len(userGame['Members'])-1
            submitted  = len(userGame['Submitted'])
            if submitted < totalUsers:
                msg = 'Waiting for *{}/{}* cards...'.format(totalUsers-submitted, totalUsers)
                await self.bot.send_message(member['User'], msg)
            else:
                msg = 'All cards submitted!  Waiting on judgement!'
                await self.bot.send_message(member['User'], msg)
                index = userGame['Members'].index(member)
                if index == userGame['Judge']:
                    # Send judgement here
                    await self.bot.send_message(member['User'], '**JUDGEMENT TIME!**')
                    await self.showOptions(ctx, member['User'])
                else:
                    await self.showOptions(ctx, member['User'], False)


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
                msg = "Still waiting on *1* card..."
            else:
                msg = "Still waiting on *{}* cards...".format(totalUsers-submitted)
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
        winner = userGame['Submitted'][card]
        for member in userGame['Members']:
            index = userGame['Members'].index(member)
            if index == userGame['Judge']:
                msg = '**YOU** picked *{}\'s* card!'.format(DisplayName.name(winner['By']))
                await self.bot.send_message(member['User'], msg)
            elif member['User'] == winner['By']:
                msg = '**YOU** won!'
                await self.bot.send_message(member['User'], msg)
                member['Points'] += 1
                member['Won'].append(userGame['BlackCard']['Text'])
            else:
                msg = '*{}* won!'.format(DisplayName.name(winner['By']))
                await self.bot.send_message(member['User'], msg)
            if len(winner['Cards']) == 1:
                msg = 'The **Winning** card was:\n\n{}'.format('{}'.format(' - '.join(winner['Cards'])))
            else:
                msg = 'The **Winning** cards were:\n\n{}'.format('{}'.format(' - '.join(winner['Cards'])))
            await self.bot.send_message(member['User'], msg)
        await self.nextPlay(ctx, userGame)


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
        await self.showHand(ctx.message.author)
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
        newGame = { 'ID': gameID, 'Members': [], 'Discard': [], 'BDiscard': [], 'Judge': -1, 'Time': currentTime, 'BlackCard': None, 'Submitted': [] }
        member = { 'ID': ctx.message.author.id, 'User': ctx.message.author, 'Points': 0, 'Won': [], 'Hand': [], 'Laid': False }
        newGame['Members'].append(member)
        self.games.append(newGame)

        msg = "You've created game id: *{}!*".format(gameID, ctx.prefix, gameID)
        await self.bot.send_message(ctx.message.channel, msg)
        await self.drawCards(ctx.message.author)
        await self.bot.send_message(ctx.message.author, "Your hand is:")
        await self.showHand(ctx.message.author)
        await self.nextPlay(ctx, newGame)
    
    @commands.command(pass_context=True)
    async def leavecah(self, ctx):        
        """Leaves the current game you're in."""
        #if not await self.checkPM(ctx.message):
            #return
        game = self.userGame(ctx.message.author)
        removeCheck = self.removeMember(ctx.message.author)
        if removeCheck:
            # Was removed
            msg = 'You were removed from game id: *{}*.'.format(removeCheck['ID'])
        else:
            msg = 'You are not in a game.'
        await self.bot.send_message(ctx.message.channel, msg)
        # Respond to the rest of the group
        msg = '*{}* left the game - re-organizing...'.format(DisplayName.name(ctx.message.author))
        for member in game['Members']:
            await self.bot.send_message(member['User'], msg)
        await self.nextPlay(ctx, game)


    @commands.command(pass_context=True)
    async def joincah(self, ctx, *, id = None):
        """Join a Cards Against Humanity game.  If no id or user is passed, joins a random game."""
        #if not await self.checkPM(ctx.message):
            #return
        # Check if the user is already in game
        userGame = self.userGame(ctx.message.author)
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
            game = { 'ID': gameID, 'Members': [], 'Discard': [], 'BDiscard': [], 'Judge': -1, 'Time': 0, 'BlackCard': None, 'Submitted': [] }
            self.games.append(game)
            
        # We got a user!
        member = { 'ID': ctx.message.author.id, 'User': ctx.message.author, 'Points': 0, 'Won': [], 'Hand': [], 'Laid': False }
        game['Members'].append(member)
        await self.drawCards(ctx.message.author)
        if len(game['Members'])==1:
            msg = "You've joined game id: *{}!*\n\nThere is *{} user* in this game.".format(game['ID'], len(game['Members']))
            await self.bot.send_message(ctx.message.channel, msg)
            # Just created the game
            msg = "You've created game id: *{}!*".format(gameID, ctx.prefix, gameID)
            await self.bot.send_message(ctx.message.author, msg)
            await self.drawCards(ctx.message.author)
            await self.bot.send_message(ctx.message.author, "Your hand is:")
            await self.showHand(ctx.message.author)
            await self.nextPlay(ctx, game)
        elif len(game['Members'])==2:
            msg = "You've joined game id: *{}!*\n\nThere are *{} users* in this game.".format(game['ID'], len(game['Members']))
            await self.bot.send_message(ctx.message.channel, msg)
            # We just got a 2nd member - let's advance
            await self.nextPlay(ctx, game)
        else:
            msg = "You've joined game id: *{}!*\n\nThere are *{} users* in this game.".format(game['ID'], len(game['Members']))
            await self.bot.send_message(ctx.message.channel, msg)
            totalUsers = len(game['Members'])-1
            submitted  = len(game['Submitted'])
            if submitted < totalUsers:
                msg = '*{}* joined the game!\n\nWaiting for *{}/{}* cards...'.format(DisplayName.name(ctx.message.author), totalUsers-submitted, totalUsers)
                for member in game['Members']:
                    if member['User']==ctx.message.author:
                        if game['BlackCard']['Pick'] == 1:
                            msg += ' The black card is:\n\nPick a card with `{}lay [card number]`.\n\n**{}**\n\nYour hand is'.format(ctx.prefix, game['BlackCard']['Text'])
                        else:
                            msg += ' The black card is:\n\nPick **{} cards** with `{}lay [card numbers separated by commas (1,2,3)]`.\n\n**{}**\n\nYour hand is'.format(game['BlackCard']['Pick'], ctx.prefix, game['BlackCard']['Text'])
                        await self.bot.send_message(member['User'], msg)
                        await self.showHand(ctx.message.author)
                    else:
                        await self.bot.send_message(member['User'], msg)
        game['Time'] = currentTime = int(time.time())

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
        stat_embed = discord.Embed(color=discord.Color.teal())
        stat_embed.set_author(name='Current Score')
        users = sorted(userGame['Members'], key=lambda card:int(card['Points']), reverse=True)
        msg = ''
        i = 0
        if len(users) > 10:
            msg = '1-10 of {} Users:\n\n'.format(len(users))
        else:
            msg = '1-{} Users:\n\n'.format(len(users))
        for user in users:
            i += 1
            if i > 10:
                break
            if user['Points'] == 1:
                msg += '{}. *{}* - {} point\n'.format(i, DisplayName.name(user['User']), user['Points'])
            else:
                msg += '{}. *{}* - {} points\n'.format(i, DisplayName.name(user['User']), user['Points'])
        stat_embed.add_field(name="Players", value=msg, inline=True)
        await self.bot.send_message(user, embed=stat_embed)
