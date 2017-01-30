import asyncio
import discord
from   datetime    import datetime
from   discord.ext import commands
from   shutil      import copyfile
import time
import json
import os
import re
from   Cogs        import DisplayName
from   Cogs        import Nullify

class Welcome:

    def __init__(self, bot, settings):
        self.bot = bot
        self.settings = settings
        self.regexUserName = re.compile(r"\[\[[user]+\]\]", re.IGNORECASE)
        self.regexUserPing = re.compile(r"\[\[[atuser]+\]\]", re.IGNORECASE)
        self.regexServer   = re.compile(r"\[\[[server]+\]\]", re.IGNORECASE)

    async def onjoin(self, member, server):
        # Welcome
        welcomeChannel = self.settings.getServerStat(server, "WelcomeChannel")
        if welcomeChannel:
            for channel in server.channels:
                if channel.id == welcomeChannel:
                    welcomeChannel = channel
                    break
        if welcomeChannel:
            await self._welcome(member, server, welcomeChannel)
        else:
            await self._welcome(member, server)

    async def onleave(self, member, server):
        # Goodbye
        welcomeChannel = self.settings.getServerStat(server, "WelcomeChannel")
        if welcomeChannel:
            for channel in server.channels:
                if channel.id == welcomeChannel:
                    welcomeChannel = channel
                    break
        if welcomeChannel:
            await self._goodbye(member, server, welcomeChannel)
        else:
            await self._goodbye(member, server)

    @commands.command(pass_context=True)
    async def setwelcome(self, ctx, *, message = None):
        """Sets the welcome message for your server (bot-admin only). [[user]] = user name, [[atuser]] = user mention, [[server]] = server name"""

        isAdmin = ctx.message.author.permissions_in(ctx.message.channel).administrator
        if not isAdmin:
            checkAdmin = self.settings.getServerStat(ctx.message.server, "AdminArray")
            for role in ctx.message.author.roles:
                for aRole in checkAdmin:
                    # Get the role that corresponds to the id
                    if aRole['ID'] == role.id:
                        isAdmin = True
        # Only allow admins to change server stats
        if not isAdmin:
            await self.bot.send_message(ctx.message.channel, 'You do not have sufficient privileges to access this command.')
            return

        if message == None:
            self.settings.setServerStat(ctx.message.server, "Welcome", None)
            await self.bot.send_message(ctx.message.channel, 'Welcome message removed!')
            return

        self.settings.setServerStat(ctx.message.server, "Welcome", message)
        await self.bot.send_message(ctx.message.channel, 'Welcome message updated!\n\nHere\'s a preview:')
        await self._welcome(ctx.message.author, ctx.message.server, ctx.message.channel)

    @commands.command(pass_context=True)
    async def testwelcome(self, ctx, *, member = None):
        """Prints the current welcome message (bot-admin only)."""

        # Check if we're suppressing @here and @everyone mentions
        if self.settings.getServerStat(ctx.message.server, "SuppressMentions").lower() == "yes":
            suppress = True
        else:
            suppress = False

        isAdmin = ctx.message.author.permissions_in(ctx.message.channel).administrator
        if not isAdmin:
            checkAdmin = self.settings.getServerStat(ctx.message.server, "AdminArray")
            for role in ctx.message.author.roles:
                for aRole in checkAdmin:
                    # Get the role that corresponds to the id
                    if aRole['ID'] == role.id:
                        isAdmin = True

        # Only allow admins to change server stats
        if not isAdmin:
            await self.bot.send_message(ctx.message.channel, 'You do not have sufficient privileges to access this command.')
            return

        if member == None:
            member = ctx.message.author
        if type(member) is str:
            memberName = member
            member = DisplayName.memberForName(memberName, ctx.message.server)
            if not member:
                msg = 'I couldn\'t find *{}*...'.format(memberName)
                # Check for suppress
                if suppress:
                    msg = Nullify.clean(msg)
                await self.bot.send_message(ctx.message.channel, msg)
                return
        # Here we have found a member, and stuff.
        # Let's make sure we have a message
        message = self.settings.getServerStat(ctx.message.server, "Welcome")
        if message == None:
            await self.bot.send_message(ctx.message.channel, 'Welcome message not setup.  You can do so with the `{}setwelcome [message]` command.'.format(ctx.prefix))
            return
        await self._welcome(member, ctx.message.server, ctx.message.channel)
        # Print the welcome channel
        welcomeChannel = self.settings.getServerStat(ctx.message.server, "WelcomeChannel")
        if welcomeChannel:
            for channel in ctx.message.server.channels:
                if channel.id == welcomeChannel:
                    welcomeChannel = channel
                    break
        if welcomeChannel:
            msg = 'The current welcome channel is **{}**.'.format(welcomeChannel.name)
        else:
            msg = 'The current welcome channel is the server\'s default channel (**{}**).'.format(ctx.message.server.default_channel.name)
        await self.bot.send_message(ctx.message.channel, msg)


    @commands.command(pass_context=True)
    async def setgoodbye(self, ctx, *, message = None):
        """Sets the goodbye message for your server (bot-admin only). [[user]] = user name, [[atuser]] = user mention, [[server]] = server name"""

        isAdmin = ctx.message.author.permissions_in(ctx.message.channel).administrator
        if not isAdmin:
            checkAdmin = self.settings.getServerStat(ctx.message.server, "AdminArray")
            for role in ctx.message.author.roles:
                for aRole in checkAdmin:
                    # Get the role that corresponds to the id
                    if aRole['ID'] == role.id:
                        isAdmin = True
        # Only allow admins to change server stats
        if not isAdmin:
            await self.bot.send_message(ctx.message.channel, 'You do not have sufficient privileges to access this command.')
            return

        if message == None:
            self.settings.setServerStat(ctx.message.server, "Goodbye", None)
            await self.bot.send_message(ctx.message.channel, 'Goodbye message removed!')
            return

        self.settings.setServerStat(ctx.message.server, "Goodbye", message)
        await self.bot.send_message(ctx.message.channel, 'Goodbye message updated!\n\nHere\'s a preview:')
        await self._goodbye(ctx.message.author, ctx.message.server, ctx.message.channel)


    @commands.command(pass_context=True)
    async def testgoodbye(self, ctx, *, member = None):
        """Prints the current goodbye message (bot-admin only)."""

        # Check if we're suppressing @here and @everyone mentions
        if self.settings.getServerStat(ctx.message.server, "SuppressMentions").lower() == "yes":
            suppress = True
        else:
            suppress = False

        isAdmin = ctx.message.author.permissions_in(ctx.message.channel).administrator
        if not isAdmin:
            checkAdmin = self.settings.getServerStat(ctx.message.server, "AdminArray")
            for role in ctx.message.author.roles:
                for aRole in checkAdmin:
                    # Get the role that corresponds to the id
                    if aRole['ID'] == role.id:
                        isAdmin = True

        # Only allow admins to change server stats
        if not isAdmin:
            await self.bot.send_message(ctx.message.channel, 'You do not have sufficient privileges to access this command.')
            return

        if member == None:
            member = ctx.message.author
        if type(member) is str:
            memberName = member
            member = DisplayName.memberForName(memberName, ctx.message.server)
            if not member:
                msg = 'I couldn\'t find *{}*...'.format(memberName)
                # Check for suppress
                if suppress:
                    msg = Nullify.clean(msg)
                await self.bot.send_message(ctx.message.channel, msg)
                return
        # Here we have found a member, and stuff.
        # Let's make sure we have a message
        message = self.settings.getServerStat(ctx.message.server, "Goodbye")
        if message == None:
            await self.bot.send_message(ctx.message.channel, 'Goodbye message not setup.  You can do so with the `{}setgoodbye [message]` command.'.format(ctx.prefix))
            return
        await self._goodbye(member, ctx.message.server, ctx.message.channel)
        
        # Print the goodbye channel
        welcomeChannel = self.settings.getServerStat(ctx.message.server, "WelcomeChannel")
        if welcomeChannel:
            for channel in ctx.message.server.channels:
                if channel.id == welcomeChannel:
                    welcomeChannel = channel
                    break
        if welcomeChannel:
            msg = 'The current goodbye channel is **{}**.'.format(welcomeChannel.name)
        else:
            msg = 'The current goodbye channel is the server\'s default channel (**{}**).'.format(ctx.message.server.default_channel.name)
        await self.bot.send_message(ctx.message.channel, msg)


    async def _welcome(self, member, server, channel = None):
        # Check if we're suppressing @here and @everyone mentions
        if self.settings.getServerStat(server, "SuppressMentions").lower() == "yes":
            suppress = True
        else:
            suppress = False
        message = self.settings.getServerStat(server, "Welcome")
        if message == None:
            return
        # Let's regex and replace [[user]] [[atuser]] and [[server]]
        message = re.sub(self.regexUserName, "{}".format(DisplayName.name(member)), message)
        message = re.sub(self.regexUserPing, "{}".format(member.mention), message)
        message = re.sub(self.regexServer,   "{}".format(server.name), message)

        if suppress:
            message = Nullify.clean(message)
        if channel:
            await self.bot.send_message(channel, message)
        else:
            await self.bot.send_message(server.default_channel, message)


    async def _goodbye(self, member, server, channel = None):
        # Check if we're suppressing @here and @everyone mentions
        if self.settings.getServerStat(server, "SuppressMentions").lower() == "yes":
            suppress = True
        else:
            suppress = False
        message = self.settings.getServerStat(server, "Goodbye")
        if message == None:
            return
        # Let's regex and replace [[user]] [[atuser]] and [[server]]
        message = re.sub(self.regexUserName, "{}".format(DisplayName.name(member)), message)
        message = re.sub(self.regexUserPing, "{}".format(member.mention), message)
        message = re.sub(self.regexServer,   "{}".format(server.name), message)

        if suppress:
            message = Nullify.clean(message)
        if channel:
            await self.bot.send_message(channel, message)
        else:
            await self.bot.send_message(server.default_channel, message)

    @commands.command(pass_context=True)
    async def setwelcomechannel(self, ctx, *, channel : discord.Channel = None):
        """Sets the channel for the welcome and goodbye messages (bot-admin only)."""

        isAdmin = ctx.message.author.permissions_in(ctx.message.channel).administrator
        if not isAdmin:
            checkAdmin = self.settings.getServerStat(ctx.message.server, "AdminArray")
            for role in ctx.message.author.roles:
                for aRole in checkAdmin:
                    # Get the role that corresponds to the id
                    if aRole['ID'] == role.id:
                        isAdmin = True

        # Only allow admins to change server stats
        if not isAdmin:
            await self.bot.send_message(ctx.message.channel, 'You do not have sufficient privileges to access this command.')
            return

        if channel == None:
            self.settings.setServerStat(ctx.message.server, "WelcomeChannel", "")
            msg = 'Welcome and goodbye messages will be displayed in the default channel (**{}**).'.format(ctx.message.server.default_channel.name)
            await self.bot.send_message(ctx.message.channel, msg)
            return

        if type(channel) is str:
            try:
                role = discord.utils.get(message.server.channels, name=role)
            except:
                print("That channel does not exist")
                return

        # If we made it this far - then we can add it
        self.settings.setServerStat(ctx.message.server, "WelcomeChannel", channel.id)

        msg = 'Welcome and goodbye messages will be displayed in **{}**.'.format(channel.name)
        await self.bot.send_message(ctx.message.channel, msg)


    @setwelcomechannel.error
    async def setwelcomechannel_error(self, ctx, error):
        # do stuff
        msg = 'setwelcomechannel Error: {}'.format(ctx)
        await self.bot.say(msg)
