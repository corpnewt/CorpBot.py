import asyncio, discord, random
from   discord.ext import commands
from   Cogs import Utils, DisplayName, UserTime, PickList

async def setup(bot):
    # Add the bot and deps
    settings = bot.get_cog("Settings")
    await bot.add_cog(Example(bot, settings))

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

    @commands.command()
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
        # Get localized user time
        local_time = UserTime.getUserTime(ctx.author, self.settings, member.joined_at)
        time_str = "{} {}".format(local_time['time'], local_time['zone'])
        await ctx.send('*{}* joined *{}*'.format(DisplayName.name(member), time_str))