import discord, json, tempfile, shutil, re, os, datetime
from discord.ext import commands
from Cogs import Message, DL, DisplayName, Utils

def setup(bot):
    # Add the bot and deps
    settings = bot.get_cog("Settings")
    bot.add_cog(Embed(bot, settings))

class Embed(commands.Cog):

    def __init__(self, bot, settings):
        self.bot = bot
        self.settings = settings
        global Utils, DisplayName
        Utils = self.bot.get_cog("Utils")
        DisplayName = self.bot.get_cog("DisplayName")

    def _get_embed_from_json(self, ctx, embed_json):
        # Helper method to ensure embed_json is valid, and doesn't bypass limits
        # Let's attempt to serialize the json
        try:
            # Allow control characters like newlines in the JSON string via strict=False
            embed_dict = json.loads(embed_json,strict=False)
            # Let's parse the author and color
            if embed_dict.get("color") and not isinstance(embed_dict["color"],list):
                # We got *something* for the color - let's first check if it's an int between 0 and 16777215
                if not isinstance(embed_dict["color"],int) or not 0<=embed_dict["color"]<=16777215:
                    color_value = None
                    if str(embed_dict["color"]).lower().startswith(("#","0x")):
                        # Should be a hex color code
                        try:
                            color_value = int(str(embed_dict["color"]).lower().lstrip("#").lstrip("0x"),16)
                            if not 0<=color_value<=16777215: color_value = None # Out of range
                        except:
                            pass
                    # Let's try to resolve it to a user
                    embed_dict["color"] = color_value if color_value is not None else DisplayName.memberForName(str(embed_dict["color"]),ctx.guild)
            if embed_dict.get("author") and not isinstance(embed_dict["author"],dict):
                # Again - got *something* for the author - try to resolve it
                embed_dict["author"] = DisplayName.memberForName(str(embed_dict["author"]),ctx.guild)
            if embed_dict.get("timestamp"):
                if isinstance(embed_dict["timestamp"],str):
                    # Check for the word "now"
                    if embed_dict["timestamp"].lower() == "now":
                        embed_dict["timestamp"] = datetime.datetime.now()
                    else:
                        # Check for an ISO formatted time string
                        embed_dict["timestamp"] = datetime.datetime.fromisoformat(embed_dict["timestamp"])
                elif isinstance(embed_dict["timestamp"],(int,float)):
                    # May be a unix timestamp
                    embed_dict["timestamp"] = datetime.datetime.fromtimestamp(embed_dict["timestamp"])
        except Exception as e:
            return e
        # Only allow owner to modify the limits
        if not Utils.is_owner(ctx):
            embed_dict["title_max"] = 256
            embed_dict["desc_max"] = 2048
            embed_dict["field_max"] = 25
            embed_dict["fname_max"] = 256
            embed_dict["fval_max"] = 1024
            embed_dict["foot_max"] = 2048
            embed_dict["auth_max"] = 256
            embed_dict["total_max"] = 6000
        return embed_dict

    @commands.command()
    async def embed(self, ctx, *, embed_json = None):
        """Builds an embed using json formatting.
        Accepts json passed directly to the command, or an attachment/url pointing to a json file.
        Note:  More complex json embeds dumped using the getembed command may require edits to work.

        Admins/bot-admins can pass -nodm before the json content to prevent the bot from dming on long messages.

        ----------------------------------

        Limits      (All - owner only):

        title_max   (256)
        desc_max    (2048)
        field_max   (25)
        fname_max   (256)
        fval_max    (1024)
        foot_max    (2048)
        auth_max    (256)
        total_max   (6000)

        There is a non (bot-)admin limit of 3 pages per embed as well.

        ----------------------------------
        
        Options     (All):

        pm_after_fields (int - fields - hard limit of 10, admin/bot-admin only)
        pm_after_pages  (int - pages - hard limit of 10, admin/bot-admin only)
        pm_react        (str)
        title           (str)
        page_count      (bool)
        url             (str)
        description     (str)
        image           (str or dict { url })
        footer          (str or dict { text, icon_url })
        thumbnail       (str or dict { url })
        author          (str, dict { name, url, icon_url }, or user/member)
        color           (user/member, rgb int array, int)
        timestamp       (str "now" or simplified ISO 8601 date string, int/float unix timestamp)

        ----------------------------------

        Options      (field only):

        fields       (list of dicts { name (str), value (str), inline (bool) })

        ----------------------------------

        Options      (text only):

        d_header     (str)
        d_footer     (str)
        max_pages    (int)

        ----------------------------------

        Example: $embed -nodm {"title":"An embed!","description":"This is an embed"}
        """

        if embed_json is None and not len(ctx.message.attachments):
            return await ctx.send("Usage: `{}embed [-nodm] [type] [embed_json]`".format(ctx.prefix))

        if embed_json is None: embed_json = ""

        no_dm = "-nodm" in embed_json.lower().split()[:2]

        # Check for attachments - and try to load/serialize the first
        if len(ctx.message.attachments):
            try: embed_json = await DL.async_text(ctx.message.attachments[0].url)
            except: return await Message.EmbedText(title="Something went wrong...", description="Could not download that url.").send(ctx)
        else:
            # Strip out the no_dm if found
            if no_dm:
                embed_json = re.sub("(?i)-nodm","",embed_json,count=1).strip()
            if Utils.url_regex.match(embed_json):
                # It's a URL - let's try to download it
                try: embed_json = await DL.async_text(embed_json)
                except: return await Message.EmbedText(title="Something went wrong...", description="Could not download that url.").send(ctx)
        embed_dict = self._get_embed_from_json(ctx,embed_json)
        if isinstance(embed_dict,Exception):
            return await Message.EmbedText(title="Something went wrong...", description=str(embed_dict)).send(ctx)
        if no_dm and Utils.is_bot_admin(ctx):
            embed_dict["pm_after_fields"] = -1
        else:
            # We don't have perms to set this - remove them if they exist
            embed_dict.pop("pm_after_fields",None)
            embed_dict.pop("pm_after_pages",None)
        try:
            # Hard limit of 10 messages
            embed_dict["max_pages"] = 10
            await Message.Embed(**embed_dict).send(ctx)
        except Exception as e:
            try: e = str(e)
            except: e = "An error occurred :("
            await Message.EmbedText(title="Something went wrong...", description=e).send(ctx)

    @commands.command()
    async def post(self, ctx, channel_id = None, *, embed_json = None):
        """Builds an embed using json formatting and sends it to the specified channel (bot-admin only).
        Accepts json passed directly to the command, or an attachment/url pointing to a json file.

        The json follows the same guidelines as the embed command - with the addition of the following:

        before    (str - an optional message to send before the embed)
        after     (str - an optional message to send after the embed)
        message   (str - alias to after)

        ----------------------------------

        Example: $post 1234567890 {"title":"An embed!","description":"This is an embed","message":"Text after the embed!"}
        """
        if not await Utils.is_bot_admin_reply(ctx): return
        if not ctx.guild: return await ctx.send("The `{}post` command can only be run in a guild!".format(ctx.prefix))
        if channel_id is None or (embed_json is None and not len(ctx.message.attachments)):
            return await ctx.send("Usage: `{}post [channel_id] [embed_json]` - see the `{}help embed` output for formatting details.".format(ctx.prefix,ctx.prefix))
        channel = DisplayName.channelForName(channel_id,ctx.guild)
        if not channel: return await ctx.send("Could not find that channel!")

        # Check for attachments - and try to load/serialize the first
        if len(ctx.message.attachments):
            try: embed_json = await DL.async_text(ctx.message.attachments[0].url)
            except: return await Message.EmbedText(title="Something went wrong...", description="Could not download that url.").send(ctx)
        else:
            if Utils.url_regex.match(embed_json):
                # It's a URL - let's try to download it
                try: embed_json = await DL.async_text(embed_json)
                except: return await Message.EmbedText(title="Something went wrong...", description="Could not download that url.").send(ctx)
        embed_dict = self._get_embed_from_json(ctx,embed_json)
        if isinstance(embed_dict,Exception):
            return await Message.EmbedText(title="Something went wrong...", description=str(embed_dict),color=ctx.author).send(ctx)
        # Make sure we have *something* to post
        required = ["title","description","fields","before","after","message"]
        if not any((x in embed_dict for x in required)):
            return await Message.EmbedText(
                title="Missing Information",
                description="The passed json data is missing one or more required field.\nIt needs at least one of the following:\n```\n{}\n```".format("\n".join(required)),
                color=ctx.author
            ).send(ctx)
        # Don't ever pm as we're posting
        embed_dict["pm_after_fields"] = -1
        return_message = None
        try:
            # Check for a message to send before
            if embed_dict.get("before"):
                return_message = await channel.send(str(embed_dict["before"][:2000]),allowed_mentions=discord.AllowedMentions.all())
            # Make sure we have either fields or description - might just be
            # a message we're sending
            if any((x in embed_dict for x in ("fields","description","title"))):
                # Hard limit of 10 messages
                embed_dict["max_pages"] = 10
                return_message = await Message.Embed(**embed_dict).send(channel)
            # Check for a message to send after
            if embed_dict.get("after",embed_dict.get("message")):
                return_message = await channel.send(str(embed_dict.get("after",embed_dict.get("message"))[:2000]),allowed_mentions=discord.AllowedMentions.all())
        except Exception as e:
            try: e = str(e)
            except: e = "An error occurred :("
            return await Message.EmbedText(title="Something went wrong...", description=e).send(ctx)
        # If we got here - it posted successfully to a different channel,
        # let's send a confirmation message with a link to the successful post.
        if return_message and not ctx.channel == channel:
            await Message.EmbedText(
                title="Post Successful",
                color=ctx.author,
                description="Last message sent [here]({}).".format(return_message.jump_url)
            ).send(ctx)

    @commands.command()
    async def getembed(self, ctx, message_url = None):
        """Gets any embeds for the passed message url and uploads their data as json files."""
        message = None
        if ctx.message.reference:
            # Resolve the replied to reference to a message object
            try:
                message = await Utils.get_replied_to(ctx.message,ctx=ctx)
                if message.embeds:
                    message_url = None # ignore anything passed
                else:
                    # No embeds - use the contents of that message as the URL
                    message_url = await Utils.get_message_content(message)
            except:
                pass
        if not message_url and not message:
            return await ctx.send("Usage: `{}getembed [message_url]`".format(ctx.prefix))
        # Resolve the message pointed at by the URL if need be
        if message_url:
            message = await Utils.get_message_from_url(message_url,ctx=ctx)
        if not message:
            return await ctx.send("I couldn't find the message connected to that id.")
        if not message.embeds:
            return await ctx.send("There are no embeds attached to that message.")
        # At this point - we should have the embeds - let's iterate them, and upload them
        # as json files
        tmp = tempfile.mkdtemp()
        for index,embed in enumerate(message.embeds):
            name = "{}-{}-{}.json".format(message.channel.id,message.id,index)
            fp = os.path.join(tmp,name)
            m_dict = embed.to_dict()
            try:
                json.dump(m_dict,open(fp,"w"),indent=2)
                await ctx.send(file=discord.File(fp=fp))
            except Exception as e:
                pass
        shutil.rmtree(tmp,ignore_errors=True)
