import asyncio
import discord
from discord.ext import commands
from Cogs import Settings, DisplayName, Utils


def setup(bot):
    # Add the bot and deps
    settings = bot.get_cog("Settings")
    bot.add_cog(Face(bot, settings))

# This is the Face module. It sends faces.


class Face(commands.Cog):

    # Init with the bot reference, and a reference to the settings var
    def __init__(self, bot, settings):
        self.bot = bot
        self.settings = settings
        global Utils, DisplayName
        Utils = self.bot.get_cog("Utils")
        DisplayName = self.bot.get_cog("DisplayName")

    @commands.command(pass_context=True)
    async def lenny(self, ctx, *, message: str = None):
        """Give me some Lenny."""

        # Log the user
        self.settings.setServerStat(
            ctx.message.guild, "LastLenny", ctx.message.author.id)

        msg = "( ͡° ͜ʖ ͡°)"
        if message:
            msg += "\n{}".format(message)
        # Check for suppress
        msg = Utils.suppressed(ctx, msg)
        # Send new message first, then delete original
        await ctx.channel.send(msg)
        # Remove original message
        await ctx.message.delete()

    @commands.command(pass_context=True)
    async def lastlenny(self, ctx):
        """Who Lenny'ed last?"""
        lastLen = self.settings.getServerStat(ctx.message.guild, "LastLenny")
        msg = 'No one has Lenny\'ed on my watch yet...'
        if lastLen:
            # Got someone
            memberName = DisplayName.name(
                DisplayName.memberForID(lastLen, ctx.message.guild))
            if memberName:
                msg = '*{}* was the last person to use the `{}lenny` command.'.format(
                    memberName, ctx.prefix)
            else:
                msg = 'The user that last used the `{}lenny` command is no longer on this server.'.format(
                    ctx.prefix)
        await ctx.channel.send(msg)

    @commands.command(pass_context=True)
    async def shrug(self, ctx, *, message: str = None):
        """Shrug it off."""

        # Log the user
        self.settings.setServerStat(
            ctx.message.guild, "LastShrug", ctx.message.author.id)

        msg = "¯\_(ツ)_/¯"
        if message:
            msg += "\n{}".format(message)
        # Check for suppress
        msg = Utils.suppressed(ctx, msg)
        # Send new message first, then delete original
        await ctx.channel.send(msg)
        # Remove original message
        await ctx.message.delete()

    @commands.command(pass_context=True)
    async def lastshrug(self, ctx):
        """Who shrugged last?"""
        lastLen = self.settings.getServerStat(ctx.message.guild, "LastShrug")
        msg = 'No one has shrugged on my watch yet...'
        if lastLen:
            # Got someone
            memberName = DisplayName.name(
                DisplayName.memberForID(lastLen, ctx.message.guild))
            if memberName:
                msg = '*{}* was the last person to use the `{}shrug` command.'.format(
                    memberName, ctx.prefix)
            else:
                msg = 'The user that last used the `{}shrug` command is no longer on this server.'.format(
                    ctx.prefix)
        await ctx.channel.send(msg)
