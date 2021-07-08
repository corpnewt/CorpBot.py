import asyncio
import discord
import re
import os
import random
import string
from discord.ext import commands
from Cogs import Settings, DisplayName, Utils


def setup(bot):
    # Add the bot and deps
    settings = bot.get_cog("Settings")
    bot.add_cog(MadLibs(bot, settings))


class MadLibs(commands.Cog):

    # Init with the bot reference, and a reference to the settings var
    def __init__(self, bot, settings):
        self.bot = bot
        self.settings = settings
        # Setup/compile our regex
        self.regex = re.compile(r"\[\[[^\[\]]+\]\]")
        #self.botPrefix = "$"
        self.prefix = "ml"
        self.leavePrefix = "mleave"
        self.playing_madlibs = {}
        global Utils, DisplayName
        Utils = self.bot.get_cog("Utils")
        DisplayName = self.bot.get_cog("DisplayName")

    @commands.command()
    async def ml(self, ctx, word=None):
        """Used to choose your words when in the middle of a madlibs."""
        pass

    @commands.command(pass_context=True)
    async def madlibs(self, ctx):
        """Let's play MadLibs!"""

        channel = ctx.message.channel
        author = ctx.message.author
        server = ctx.message.guild

        # Check if we're suppressing @here and @everyone mentions
        if self.settings.getServerStat(ctx.message.guild, "SuppressMentions"):
            suppress = True
        else:
            suppress = False

        # Check if we have a MadLibs channel - and if so, restrict to that
        channelID = self.settings.getServerStat(server, "MadLibsChannel")
        if not (not channelID or channelID == ""):
            # We need the channel id
            if not str(channelID) == str(channel.id):
                msg = 'This isn\'t the channel for that...'
                for chan in server.channels:
                    if str(chan.id) == str(channelID):
                        msg = 'This isn\'t the channel for that.  Take the MadLibs to the **{}** channel.'.format(
                            chan.name)
                await channel.send(msg)
                return

        # Check if our folder exists
        if not os.path.isdir("./Cogs/MadLibs"):
            msg = 'I\'m not configured for MadLibs yet...'
            await channel.send(msg)
            return

        # Folder exists - let's see if it has any files
        choices = []  # Empty array
        for file in os.listdir("./Cogs/MadLibs"):
            if file.endswith(".txt"):
                choices.append(file)

        if len(choices) == 0:
            # No madlibs...
            msg = 'I\'m not configured for MadLibs yet...'
            await channel.send(msg)
            return

        # Check if we're already in a game
        if self.playing_madlibs.get(str(server.id), False):
            msg = 'I\'m already playing MadLibs - use `{}{} [your word]` to submit answers.'.format(
                ctx.prefix, self.prefix)
            await channel.send(msg)
            return

        self.playing_madlibs[str(server.id)] = True

        # Get a random madlib from those available
        randnum = random.randint(0, (len(choices)-1))
        randLib = choices[randnum]

        # Let's load our text and get to work
        with open("./Cogs/MadLibs/{}".format(randLib), 'rb') as myfile:
            data = myfile.read().decode("utf-8")

        # Set up an empty arry
        words = []

        # Match
        matches = re.finditer(self.regex, data)

        # Iterate matches
        for match in matches:
            words.append(match.group(0))

        # Create empty substitution array
        subs = []

        # Iterate words and ask for input
        i = 0
        while i < len(words):
            # Ask for the next word
            vowels = "aeiou"
            word = words[i][2:-2]
            if word[:1].lower() in vowels:
                msg = "I need an **{}** (word *{}/{}*).  `{}{} [your word]`".format(
                    words[i][2:-2], str(i+1), str(len(words)), ctx.prefix, self.prefix)
            else:
                msg = "I need a **{}** (word *{}/{}*).  `{}{} [your word]`".format(
                    words[i][2:-2], str(i+1), str(len(words)), ctx.prefix, self.prefix)
            await channel.send(msg)

            # Setup the check
            def check(msg):
                return msg.content.startswith("{}{}".format(ctx.prefix, self.prefix)) and msg.channel == channel

            # Wait for a response
            try:
                talk = await self.bot.wait_for('message', check=check, timeout=60)
            except Exception:
                talk = None

            if not talk:
                # We timed out - leave the loop
                msg = "*{}*, I'm done waiting... we'll play another time.".format(
                    DisplayName.name(author))
                await channel.send(msg)
                self.playing_madlibs.pop(str(server.id), None)
                return

            # Check if the message is to leave
            if talk.content.lower().startswith('{}{}'.format(ctx.prefix, self.leavePrefix.lower())):
                if talk.author is author:
                    msg = "Alright, *{}*.  We'll play another time.".format(
                        DisplayName.name(author))
                    await channel.send(msg)
                    self.playing_madlibs.pop(str(server.id), None)
                    return
                else:
                    # Not the originator
                    msg = "Only the originator (*{}*) can leave the MadLibs.".format(
                        DisplayName.name(author))
                    await channel.send(msg)
                    continue

            # We got a relevant message
            word = talk.content
            # Let's remove the $ml prefix (with or without space)
            if word.startswith('{}{} '.format(ctx.prefix.lower(), self.prefix.lower())):
                word = word[len(ctx.prefix)+len(self.prefix)+1:]
            if word.startswith('{}{}'.format(ctx.prefix.lower(), self.prefix.lower())):
                word = word[len(ctx.prefix)+len(self.prefix):]

            # Check capitalization
            if words[i][:3].isupper():
                # Capitalized
                word = string.capwords(word)

            # Add to our list
            subs.append(word)
            # Increment our index
            i += 1

        # Let's replace
        for asub in subs:
            # Only replace the first occurence
            data = re.sub(self.regex, "**{}**".format(asub), data, 1)

        self.playing_madlibs.pop(str(server.id), None)

        data = Utils.suppressed(ctx, data)
        # Message the output
        await channel.send(data)

    @madlibs.error
    async def madlibs_error(self, ctx, error):
        # Reset playing status and display error
        self.playing_madlibs.pop(str(error.guild.id), None)
        msg = 'madlibs Error: {}'.format(ctx)
        await error.send(msg)
