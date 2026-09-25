import re
import aiohttp
import asyncio
import discord

from discord.ext import commands
from Cogs import Utils


def setup(bot):
    settings = bot.get_cog("Settings")
    bot.add_cog(FixupX(bot, settings))


class FixupX(commands.Cog):
    def __init__(self, bot, settings):
        self.bot = bot
        self.settings = settings

        global Utils
        Utils = self.bot.get_cog("Utils")

        self.twitter_status_regex = re.compile(
            r"https?://(?:www\.)?(?:x\.com|twitter\.com)/"
            r"(?P<username>[A-Za-z0-9_]+)/status/(?P<status_id>\d+)"
            r"[^\s<>()]*",
            re.IGNORECASE
        )

    async def _has_media(self, status_id):
        # Returns true if a post contains image, video or GIF
        api_url = "https://api.fxtwitter.com/2/status/{}".format(
            status_id
        )

        timeout = aiohttp.ClientTimeout(total=8)

        headers = {
            "User-Agent": "CorpBot"
        }

        try:
            async with aiohttp.ClientSession(
                timeout=timeout,
                headers=headers
            ) as session:

                async with session.get(api_url) as response:
                    if response.status != 200:
                        return False

                    data = await response.json()

        except (
            aiohttp.ClientError,
            asyncio.TimeoutError,
            ValueError
        ):
            return False

        status = data.get("status")

        if not isinstance(status, dict):
            return False

        return self._status_has_media(status)

    def _status_has_media(self, status):
        media = status.get("media")

        if isinstance(media, dict):

            photos = media.get("photos")
            if isinstance(photos, list) and photos:
                return True

            videos = media.get("videos")
            if isinstance(videos, list) and videos:
                return True

            all_media = media.get("all")
            if isinstance(all_media, list) and all_media:
                return True

            if media.get("mosaic"):
                return True

            if media.get("external"):
                return True

        quote = status.get("quote")

        if isinstance(quote, dict):
            if self._status_has_media(quote):
                return True

        return False

    def _convert_url(self, url):
        return re.sub(
            r"https?://(?:www\.)?(?:x\.com|twitter\.com)",
            "https://fixupx.com",
            url,
            count=1,
            flags=re.IGNORECASE
        )

    async def _flush_settings(self):
        if not self.settings:
            return

        try:
            await self.bot.loop.run_in_executor(
                None,
                self.settings.flushSettings,
                self.settings.file,
                True
            )
        except Exception:
            pass

    @commands.command()
    async def fixupx(self, ctx, *, yes_no: str = None):
        """
        Queries or turns FixupX automatic link conversion on/off
        for this server (admin-only).
        """

        if not await Utils.is_admin_reply(ctx):
            return

        if not self.settings:
            self.settings = self.bot.get_cog("Settings")

        if not self.settings:
            return await ctx.send(
                "Something is wrong with my settings module :("
            )

        current = self.settings.getServerStat(
            ctx.guild,
            "FixupX",
            True
        )

        if yes_no is None:
            return await ctx.send(
                "FixupX is currently *{}*.".format(
                    "enabled" if current else "disabled"
                )
            )

        setting = yes_no.lower().strip()

        enable_values = (
            "1",
            "yes",
            "on",
            "true",
            "enabled",
            "enable"
        )

        disable_values = (
            "0",
            "no",
            "off",
            "false",
            "disabled",
            "disable"
        )

        if setting in enable_values:
            new_value = True

        elif setting in disable_values:
            new_value = False

        else:
            return await ctx.send(
                "That's not a valid setting. Use `{0}fixupx on` "
                "or `{0}fixupx off`.".format(ctx.prefix)
            )

        if new_value == current:
            return await ctx.send(
                "FixupX is already *{}*.".format(
                    "enabled" if new_value else "disabled"
                )
            )

        self.settings.setServerStat(
            ctx.guild,
            "FixupX",
            new_value
        )

        await ctx.send(
            "FixupX is now *{}*.".format(
                "enabled" if new_value else "disabled"
            )
        )

    @commands.Cog.listener()
    async def on_message(self, message):

        if message.guild is None:
            return

        if message.author.bot or message.webhook_id:
            return

        if not message.content:
            return

        if not self.settings:
            self.settings = self.bot.get_cog("Settings")

        if not self.settings:
            return

        if not self.settings.getServerStat(
            message.guild,
            "FixupX",
            True
        ):
            return

        matches = list(
            self.twitter_status_regex.finditer(message.content)
        )

        if not matches:
            return

        if message.attachments:
            return

        fixed_content = message.content
        changed = False

        checked_posts = {}

        for match in matches:

            status_id = match.group("status_id")
            original_url = match.group(0)

            if status_id not in checked_posts:
                checked_posts[status_id] = await self._has_media(
                    status_id
                )

            if not checked_posts[status_id]:
                continue

            fixed_url = self._convert_url(
                original_url
            )

            fixed_content = fixed_content.replace(
                original_url,
                fixed_url
            )

            changed = True

        if not changed:
            return

        try:
            await message.delete()

        except (
            discord.Forbidden,
            discord.NotFound,
            discord.HTTPException
        ):
            return

        try:
            await message.channel.send(
                "*{} sent:*\n{}".format(
                    message.author.mention,
                    fixed_content
                ),
                allowed_mentions=discord.AllowedMentions(
                    users=message.mentions,
                    roles=False,
                    everyone=False
                )
            )

        except discord.HTTPException:
            pass