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
        '''Outputs your CUSTOM emoji... but bigger! (Does not work with standard discord emojis)'''
        emojiparts = emoji.replace("<","").replace(">","").split(":") if emoji else []
        if not len(emojiparts) == 3:
            await ctx.send("Usage: `{}emoji [emoji]` - must be a CUSTOM emoji, and not just the name.".format(ctx.prefix))
            return
        emoji_obj = discord.PartialEmoji(len(emojiparts[0]) > 0, emojiparts[1], emojiparts[2])
        if not emoji_obj.url:
            await ctx.send("Could not find url for emoji :(")
            return
        f = await GetImage.download(emoji_obj.url)
        if not f:
            await ctx.send("I couldn't get that emoji :(")
            return
        await ctx.send(file=discord.File(f))