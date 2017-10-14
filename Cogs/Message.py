import asyncio
import discord
import textwrap
import random
import math
from   discord.ext import commands

def setup(bot):
    # Not a cog
    return

class Message:
    def __init__(self, **kwargs):
        # Creates a new message - with an optional setup dictionary
        self.max_chars = 2000
        self.pm_after = kwargs.get("pm_after", 1)
        self.header = kwargs.get("header", "")
        self.footer = kwargs.get("footer", "")
        self.pm_react = kwargs.get("pm_react", "📬")
        self.message = kwargs.get("message", None)
        self.max_pages = 0

    async def _send_message(self, ctx, message, pm = False):
        # Helper method to send embeds to their proper location
        if pm == True and not ctx.channel == ctx.author.dm_channel:
            # More than 2 pages - try to dm
            try:
                message = await ctx.author.send(message)
                await ctx.message.add_reaction(self.pm_react)
                return message
            except discord.Forbidden:
                pass
        return await ctx.send(message)

    async def send(self, ctx):
        if not ctx or not self.message or not len(self.message):
            return
        text_list = textwrap.wrap(
            self.message,
            self.max_chars - len(self.header) - len(self.footer),
            break_long_words=True,
            replace_whitespace=False)

        # Only pm if our self.pm_after is above 0
        to_pm = len(text_list) > self.pm_after if self.pm_after else False

        page_count = 1
        for m in text_list:
            if self.max_pages > 0 and page_count > self.max_pages:
                break
            message = await self._send_message(ctx, self.header + m + self.footer, to_pm)
            page_count += 1
        return message

