import asyncio
import discord
from   discord.ext import commands
import os
import tempfile
import shutil
import plistlib
from   Cogs        import DL
from   Cogs        import Message

def setup(bot):
    # Add the bot and deps
    settings = bot.get_cog("Settings")
    bot.add_cog(Plist(bot, settings))

class Plist:

    # Init with the bot reference
    def __init__(self, bot, settings):
        self.bot = bot
        self.settings = settings

    async def download(self, url):
        url = url.strip("<>")
        # Set up a temp directory
        dirpath = tempfile.mkdtemp()
        tempFileName = url.rsplit('/', 1)[-1]
        # Strip question mark
        tempFileName = tempFileName.split('?')[0]
        imagePath = dirpath + "/" + tempFileName
        rImage = None
        
        try:
            rImage = await DL.async_dl(url)
        except:
            pass
        if not rImage:
            self.remove(dirpath)
            return None

        with open(imagePath, 'wb') as f:
            f.write(rImage)

        # Check if the file exists
        if not os.path.exists(imagePath):
            self.remove(dirpath)
            return None

        return imagePath
        
    def remove(self, path):
        if not path == None and os.path.exists(path):
            shutil.rmtree(os.path.dirname(path), ignore_errors=True)
            
    @commands.command(pass_context=True)
    async def plist(self, ctx, *, url = None):
        """Validates plist file structure.  Accepts a url - or picks the first attachment."""
        if url == None and len(ctx.message.attachments) == 0:
            await ctx.send("Usage: `{}plist [url or attachment]`".format(ctx.prefix))
            return

        if url == None:
            url = ctx.message.attachments[0].url
            
        message = await Message.Embed(description="Downloading...", color=ctx.author).send(ctx)
        
        path = await self.download(url)
        if not path:
            await Message.Embed(title="⚠ An error occurred!", description="I guess I couldn't get that plist...  Make sure you're passing a valid url or attachment.").edit(ctx, message)
            return
        
        try:
            plist_data = plistlib.readPlist(path)
        except Exception as e:
            await Message.Embed(title="❌ Plist format invalid!", description=str(e)).edit(ctx, message)
            self.remove(path)
            return
        await Message.Embed(title="✅ Plist format OK!").edit(ctx, message)
        self.remove(path)
