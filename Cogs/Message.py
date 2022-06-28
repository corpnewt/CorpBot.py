import asyncio, discord, textwrap, random, math, os
from   discord.ext import commands

async def setup(bot):
    # Not a cog
    return

class Message:
    def __init__(self, **kwargs):
        # Creates a new message - with an optional setup dictionary
        self.max_chars = 2000
        self.pm_after = kwargs.get("pm_after", 1) # -1 to disable, 0 to always pm
        self.force_pm = kwargs.get("force_pm", False)
        self.header = kwargs.get("header", "")
        self.footer = kwargs.get("footer", "")
        self.pm_react = kwargs.get("pm_react", "📬")
        self.message = kwargs.get("message", None)
        self.file = kwargs.get("file", None) # Accepts a file path
        self.max_pages = 0
        self.delete_after = kwargs.get("delete_after",None)

    def _get_file(self, file_path):
        if not os.path.exists(file_path):
            return None
        # Path exists, let's get the extension if there is one
        ext = file_path.split(".")
        fname = "Upload." + ext[-1] if len(ext) > 1 else "Upload"
        file_handle = discord.File(fp=file_path, filename=fname)
        return (file_handle, fname)

    async def _send_message(self, ctx, message, pm = False, file_path = None):
        # Helper method to send embeds to their proper location
        send_file = None
        if not file_path == None:
            dfile = self._get_file(file_path)
            if not dfile:
                # File doesn't exist...
                try:
                    await ctx.send("An error occurred!\nThe file specified couldn't be sent :(")
                except:
                    # We tried...
                    pass
                return None
            else:
                # Setup our file
                send_file = dfile[0]
        if pm == True and type(ctx) is discord.ext.commands.Context and not ctx.channel == ctx.author.dm_channel:
            # More than 2 pages - try to dm
            try:
                message = await ctx.author.send(message, file=send_file, delete_after=self.delete_after)
                await ctx.message.add_reaction(self.pm_react)
                return message
            except discord.Forbidden:
                if self.force_pm:
                    # send an error message
                    try:
                        await ctx.send("An error occurred!\nCould not dm this message to you :(")
                    except:
                        # We tried...
                        pass
                    return None
                pass
        return await ctx.send(message, file=send_file, delete_after=self.delete_after)

    async def send(self, ctx):
        if not ctx or not self.message or not len(self.message):
            return
        text_list = textwrap.wrap(
            self.message,
            self.max_chars - len(self.header) - len(self.footer),
            break_long_words=True,
            replace_whitespace=False)

        # Only pm if our self.pm_after is above -1
        to_pm = len(text_list) > self.pm_after if self.pm_after > -1 else False
        page_count = 1
        for m in text_list:
            if self.max_pages > 0 and page_count > self.max_pages:
                break
            message = await self._send_message(ctx, self.header + m + self.footer, to_pm)
            # Break if things didn't work
            if not message:
                return None
            page_count += 1
        return message

