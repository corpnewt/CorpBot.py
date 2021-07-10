from   discord.ext import commands
from   Cogs import DL

def setup(bot):
    # Add the bot
    bot.add_cog(HackAudio(bot))

# layouts/alcids is a simple command that allows members to quickly retrieve all the available
# layout id's for a certain audio codec by *reading* the AppleALC GitHub repository

class HackAudio(commands.Cog):
    
	# Init with the bot reference
    def __init__(self, bot):
        self.bot = bot

    @commands.command(aliases=["alcids"])
    async def layouts(self, ctx, codec : str = None):
        """Search the AppleALC repository for available codec layouts."""

        if codec is None:
            return await ctx.send("Usage: `{}layouts [codec]`".format(ctx.prefix))

        layouts = []
        req_url = "https://api.github.com/repos/acidanthera/AppleALC/contents/Resources/{}".format(codec.upper())
        # Try to find available layouts and store them in a list
        try:
            response = await DL.async_json(req_url)
            for file in response:
                if file["name"].startswith("layout"):
                    layouts.append(file["name"].replace("layout", "").replace(".xml", ""))
        # No such directory
        except:
            return await ctx.send("I couldn't find that codec!")

        msg = '**Available layouts for codec *{}*:**\nlayout {}'.format(codec.upper(), ', '.join(map(str, sorted(layouts, key=len))))
        await ctx.send(msg)
        