import asyncio
import discord
import re
from   discord.ext import commands
from   Cogs import Settings

def setup(bot):
    # Add the bot and deps
    settings = bot.get_cog("Settings")
    bot.add_cog(Stream(bot, settings))

class Stream:

    def __init__(self, bot, settings):
        self.bot = bot
        self.settings = settings
        self.regexUserName = re.compile(r"\[\[[user]+\]\]", re.IGNORECASE)
        self.regexUserPing = re.compile(r"\[\[[atuser]+\]\]", re.IGNORECASE)
        self.regexServer   = re.compile(r"\[\[[server]+\]\]", re.IGNORECASE)
        self.regexCount    = re.compile(r"\[\[[count]+\]\]", re.IGNORECASE)
        self.regexPlace    = re.compile(r"\[\[[place]+\]\]", re.IGNORECASE)
        self.regexOnline   = re.compile(r"\[\[[online]+\]\]", re.IGNORECASE)
        self.regexHere     = re.compile(r"\[\[[here]+\]\]", re.IGNORECASE)
        self.regexEveryone = re.compile(r"\[\[[everyone]+\]\]", re.IGNORECASE)
        
    @commands.command(pass_context=True)
    async def streamchannel(self, ctx, *, channel : discord.TextChannel = None):
        """Displays the channel for the stream announcements - if any."""
        
        chan = self.settings.getServerStat(ctx.message.guild, "StreamChannel")
        if not chan:
            await ctx.send("There is no channel setup for stream announcements.")
            return
        channel = ctx.guild.get_channel(chan)
        if not channel:
            await ctx.send("The stream announcement channel (`{}`) no longer exists on this server.".format(chan))
            return
        await ctx.send("Stream announcements will be mentioned in {}.".format(channel.mention))
        
    @commands.command(pass_context=True)
    async def setstreamchannel(self, ctx, *, channel : discord.TextChannel = None):
        """Sets the channel for the stream announcements (bot-admin only)."""

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
            self.settings.setServerStat(ctx.message.guild, "StreamChannel", None)
            msg = "Stream announcements **not** be displayed."
            await ctx.channel.send(msg)
            return

        # If we made it this far - then we can add it
        self.settings.setServerStat(ctx.message.guild, "StreamChannel", channel.id)

        msg = 'Stream announcements will be displayed in **{}**.'.format(channel.mention)
        await ctx.channel.send(msg)


    @setstreamchannel.error
    async def setstreamchannel_error(self, ctx, error):
        # do stuff
        msg = 'setstreamchannel Error: {}'.format(ctx)
        await error.channel.send(msg)
