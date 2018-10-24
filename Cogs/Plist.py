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
from   Cogs        import DisplayName

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
        self.NVloop = None # Loop used for the Nvidia Webdriver update check, 
        #                    gets closed and opened on extension load/unload
        self.NVsec = 300 # 5 minute time-out per Nvdia Webdriver update check

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
            split = re.findall(r"[^\W\d_]+|\d+", build_number)
            major = int(split[0])-4
            minor = alpha.index(split[1].lower())
            os_version = "10.{}.{}".format(major, minor)
        except:
            pass
        return os_version
    
    def get_value(self, build_number):
        alpha = "abcdefghijklmnopqrstuvwxyz"
        # Split them up
        split = re.findall(r"[^\W\d_]+|\d+", build_number)
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
            await Message.EmbedText(
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
                await Message.EmbedText(
                    title="⚠ An error occurred!", 
                    description="There were no updates found at \"{}\".".format(self.nv_link),
                    color=ctx.author
                ).send(ctx)
                return
            wd = [{
                    "name": "{} ({})".format(
                        self.get_os(sorted_list[0]["update"]["OS"]),
                        sorted_list[0]["update"]["OS"]),
                    "value": "└─ [{}]({})".format(
                        sorted_list[0]["update"]["version"],
                        sorted_list[0]["update"]["downloadURL"]
                    ),
                    "inline": False
                }]
        else:
            # We need to find it
            mwd = next((x for x in plist_data.get("updates", []) if x["OS"].lower() == os_build.lower()), None)
            if mwd:
                wd = [{
                    "name": "{} ({})".format(self.get_os(mwd["OS"]), mwd["OS"]),
                    "value": "└─ [{}]({})".format(mwd["version"], mwd["downloadURL"]),
                    "inline": False
                }]
            else:
                # We didn't get an exact match, let's try to determine what's up
                # First check if it's a build number (##N####) or OS number (10.##.##)
                p = os_build.split(".")
                p = [x for x in p if x != ""]
                if len(p) > 1 and len(p) < 4:
                    # We have . separated stuffs
                    wd_list = [x for x in plist_data.get("updates", []) if self.get_os(x["OS"]).startswith(os_build)]
                    if len(wd_list):
                        # We got some matches
                        wd = []
                        for i in wd_list:
                            wd.append({
                                "name": "{} ({})".format(self.get_os(i["OS"]), i["OS"]),
                                "value": "└─ [{}]({})".format(i["version"], i["downloadURL"]),
                                "inline": False
                            })
            if not wd:
                await Message.EmbedText(
                    title="⚠ An error occurred!", 
                    description="There were no web drivers found for \"{}\".".format(os_build),
                    color=ctx.author
                ).send(ctx)
                return
        await Message.Embed(
            title="NVIDIA Web Driver Results For \"{}\" ({} total)".format(os_build if os_build != None else "Latest", len(wd)),
            fields=wd,
            color=ctx.author,
            pm_after=25,
            footer="All links pulled from {}".format(self.nv_link)
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

    @asyncio.coroutine
    async def on_unloaded_extension(self, ext):
        # Check if we were unloaded
        if not self.settings._is_submodule(ext.__name__, self.__module__):
            # We weren't, return
            return

        # Stop our loop
        self.NVloop.cancel()

    @asyncio.coroutine
    async def on_loaded_extension(self, ext):
        # Check if we were loaded
        if not self.settings._is_submodule(ext.__name__, self.__module__):
            # We weren't, return
            return

        self.NVloop = self.bot.loop.create_task(self.checkLoop())

    async def checkLoop(self):
        print("Starting NvUpdate loop - runs every {} seconds".format(self.NVsec))
        originalFile = await DL.async_dl(self.nv_link)

        while not self.bot.is_closed():
            checkFile = await DL.async_dl(self.nv_link)

            if checkFile != originalFile:
                # There's a new webdriver, load the plist and read the info we want from it
                plist = plistlib.readPlistFromBytes(checkFile)

                # Set the file to check to the file we *just* pulled so we don't get spammed with updates
                originalFile = checkFile

                # BUILD AN EMBED
                updateEmbed = discord.Embed(title="New Nvidia WebDriver available!", url=plist["updates"][0]["downloadURL"])    # Webdriver URL
                updateEmbed.add_field(name="Webdriver version", value=plist["updates"][0]["version"], inline=True)              # Webdriver version
                updateEmbed.add_field(name="MacOS build number", value=plist["updates"][0]["OS"], inline=True)                  # macOS build number
                new_size = int(plist["updates"][0]["size"])/1000000
                new_size = str(new_size)[:4]
                updateEmbed.add_field(name="Size (Mb)", value="{} Mb".format(new_size), inline=True)                            # Webdriver size

                # Send the embed to all the people *subscribed* to the Webdriver updates
                for guild in self.bot.guilds:
                    # Get the channel ID
                    c = self.settings.getServerStat(guild, "NvUpdateChannel")
                    if not c:
                        # No ID, not subscribed to Webdriver updates
                        continue
                    # Try to get a discord.Channel object for the channel ID
                    chan = DisplayName.channelForName(c, guild)
                    if not chan:
                        # There's none, inform the owner and continue
                        prefix = self.settings.getServerStat(guild, "Prefix")
                        if not prefix:
                            prefix = self.bot.command_prefix
                        await guild.owner.send("Hi! The channel for Nvidia Webdriver updates is currently set to ID {}. Unfortunaly, this channel does not exist anymore. Please use {}nvupdate [channel] to either clear or set a channel.").format(c, prefix)
                        continue

                    await chan.send(embed=updateEmbed)

            # Sleep, then check for updates
            await asyncio.sleep(self.NVsec)


    @commands.command(pass_context=True)
    async def nvupdate(self, ctx, channel = None):
        """Set the channel Nvidia Webdriver updates should be sent in. Will clear if channel is not set."""
        isAdmin = ctx.author.permissions_in(ctx.channel).administrator
        # Only allow admins to change server stats
        if not isAdmin: 
            await ctx.channel.send('You do not have sufficient privileges to access this command.')
            return

        # Clear the nvupdatechannel if no channel passed, disabling updates to the channel
        if not channel:
            self.settings.setServerStat(ctx.guild, "NvUpdateChannel", None)
            await ctx.send("NvUpdate channel cleared!")
            return

        # Try and find a channel for the string passed
        chan = DisplayName.channelForName(channel, ctx.guild)

        if not chan:
            # We couldn't find anything
            await ctx.send("I couldn't find that channel...".format(channel))
            return

        # Check if the new channel is already the thing we want to set
        updateChannel = self.settings.getServerStat(ctx.guild, "NvUpdateChannel")
        if str(updateChannel) == str(chan.id):
            await ctx.send("NvUpdate channel is already set to {}!".format(chan.mention))
            return

        # Set the new channel ID as the NvUpdate channel
        self.settings.setServerStat(ctx.guild, "NvUpdateChannel", str(chan.id))
        await ctx.send("NvUpdate channel set to {}!".format(chan.mention))