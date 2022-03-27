import asyncio
import discord
import re
from   discord.ext import commands
from   Cogs import Nullify

def setup(bot):
    # This module isn't actually a cog - but it is a place
    # we can start small fires and watch them burn the entire
    # house to the ground.
    bot.add_cog(DisplayName(bot))

class DisplayName(commands.Cog):
    def __init__(self,bot):
        self.bot = bot

    def name(self, member : discord.Member):
        # A helper function to return the member's display name
        return Nullify.escape_all(getattr(member,"display_name",member.name))

    def memberForID(self, checkid, server):
        try:
            return server.get_member(int(checkid)) if server else self.bot.get_user(int(checkid))
        except:
            return None

    def memberForName(self, name, server):
        mems = server.members if server else self.bot.users
        # Check nick first - then name
        name = str(name)
        for member in mems:
            if not hasattr(member,"nick"):
                # No nick property - must be a user, bail
                break
            if member.nick and member.nick.lower() == name.lower():
                return member
        for member in mems:
            if member.name.lower() == name.lower():
                return member
        mem_parts = name.split("#")
        if len(mem_parts) == 2:
            # We likely have a name#descriminator
            try:
                mem_name = mem_parts[0]
                mem_disc = int(mem_parts[1])
            except:
                mem_name = mem_disc = None
            if mem_name:
                for member in mems:
                    if member.name.lower() == mem_name.lower() and int(member.discriminator) == mem_disc:
                        return member
        mem_id = re.sub(r'\W+', '', name)
        new_mem = self.memberForID(mem_id, server)
        if new_mem:
            return new_mem
        
        return None

    def channelForID(self, checkid, server, typeCheck = None):
        try:
            checkid = int(checkid)
        except:
            return None
        for channel in server.channels:
            if typeCheck:
                if typeCheck.lower() == "text" and not type(channel) is discord.TextChannel:
                    continue
                if typeCheck.lower() == "voice" and not type(channel) is discord.VoiceChannel:
                    continue
                if typeCheck.lower() == "category" and not type(channel) is discord.CategoryChannel:
                    continue
            if channel.id == checkid:
                return channel
        return None

    def channelForName(self, name, server, typeCheck = None):
        name = str(name)
        for channel in server.channels:
            if typeCheck:
                if typeCheck.lower() == "text" and not type(channel) is discord.TextChannel:
                    continue
                if typeCheck.lower() == "voice" and not type(channel) is discord.VoiceChannel:
                    continue
                if typeCheck.lower() == "category" and not type(channel) is discord.CategoryChannel:
                    continue
            if channel.name.lower() == name.lower():
                return channel
        chanID = re.sub(r'\W+', '', name)
        newChan = self.channelForID(chanID, server, typeCheck)
        if newChan:
            return newChan
        return None

    def roleForID(self, checkid, server):
        try:
            checkid = int(checkid)
        except:
            return None
        for role in server.roles:
            if role.id == checkid:
                return role
        return None

    def roleForName(self, name, server):
        name = str(name)
        # Adjust for "everyone"
        if name.lower() == "everyone":
            name = "@everyone"
        for role in server.roles:
            if role.name.lower() == name.lower():
                return role
        # No role yet - try ID
        roleID = ''.join(list(filter(str.isdigit, name)))
        newRole = self.roleForID(roleID, server)
        if newRole:
            return newRole
        return None

    def serverNick(self, user, server):
        for member in server.members:
            if member.id == user.id:
                return self.name(member)
        return None

    def checkNameForInt(self, name, server):
        name = str(name)
        theList = name.split()
        # We see if we have multiple parts split by a space
        if len(theList)<2:
            # Only one part - no int included (or not separated by space)
            # Check if member exists - and if not throw an error, if so, throw a diff error
            amember = self.memberForName(name, server)
            if amember:
                # We at least have a member
                return { "Member" : amember, "Int" : None }
            else:
                # Now we check if we got an ID instead
                # Get just the numbers
                memID = ''.join(list(filter(str.isdigit, name)))
                newMem = self.memberForID(memID, server)
                if newMem:
                    # We FOUND it!
                    return { "Member" : newMem, "Int" : None }
                else:
                    # Nothing was right about this...
                    return { "Member" : None, "Int" : None }
        try:
            # Let's cast the last item as an int and catch any exceptions
            theInt = int(theList[len(theList)-1])
            newMemberName = " ".join(theList[:-1])
            amember = self.memberForName(newMemberName, server)
            if amember:
                return { "Member" : amember, "Int" : theInt }
            else:
                # Now we check if we got an ID instead
                # Get just the numbers
                memID = ''.join(list(filter(str.isdigit, newMemberName)))
                newMem = self.memberForID(memID, server)
                if newMem:
                    # We FOUND it!
                    return { "Member" : newMem, "Int" : theInt }
                else:
                    # Nothing was right about this...
                    return { "Member" : None, "Int" : None }
        except ValueError:
            # Last section wasn't an int
            amember = self.memberForName(name, server)
            if amember:
                # Name was just a member - return
                return { "Member" : amember, "Int" : None }
            else:
                # Now we check if we got an ID instead
                # Get just the numbers
                memID = ''.join(list(filter(str.isdigit, name)))
                newMem = self.memberForID(memID, server)
                if newMem:
                    # We FOUND it!
                    return { "Member" : newMem, "Int" : None }
                else:
                    # Nothing was right about this...
                    return { "Member" : None, "Int" : None }
        # Should never get here
        return None

    def checkRoleForInt(self, name, server):
        name = str(name)
        theList = name.split()
        # We see if we have multiple parts split by a space
        if len(theList)<2:
            # Only one part - no int included (or not separated by space)
            # Check if role exists - and if not throw an error, if so, throw a diff error
            amember = self.roleForName(name, server)
            if amember:
                # We at least have a member
                return { "Role" : amember, "Int" : None }
            else:
                # Now we check if we got an ID instead
                # Get just the numbers
                memID = ''.join(list(filter(str.isdigit, name)))
                newMem = self.roleForID(memID, server)
                if newMem:
                    # We FOUND it!
                    return { "Role" : newMem, "Int" : None }
                else:
                    # Nothing was right about this...
                    return { "Role" : None, "Int" : None }
        try:
            # Let's cast the last item as an int and catch any exceptions
            theInt = int(theList[len(theList)-1])
            newMemberName = " ".join(theList[:-1])
            amember = self.roleForName(newMemberName, server)
            if amember:
                return { "Role" : amember, "Int" : theInt }
            else:
                # Now we check if we got an ID instead
                # Get just the numbers
                memID = ''.join(list(filter(str.isdigit, newMemberName)))
                newMem = self.roleForID(memID, server)
                if newMem:
                    # We FOUND it!
                    return { "Role" : newMem, "Int" : theInt }
                else:
                    # Nothing was right about this...
                    return { "Role" : None, "Int" : None }
        except ValueError:
            # Last section wasn't an int
            amember = self.roleForName(name, server)
            if amember:
                # Name was just a role - return
                return { "Role" : amember, "Int" : None }
            else:
                # Now we check if we got an ID instead
                # Get just the numbers
                memID = ''.join(list(filter(str.isdigit, name)))
                newMem = self.roleForID(memID, server)
                if newMem:
                    # We FOUND it!
                    return { "Role" : newMem, "Int" : None }
                else:
                    # Nothing was right about this...
                    return { "Role" : None, "Int" : None }
        # Should never get here
        return None
