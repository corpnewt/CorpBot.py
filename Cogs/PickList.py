import asyncio
import discord
from   discord.ext import commands

def setup(bot):
	# This module isn't actually a cog
    return

class Picker:
    def __init__(self, **kwargs):
        self.list = kwargs.get("list", [])
        self.title = kwargs.get("title", None)
        self.timeout = kwargs.get("timeout", 60)
        self.ctx = kwargs.get("ctx", None)
        self.message = kwargs.get("message", None) # message to edit
        self.max = 10 # Don't set programmatically - as we don't want this overridden
        self.reactions = [ "⏹" ]

    async def _add_reactions(self, message, react_list):
        for r in react_list:
            await message.add_reaction(r)

    async def pick(self):
        # This actually brings up the pick list and handles the nonsense
        # Returns a tuple of (return_code, message)
        # The return code is -1 for cancel, -2 for timeout, -3 for error, 0+ is index
        # Let's check our prerequisites first
        if self.ctx == None or not len(self.list) or len(self.list) > self.max:
            return (-3, None)
        msg = ""
        if self.title:
            msg += self.title + "\n"
        msg += "```\n"
        # Show our list items
        current = 0
        current_reactions = [self.reactions[0]]
        for item in self.list:
            current += 1
            current_reactions.append("{}\N{COMBINING ENCLOSING KEYCAP}".format(current))
            msg += "{}. {}\n".format(current, item)
        msg += "```"
        if self.message:
            message = self.message
            await message.edit(content=msg)
        else:
            message = await self.ctx.send(msg)
        # Add our reactions
        await self._add_reactions(message, current_reactions)
        # Now we would wait...
        def check(reaction, user):
            return user == self.ctx.author and str(reaction.emoji) in current_reactions
        try:
            reaction, user = await self.ctx.bot.wait_for('reaction_add', timeout=self.timeout, check=check)
        except:
            # Didn't get a reaction
            await message.clear_reactions()
            return (-2, message)
        
        await message.clear_reactions()
        return (current_reactions.index(str(reaction.emoji))-1, message)