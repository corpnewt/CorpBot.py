import asyncio, discord, time, json, os, re
from   datetime    import datetime
from   discord.ext import commands
from   shutil      import copyfile
from Cogs import Utils, DisplayName, Nullify

def setup(bot):
    # Add the bot and deps
    settings = bot.get_cog("Settings")
    bot.add_cog(Welcome(bot, settings))

class Welcome(commands.Cog):

    def __init__(self, bot, settings):
        self.bot = bot
        self.settings = settings
        self.regexUserName = re.compile(r"\[\[[user]+\]\]", re.IGNORECASE)
        self.regexUserPing = re.compile(r"\[\[[atuser]+\]\]", re.IGNORECASE)
        self.regexServer   = re.compile(r"\[\[[server]+\]\]", re.IGNORECASE)
        self.regexCount    = re.compile(r"\[\[[count]+\]\]", re.IGNORECASE)
        self.regexPlace    = re.compile(r"\[\[[place]+\]\]", re.IGNORECASE)
        self.regexOnline   = re.compile(r"\[\[[online]+\]\]", re.IGNORECASE)
        global Utils, DisplayName
        Utils = self.bot.get_cog("Utils")
        DisplayName = self.bot.get_cog("DisplayName")

    async def onjoin(self, member, server):
        # Welcome
        try: welcomeChannel = server.get_channel(int(self.settings.getServerStat(server,"WelcomeChannel")))
        except: welcomeChannel = None
        if welcomeChannel: await self._welcome(member, server, welcomeChannel)
        else: await self._welcome(member, server)
        if not self.settings.getServerStat(server,"JoinPM",False): return
        # We need to attempt to dm the rules
        rules = self.settings.getServerStat(server, "Rules")
        if rules:
            try: await member.send(Utils.suppressed(server,"***{}*** **Rules:**:\n{}".format(server.name,rules)))
            except: pass

    async def onleave(self, member, server):
        # Goodbye
        if not server in self.bot.guilds:
            # We're not on this server - and can't say anything there
            return
        try: welcomeChannel = server.get_channel(int(self.settings.getServerStat(server,"WelcomeChannel")))
        except: welcomeChannel = None
        if welcomeChannel: await self._goodbye(member, server, welcomeChannel)
        else: await self._goodbye(member, server)
            
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

        if not await Utils.is_bot_admin_reply(ctx): return

        if message == None:
            self.settings.setServerStat(ctx.guild, "Welcome", "")
            return await ctx.send('Welcome message removed!')

        self.settings.setServerStat(ctx.guild, "Welcome", message)
        await ctx.send('Welcome message updated!\n\nHere\'s a preview:')
        await self._welcome(ctx.message.author, ctx.guild, ctx.message.channel)
        # Print the welcome channel
        try: welcomeChannel = ctx.guild.get_channel(int(self.settings.getServerStat(ctx.guild,"WelcomeChannel")))
        except: welcomeChannel = None
        if welcomeChannel:
            msg = 'The current welcome channel is **{}**.'.format(welcomeChannel.mention)
        else:
            if self._getDefault(ctx.guild):
                msg = 'The current welcome channel is the default channel (**{}**).'.format(self._getDefault(ctx.guild).mention)
            else:
                msg = 'There is *no channel* set for welcome messages.'
        await ctx.send(msg)

    @commands.command(pass_context=True)
    async def testwelcome(self, ctx, *, member = None):
        """Prints the current welcome message (bot-admin only)."""
        if not await Utils.is_bot_admin_reply(ctx): return

        if member == None:
            member = ctx.message.author
        if type(member) is str:
            memberName = member
            member = DisplayName.memberForName(memberName, ctx.guild)
            if not member:
                msg = 'I couldn\'t find *{}*...'.format(Nullify.escape_all(memberName))
                return await ctx.send(msg)
        # Here we have found a member, and stuff.
        # Let's make sure we have a message
        message = self.settings.getServerStat(ctx.guild, "Welcome")
        if message in (None,""):
            return await ctx.send('Welcome message not setup.  You can do so with the `{}setwelcome [message]` command.'.format(ctx.prefix))
        await self._welcome(member, ctx.guild, ctx.channel)
        # Print the welcome channel
        try: welcomeChannel = ctx.guild.get_channel(int(self.settings.getServerStat(ctx.guild,"WelcomeChannel")))
        except: welcomeChannel = None
        if welcomeChannel:
            msg = 'The current welcome channel is **{}**.'.format(welcomeChannel.mention)
        else:
            if self._getDefault(ctx.guild):
                msg = 'The current welcome channel is the default channel (**{}**).'.format(self._getDefault(ctx.guild).mention)
            else:
                msg = 'There is *no channel* set for welcome messages.'
        await ctx.send(msg)
        
        
    @commands.command(pass_context=True)
    async def rawwelcome(self, ctx, *, member = None):
        """Prints the current welcome message's markdown (bot-admin only)."""
        if not await Utils.is_bot_admin_reply(ctx): return

        if member == None:
            member = ctx.message.author
        if type(member) is str:
            memberName = member
            member = DisplayName.memberForName(memberName, ctx.guild)
            if not member:
                msg = 'I couldn\'t find *{}*...'.format(Nullify.escape_all(memberName))
                return await ctx.send(msg)
        # Here we have found a member, and stuff.
        # Let's make sure we have a message
        message = self.settings.getServerStat(ctx.guild, "Welcome")
        if message in (None,""):
            return await ctx.send('Welcome message not setup.  You can do so with the `{}setwelcome [message]` command.'.format(ctx.prefix))
        # Escape the markdown
        message = discord.utils.escape_markdown(message)
        await ctx.send(message)
        # Print the welcome channel
        try: welcomeChannel = ctx.guild.get_channel(int(self.settings.getServerStat(ctx.guild,"WelcomeChannel")))
        except: welcomeChannel = None
        if welcomeChannel:
            msg = 'The current welcome channel is **{}**.'.format(welcomeChannel.mention)
        else:
            if self._getDefault(ctx.guild):
                msg = 'The current welcome channel is the default channel (**{}**).'.format(self._getDefault(ctx.guild).mention)
            else:
                msg = 'There is *no channel* set for welcome messages.'
        await ctx.send(msg)


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

        if not await Utils.is_bot_admin_reply(ctx): return

        if message == None:
            self.settings.setServerStat(ctx.guild, "Goodbye", "")
            return await ctx.send('Goodbye message removed!')

        self.settings.setServerStat(ctx.guild, "Goodbye", message)
        await ctx.send('Goodbye message updated!\n\nHere\'s a preview:')
        await self._goodbye(ctx.message.author, ctx.guild, ctx.message.channel)
        # Print the goodbye channel
        try: welcomeChannel = ctx.guild.get_channel(int(self.settings.getServerStat(ctx.guild,"WelcomeChannel")))
        except: welcomeChannel = None
        if welcomeChannel:
            msg = 'The current goodbye channel is **{}**.'.format(welcomeChannel.mention)
        else:
            if self._getDefault(ctx.guild):
                msg = 'The current goodbye channel is the default channel (**{}**).'.format(self._getDefault(ctx.guild).mention)
            else:
                msg = 'There is *no channel* set for goodbye messages.'
        await ctx.send(msg)


    @commands.command(pass_context=True)
    async def testgoodbye(self, ctx, *, member = None):
        """Prints the current goodbye message (bot-admin only)."""
        if not await Utils.is_bot_admin_reply(ctx): return

        if member == None:
            member = ctx.message.author
        if type(member) is str:
            memberName = member
            member = DisplayName.memberForName(memberName, ctx.guild)
            if not member:
                msg = 'I couldn\'t find *{}*...'.format(Nullify.escape_all(memberName))
                return await ctx.send(msg)
        # Here we have found a member, and stuff.
        # Let's make sure we have a message
        message = self.settings.getServerStat(ctx.guild, "Goodbye")
        if message in (None,""):
            return await ctx.send('Goodbye message not setup.  You can do so with the `{}setgoodbye [message]` command.'.format(ctx.prefix))
        await self._goodbye(member, ctx.guild, ctx.channel)
        
        # Print the goodbye channel
        try: welcomeChannel = ctx.guild.get_channel(int(self.settings.getServerStat(ctx.guild,"WelcomeChannel")))
        except: welcomeChannel = None
        if welcomeChannel:
            msg = 'The current goodbye channel is **{}**.'.format(welcomeChannel.mention)
        else:
            if self._getDefault(ctx.guild):
                msg = 'The current goodbye channel is the default channel (**{}**).'.format(self._getDefault(ctx.guild).mention)
            else:
                msg = 'There is *no channel* set for goodbye messages.'
        await ctx.send(msg)
        
        
    @commands.command(pass_context=True)
    async def rawgoodbye(self, ctx, *, member = None):
        """Prints the current goodbye message's markdown (bot-admin only)."""
        if not await Utils.is_bot_admin_reply(ctx): return

        if member == None:
            member = ctx.message.author
        if type(member) is str:
            memberName = member
            member = DisplayName.memberForName(memberName, ctx.guild)
            if not member:
                msg = 'I couldn\'t find *{}*...'.format(Nullify.escape_all(memberName))
                return await ctx.send(msg)
        # Here we have found a member, and stuff.
        # Let's make sure we have a message
        message = self.settings.getServerStat(ctx.guild, "Goodbye")
        if message in (None,""):
            return await ctx.send('Goodbye message not setup.  You can do so with the `{}setgoodbye [message]` command.'.format(ctx.prefix))
        # Escape the markdown
        message = discord.utils.escape_markdown(message)
        await ctx.send(message)
        # Print the goodbye channel
        try: welcomeChannel = ctx.guild.get_channel(int(self.settings.getServerStat(ctx.guild,"WelcomeChannel")))
        except: welcomeChannel = None
        if welcomeChannel:
            msg = 'The current goodbye channel is **{}**.'.format(welcomeChannel.mention)
        else:
            if self._getDefault(ctx.guild):
                msg = 'The current goodbye channel is the default channel (**{}**).'.format(self._getDefault(ctx.guild).mention)
            else:
                msg = 'There is *no channel* set for goodbye messages.'
        await ctx.send(msg)

    async def _send_greeting(self,member,server,channel=None,stat_name="Welcome"):
        # Helper to send the welcome/goodbye message
        message = self.settings.getServerStat(server, stat_name)
        if message in (None,""): return
        # Let's regex and replace [[user]] [[atuser]] and [[server]]
        message = re.sub(self.regexUserName, "{}".format(DisplayName.name(member)), message)
        message = re.sub(self.regexUserPing, "{}".format(member.mention), message)
        message = re.sub(self.regexServer,   "{}".format(Utils.suppressed(server, server.name)), message)
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
        message = re.sub(self.regexPlace, "{:,}{}".format(len(server.members), end_str), message)
        # Get online users
        online_count = len([x for x in server.members if not x.status == discord.Status.offline])
        message = re.sub(self.regexOnline, "{:,}".format(online_count), message)
        if channel: return await channel.send(message)
        try:
            await self._getDefault(server).send(message)
        except:
            pass

    async def _welcome(self, member, server, channel = None):
        await self._send_greeting(member,server,channel,"Welcome")

    async def _goodbye(self, member, server, channel = None):
        await self._send_greeting(member,server,channel,"Goodbye")

    @commands.command(pass_context=True)
    async def setwelcomechannel(self, ctx, *, channel : discord.TextChannel = None):
        """Sets the channel for the welcome and goodbye messages (bot-admin only)."""
        if not await Utils.is_bot_admin_reply(ctx): return

        if channel == None:
            self.settings.setServerStat(ctx.guild, "WelcomeChannel", "")
            if self._getDefault(ctx.guild):
                msg = 'Welcome and goodbye messages will be displayed in the default channel (**{}**).'.format(self._getDefault(ctx.guild).mention)
            else:
                msg = "Welcome and goodbye messages will **not** be displayed."
            return await ctx.send(msg)

        # If we made it this far - then we can add it
        self.settings.setServerStat(ctx.guild, "WelcomeChannel", channel.id)

        msg = 'Welcome and goodbye messages will be displayed in **{}**.'.format(channel.mention)
        await ctx.send(msg)


    @setwelcomechannel.error
    async def setwelcomechannel_error(self, ctx, error):
        # do stuff
        msg = 'setwelcomechannel Error: {}'.format(ctx)
        await error.channel.send(msg)
