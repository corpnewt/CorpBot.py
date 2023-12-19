from discord.ext import commands
import random

def setup(bot):
    bot.add_cog(RPS(bot))

class RPS(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.rps_dict = {
            "rock":"scissors",
            "paper":"rock",
            "scissors":"paper"
        }

    @commands.command(aliases=["prs","rockpaperscissors","paperscissorsrock"])
    async def rps(self, ctx, choice = None):
        """Play rock, paper, scissors."""

        # Make sure we got something from the user
        if not choice:
            return await ctx.send("Usage: `{}rps [choice]`".format(ctx.prefix))
        # Make sure it matches one of the options
        player = next((x for x in self.rps_dict if x.startswith(choice.lower())),None)
        if not player:
            return await ctx.send("Please choose rock, paper, or scissors.")
        # Get the bot's choice and report the results
        comp = random.choice(list(self.rps_dict))
        if player == comp:
            await ctx.send("I also chose {} - it's a tie!".format(comp))
        elif self.rps_dict[player] == comp:
            await ctx.send("{} beats {} - YOU WIN!".format(player.capitalize(),comp))
        else:
            await ctx.send("{} beats {} - I WIN!".format(comp.capitalize(),player))