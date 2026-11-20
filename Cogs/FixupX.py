import asyncio, discord, re
from discord.ext import commands
from Cogs import DL

def setup(bot):
    bot.add_cog(FixupX(bot, bot.get_cog("Settings")))

class FixupX(commands.Cog):
    def __init__(self, bot, settings):
        self.bot = bot
        self.settings = settings
        self.twitter_status_regex = re.compile(
            r"https?://(?:www\.)?(?:x\.com|twitter\.com)/"
            r"(?P<username>[A-Za-z0-9_]+)/status/(?P<status_id>\d+)"
            r"[^\s<>()]*",
            re.IGNORECASE,
        )

    async def _has_media(self, status_id):
        url = "https://api.fxtwitter.com/2/status/{}".format(status_id)

        try:
            data = await asyncio.wait_for(
                DL.async_json(
                    url,
                    headers={"User-Agent": "CorpBot"},
                ),
                timeout=8,
            )
        except Exception:
            return False

        if not isinstance(data, dict):
            return False

        status = data.get("status")
        return isinstance(status, dict) and self._status_has_media(status)

    def _status_has_media(self, status):
        media = status.get("media")

        if isinstance(media, dict):
            for key in ("photos", "videos", "all"):
                if isinstance(media.get(key), list) and media[key]:
                    return True

            if media.get("mosaic") or media.get("external"):
                return True

        quote = status.get("quote")
        return isinstance(quote, dict) and self._status_has_media(quote)

    @commands.command()
    async def fixupx(self, ctx, *, yes_no=None):
        """Queries or toggles automatic FixupX conversion for this server."""
        utils = self.bot.get_cog("Utils")
        if not utils or not await utils.is_admin_reply(ctx):
            return

        await ctx.send(
            utils.yes_no_setting(
                ctx,
                "FixupX",
                "FixupX",
                yes_no.strip() if yes_no is not None else None,
                default=True,
            )
        )

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.guild is None or message.author.bot or message.webhook_id:
            return

        if not message.content or message.attachments:
            return

        if not self.settings:
            self.settings = self.bot.get_cog("Settings")

        if not self.settings or not self.settings.getServerStat(message.guild, "FixupX", True):
            return

        matches = list(self.twitter_status_regex.finditer(message.content))
        if not matches:
            return

        checked_posts = {}
        pieces = []
        previous_end = 0
        changed = False

        for match in matches:
            matched_text = match.group(0)
            original_url = matched_text.rstrip(".,!?;:")
            punctuation = matched_text[len(original_url):]
            status_id = match.group("status_id")

            if status_id not in checked_posts:
                checked_posts[status_id] = await self._has_media(status_id)

            pieces.append(message.content[previous_end:match.start()])

            if checked_posts[status_id]:
                fixed_url = re.sub(
                    r"^https?://(?:www\.)?(?:x\.com|twitter\.com)",
                    "https://fixupx.com",
                    original_url,
                    count=1,
                    flags=re.IGNORECASE,
                )
                pieces.append(fixed_url + punctuation)
                changed = True
            else:
                pieces.append(matched_text)

            previous_end = match.end()

        if not changed:
            return

        pieces.append(message.content[previous_end:])
        fixed_content = "".join(pieces)
        replacement_content = "*{} sent:*\n{}".format(
            message.author.mention, fixed_content
        )

        if len(replacement_content) > 2000:
            return

        try:
            replacement = await message.channel.send(
                replacement_content,
                allowed_mentions=discord.AllowedMentions(
                    users=message.mentions,
                    roles=False,
                    everyone=False,
                ),
            )
        except (discord.Forbidden, discord.HTTPException):
            return

        try:
            await message.delete()
        except (discord.Forbidden, discord.NotFound, discord.HTTPException):
            try:
                await replacement.delete()
            except (discord.Forbidden, discord.NotFound, discord.HTTPException):
                pass