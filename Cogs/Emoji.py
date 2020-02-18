import discord, os
from discord.ext import commands
from Cogs import GetImage, Utils

def setup(bot):
    bot.add_cog(Emoji(bot))

class Emoji(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    def _get_emoji_url(self, emoji):
        if len(emoji) < 3:
            # Emoji is likely a built-in like :)
            h = "-".join([hex(ord(x)).lower()[2:] for x in emoji])
            return ("https://github.com/twitter/twemoji/raw/master/assets/72x72/{}.png".format(h),h)
        # Must be a custom emoji
        emojiparts = emoji.replace("<","").replace(">","").split(":") if emoji else []
        if not len(emojiparts) == 3: return None
        # Build a custom emoji object
        emoji_obj = discord.PartialEmoji(animated=len(emojiparts[0]) > 0, name=emojiparts[1], id=emojiparts[2])
        # Return the url
        return (emoji_obj.url,emoji_obj.name)

    def _get_emoji_mention(self, emoji):
        return "<{}:{}:{}>".format("a" if emoji.animated else "",emoji.name,emoji.id)

    @commands.command()
    async def addemoji(self, ctx, *, emoji = None, name = None):
        '''Adds the passed emoji, url, or attachment as a custom emoji with the passed name (bot-admin only).'''
        if not await Utils.is_bot_admin_reply(ctx): return
        if not len(ctx.message.attachments) and emoji == name == None:
            return await ctx.send("Usage: `{}addemoji [emoji, url, attachment] [name]`".format(ctx.prefix))
        # Let's find out if we have an attachment, emoji, or a url
        # Check attachments first - as they'll have priority
        if len(ctx.message.attachments):
            name = emoji
            emoji = ctx.message.attachments[0].url
        else:
            # We can assume we have something text based, let's split, set emoji to the first item, and name
            # to anything else with spaces replaced by _
            emoji_parts = emoji.split()
            emoji = emoji_parts[0]
            if len(emoji_parts) > 1:
                name = "_".join(emoji_parts[1:])
        # Now we should have the emoji - let's see if we have a direct url, or if it's an emoji item
        urls = Utils.get_urls(emoji)
        if urls:
            # It's a url - sweet, save only the first
            emoji = (urls[0], os.path.basename(urls[0]).split(".")[0])
        else:
            # It's not a url - check if it's an emoji
            emoji = self._get_emoji_url(emoji)
        if not emoji:
            # Something is bonked
            return await ctx.send("The passed emoji, url, or attachment was not valid.")
        # Let's try to download it
        emoji, e_name = emoji # Expand into the parts
        f = await GetImage.download(emoji)
        if not f: return await ctx.send("I couldn't get that image :(")
        # Open the image file
        with open(f,"rb") as e:
            image = e.read()
        # Clean up
        GetImage.remove(f)
        # Let's get the name
        if not name:
            name = os.path.basename(e_name).split(".")[0]
        # Ensure it's only A-Z,0-9 or _ in the name
        name = "".join([x for x in name if x.isalnum() or x is "_"])
        if not name.replace("_",""): return await ctx.send("Invalid name - cannot create this emoji.")
        # Create the emoji and display it
        try: new_emoji = await ctx.guild.create_custom_emoji(name=name,image=image,roles=None,reason="Added by {}#{}".format(ctx.author.name,ctx.author.discriminator))
        except: return await ctx.send("Something went wrong creating that emoji :(")
        await ctx.send("Created `:{}:` - {}".format(new_emoji.name,self._get_emoji_mention(new_emoji)))

    @commands.command()
    async def emoji(self, ctx, emoji = None):
        '''Outputs the passed emoji... but bigger!'''
        if emoji is None:
            await ctx.send("Usage: `{}emoji [emoji]`".format(ctx.prefix))
            return
        # Get the emoji
        emoji_url = self._get_emoji_url(emoji)
        if not emoji_url: return await ctx.send("Usage: `{}emoji [emoji]`".format(ctx.prefix))
        f = await GetImage.download(emoji_url[0])
        if not f: return await ctx.send("I couldn't get that emoji :(")
        await ctx.send(file=discord.File(f))
        # Clean up
        GetImage.remove(f)
