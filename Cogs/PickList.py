import asyncio, discord, math
from   discord.ext import commands
from   Cogs import Message

def setup(bot):
	# Add the bot and deps
	bot.add_cog(PickList(bot))

class PickList(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    # Fluff class to post the reactions we need
    @commands.Cog.listener()
    async def on_reaction_add(self, reaction, user):
        self.bot.dispatch("picklist_reaction", reaction, user)

    @commands.Cog.listener()
    async def on_reaction_remove(self, reaction, user):
        self.bot.dispatch("picklist_reaction", reaction, user)

class Picker:
    def __init__(self, **kwargs):
        self.list = kwargs.get("list", [])
        self.title = kwargs.get("title", None)
        self.timeout = kwargs.get("timeout", 60)
        self.ctx = kwargs.get("ctx", None)
        self.message = kwargs.get("message", None) # message to edit
        self.self_message = None
        self.max = 10 # Don't set programmatically - as we don't want this overridden
        self.reactions = [ "🛑" ]

    async def _add_reactions(self, message, react_list):
        for r in react_list:
            await message.add_reaction(r)

    async def _remove_reactions(self, react_list = []):
        # Try to remove all reactions - if that fails, iterate and remove our own
        try:
            await self.self_message.clear_reactions()
        except:
            pass
            # The following "works", but is super slow - and if we can't clear
            # all reactions, it's probably just best to leave them there and bail.
            '''for r in react_list:
                await message.remove_reaction(r,message.author)'''

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
        # current_reactions = [self.reactions[0]]
        current_reactions = []
        for item in self.list:
            current += 1
            current_number = current if current < 10 else 0
            current_reactions.append("{}\N{COMBINING ENCLOSING KEYCAP}".format(current_number))
            msg += "{}. {}\n".format(current, item)
        msg += "```"
        # Add the stop reaction
        current_reactions.append(self.reactions[0])
        if self.message:
            self.self_message = self.message
            await self.self_message.edit(content=msg, embed=None)
        else:
            self.self_message = await self.ctx.send(msg)
        # Add our reactions
        await self._add_reactions(self.self_message, current_reactions)
        # Now we would wait...
        def check(reaction, user):
            return reaction.message.id == self.self_message.id and user == self.ctx.author and str(reaction.emoji) in current_reactions
        try:
            reaction, user = await self.ctx.bot.wait_for('picklist_reaction', timeout=self.timeout, check=check)
        except:
            # Didn't get a reaction
            await self._remove_reactions(current_reactions)
            return (-2, self.self_message)
        
        await self._remove_reactions(current_reactions)
        # Get the adjusted index
        ind = current_reactions.index(str(reaction.emoji))
        if ind == len(current_reactions)-1:
            ind = -1
        return (ind, self.self_message)

class PagePicker(Picker):
    def __init__(self, **kwargs):
        Picker.__init__(self, **kwargs)
        # Expects self.list to contain the fields needed - each a dict with {"name":name,"value":value,"inline":inline}
        self.max = kwargs.get("max",10) # Must be between 1 and 25
        self.max = 1 if self.max < 1 else 10 if self.max > 10 else self.max
        self.reactions = ["⏪","◀","▶","⏩","🔢","🛑"] # These will always be in the same order
        self.url = kwargs.get("url",None) # The URL the title of the embed will link to
        self.description = kwargs.get("description", None)

    def _get_page_contents(self, page_number):
        # Returns the contents of the page passed
        start = self.max*page_number
        return self.list[start:start+self.max]

    async def pick(self):
        # This brings up the page picker and handles the events
        # It will return a tuple of (last_page_seen, message)
        # The return code is -1 for cancel, -2 for timeout, -3 for error, 0+ is index
        # Let's check our prerequisites first
        if self.ctx == None or not len(self.list):
            return (-3, None)
        page  = 0 # Set the initial page index
        pages = int(math.ceil(len(self.list)/self.max))
        # Setup the embed
        embed = {
            "title":self.title,
            "url":self.url,
            "description":self.description,
            "color":self.ctx.author,
            "pm_after":25,
            "fields":self._get_page_contents(page),
            "footer":"Page {} of {}".format(page+1,pages)
        }
        if self.message:
            self.self_message = self.message
            await Message.Embed(**embed).edit(self.ctx,self.message)
        else:
            self.self_message = await Message.Embed(**embed).send(self.ctx)
        # First verify we have more than one page to display
        if pages <= 1:
            return (0,self.self_message)
        # Add our reactions
        await self._add_reactions(self.self_message, self.reactions)
        # Now we would wait...
        def check(reaction, user):
            return reaction.message.id == self.self_message.id and user == self.ctx.author and str(reaction.emoji) in self.reactions
        while True:
            try:
                reaction, user = await self.ctx.bot.wait_for('picklist_reaction', timeout=self.timeout, check=check)
            except:
                # Didn't get a reaction
                await self._remove_reactions(self.reactions)
                return (page, self.self_message)
            # Got a reaction - let's process it
            ind = self.reactions.index(str(reaction.emoji))
            if ind == 5:
                # We bailed - let's clear reactions and close it down
                await self._remove_reactions(self.reactions)
                return (page, self.self_message)
            page = 0 if ind==0 else page-1 if ind==1 else page+1 if ind==2 else pages if ind==3 else page
            if ind == 4:
                # User selects a page
                page_instruction = await self.ctx.send("Type the number of that page to go to from {} to {}.".format(1,pages))
                def check_page(message):
                    try:
                        num = int(message.content)
                    except:
                        return False
                    return message.channel == self.self_message.channel and user == message.author
                try:
                    page_message = await self.ctx.bot.wait_for('message', timeout=self.timeout, check=check_page)
                    page = int(page_message.content)-1
                except:
                    # Didn't get a message
                    pass
                # Delete the instruction
                await page_instruction.delete()
                # Try to delete the user's page message too
                try:
                    await page_message.delete()
                except:
                    pass
            page = 0 if page < 0 else pages-1 if page > pages-1 else page
            embed["fields"] = self._get_page_contents(page)
            embed["footer"] = "Page {} of {}".format(page+1,pages)
            await Message.Embed(**embed).edit(self.ctx,self.self_message)
        await self._remove_reactions(self.reactions)
        # Get the adjusted index
        return (page, self.self_message)
