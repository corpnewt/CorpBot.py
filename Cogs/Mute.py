import asyncio
import discord
import time
from Cogs import DisplayName
from Cogs import Nullify

def setup(bot):
    # Add the bot and deps
    settings = bot.get_cog("Settings")
    bot.add_cog(Mute(bot, settings))

class Mute:

    # Init with the bot reference, and a reference to the settings var
    def __init__(self, bot, settings):
        self.bot = bot
        self.settings = settings
        self.loop_list = []

    def _is_submodule(self, parent, child):
        return parent == child or child.startswith(parent + ".")

    async def onjoin(self, member, server):
        # Check id against the mute list and react accordingly
        mute_list = self.settings.getServerStat(server, "MuteList")
        for mem in mute_list:
            if str(member.id) == str(mem["ID"]):
                # The user was muted when they left - remute
                cd = mem["Cooldown"]
                await self.mute(member, server, cd)

    @asyncio.coroutine
    async def on_unloaded_extension(self, ext):
        # Called to shut things down
        if not self._is_submodule(ext.__name__, self.__module__):
            return
        for task in self.loop_list:
            task.cancel()

    @asyncio.coroutine
    async def on_loaded_extension(self, ext):
        # See if we were loaded
        if not self._is_submodule(ext.__name__, self.__module__):
            return
        # Check all mutes and start timers
        for server in self.bot.guilds:
            muteList = self.settings.getServerStat(server, "MuteList")
            for entry in muteList:
                member = DisplayName.memberForID(entry['ID'], server)
                if member:
                    # We have a user! Check for a cooldown
                    cooldown = entry['Cooldown']
                    if cooldown == None:
                        continue
                    self.loop_list.append(self.bot.loop.create_task(self.checkMute(member, server, cooldown)))
        # Add a loop to remove expired mutes in the MuteList
        self.loop_list.append(self.bot.loop.create_task(self.mute_list_check()))
                    
        
    def suppressed(self, guild, msg):
        # Check if we're suppressing @here and @everyone mentions
        if self.settings.getServerStat(guild, "SuppressMentions"):
            return Nullify.clean(msg)
        else:
            return msg

    async def onjoin(self, member, server):
        # Check if the new member was muted when they left
        muteList = self.settings.getServerStat(server, "MuteList")
        for entry in muteList:
            if str(entry['ID']) == str(member.id):
                # Found them - mute them
                await self.mute(member, server, entry['Cooldown'])
            
    async def mute_list_check(self):
        while not self.bot.is_closed():
            # Iterate through the servers and check for roll-off mutes
            for guild in self.bot.guilds:
                mute_list = self.settings.getServerStat(guild, "MuteList")
                # Go through the id's and check for orphaned ones
                remove_mute = []
                for entry in mute_list:
                    if guild.get_member(int(entry["ID"])):
                        # Still on the server - ignore
                        continue
                    if entry["Cooldown"] == None:
                        # Perma-muted - let's see if we have a rolloff time
                        if not "Added" in entry:
                            # Old mute - set "Added" to now
                            entry["Added"] = int(time.time())
                            continue
                        # See if we're over 90 days and remove perma mute
                        if int(time.time())-int(entry["Added"]) > 3600*24*90:
                            remove_mute.append(entry)
                        continue
                    if int(entry["Cooldown"])-int(time.time()) > 0:
                        # Still going on
                        continue
                    # We can remove them
                    remove_mute.append(entry)
                if len(remove_mute) == 0:
                    # No one to remove
                    continue
                for entry in remove_mute:
                    mute_list.remove(entry)
                self.settings.setServerStat(guild, "MuteList", mute_list)
            # Check once per hour
            await asyncio.sleep(3600)
            
    def _remove_task(self, task):
        if task in self.loop_list:
            self.loop_list.remove(task)

    async def checkMute(self, member, server, cooldown):
        # Get the current task
        task = asyncio.Task.current_task()
        # Check if we have a cooldown left - and unmute accordingly
        timeleft = int(cooldown)-int(time.time())
        if timeleft > 0:
            # Time to wait yet - sleep
            await asyncio.sleep(timeleft)

        # We've waited it out - unmute if needed
        # But check if the mute time has changed
        cd = self.settings.getUserStat(member, server, "Cooldown")
        isMute = self.settings.getUserStat(member, server, "Muted")
        
        if cd == None:
            if isMute.lower() == 'yes':
                # We're now muted permanently
                self._remove_task(task)
                return
        else:
            timeleft = int(cd)-int(time.time())
            if timeleft > 0:
                # Our cooldown changed - rework
                self.loop_list.append(self.bot.loop.create_task(self.checkMute(member, server, cd)))
                self._remove_task(task)
                return

        # Here - we either have surpassed our cooldown - or we're not muted anymore
        isMute = self.settings.getUserStat(member, server, "Muted")
        if isMute:
            await self.unmute(member, server)
            pm = 'You have been **Unmuted**.\n\nYou can send messages on *{}* again.'.format(self.suppressed(server, server.name))
            await member.send(pm)
        self._remove_task(task)


    async def mute(self, member, server, cooldown = None):
        # Mutes the specified user on the specified server
        for channel in server.channels:
            if not type(channel) is discord.TextChannel:
                continue
            perms = member.permissions_in(channel)
            if perms.read_messages:
                overs = channel.overwrites_for(member)
                if not overs.send_messages == False:
                    # We haven't been muted here yet
                    overs.send_messages = False
                    overs.add_reactions = False
                    try:
                        await channel.set_permissions(member, overwrite=overs)
                    except Exception:
                        continue
        
        self.settings.setUserStat(member, server, "Muted", True)
        self.settings.setUserStat(member, server, "Cooldown", cooldown)

        muteList = self.settings.getServerStat(server, "MuteList")
        
        # check if we're already muted
        found = False
        for entry in muteList:
            if str(entry['ID']) == str(member.id):
                # Set the cooldown
                found = True
                entry['Cooldown'] = cooldown
                break
        if not found:
            muteList.append({ 'ID': member.id, 'Cooldown': cooldown, 'Added' : int(time.time()) })
        
        if not cooldown == None:
            # We have a cooldown - set a timer
            self.loop_list.append(self.bot.loop.create_task(self.checkMute(member, server, cooldown)))


    async def unmute(self, member, server):
        # Unmutes the specified user on the specified server
        for channel in server.channels:
                if not type(channel) is discord.TextChannel:
                    continue
                perms = member.permissions_in(channel)
                if perms.read_messages:
                    overs = channel.overwrites_for(member)
                    otherPerms = False
                    for perm in overs:
                        if not perm[1] == None and not str(perm[0]) == 'send_messages' and not str(perm[0]) == 'add_reactions':
                            otherPerms = True
                    if overs.send_messages == False:
                        # We haven't been muted here yet
                        if otherPerms:
                            # We have other overwrites - preserve those
                            overs.send_messages = None
                            overs.add_reactions = None
                            try:
                                await channel.set_permissions(member, overwrite=overs)
                            except Exception:
                                continue
                        else:
                            # No other overwrites - delete custom perms
                            try:
                                await channel.set_permissions(member, overwrite=None)
                            except Exception:
                                continue
        self.settings.setUserStat(member, server, "Muted", False)
        self.settings.setUserStat(member, server, "Cooldown", None)

        muteList = self.settings.getServerStat(server, "MuteList")
        for entry in muteList:
            if str(entry['ID']) == str(member.id):
                # Found them - remove from the mutelist
                muteList.remove(entry)
