import asyncio
import discord
import re
from   discord.ext import commands
from   Cogs import Settings
from   Cogs import DisplayName
from   Cogs import Message

def setup(bot):
    # Add the bot and deps
    settings = bot.get_cog("Settings")
    bot.add_cog(Stream(bot, settings))

class Stream(commands.Cog):

    def __init__(self, bot, settings):
        self.bot = bot
        self.settings = settings
        global Utils, DisplayName
        Utils = self.bot.get_cog("Utils")
        DisplayName = self.bot.get_cog("DisplayName")
        # Regex values
        self.regexUserName = re.compile(r"\[\[[user]+\]\]",     re.IGNORECASE)
        self.regexUserPing = re.compile(r"\[\[[atuser]+\]\]",   re.IGNORECASE)
        self.regexServer   = re.compile(r"\[\[[server]+\]\]",   re.IGNORECASE)
        self.regexUrl      = re.compile(r"\[\[[url]+\]\]",      re.IGNORECASE)
        self.regexGame     = re.compile(r"\[\[[game]+\]\]",     re.IGNORECASE)
        self.regexHere     = re.compile(r"\[\[[here]+\]\]",     re.IGNORECASE)
        self.regexEveryone = re.compile(r"\[\[[everyone]+\]\]", re.IGNORECASE)

    # Check for events!
    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        stream_list = self.settings.getServerStat(before.guild, "StreamList")
        if not before.id in stream_list:
            # We're not watching for them
            return
        # Find out if we weren't streaming before - and display it
        s_before = next((x for x in list(before.activities) if x.type is discord.ActivityType.streaming), None)
        if s_before:
            # Already streaming - ignore it.
            return
        # Not streaming before, see if we are now
        s_after = next((x for x in list(after.activities) if x.type is discord.ActivityType.streaming), None)
        if not s_after:
            # Not streaming - ignore it.
            return
        # We're STREAMING
        chan = self.settings.getServerStat(before.guild, "StreamChannel")
        channel = before.guild.get_channel(chan)
        if not channel:
            # Something isn't right - bail
            return
        message = self.settings.getServerStat(before.guild, "StreamMessage")
        if not message or not len(message):
            # Nothing to say
            return
        # We've got a message and a place
        # Let's regex and replace [[user]] [[atuser]] and [[server]]
        await self._stream_message(after, message, channel)

    def check_bot_admin(self, member, channel):
        # Returns whether we're at least bot-admin
        isAdmin = member.permissions_in(channel).administrator
        if not isAdmin:
            checkAdmin = self.settings.getServerStat(channel.guild, "AdminArray")
            for role in member.roles:
                if isAdmin:
                    break
                for aRole in checkAdmin:
                    # Get the role that corresponds to the id
                    if str(aRole['ID']) == str(role.id):
                        isAdmin = True
                        break
        return isAdmin

    @commands.command(pass_context=True)
    async def setstream(self, ctx, *, message = None):
        """Sets the stream announcement message (bot-admin only).
        Available Options:
        
        [[user]]     = user name
        [[atuser]]   = user mention
        [[server]]   = server name
        [[game]]     = the game name
        [[url]]      = stream url
        [[here]]     = @​here ping
        [[everyone]] = @​everyone ping"""

        if not self.check_bot_admin(ctx.author, ctx.channel):
            await ctx.send('You do not have sufficient privileges to access this command.')
            return
        
        if message == None:
            self.settings.setServerStat(ctx.message.guild, "StreamMessage", None)
            await ctx.channel.send('Stream announcement message removed!')
            return

        self.settings.setServerStat(ctx.message.guild, "StreamMessage", message)
        await ctx.send("Stream announcement message sent - here's a preview (note that @​here and @​everyone pings are suppressed here):")
        await self._stream_message(ctx.author, message, ctx, True)
        chan = self.settings.getServerStat(ctx.message.guild, "StreamChannel")
        channel = ctx.guild.get_channel(chan)
        if not channel:
            await ctx.send("There is currently **no channel** set for stream announcements.")
        else:
            await ctx.send("Stream announcements will be displayed in {}.".format(channel.mention))

    @commands.command(pass_context=True)
    async def teststream(self, ctx, *, message = None):
        """Tests the stream announcement message (bot-admin only)."""
        if not self.check_bot_admin(ctx.author, ctx.channel):
            await ctx.send('You do not have sufficient privileges to access this command.')
            return
        message = self.settings.getServerStat(ctx.guild, "StreamMessage")
        if not message:
            await ctx.send("There is no stream announcement setup.")
            return
        await self._stream_message(ctx.author, message, ctx, True)
        chan = self.settings.getServerStat(ctx.message.guild, "StreamChannel")
        channel = ctx.guild.get_channel(chan)
        if not channel:
            await ctx.send("There is currently **no channel** set for stream announcements.")
        else:
            await ctx.send("Stream announcements will be displayed in {}.".format(channel.mention))

    @commands.command(pass_context=True)
    async def rawstream(self, ctx, *, message = None):
        """Displays the raw markdown for the stream announcement message (bot-admin only)."""
        if not self.check_bot_admin(ctx.author, ctx.channel):
            await ctx.send('You do not have sufficient privileges to access this command.')
            return
        message = self.settings.getServerStat(ctx.guild, "StreamMessage")
        if not message:
            await ctx.send("There is no stream announcement setup.")
            return
        # Nullify markdown
        message = message.replace('\\', '\\\\').replace('*', '\\*').replace('`', '\\`').replace('_', '\\_')
        await ctx.send(message)
        chan = self.settings.getServerStat(ctx.message.guild, "StreamChannel")
        channel = ctx.guild.get_channel(chan)
        if not channel:
            await ctx.send("There is currently **no channel** set for stream announcements.")
        else:
            await ctx.send("Stream announcements will be displayed in {}.".format(channel.mention))

    async def _stream_message(self, member, message, dest, test = False):
        message = re.sub(self.regexUserName, "{}".format(DisplayName.name(member)), message)
        message = re.sub(self.regexUserPing, "{}".format(member.mention), message)
        message = re.sub(self.regexServer,   "{}".format(dest.guild.name.replace("@here", "@​here").replace("@everyone", "@​everyone")), message)
        # Get the activity info
        act = next((x for x in list(member.activities) if x.type is discord.ActivityType.streaming), None)
        try:
            name = act.name
        except:
            name = "Mystery Game"
        try:
            url = act.url
        except:
            url = "Mystery URL"
        if test:
            message = re.sub(self.regexUrl,      "GameURL", message)
            message = re.sub(self.regexGame,     "GameName", message)
            message = re.sub(self.regexHere,     "@​here", message)
            message = re.sub(self.regexEveryone, "@​everyone", message)
        else:
            message = re.sub(self.regexUrl,      "{}".format(url), message)
            message = re.sub(self.regexGame,     "{}".format(name), message)
            message = re.sub(self.regexHere,     "@here", message)
            message = re.sub(self.regexEveryone, "@everyone", message)
        await dest.send(message)

    @commands.command(pass_context=True)
    async def addstreamer(self, ctx, *, member = None):
        """Adds the passed member to the streamer list (bot-admin only)."""
        if not self.check_bot_admin(ctx.author, ctx.channel):
            await ctx.send('You do not have sufficient privileges to access this command.')
            return
        if member == None:
            await ctx.send("Usage: `{}addstreamer [member]`".format(ctx.context))
            return
        mem = DisplayName.memberForName(member, ctx.guild)
        if not mem:
            await ctx.send("I couldn't find `{}`...".format(member.replace("`", "\\`")))
            return
        # Got a member
        stream_list = self.settings.getServerStat(ctx.guild, "StreamList")
        if mem.id in stream_list:
            await ctx.send("I'm already watching for streams from `{}`.".format(DisplayName.name(mem).replace("`", "").replace("\\","")))
            return
        stream_list.append(mem.id)
        self.settings.setServerStat(ctx.guild, "StreamList", stream_list)
        await ctx.send("`{}` added to the stream list!".format(DisplayName.name(mem).replace("`", "").replace("\\","")))

    @commands.command(pass_context=True)
    async def remstreamer(self, ctx, *, member = None):
        """Removes the passed member from the streamer list (bot-admin only)."""
        if not self.check_bot_admin(ctx.author, ctx.channel):
            await ctx.send('You do not have sufficient privileges to access this command.')
            return
        if member == None:
            await ctx.send("Usage: `{}remstreamer [member]`".format(ctx.context))
            return
        mem = DisplayName.memberForName(member, ctx.guild)
        if not mem:
            await ctx.send("I couldn't find `{}`...".format(member.replace("`", "").replace("\\","")))
            return
        # Got a member
        stream_list = self.settings.getServerStat(ctx.guild, "StreamList")
        if not mem.id in stream_list:
            await ctx.send("I'm not currently watching for streams from `{}`.".format(DisplayName.name(mem).replace("`", "").replace("\\","")))
            return
        stream_list.remove(mem.id)
        self.settings.setServerStat(ctx.guild, "StreamList", stream_list)
        await ctx.send("`{}` removed from the stream list!".format(DisplayName.name(mem).replace("`", "").replace("\\","")))

    @commands.command(pass_context=True)
    async def streamers(self, ctx):
        """Lists the current members in the streamer list."""
        stream_list = self.settings.getServerStat(ctx.guild, "StreamList")
        streamers = []
        for x in stream_list:
            mem = DisplayName.memberForName(x, ctx.guild)
            if not mem:
                continue
            streamers.append(DisplayName.name(mem))
        if not len(streamers):
            await ctx.send("Not currently watching for any streamers.")
            return
        stream_string = "\n".join(streamers)
        await Message.Message(message=stream_string, header="__Streamer List:__\n```\n", footer="```").send(ctx)
        
    @commands.command(pass_context=True)
    async def streamchannel(self, ctx):
        """Displays the channel for the stream announcements - if any."""
        
        chan = self.settings.getServerStat(ctx.message.guild, "StreamChannel")
        if not chan:
            await ctx.send("There is no channel setup for stream announcements.")
            return
        channel = ctx.guild.get_channel(chan)
        if not channel:
            await ctx.send("The stream announcement channel (`{}`) no longer exists on this server.".format(chan))
            return
        await ctx.send("Stream announcements will be displayed in {}.".format(channel.mention))
        
    @commands.command(pass_context=True)
    async def setstreamchannel(self, ctx, *, channel : discord.TextChannel = None):
        """Sets the channel for the stream announcements (bot-admin only)."""
        if not self.check_bot_admin(ctx.author, ctx.channel):
            await ctx.send('You do not have sufficient privileges to access this command.')
            return

        if channel == None:
            self.settings.setServerStat(ctx.message.guild, "StreamChannel", None)
            msg = "Stream announcements **not** be displayed."
            await ctx.send(msg)
            return

        # If we made it this far - then we can add it
        self.settings.setServerStat(ctx.message.guild, "StreamChannel", channel.id)

        msg = 'Stream announcements will be displayed in **{}**.'.format(channel.mention)
        await ctx.send(msg)

    @setstreamchannel.error
    async def setstreamchannel_error(self, ctx, error):
        # do stuff
        msg = 'setstreamchannel Error: {}'.format(ctx)
        await error.send(msg)

    
