import asyncio
import discord
from   discord.ext import commands
import os
import re
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
        self.nv_link = "https://gfe.nvidia.com/mac-update"

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
            
    def get_os(self, build_number):
        # Returns the best-guess OS version for the build number
        alpha = "abcdefghijklmnopqrstuvwxyz"
        os_version = "Unknown"
        major = minor = ""
        try:
            # Formula looks like this:  AAB; AA - 4 = 10.## version
            # B index in "ABCDEFGHIJKLMNOPQRSTUVXYZ" = 10.##.## version
            major = int(build_number[:2])-4
            minor = alpha.index(build_number[2:3].lower())
            os_version = "10.{}.{}".format(major, minor)
        except:
            pass
        return os_version
    
    def get_value(self, build_number):
        alpha = "abcdefghijklmnopqrstuvwxyz"
        # Split them up
        split = re.findall(r"[^\W\d_]+|\d+", i)
        start = split[0].rjust(4, "0")
        alph  = split[1]
        end   = split[2].rjust(6, "0")
        alpha_num = str(alpha.index(alph.lower())).rjust(2, "0")
        return int(start + alpha_num + end)
            
    @commands.command(pass_context=True)
    async def nvweb(self, ctx, os_build = None):
        """Prints the download url for the passed OS build number (if it exists).  If no build number is passed, prints the newest web driver link."""
        # Get the current manifest
        try:
            data = await DL.async_dl(self.nv_link)
            plist_data = plistlib.loads(data)
        except:
            await Message.Embed(
                title="⚠ An error occurred!", 
                description="I guess I couldn't get the manifest...\n\"{}\" may no longer be valid.".format(self.nv_link),
                color=ctx.author
            ).send(ctx)
            return
        # We have the plist data
        wd = None
        if os_build == None:
            # We just need the newest - let's give everything a numeric value
            alpha = "abcdefghijklmnopqrstuvwxyz"
            new_items = []
            for x in plist_data.get("updates", []):
                new_items.append({"update" : x, "value" : self.get_value(x["OS"])})
            sorted_list = sorted(new_items, key=lambda x:x["value"], reverse=True)
            if not len(sorted_list):
                await Message.Embed(
                    title="⚠ An error occurred!", 
                    description="There were no updates found at \"{}\".".format(self.nv_link),
                    color=ctx.author
                ).send(ctx)
                return
            wd = sorted_list[0]["update"]
        else:
            # We need to find it
            for x in plist_data.get("updates", []):
                if x["OS"].lower() == os_build.lower():
                    wd = x
                    break
            if not wd:
                if not len(sorted_list):
                    await Message.Embed(
                        title="⚠ An error occurred!", 
                        description="There were no web drivers found for \"{}\".".format(os_build),
                        color=ctx.author
                    ).send(ctx)
                    return
        await Message.Embed(
            title="Web Driver For {} ({})".format(self.get_os(wd["OS"]), wd["OS"]),
            description="[{}]({})".format(wd["version"], wd["downloadURL"]),
            color=ctx.author
        ).send(ctx)

            
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
