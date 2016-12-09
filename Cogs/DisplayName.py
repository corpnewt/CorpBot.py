import asyncio
import discord
from   discord.ext import commands

def name(member : discord.Member):
    # A helper function to return the member's display name
    nick = name = None
    try:
        nick = member.nick
    except AttributeError:
        pass
    try:
        name = member.name
    except AttributeError:
        pass
    if nick:
        return nick
    if name:
        return name
    return None

def memberForID(id, server):
    for member in server.members:
        if member.id == id:
            return member
    return None

def memberForName(name, server):
    # Check nick first - then name
    for member in server.members:
        if member.nick == name:
            return member
    for member in server.members:
        if member.name == name:
            return member
    # No member yet - try ID
    memID = ''.join(list(filter(str.isdigit, name)))
    newMem = memberForID(memID, server)
    if newMem:
        return newMem
    return None

def roleForID(id, server):
    for role in server.roles:
        if role.id == id:
            return role
    return None

def roleForName(name, server):
    for role in server.roles:
        if role.name == name:
            return role
    return None

def serverNick(user, server):
    for member in server.members:
        if member.id == user.id:
            return name(member)
    return None

def checkNameForInt(name, server):
    theList = name.split()
    # We see if we have multiple parts split by a space
    if len(theList)<2:
        # Only one part - no int included (or not separated by space)
        # Check if member exists - and if not throw an error, if so, throw a diff error
        amember = memberForName(name, server)
        if amember:
            # We at least have a member
            return { "Member" : amember, "Int" : None }
        else:
            # Now we check if we got an ID instead
            # Get just the numbers
            memID = ''.join(list(filter(str.isdigit, name)))
            newMem = memberForID(memID, server)
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
        amember = memberForName(newMemberName, server)
        if amember:
            return { "Member" : amember, "Int" : theInt }
        else:
            # Now we check if we got an ID instead
            # Get just the numbers
            memID = ''.join(list(filter(str.isdigit, newMemberName)))
            newMem = memberForID(memID, server)
            if newMem:
                # We FOUND it!
                return { "Member" : newMem, "Int" : theInt }
            else:
                # Nothing was right about this...
                return { "Member" : None, "Int" : None }
    except ValueError:
        # Last section wasn't an int
        amember = memberForName(name, server)
        if amember:
            # Name was just a member - return
            return { "Member" : amember, "Int" : None }
        else:
            # Now we check if we got an ID instead
            # Get just the numbers
            memID = ''.join(list(filter(str.isdigit, name)))
            newMem = memberForID(memID, server)
            if newMem:
                # We FOUND it!
                return { "Member" : newMem, "Int" : None }
            else:
                # Nothing was right about this...
                return { "Member" : None, "Int" : None }
    # Should never get here
    return None

def checkRoleForInt(name, server):
    theList = name.split()
    # We see if we have multiple parts split by a space
    if len(theList)<2:
        # Only one part - no int included (or not separated by space)
        # Check if role exists - and if not throw an error, if so, throw a diff error
        amember = roleForName(name, server)
        if amember:
            # We at least have a member
            return { "Role" : amember, "Int" : None }
        else:
            # Now we check if we got an ID instead
            # Get just the numbers
            memID = ''.join(list(filter(str.isdigit, name)))
            newMem = roleForID(memID, server)
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
        amember = roleForName(newMemberName, server)
        if amember:
            return { "Role" : amember, "Int" : theInt }
        else:
            # Now we check if we got an ID instead
            # Get just the numbers
            memID = ''.join(list(filter(str.isdigit, newMemberName)))
            newMem = roleForID(memID, server)
            if newMem:
                # We FOUND it!
                return { "Role" : newMem, "Int" : theInt }
            else:
                # Nothing was right about this...
                return { "Role" : None, "Int" : None }
    except ValueError:
        # Last section wasn't an int
        amember = roleForName(name, server)
        if amember:
            # Name was just a role - return
            return { "Role" : amember, "Int" : None }
        else:
            # Now we check if we got an ID instead
            # Get just the numbers
            memID = ''.join(list(filter(str.isdigit, name)))
            newMem = roleForID(memID, server)
            if newMem:
                # We FOUND it!
                return { "Role" : newMem, "Int" : None }
            else:
                # Nothing was right about this...
                return { "Role" : None, "Int" : None }
    # Should never get here
    return None