class Embed:
    def __init__(self, **kwargs):
        # Set defaults
        self.title_max = 256
        self.desc_max = 2048
        self.field_max = 25
        self.fname_max = 256
        self.fval_max = 1024
        self.foot_max = 2048
        self.auth_max = 256
        self.total_max = 6000
        # Creates a new embed - with an option setup dictionary
        self.pm_after = kwargs.get("pm_after", 10)
        self.pm_react = kwargs.get("pm_react", "📬")
        self.title = kwargs.get("title", None)
        self.page_count = kwargs.get("page_count", True)
        self.url = kwargs.get("url", None)
        self.description = kwargs.get("description", None)
        self.image = kwargs.get("image", None)
        self.footer = kwargs.get("footer", None)
        # self.footer_text = kwargs.get("footer_text", discord.Embed.Empty)
        # self.footer_icon = kwargs.get("footer_icon", discord.Embed.Empty)
        self.thumbnail = kwargs.get("thumbnail", None)
        self.author = kwargs.get("author", None)
        self.fields = kwargs.get("fields", [])
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
        self.color = kwargs.get("color", random.choice(self.colors))

    def add_field(self, **kwargs):
        self.fields.append({
            "name" : kwargs.get("name", "None"),
            "value" : kwargs.get("value", "None"),
            "inline" : kwargs.get("inline", False)
        })

    def clear_fields(self):
        self.fields = []

    # Embed stuff!
    async def _send_embed(self, ctx, embed, pm = False):
        # Helper method to send embeds to their proper location
        if pm == True and not ctx.channel == ctx.author.dm_channel:
            # More than 2 pages - try to dm
            try:
                message = await ctx.author.send(embed=embed)
                await ctx.message.add_reaction(self.pm_react)
                return message
            except discord.Forbidden:
                pass
        return await ctx.send(embed=embed)

    def _truncate_string(self, value, max_chars):
        if not type(value) is str:
            return value
        # Truncates the string to the max chars passed
        return (value[:max_chars-3]+"...") if len(value) > max_chars else value

    def _total_chars(self, embed):
        # Returns how many chars are in the embed
        tot = 0
        if embed.title:
            tot += len(embed.title)
        if embed.description:
            tot += len(embed.description)
        if not embed.footer is discord.Embed.Empty:
            tot += len(embed.footer)
        for field in embed.fields:
            tot += len(field.name) + len(field.value)
        return tot

    def _embed_with_self(self):
        if type(self.color) is discord.Member:
            self.color = self.color.color
        elif type(self.color) is discord.User:
            self.color = random.choice(self.colors)
        # Sends the current embed
        em = discord.Embed(color=self.color)
        em.title = self._truncate_string(self.title, self.title_max)
        em.url = self.url
        em.description = self._truncate_string(self.description, self.desc_max)
        if self.image:
            em.set_image(url=self.image)
        if self.thumbnail:
            em.set_thumbnail(self.thumbnail)
        if self.author:
            if type(self.author) is discord.Member or type(self.author) is discord.User:
                name = self.author.nick if hasattr(self.author, "nick") and self.author.nick else self.author.name
                em.set_author(
                    name    =self._truncate_string(name, self.auth_max),
                    # Ignore the url here
                    icon_url=self.author.avatar_url
                )      
            elif type(self.author) is dict:
                if any(item in self.author for item in ["name", "url", "icon"]):
                    em.set_author(
                        name    =self._truncate_string(self.author.get("name",     discord.Embed.Empty), self.auth_max),
                        url     =self.author.get("url",      discord.Embed.Empty),
                        icon_url=self.author.get("icon_url", discord.Embed.Empty)
                    )
                else:
                    em.set_author(name=self._truncate_string(str(self.author), self.auth_max))
            else:
                # Cast to string and hope for the best
                em.set_author(name=self._truncate_string(str(self.author), self.auth_max))
        return em

    def _get_footer(self):
        # Get our footer if we have one
        footer_text = footer_icon = discord.Embed.Empty
        if type(self.footer) is str:
                footer_text = self.footer
        elif type(self.footer) is dict:
                footer_text = self.footer.get("text", discord.Embed.Empty)
                footer_icon = self.footer.get("icon_url", discord.Embed.Empty)
        elif self.footer == None:
                # Never setup
                pass
        else:
                # Try to cast it
                footer_text = str(self.footer)
        return (footer_text, footer_icon)

    async def edit(self, ctx, message):
        # Edits the passed message - and sends any remaining pages
        em = self._embed_with_self()
        footer_text, footer_icon = self._get_footer()

        to_pm = len(self.fields) > self.pm_after if self.pm_after else False

        if len(self.fields) <= self.pm_after and not to_pm:
            # Edit in place, nothing else needs to happen
            for field in self.fields:
                em.add_field(
                    name=self._truncate_string(field.get("name", "None"), self.fname_max),
                    value=self._truncate_string(field.get("value", "None"), self.fval_max),
                    inline=field.get("inline", False)
                )
            em.set_footer(
                text=self._truncate_string(footer_text, self.foot_max),
                icon_url=footer_icon
            )
            return await message.edit(embed=em)
        # Now we need to edit the first message to just a space - then send the rest
        new_message = await self.send(ctx)
        if new_message.channel == ctx.author.dm_channel:
            em = Embed(title=self.title, description="📬 Check your dm's", color=self.color)._embed_with_self()
            await message.edit(embed=em)
        else:
            await message.edit(content=" ", embed=None)

    async def send(self, ctx):
        if not ctx:
            return
        
        em = self._embed_with_self()
        footer_text, footer_icon = self._get_footer()

        # First check if we have any fields at all - and try to send
        # as one page if not
        if not len(self.fields):
            em.set_footer(
                text=self._truncate_string(footer_text, self.foot_max),
                icon_url=footer_icon
            )
            return await self._send_embed(ctx, em, False)
        
        # Only pm if our self.pm_after is above 0
        to_pm = len(self.fields) > self.pm_after if self.pm_after else False

        page_count = 1
        page_total = math.ceil(len(self.fields)/self.field_max)

        if page_total > 1 and self.page_count and self.title:
            add_title = " (Page {:,} of {:,})".format(page_count, page_total)
            em.title = self._truncate_string(self.title, self.title_max - len(add_title)) + add_title
        for field in self.fields:
            em.add_field(
                name=self._truncate_string(field.get("name", "None"), self.fname_max),
                value=self._truncate_string(field.get("value", "None"), self.fval_max),
                inline=field.get("inline", False)
            )
            # 25 field max - send the embed if we get there
            if len(em.fields) >= self.field_max:
                if page_total == page_count:
                    em.set_footer(
                        text=self._truncate_string(footer_text, self.foot_max),
                        icon_url=footer_icon
                    )
                message = await self._send_embed(ctx, em, to_pm)
                em.clear_fields()
                page_count += 1
                if page_total > 1 and self.page_count and self.title:
                    add_title = " (Page {:,} of {:,})".format(page_count, page_total)
                    em.title = self._truncate_string(self.title, self.title_max - len(add_title)) + add_title

        if len(em.fields):
            em.set_footer(
                text=self._truncate_string(footer_text, self.foot_max),
                icon_url=footer_icon
            )
            message = await self._send_embed(ctx, em, to_pm)
        return message

