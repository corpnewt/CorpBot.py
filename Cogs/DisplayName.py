import asyncio
import discord
from   discord.ext import commands

def name(member : discord.Member):
    # A helper function to return the member's display name
    if member.nick:
        return member.nick
    elif member.name:
        return member.name
    else:
        return None

def memberForID(id, server):
    for member in server.members:
        if member.id == id:
            return member
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
