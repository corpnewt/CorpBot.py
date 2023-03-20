import discord, os
from discord.ext import commands
from Cogs import GetImage, Utils

def setup(bot):
    bot.add_cog(Emoji(bot))

class Emoji(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.max_emojis = 10
        global Utils, DisplayName
        Utils = self.bot.get_cog("Utils")
        DisplayName = self.bot.get_cog("DisplayName")

    def _get_emoji_url(self, emoji):
        emojiparts = emoji.replace("<","").replace(">","").split(":") if emoji else []
        if not len(emojiparts) == 3:
            # Emoji is likely a built-in like :)
            h = "-".join([hex(ord(x)).lower()[2:] for x in emoji])
            if any((len(x)<4 for x in h.split("-"))): return None # We got a built-in emoji, but it lacks proper hex setup
            return ("https://github.com/twitter/twemoji/raw/master/assets/72x72/{}.png".format(h),h)
        # Build a custom emoji object
        emoji_obj = discord.PartialEmoji(animated=len(emojiparts[0]) > 0, name=emojiparts[1], id=emojiparts[2])
        # Return the url
        return (emoji_obj.url,emoji_obj.name)

    def _get_emoji_mention(self, emoji):
        return "<{}:{}:{}>".format("a" if emoji.animated else "",emoji.name,emoji.id)

    @commands.command(aliases=["addemote"])
    async def addemoji(self, ctx, *, emoji = None, name = None):
        '''Adds the passed emoji, url, or attachment as a custom emoji with the passed name.  Names can only contain alphanumeric and underscore chars (bot-admin only, max of 10).'''
        usage = "Usage: `{}addemoji [emoji, url, attachment] [name]`".format(ctx.prefix)
        if not await Utils.is_bot_admin_reply(ctx): return
        if not ctx.message.attachments and emoji is name is None:
            return await ctx.send(usage)
        # Let's find out if we have an attachment, emoji, or a url
        # Check attachments first - as they'll have priority
        if ctx.message.attachments:
            name = emoji
            emoji = " ".join([x.url for x in ctx.message.attachments])
            if name: # Add the name separated by a space
                emoji += " "+name
        # Now we split the emoji string, and walk it, looking for urls, emojis, and names
        emoji_urls  = []
        emoji_names = []
        for x in emoji.split():
            # Let's see if we have an emoji or a name
            urls = Utils.get_urls(x)
            url = urls[0] if urls else self._get_emoji_url(x)
            if url: # Got an emoji URL
                emoji_urls.append(url)
            else: # Not a URL, must be a name
                emoji_names.append(x)
        # Let's walk our URLs - and map them to names if possible, or rip the name from the URL itself
        emojis_to_add = []
        for i,url in enumerate(emoji_urls):
            name = None
            if isinstance(url,(tuple,list)):
                url,name = url
            if i<len(emoji_names):
                name = "".join([z for z in emoji_names[i] if z.isalnum() or z=="_"])
            else:
                if not name:
                    name = os.path.basename(url).split(".")[0]
            emojis_to_add.append((url,name))
        if not emojis_to_add: return await ctx.send("Usage: `{}addemoji [list of names and emojis/urls/attachments]`".format(ctx.prefix))
        # Now we have a list of emojis and names
        added_emojis = []
        allowed = min(len(emojis_to_add),self.max_emojis)
        omitted = " ({} omitted, beyond the limit of {})".format(len(emojis_to_add)-self.max_emojis,self.max_emojis) if len(emojis_to_add)>self.max_emojis else ""
        message = await ctx.send("Adding {} emoji{}{}...".format(
            allowed,
            "" if allowed==1 else "s",
            omitted))
        for emoji_to_add in emojis_to_add[:self.max_emojis]:
            # Let's try to download it
            emoji,e_name = emoji_to_add # Expand into the parts
            f = await GetImage.download(emoji)
            if not f: continue
            # Open the image file
            with open(f,"rb") as e:
                image = e.read()
            # Clean up
            GetImage.remove(f)
            # Ensure the name isn't *just* underscores
            if not e_name.replace("_",""): continue
            # Create the emoji and save it
            try: new_emoji = await ctx.guild.create_custom_emoji(name=e_name,image=image,roles=None,reason="Added by {}#{}".format(ctx.author.name,ctx.author.discriminator))
            except: continue
            added_emojis.append(new_emoji)
        msg = "Created {} of {} emoji{}{}.".format(
            len(added_emojis),
            allowed,"" if allowed==1 else "s",
            omitted
            )
        if len(added_emojis):
            msg += "\n\n"
            emoji_text = ["{} - `:{}:`".format(self._get_emoji_mention(x),x.name) for x in added_emojis]
            msg += "\n".join(emoji_text)
        await message.edit(content=msg)

    @commands.command(aliases=["emote"])
    async def emoji(self, ctx, emoji = None):
        '''Outputs the passed emoji... but bigger!'''
        if emoji is None:
            return await ctx.send("Usage: `{}emoji [emoji]`".format(ctx.prefix))
        # Get the emoji
        emoji_url = self._get_emoji_url(emoji)
        if not emoji_url: return await ctx.send("Usage: `{}emoji [emoji]`".format(ctx.prefix))
        f = await GetImage.download(emoji_url[0])
        if not f: return await ctx.send("I couldn't get that emoji :(")
        await ctx.send(file=discord.File(f))
        # Clean up
        GetImage.remove(f)
