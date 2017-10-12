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
                await ctx.author.send(message)
                await ctx.message.add_reaction(self.pm_react)
            except discord.Forbidden:
                await ctx.send(message)
            return
        await ctx.send(message)

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
            await self._send_message(ctx, self.header + m + self.footer, to_pm)
            page_count += 1

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
        self.footer_text = kwargs.get("footer_text", discord.Embed.Empty)
        self.footer_icon = kwargs.get("footer_icon", discord.Embed.Empty)
        self.thumbnail = kwargs.get("thumbnail", None)
        self.author = kwargs.get("author", None)
        self.fields = kwargs.get("fields", [])
        colors = [ 
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
        self.color = kwargs.get("color", random.choice(colors))

    def add_field(self, **kwargs):
        self.fields.append({"name" : kwargs.get("name", "None"), "value" : kwargs.get("value", "None")})

    def clear_fields(self):
        self.fields = []

    # Embed stuff!
    async def _send_embed(self, ctx, embed, pm = False):
        # Helper method to send embeds to their proper location
        if pm == True and not ctx.channel == ctx.author.dm_channel:
            # More than 2 pages - try to dm
            try:
                await ctx.author.send(embed=embed)
                await ctx.message.add_reaction(self.pm_react)
            except discord.Forbidden:
                await ctx.send(embed=embed)
            return
        await ctx.send(embed=embed)

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

    async def send(self, ctx):
        if not ctx:
            return
        # Sends the current embed
        em = discord.Embed(color=self.color)
        em.title = self._truncate_string(self.title, self.title_max)
        em.url = self.url
        em.description = self._truncate_string(self.description, self.desc_max)
        if self.image:
            em.set_image(self.image)
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
            if len(em.fields) >= 25:
                if page_total == page_count:
                    em.set_footer(
                        text=self.footer_text,
                        icon_url=self.footer_icon
                    )
                await self._send_embed(ctx, em, to_pm)
                em.clear_fields()
                page_count += 1
                if page_total > 1 and self.page_count and self.title:
                    add_title = " (Page {:,} of {:,})".format(page_count, page_total)
                    em.title = self._truncate_string(self.title, self.title_max - len(add_title)) + add_title

        if len(em.fields):
            em.set_footer(
                text=self._truncate_string(self.footer_text, self.foot_max),
                icon_url=self.footer_icon
            )
            await self._send_embed(ctx, em, to_pm)