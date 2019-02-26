import discord
from discord.ext import commands
import random

def setup(bot):
    bot.add_cog(Groot(bot))

class Groot(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def groot(self, ctx):
        """Who... who are you?"""
        groots = [
            "I am Groot",
            "**I AM GROOT**",
            "I... am... *Groot*",
            "I am Grooooot",
        ]
        punct = [
            "!",
            ".",
            "?"
        ]
        # Build our groots
        groot_max = 5
        groot = " ".join([random.choice(groots) + (random.choice(punct)*random.randint(0, 5)) for x in range(random.randint(1, groot_max))])
        await ctx.send(groot)