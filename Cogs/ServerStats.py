import asyncio
import discord
from   datetime    import datetime
from   operator    import itemgetter
from   discord.ext import commands
from   Cogs        import Nullify
from   Cogs        import DisplayName

class ServerStats:

    def __init__(self, bot, settings):
        self.bot = bot
        self.settings = settings

    async def message(self, message):
        # Check the message and see if we should allow it - always yes.
        # This module doesn't need to cancel messages.

        # Don't count your own, Pooter
        if not message.author.id == self.bot.user.id:
            server = message.server
            messages = int(self.settings.getServerStat(server, "TotalMessages"))
            if messages == None:
                messages = 0
            messages += 1
            self.settings.setServerStat(server, "TotalMessages", messages)
            
        return { 'Ignore' : False, 'Delete' : False}

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
    async def topservers(self, ctx, number : int = 10):
        """Lists the top servers I'm connected to ordered by population - default is 10, max is 50."""
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
        serverList = []
        for server in self.bot.servers:
            memberCount = 0
            for member in server.members:
                memberCount += 1
            serverList.append({ 'Name' : server.name, 'Users' : memberCount })

        # sort the servers by population
        serverList = sorted(serverList, key=lambda x:int(x['Users']), reverse=True)

        if number > len(serverList):
            number = len(serverList)

        i = 1
        msg = ''
        for server in serverList:
            if i > number:
                break
            msg += '{}. *{}* - *{}* members\n'.format(i, server['Name'], server['Users'])
            i += 1

        if number < len(serverList):
            msg = '__**Top {} of {} Servers:**__\n\n'.format(number, len(serverList))+msg
        else:
            msg = '__**Top {} Servers:**__\n\n'.format(len(serverList))+msg
        # Check for suppress
        if suppress:
            msg = Nullify.clean(msg)
        await self.bot.send_message(ctx.message.channel, msg)

    @commands.command(pass_context=True)
    async def bottomservers(self, ctx, number : int = 10):
        """Lists the bottom servers I'm connected to ordered by population - default is 10, max is 50."""
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
        serverList = []
        for server in self.bot.servers:
            serverList.append({ 'Name' : server.name, 'Users' : len(server.members) })

        # sort the servers by population
        serverList = sorted(serverList, key=lambda x:int(x['Users']))

        if number > len(serverList):
            number = len(serverList)

        i = 1
        msg = ''
        for server in serverList:
            if i > number:
                break
            msg += '{}. *{}* - *{}* members\n'.format(i, server['Name'], server['Users'])
            i += 1

        if number < len(serverList):
            msg = '__**Bottom {} of {} Servers:**__\n\n'.format(number, len(serverList))+msg
        else:
            msg = '__**Bottom {} Servers:**__\n\n'.format(len(serverList))+msg
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
            userCount += len(server.members)
        await self.bot.send_message(ctx.message.channel, 'There are *{} users* on the *{} servers* I am currently a part of!'.format(userCount, serverCount))

    
    @commands.command(pass_context=True)
    async def firstjoins(self, ctx, number : int = 10):
        """Lists the most recent users to join - default is 10, max is 25."""
        # Check if we're suppressing @here and @everyone mentions
        if self.settings.getServerStat(ctx.message.server, "SuppressMentions").lower() == "yes":
            suppress = True
        else:
            suppress = False

        if number > 25:
            number = 25
        if number < 1:
            await self.bot.send_message(ctx.message.channel, 'Oookay - look!  No users!  Just like you wanted!')
            return

        joinedList = []
        for member in ctx.message.server.members:
            joinedList.append({ 'ID' : member.id, 'Joined' : member.joined_at })
        
        # sort the users by join date
        joinedList = sorted(joinedList, key=lambda x:x['Joined'])

        i = 1
        msg = ''
        for member in joinedList:
            if i > number:
                break
            msg += '{}. *{}* - *{}*\n'.format(i, DisplayName.name(DisplayName.memberForID(member['ID'], ctx.message.server)), member['Joined'].strftime("%Y-%m-%d %I:%M %p"))
            i += 1
        
        if number < len(joinedList):
            msg = '__**First {} of {} Members to Join:**__\n\n'.format(number, len(joinedList))+msg
        else:
            msg = '__**First {} Members to Join:**__\n\n'.format(len(joinedList))+msg

        # Check for suppress
        if suppress:
            msg = Nullify.clean(msg)
        await self.bot.send_message(ctx.message.channel, msg)

    @commands.command(pass_context=True)
    async def recentjoins(self, ctx, number : int = 10):
        """Lists the most recent users to join - default is 10, max is 25."""
        # Check if we're suppressing @here and @everyone mentions
        if self.settings.getServerStat(ctx.message.server, "SuppressMentions").lower() == "yes":
            suppress = True
        else:
            suppress = False

        if number > 25:
            number = 25
        if number < 1:
            await self.bot.send_message(ctx.message.channel, 'Oookay - look!  No users!  Just like you wanted!')
            return

        joinedList = []
        for member in ctx.message.server.members:
            joinedList.append({ 'ID' : member.id, 'Joined' : member.joined_at })
        
        # sort the users by join date
        joinedList = sorted(joinedList, key=lambda x:x['Joined'], reverse=True)

        i = 1
        msg = ''
        for member in joinedList:
            if i > number:
                break
            msg += '{}. *{}* - *{}*\n'.format(i, DisplayName.name(DisplayName.memberForID(member['ID'], ctx.message.server)), member['Joined'].strftime("%Y-%m-%d %I:%M %p"))
            i += 1
        
        if number < len(joinedList):
            msg = '__**Last {} of {} Members to Join:**__\n\n'.format(number, len(joinedList))+msg
        else:
            msg = '__**Last {} Members to Join:**__\n\n'.format(len(joinedList))+msg

        # Check for suppress
        if suppress:
            msg = Nullify.clean(msg)
        await self.bot.send_message(ctx.message.channel, msg)

    @commands.command(pass_context=True)
    async def messages(self, ctx):
        """Lists the number of messages I've seen on this sever so far. (only applies after this module's inception, and if I'm online)"""
        messages = int(self.settings.getServerStat(ctx.message.server, "TotalMessages"))
        messages -= 1
        self.settings.setServerStat(ctx.message.server, "TotalMessages", messages)
        if messages == None:
            messages = 0
        if messages == 1:
            await self.bot.send_message(ctx.message.channel, 'So far, I\'ve witnessed *{} message!*.'.format(messages))
        else:
            await self.bot.send_message(ctx.message.channel, 'So far, I\'ve witnessed *{} messages!*.'.format(messages))