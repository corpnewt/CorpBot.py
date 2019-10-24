import discord
from discord.ext import commands
from Cogs import GetImage

def setup(bot):
    bot.add_cog(Emoji(bot))

class Emoji(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def emoji(self, ctx, emoji = None):
        '''Outputs the passed emoji... but bigger!'''
        if emoji is None:
            await ctx.send("Usage: `{}emoji [emoji]`".format(ctx.prefix))
            return
        if len(emoji) < 3:
            # Try to get just the unicode
            h = "-".join([hex(ord(x)).lower()[2:] for x in emoji])
            url = "https://raw.githubusercontent.com/twitter/twemoji/gh-pages/2/72x72/{}.png".format(h)
            f = await GetImage.download(url)
            if not f:
                await ctx.send("I couldn't get that emoji :(")
            else:
                await ctx.send(file=discord.File(f))
            return
        emojiparts = emoji.replace("<","").replace(">","").split(":") if emoji else []
        if not len(emojiparts) == 3:
            await ctx.send("Usage: `{}emoji [emoji]`".format(ctx.prefix))
            return
        emoji_obj = discord.PartialEmoji(animated=len(emojiparts[0]) > 0, name=emojiparts[1], id=emojiparts[2])
        if not emoji_obj.url:
            await ctx.send("Could not find a url for that emoji :(")
            return
        f = await GetImage.download(emoji_obj.url)
        if not f:
            await ctx.send("I couldn't get that emoji :(")
            return
        await ctx.send(file=discord.File(f))
