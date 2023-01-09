import asyncio, discord, random
from   discord.ext import commands
from   Cogs import Utils, DisplayName, PickList

def setup(bot):
    # Add the bot and deps
    settings = bot.get_cog("Settings")
    bot.add_cog(Example(bot, settings))

class Example(commands.Cog):

    def __init__(self, bot, settings):
        self.bot = bot
        self.settings = settings
        global Utils, DisplayName
        Utils = self.bot.get_cog("Utils")
        DisplayName = self.bot.get_cog("DisplayName")

    @commands.command()
    async def add(self, ctx, left : int, right : int):
        """Adds two numbers together."""
        await ctx.send(left + right)

    @commands.command(description='For when you wanna settle the score some other way')
    async def choose(self, ctx, *choices : str):
        """Chooses between multiple choices."""
        await ctx.send(Utils.suppressed(ctx,random.choice(choices)))

    @commands.command(pass_context=True)
    async def joined(self, ctx, *, member : str = None):
        """Says when a member joined."""
        if member is None:
            member = ctx.message.author
            
        if type(member) is str:
            memberName = member
            member = DisplayName.memberForName(memberName, ctx.message.guild)
            if not member:
                msg = 'I couldn\'t find *{}*...'.format(memberName)
                return await Utils.suppressed(ctx,msg)
        ts = int(member.joined_at.timestamp())
        joined = "<t:{}> (<t:{}:R>)".format(ts,ts)
        await ctx.send("*{}* joined {}".format(DisplayName.name(member),joined))
