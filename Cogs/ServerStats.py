import asyncio
import discord
from   discord.ext import commands
from   Cogs        import Nullify

class ServerStats:

    def __init__(self, bot, settings):
        self.bot = bot
        self.settings = settings

    @commands.command(pass_context=True)
    async def listservers(self, ctx, number : int = 10):
        """Lists the servers I'm connected to - default is 10, max is 50."""

        # Check if we're suppressing @here and @everyone mentions
        if self.settings.getServerStat(ctx.message.server, "SuppressMentions").lower() == "yes":
            suppress = True
        else:
            suppress = False

        if number > 50:
            number = 50
        if number < 1:
            await self.bot.send_message(ctx.message.channel, 'Oookay - look!  No servers!  Just like you wanted!')
            return
        i = 1
        msg = '__**Servers I\'m On:**__\n\n'
        for server in self.bot.servers:
            if i > number:
                break
            msg += '{}. *{}*\n'.format(i, server.name)
            i += 1
        # Check for suppress
        if suppress:
            msg = Nullify.clean(msg)
        await self.bot.send_message(ctx.message.channel, msg)
    
    @commands.command(pass_context=True)
    async def users(self, ctx):
        """Lists the total number of users on all servers I'm connected to."""
        userCount = 0
        serverCount = 0
        for server in self.bot.servers:
            serverCount += 1
            for member in server.members:
                userCount += 1
        await self.bot.send_message(ctx.message.channel, 'There are *{} users* on the *{} servers* I am currently a part of!'.format(userCount, serverCount))

    