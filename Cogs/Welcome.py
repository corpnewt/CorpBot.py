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

def setup(bot):
	# Add the bot and deps
	settings = bot.get_cog("Settings")
	bot.add_cog(Welcome(bot, settings))

class Welcome:

    def __init__(self, bot, settings):
        self.bot = bot
        self.settings = settings
        self.regexUserName = re.compile(r"\[\[[user]+\]\]", re.IGNORECASE)
        self.regexUserPing = re.compile(r"\[\[[atuser]+\]\]", re.IGNORECASE)
        self.regexServer   = re.compile(r"\[\[[server]+\]\]", re.IGNORECASE)
        self.regexCount    = re.compile(r"\[\[[count]+\]\]", re.IGNORECASE)
        self.regexPlace    = re.compile(r"\[\[[place]+\]\]", re.IGNORECASE)
        self.regexOnline   = re.compile(r"\[\[[online]+\]\]", re.IGNORECASE)

    def suppressed(self, guild, msg):
        # Check if we're suppressing @here and @everyone mentions
        if self.settings.getServerStat(guild, "SuppressMentions"):
            return Nullify.clean(msg)
        else:
            return msg

    async def onjoin(self, member, server):
        # Welcome
        welcomeChannel = self.settings.getServerStat(server, "WelcomeChannel")
        if welcomeChannel:
            for channel in server.channels:
                if str(channel.id) == str(welcomeChannel):
                    welcomeChannel = channel
                    break
        if welcomeChannel:
            await self._welcome(member, server, welcomeChannel)
        else:
            await self._welcome(member, server)

    async def onleave(self, member, server):
        # Goodbye
        if not server in self.bot.guilds:
            # We're not on this server - and can't say anything there
            return
        welcomeChannel = self.settings.getServerStat(server, "WelcomeChannel")
        if welcomeChannel:
            for channel in server.channels:
                if str(channel.id) == str(welcomeChannel):
                    welcomeChannel = channel
                    break
        if welcomeChannel:
            await self._goodbye(member, server, welcomeChannel)
        else:
            await self._goodbye(member, server)
            
    def _getDefault(self, server):
        # Returns the default channel for the server
        targetChan = server.get_channel(server.id)
        targetChanID = self.settings.getServerStat(server, "DefaultChannel")
        if len(str(targetChanID)):
            # We *should* have a channel
            tChan = self.bot.get_channel(int(targetChanID))
            if tChan:
                # We *do* have one
                targetChan = tChan
        return targetChan

    @commands.command(pass_context=True)
    async def setwelcome(self, ctx, *, message = None):
        """Sets the welcome message for your server (bot-admin only). 
        Available Options:
        
        [[user]]   = user name
        [[atuser]] = user mention
        [[server]] = server name
        [[count]]  = user count
        [[place]]  = user's place (1st, 2nd, 3rd, etc)
        [[online]] = count of users not offline"""

        isAdmin = ctx.message.author.permissions_in(ctx.message.channel).administrator
        if not isAdmin:
            checkAdmin = self.settings.getServerStat(ctx.message.guild, "AdminArray")
            for role in ctx.message.author.roles:
                for aRole in checkAdmin:
                    # Get the role that corresponds to the id
                    if str(aRole['ID']) == str(role.id):
                        isAdmin = True
        # Only allow admins to change server stats
        if not isAdmin:
            await ctx.channel.send('You do not have sufficient privileges to access this command.')
            return

        if message == None:
            self.settings.setServerStat(ctx.message.guild, "Welcome", None)
            await ctx.channel.send('Welcome message removed!')
            return

        self.settings.setServerStat(ctx.message.guild, "Welcome", message)
        await ctx.channel.send('Welcome message updated!\n\nHere\'s a preview:')
        await self._welcome(ctx.message.author, ctx.message.guild, ctx.message.channel)
        # Print the welcome channel
        welcomeChannel = self.settings.getServerStat(ctx.message.guild, "WelcomeChannel")
        if welcomeChannel:
            for channel in ctx.message.guild.channels:
                if str(channel.id) == str(welcomeChannel):
                    welcomeChannel = channel
                    break
        if welcomeChannel:
            msg = 'The current welcome channel is **{}**.'.format(welcomeChannel.mention)
        else:
            if self._getDefault(ctx.guild):
                msg = 'The current welcome channel is the default channel (**{}**).'.format(self._getDefault(ctx.guild).mention)
            else:
                msg = 'There is *no channel* set for welcome messages.'
        await ctx.channel.send(msg)

    @commands.command(pass_context=True)
    async def testwelcome(self, ctx, *, member = None):
        """Prints the current welcome message (bot-admin only)."""

        # Check if we're suppressing @here and @everyone mentions
        if self.settings.getServerStat(ctx.message.guild, "SuppressMentions"):
            suppress = True
        else:
            suppress = False

        isAdmin = ctx.message.author.permissions_in(ctx.message.channel).administrator
        if not isAdmin:
            checkAdmin = self.settings.getServerStat(ctx.message.guild, "AdminArray")
            for role in ctx.message.author.roles:
                for aRole in checkAdmin:
                    # Get the role that corresponds to the id
                    if str(aRole['ID']) == str(role.id):
                        isAdmin = True

        # Only allow admins to change server stats
        if not isAdmin:
            await ctx.channel.send('You do not have sufficient privileges to access this command.')
            return

        if member == None:
            member = ctx.message.author
        if type(member) is str:
            memberName = member
            member = DisplayName.memberForName(memberName, ctx.message.guild)
            if not member:
                msg = 'I couldn\'t find *{}*...'.format(memberName)
                # Check for suppress
                if suppress:
                    msg = Nullify.clean(msg)
                await ctx.channel.send(msg)
                return
        # Here we have found a member, and stuff.
        # Let's make sure we have a message
        message = self.settings.getServerStat(ctx.message.guild, "Welcome")
        if message == None:
            await ctx.channel.send('Welcome message not setup.  You can do so with the `{}setwelcome [message]` command.'.format(ctx.prefix))
            return
        await self._welcome(member, ctx.message.guild, ctx.message.channel)
        # Print the welcome channel
        welcomeChannel = self.settings.getServerStat(ctx.message.guild, "WelcomeChannel")
        if welcomeChannel:
            for channel in ctx.message.guild.channels:
                if str(channel.id) == str(welcomeChannel):
                    welcomeChannel = channel
                    break
        if welcomeChannel:
            msg = 'The current welcome channel is **{}**.'.format(welcomeChannel.mention)
        else:
            if self._getDefault(ctx.guild):
                msg = 'The current welcome channel is the default channel (**{}**).'.format(self._getDefault(ctx.guild).mention)
            else:
                msg = 'There is *no channel* set for welcome messages.'
        await ctx.channel.send(msg)
        
        
    @commands.command(pass_context=True)
    async def rawwelcome(self, ctx, *, member = None):
        """Prints the current welcome message's markdown (bot-admin only)."""

        # Check if we're suppressing @here and @everyone mentions
        if self.settings.getServerStat(ctx.message.guild, "SuppressMentions"):
            suppress = True
        else:
            suppress = False

        isAdmin = ctx.message.author.permissions_in(ctx.message.channel).administrator
        if not isAdmin:
            checkAdmin = self.settings.getServerStat(ctx.message.guild, "AdminArray")
            for role in ctx.message.author.roles:
                for aRole in checkAdmin:
                    # Get the role that corresponds to the id
                    if str(aRole['ID']) == str(role.id):
                        isAdmin = True

        # Only allow admins to change server stats
        if not isAdmin:
            await ctx.channel.send('You do not have sufficient privileges to access this command.')
            return

        if member == None:
            member = ctx.message.author
        if type(member) is str:
            memberName = member
            member = DisplayName.memberForName(memberName, ctx.message.guild)
            if not member:
                msg = 'I couldn\'t find *{}*...'.format(memberName)
                # Check for suppress
                if suppress:
                    msg = Nullify.clean(msg)
                await ctx.channel.send(msg)
                return
        # Here we have found a member, and stuff.
        # Let's make sure we have a message
        message = self.settings.getServerStat(ctx.message.guild, "Welcome")
        if message == None:
            await ctx.channel.send('Welcome message not setup.  You can do so with the `{}setwelcome [message]` command.'.format(ctx.prefix))
            return
        # Escape the markdown
        message = message.replace('\\', '\\\\').replace('*', '\\*').replace('`', '\\`').replace('_', '\\_')
        await ctx.send(message)
        # Print the welcome channel
        welcomeChannel = self.settings.getServerStat(ctx.message.guild, "WelcomeChannel")
        if welcomeChannel:
            for channel in ctx.message.guild.channels:
                if str(channel.id) == str(welcomeChannel):
                    welcomeChannel = channel
                    break
        if welcomeChannel:
            msg = 'The current welcome channel is **{}**.'.format(welcomeChannel.mention)
        else:
            if self._getDefault(ctx.guild):
                msg = 'The current welcome channel is the default channel (**{}**).'.format(self._getDefault(ctx.guild).mention)
            else:
                msg = 'There is *no channel* set for welcome messages.'
        await ctx.channel.send(msg)


    @commands.command(pass_context=True)
    async def setgoodbye(self, ctx, *, message = None):
        """Sets the goodbye message for your server (bot-admin only).
        Available Options:
        
        [[user]]   = user name
        [[atuser]] = user mention
        [[server]] = server name
        [[count]]  = user count
        [[place]]  = user's place (1st, 2nd, 3rd, etc) - will be count + 1
        [[online]] = count of users not offline"""

        isAdmin = ctx.message.author.permissions_in(ctx.message.channel).administrator
        if not isAdmin:
            checkAdmin = self.settings.getServerStat(ctx.message.guild, "AdminArray")
            for role in ctx.message.author.roles:
                for aRole in checkAdmin:
                    # Get the role that corresponds to the id
                    if str(aRole['ID']) == str(role.id):
                        isAdmin = True
        # Only allow admins to change server stats
        if not isAdmin:
            await ctx.channel.send('You do not have sufficient privileges to access this command.')
            return

        if message == None:
            self.settings.setServerStat(ctx.message.guild, "Goodbye", None)
            await ctx.channel.send('Goodbye message removed!')
            return

        self.settings.setServerStat(ctx.message.guild, "Goodbye", message)
        await ctx.channel.send('Goodbye message updated!\n\nHere\'s a preview:')
        await self._goodbye(ctx.message.author, ctx.message.guild, ctx.message.channel)
        # Print the goodbye channel
        welcomeChannel = self.settings.getServerStat(ctx.message.guild, "WelcomeChannel")
        if welcomeChannel:
            for channel in ctx.message.guild.channels:
                if str(channel.id) == str(welcomeChannel):
                    welcomeChannel = channel
                    break
        if welcomeChannel:
            msg = 'The current goodbye channel is **{}**.'.format(welcomeChannel.mention)
        else:
            if self._getDefault(ctx.guild):
                msg = 'The current goodbye channel is the default channel (**{}**).'.format(self._getDefault(ctx.guild).mention)
            else:
                msg = 'There is *no channel* set for goodbye messages.'
        await ctx.channel.send(msg)


    @commands.command(pass_context=True)
    async def testgoodbye(self, ctx, *, member = None):
        """Prints the current goodbye message (bot-admin only)."""

        # Check if we're suppressing @here and @everyone mentions
        if self.settings.getServerStat(ctx.message.guild, "SuppressMentions"):
            suppress = True
        else:
            suppress = False

        isAdmin = ctx.message.author.permissions_in(ctx.message.channel).administrator
        if not isAdmin:
            checkAdmin = self.settings.getServerStat(ctx.message.guild, "AdminArray")
            for role in ctx.message.author.roles:
                for aRole in checkAdmin:
                    # Get the role that corresponds to the id
                    if str(aRole['ID']) == str(role.id):
                        isAdmin = True

        # Only allow admins to change server stats
        if not isAdmin:
            await ctx.channel.send('You do not have sufficient privileges to access this command.')
            return

        if member == None:
            member = ctx.message.author
        if type(member) is str:
            memberName = member
            member = DisplayName.memberForName(memberName, ctx.message.guild)
            if not member:
                msg = 'I couldn\'t find *{}*...'.format(memberName)
                # Check for suppress
                if suppress:
                    msg = Nullify.clean(msg)
                await ctx.channel.send(msg)
                return
        # Here we have found a member, and stuff.
        # Let's make sure we have a message
        message = self.settings.getServerStat(ctx.message.guild, "Goodbye")
        if message == None:
            await ctx.channel.send('Goodbye message not setup.  You can do so with the `{}setgoodbye [message]` command.'.format(ctx.prefix))
            return
        await self._goodbye(member, ctx.message.guild, ctx.message.channel)
        
        # Print the goodbye channel
        welcomeChannel = self.settings.getServerStat(ctx.message.guild, "WelcomeChannel")
        if welcomeChannel:
            for channel in ctx.message.guild.channels:
                if str(channel.id) == str(welcomeChannel):
                    welcomeChannel = channel
                    break
        if welcomeChannel:
            msg = 'The current goodbye channel is **{}**.'.format(welcomeChannel.mention)
        else:
            if self._getDefault(ctx.guild):
                msg = 'The current goodbye channel is the default channel (**{}**).'.format(self._getDefault(ctx.guild).mention)
            else:
                msg = 'There is *no channel* set for goodbye messages.'
        await ctx.channel.send(msg)
        
        
    @commands.command(pass_context=True)
    async def rawgoodbye(self, ctx, *, member = None):
        """Prints the current goodbye message's markdown (bot-admin only)."""

        # Check if we're suppressing @here and @everyone mentions
        if self.settings.getServerStat(ctx.message.guild, "SuppressMentions"):
            suppress = True
        else:
            suppress = False

        isAdmin = ctx.message.author.permissions_in(ctx.message.channel).administrator
        if not isAdmin:
            checkAdmin = self.settings.getServerStat(ctx.message.guild, "AdminArray")
            for role in ctx.message.author.roles:
                for aRole in checkAdmin:
                    # Get the role that corresponds to the id
                    if str(aRole['ID']) == str(role.id):
                        isAdmin = True

        # Only allow admins to change server stats
        if not isAdmin:
            await ctx.channel.send('You do not have sufficient privileges to access this command.')
            return

        if member == None:
            member = ctx.message.author
        if type(member) is str:
            memberName = member
            member = DisplayName.memberForName(memberName, ctx.message.guild)
            if not member:
                msg = 'I couldn\'t find *{}*...'.format(memberName)
                # Check for suppress
                if suppress:
                    msg = Nullify.clean(msg)
                await ctx.channel.send(msg)
                return
        # Here we have found a member, and stuff.
        # Let's make sure we have a message
        message = self.settings.getServerStat(ctx.message.guild, "Goodbye")
        if message == None:
            await ctx.channel.send('Goodbye message not setup.  You can do so with the `{}setgoodbye [message]` command.'.format(ctx.prefix))
            return
        # Escape the markdown
        message = message.replace('\\', '\\\\').replace('*', '\\*').replace('`', '\\`').replace('_', '\\_')
        await ctx.send(message)
        # Print the goodbye channel
        welcomeChannel = self.settings.getServerStat(ctx.message.guild, "WelcomeChannel")
        if welcomeChannel:
            for channel in ctx.message.guild.channels:
                if str(channel.id) == str(welcomeChannel):
                    welcomeChannel = channel
                    break
        if welcomeChannel:
            msg = 'The current goodbye channel is **{}**.'.format(welcomeChannel.mention)
        else:
            if self._getDefault(ctx.guild):
                msg = 'The current goodbye channel is the default channel (**{}**).'.format(self._getDefault(ctx.guild).mention)
            else:
                msg = 'There is *no channel* set for goodbye messages.'
        await ctx.channel.send(msg)


    async def _welcome(self, member, server, channel = None):
        # Check if we're suppressing @here and @everyone mentions
        if self.settings.getServerStat(server, "SuppressMentions"):
            suppress = True
        else:
            suppress = False
        message = self.settings.getServerStat(server, "Welcome")
        if message == None:
            return
        # Let's regex and replace [[user]] [[atuser]] and [[server]]
        message = re.sub(self.regexUserName, "{}".format(DisplayName.name(member)), message)
        message = re.sub(self.regexUserPing, "{}".format(member.mention), message)
        message = re.sub(self.regexServer,   "{}".format(self.suppressed(server, server.name)), message)
        message = re.sub(self.regexCount,    "{:,}".format(len(server.members)), message)
        # Get place info
        place_str = str(len(server.members))
        end_str = "th"
        if place_str.endswith("1") and not place_str.endswith("11"):
            end_str = "st"
        elif place_str.endswith("2") and not place_str.endswith("12"):
            end_str = "nd"
        elif place_str.endswith("3") and not place_str.endswith("13"):
            end_str = "rd"
        message = re.sub(self.regexPlace,    "{:,}{}".format(len(server.members), end_str), message)
        # Get online users
        online_count = 0
        for m in server.members:
            if not m.status == discord.Status.offline:
                online_count += 1
        message = re.sub(self.regexOnline,    "{:,}".format(online_count), message)
                
        if suppress:
            message = Nullify.clean(message)

        if channel:
            await channel.send(message)
        else:
            try:
                if self._getDefault(server):
                    # Only message if we can
                    await self._getDefault(server).send(message)
            except Exception:
                pass


    async def _goodbye(self, member, server, channel = None):
        # Check if we're suppressing @here and @everyone mentions
        if self.settings.getServerStat(server, "SuppressMentions"):
            suppress = True
        else:
            suppress = False
        message = self.settings.getServerStat(server, "Goodbye")
        if message == None:
            return
        # Let's regex and replace [[user]] [[atuser]] and [[server]]
        message = re.sub(self.regexUserName, "{}".format(DisplayName.name(member)), message)
        message = re.sub(self.regexUserPing, "{}".format(member.mention), message)
        message = re.sub(self.regexServer,   "{}".format(self.suppressed(server, server.name)), message)
        message = re.sub(self.regexCount,    "{:,}".format(len(server.members)), message)
        # Get place info
        place_str = str(len(server.members)+1)
        end_str = "th"
        if place_str.endswith("1") and not place_str.endswith("11"):
            end_str = "st"
        elif place_str.endswith("2") and not place_str.endswith("12"):
            end_str = "nd"
        elif place_str.endswith("3") and not place_str.endswith("13"):
            end_str = "rd"
        message = re.sub(self.regexPlace,    "{:,}{}".format(len(server.members)+1, end_str), message)
        # Get online users
        online_count = 0
        for m in server.members:
            if not m.status == discord.Status.offline:
                online_count += 1
        message = re.sub(self.regexOnline,    "{:,}".format(online_count), message)

        if suppress:
            message = Nullify.clean(message)
        if channel:
            await channel.send(message)
        else:
            try:
                if self._getDefault(server):
                    # Only message if we can
                    await self._getDefault(server).send(message)
            except Exception:
                pass

    @commands.command(pass_context=True)
    async def setwelcomechannel(self, ctx, *, channel : discord.TextChannel = None):
        """Sets the channel for the welcome and goodbye messages (bot-admin only)."""

        isAdmin = ctx.message.author.permissions_in(ctx.message.channel).administrator
        if not isAdmin:
            checkAdmin = self.settings.getServerStat(ctx.message.guild, "AdminArray")
            for role in ctx.message.author.roles:
                for aRole in checkAdmin:
                    # Get the role that corresponds to the id
                    if str(aRole['ID']) == str(role.id):
                        isAdmin = True

        # Only allow admins to change server stats
        if not isAdmin:
            await ctx.channel.send('You do not have sufficient privileges to access this command.')
            return

        if channel == None:
            self.settings.setServerStat(ctx.message.guild, "WelcomeChannel", "")
            if self._getDefault(ctx.guild):
                msg = 'Welcome and goodbye messages will be displayed in the default channel (**{}**).'.format(self._getDefault(ctx.guild).mention)
            else:
                msg = "Welcome and goodbye messages will **not** be displayed."
            await ctx.channel.send(msg)
            return

        # If we made it this far - then we can add it
        self.settings.setServerStat(ctx.message.guild, "WelcomeChannel", channel.id)

        msg = 'Welcome and goodbye messages will be displayed in **{}**.'.format(channel.mention)
        await ctx.channel.send(msg)


    @setwelcomechannel.error
    async def setwelcomechannel_error(self, ctx, error):
        # do stuff
        msg = 'setwelcomechannel Error: {}'.format(ctx)
        await error.channel.send(msg)