class EmbedText(Embed):
    def __init__(self, **kwargs):
        Embed.__init__(self, **kwargs)
        # Creates a new embed - with an option setup dictionary
        self.pm_after = kwargs.get("pm_after", 1)
        self.desc_head = kwargs.get("desc_head", "") # Header for description markdown
        self.desc_foot = kwargs.get("desc_foot", "") # Footer for description markdown

    async def edit(self, ctx, message):
        # Edits the passed message - and sends any remaining pages
        em = self._embed_with_self()
        footer_text, footer_icon = self._get_footer()

        if self.description == None or not len(self.description):
            text_list = []
        else:
            text_list = textwrap.wrap(
                self.description,
                self.desc_max - len(self.desc_head) - len(self.desc_foot),
                break_long_words=True,
                replace_whitespace=False)
        to_pm = len(text_list) > self.pm_after if self.pm_after else False
        if len(text_list) <= 1 and not to_pm:
            # Edit in place, nothing else needs to happen
            if len(text_list):
                em.description = self.desc_head + text_list[0] + self.desc_foot
            em.set_footer(
                text=self._truncate_string(footer_text, self.foot_max),
                icon_url=footer_icon
            )
            return await message.edit(embed=em)
        # Now we need to edit the first message to just a space - then send the rest
        new_message = await self.send(ctx)
        if new_message.channel == ctx.author.dm_channel:
            em = Embed(title=self.title, description="📬 Check your dm's", color=self.color)._embed_with_self()
            await message.edit(embed=em)
        else:
            await message.edit(content=" ", embed=None)

    async def send(self, ctx):
        if not ctx:
            return
        
        em = self._embed_with_self()
        footer_text, footer_icon = self._get_footer()

        # First check if we have any fields at all - and try to send
        # as one page if not
        if self.description == None or not len(self.description):
            em.set_footer(
                text=self._truncate_string(footer_text, self.foot_max),
                icon_url=footer_icon
            )
            return await self._send_embed(ctx, em, False)
        
        text_list = textwrap.wrap(
            self.description,
            self.desc_max - len(self.desc_head) - len(self.desc_foot),
            break_long_words=True,
            replace_whitespace=False)

        # Only pm if our self.pm_after is above 0
        to_pm = len(text_list) > self.pm_after if self.pm_after else False

        i = 0
        for i in range(len(text_list)):
            m = text_list[i]
            if self.max_pages > 0 and i >= self.max_pages:
                break
            # Strip the title if not the first page
            if i > 0:
                em.title = None
            if i == len(text_list)-1:
                # Last item - apply footer
                em.set_footer(
                    text=self._truncate_string(footer_text, self.foot_max),
                    icon_url=footer_icon
                )
            em.description = self.desc_head + m + self.desc_foot
            message = await self._send_embed(ctx, em, to_pm)
        return message