class Embed:
    def __init__(self, **kwargs):
        # Set defaults
        self.title_max = kwargs.get("title_max", 256)
        self.desc_max = kwargs.get("desc_max", 2048)
        self.field_max = kwargs.get("field_max", 25)
        self.fname_max = kwargs.get("fname_max", 256)
        self.fval_max = kwargs.get("fval_max", 1024)
        self.foot_max = kwargs.get("foot_max", 2048)
        self.auth_max = kwargs.get("auth_max", 256)
        self.total_max = kwargs.get("total_max", 6000)
        # Creates a new embed - with an option setup dictionary
        self.pm_after_fields = kwargs.get("pm_after_fields", 10)
        self.force_pm = kwargs.get("force_pm", False)
        self.pm_react = kwargs.get("pm_react", "📬")
        self.title = kwargs.get("title", None)
        self.page_count = kwargs.get("page_count", False)
        self.max_pages = kwargs.get("max_pages",0) # 1 or above to limit
        self.url = kwargs.get("url", None)
        self.description = kwargs.get("description", None)
        self.image = kwargs.get("image", None)
        self.footer = kwargs.get("footer", None)
        self.thumbnail = kwargs.get("thumbnail", None)
        self.author = kwargs.get("author", None)
        self.fields = kwargs.get("fields", [])
        self.file = kwargs.get("file", None) # Accepts a file path
        self.delete_after = kwargs.get("delete_after",None)
        self.colors = [ 
            discord.Color.teal(),
            discord.Color.dark_teal(),
            discord.Color.green(),
            discord.Color.dark_green(),
            discord.Color.blue(),
            discord.Color.dark_blue(),
            discord.Color.purple(),
            discord.Color.dark_purple(),
            discord.Color.magenta(),
            discord.Color.dark_magenta(),
            discord.Color.gold(),
            discord.Color.dark_gold(),
            discord.Color.orange(),
            discord.Color.dark_orange(),
            discord.Color.red(),
            discord.Color.dark_red(),
            discord.Color.lighter_grey(),
            discord.Color.dark_grey(),
            discord.Color.light_grey(),
            discord.Color.darker_grey(),
            discord.Color.blurple(),
            discord.Color.greyple(),
            discord.Color.default()
        ]
        self.color = kwargs.get("color", None)
        # Description-based args
        self.pm_after_pages = kwargs.get("pm_after_pages",1)
        self.newline_split = kwargs.get("newline_split",False)
        self.max_rows = kwargs.get("max_rows",20) # used with newline_split for max rows per page
        self.d_header = kwargs.get("d_header","")
        self.d_footer = kwargs.get("d_footer","")

    def add_field(self, **kwargs):
        self.fields.append({
            "name" : kwargs.get("name", "None"),
            "value" : kwargs.get("value", "None"),
            "inline" : kwargs.get("inline", False)
        })

    def clear_fields(self):
        self.fields = []

    def _get_file(self, file_path):
        if not os.path.exists(file_path):
            return None
        # Path exists, let's get the extension if there is one
        ext = file_path.split(".")
        fname = "Upload." + ext[-1] if len(ext) > 1 else "Upload"
        file_handle = discord.File(fp=file_path, filename=fname)
        return (file_handle, fname)

    # Embed stuff!
    async def _send_embed(self, ctx, embed, pm = False, file_path = None):
        # Helper method to send embeds to their proper location
        send_file = None
        if not file_path == None:
            dfile = self._get_file(file_path)
            if not dfile:
                # File doesn't exist...
                try:
                    await Embed(title="An error occurred!", description="The file specified couldn't be sent :(", color=self.color).send(ctx)
                except:
                    # We tried...
                    pass
                return None
            else:
                # Setup our file
                send_file = dfile[0]
                embed.set_image(url="attachment://" + str(dfile[1]))
        if pm == True and type(ctx) is discord.ext.commands.Context and not ctx.channel == ctx.author.dm_channel:
            # More than 2 pages and targeting context - try to dm
            try:
                message = await ctx.author.send(embed=embed,file=send_file,delete_after=self.delete_after)
                await ctx.message.add_reaction(self.pm_react)
                return message
            except discord.Forbidden:
                if self.force_pm:
                    # send an error embed
                    try:
                        await Embed(title="An error occurred!", description="Could not dm this message to you :(", color=self.color).send(ctx)
                    except:
                        # We tried...
                        pass
                    return None
        return await ctx.send(embed=embed,file=send_file,delete_after=self.delete_after)

    def _truncate_string(self, value, max_chars):
        if not type(value) is str: return value
        # Truncates the string to the max chars passed
        return (value[:max_chars-3]+"...") if len(value) > max_chars else value

    def _total_chars(self, embed):
        # Returns how many chars are in the embed
        tot = 0
        if embed.title:
            tot += len(embed.title)
        if embed.description:
            tot += len(embed.description)
        if not embed.footer is discord.Embed(title=None):
            tot += len(embed.footer)
        for field in embed.fields:
            tot += len(field.name) + len(field.value)
        return tot

    def _embed_with_self(self):
        if isinstance(self.color,discord.Member):
            self.color = self.color.color
        elif isinstance(self.color,discord.User):
            self.color = None
        elif isinstance(self.color,int):
            try:
                self.color = discord.Color(value=self.color)
            except:
                self.color = None
        elif isinstance(self.color,(tuple,list)):
            try:
                self.color = discord.Color.from_rgb(*[int(a) for a in self.color])
            except:
                self.color = None

        # Sends the current embed
        em = discord.Embed(color=self.color if isinstance(self.color,discord.Color) else random.choice(self.colors))
        em.title = self._truncate_string(self.title, self.title_max)
        em.url = self.url
        # em.description = self._truncate_string(self.description, self.desc_max)
        if self.image:
            em.set_image(url=self.image.get("url",discord.Embed(title=None)) if isinstance(self.image,dict) else self.image)
        if self.thumbnail:
            em.set_thumbnail(url=self.thumbnail.get("url",discord.Embed(title=None)) if isinstance(self.thumbnail,dict) else self.thumbnail)
        if self.author:
            if type(self.author) is discord.Member or type(self.author) is discord.User:
                name = self.author.nick if hasattr(self.author, "nick") and self.author.nick else self.author.name
                em.set_author(
                    name = self._truncate_string(name, self.auth_max),
                    icon_url=next((x for x in (self.author.avatar_url,self.author.default_avatar_url) if x),None) if hasattr(self.author,"avatar_url") else self.author.display_avatar.url
                )      
            elif type(self.author) is dict:
                if any(item in self.author for item in ["name", "url", "icon"]):
                    em.set_author(
                        name = self._truncate_string(self.author.get("name",     discord.Embed(title=None)), self.auth_max),
                        url = self.author.get("url",      discord.Embed(title=None)),
                        icon_url = self.author.get("icon_url", discord.Embed(title=None))
                    )
                else:
                    em.set_author(name=self._truncate_string(str(self.author), self.auth_max))
            else:
                # Cast to string and hope for the best
                em.set_author(name=self._truncate_string(str(self.author), self.auth_max))
        return em

    def _get_footer(self):
        # Get our footer if we have one
        footer_text = discord.Embed(title=None)
        if type(self.footer) is str:
            footer_text = self.footer
        elif type(self.footer) is dict:
            footer_text = self.footer.get("text", discord.Embed(title=None))
        elif self.footer == None:
            # Never setup
            pass
        else:
            # Try to cast it
            footer_text = str(self.footer)
        return (footer_text)

    def _get_desc_page_list(self):
        # Returns the list of pages based on our settings
        if not self.description: return [] # Empty list
        adj_max = self.desc_max - len(self.d_header) - len(self.d_footer)
        if self.newline_split:
            chunks = []
            curr   = ""
            row    = 0
            for line in self.description.split("\n"):
                test = curr+"\n"+line if len(curr) else line
                row += 1
                if len(line) > adj_max: # The line itself is too long
                    if len(curr): chunks.append(self.d_header+curr+self.d_footer)
                    chunks.extend([self.d_header+x+self.d_footer for x in textwrap.wrap(
                        line,
                        adj_max,
                        break_long_words=True
                    )])
                    curr = ""
                elif len(test) >= adj_max or row > self.max_rows: # Exact or too big - adjust
                    chunks.append(self.d_header+(test if len(test)==adj_max else curr)+self.d_footer)
                    curr = "" if len(test)==adj_max else line
                    row = 0 if len(test)==adj_max else 1
                else: # Not big enough yet - just append
                    curr = test
            if len(curr): chunks.append(self.d_header+curr+self.d_footer)
            return chunks
        # Use textwrap to wrap the words, not newlines
        return [self.d_header+x+self.d_footer for x in textwrap.wrap(
            self.description,
            adj_max,
            break_long_words=True,
            replace_whitespace=False
        )]

    def _to_pm(self,field_pages=None,desc_pages=None):
        if field_pages is None or desc_pages is None:
            # Missing info - regen
            field_pages,desc_pages = self._get_pages()
        return len(self.fields)>self.pm_after_fields or len(desc_pages)>self.pm_after_pages if self.pm_after_fields>-1 and self.pm_after_pages>-1 else False

    def _get_pages(self):
        # Returns a tuple of (pages_of_fields, pages_of_descriptions)
        if not isinstance(self.fields,list): self.fields = []
        field_pages = [self.fields[i:i+self.field_max] for i in range(0, len(self.fields), self.field_max)]
        desc_pages = self._get_desc_page_list()
        return (field_pages,desc_pages)

    async def edit(self, ctx, message):
        # Edits the passed message - and sends any remaining pages
        # check if we can steal the color from the message - but only if using a User color in dm,
        # or if the color is set to None and the message we're editing has an embed
        if (self.color is None or isinstance(self.color,discord.User)) and len(message.embeds):
            self.color = message.embeds[0].color
        # Pipe to our send() function
        return await self.send(ctx,original_message=message)

    async def _edit_embed(self, ctx, embed, to_pm, original_message):
        # Helper to determine how to edit a message - then actually edit it
        if not to_pm and not self.file:
            # Edit in place
            await original_message.edit(content=None,embed=embed,delete_after=self.delete_after)
            return original_message
        # We're dming this message - send the new, and edit the original
        message = await self._send_embed(ctx,embed,to_pm,self.file)
        if message.channel == ctx.author.dm_channel != ctx.channel:
            # We sent a dm - edit the original message to reflect this
            em = Embed(title=self.title, description="📬 Check your dm's", color=self.color)._embed_with_self()
            await message.edit(content=None, embed=em, delete_after=self.delete_after)
        else:
            # No dm - just delete the original
            await original_message.delete()
        return message

    async def send(self, ctx, original_message=None):
        if not ctx: return
        # Create the shell embed with our self properties
        em = self._embed_with_self()
        # Gather our footer - if any
        footer_text = self._get_footer()
        # Gather our field and description pages
        field_pages,desc_pages = self._get_pages()
        # Total is whichever is largest
        total_pages = max((len(field_pages),len(desc_pages)))
        if self.max_pages > 0 and total_pages > self.max_pages: # Need to limit the total_pages
            total_pages = self.max_pages
        # First check if we have any pages at all - and if not, try to send
        # an embed with what we have
        if not total_pages:
            em.set_footer(
                text=self._truncate_string(footer_text, self.foot_max)
            )
            # If we're editing - remove/update messages as needed
            if original_message: return await self._edit_embed(ctx,em,False,original_message)
            else: return await self._send_embed(ctx,em,False,self.file)
                
        # Take note of whether or not we should try to pm
        to_pm = self._to_pm(field_pages=field_pages,desc_pages=desc_pages)
        # Let's walk the pages and send the slices of our fields/desc as needed
        for page in range(total_pages):
            em.description = None
            em.clear_fields() # Start with a clean slate
            if len(field_pages)>page: # We have fields to add
                for field in field_pages[page]:
                    em.add_field(
                        name=self._truncate_string(field.get("name", "None"), self.fname_max),
                        value=self._truncate_string(field.get("value", "None"), self.fval_max),
                        inline=field.get("inline", False)
                    )
            if len(desc_pages)>page: # We have description to add
                em.description = desc_pages[page]
            # Check if we need to adjust the title
            if total_pages > 1 and self.page_count and self.title:
                add_title = " (Page {:,} of {:,})".format(page+1,total_pages)
                em.title = self._truncate_string(self.title,self.title_max-len(add_title))+add_title
            # If we're on the last message - set the footer
            if page+1 == total_pages:
                em.set_footer(
                    text=self._truncate_string(footer_text, self.foot_max),
                )
            if original_message and page==0:
                message = await self._edit_embed(ctx,em,False,original_message)
            else:
                # Send the embed - and include a file if present and we're on the first page
                message = await self._send_embed(ctx,em,to_pm,self.file if page==0 else None)
            # Check if our message didn't send - and bail if that's the case
            if not message: return None
        # Return the last message we sent
        return message

class EmbedText(Embed): # Kept as a placeholder
    def __init__(self, **kwargs):
        Embed.__init__(self, **kwargs)
