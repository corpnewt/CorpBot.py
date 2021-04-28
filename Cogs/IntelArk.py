from discord.ext import commands
from Cogs import Message
from urllib.request import urlopen
from googlesearch import search
from bs4 import BeautifulSoup


def setup(bot):
    # Add the bot
    bot.add_cog(IntelArk(bot))


class IntelArk(commands.Cog):
    # CSS Selectors for processor name, thumbnail image
    SELECTOR_NAME = ".h1"
    SELECTOR_THUMBNAIL = ".badge-loaded > img"
    SELECTOR_TABLE_ROW = ".specs-list li"
    TAG_TABLE_CELL = "span"
    desired_fields = ['Processor Number',
                      'Product Collection',
                      'Launch Date',
                      'Processor Base Frequency',
                      '# of Cores',
                      '# of Threads',
                      '# of Threads',
                      'Max Memory Size',
                      'TDP',
                      'Processor Graphics',
                      'Instruction Set']

    def __init__(self, bot):
        self.bot = bot
        self.fields = dict()

    @staticmethod
    def get_ark_url(query):
        """Uses google search to retrieve iArk url for a query."""

        res = search(query + " site:ark.intel.com", num=1, verify_ssl=False)
        return next(res, None)

    @staticmethod
    def parse_ark_data(page):
        """Scrape ark URL for relevant info"""

        results = page.select(IntelArk.SELECTOR_TABLE_ROW)
        data = list()
        for x in results:
            spans = x.find_all(IntelArk.TAG_TABLE_CELL, recursive=False)
            data.append([spans[0].get_text().strip(), spans[1].get_text().strip()])
        return data

    @staticmethod
    def get_ark_name(page):
        heading = page.select_one(IntelArk.SELECTOR_NAME)
        if heading:
            return heading.get_text().strip()
        elif page.title:
            return page.title.string
        else:
            return "Intel Ark"

    @staticmethod
    def get_ark_thumbnail(page):
        img = page.select_one(IntelArk.SELECTOR_THUMBNAIL)
        if not img:
            return None
        else:
            return img['src']

    @commands.command(pass_context=True, no_pm=True)
    async def iark(self, ctx, *, text: str = None):
        """Search Ark for Intel CPU info."""

        self.fields.clear()
        args = {
            "title": "Intel Ark Search",
            "description": 'Usage: `{}iark [cpu model]`'.format(ctx.prefix),
            "footer": "Powered by http://ark.intel.com",
            "color": ctx.author
        }

        if text == None:
            await Message.EmbedText(**args).send(ctx)
            return

        # Strip single quotes
        text = text.replace("'", "")
        if not len(text):
            await Message.EmbedText(**args).send(ctx)
            return

        # message = await Message.EmbedText(title="Intel Ark Search",description="Gathering info...",color=ctx.author,footer="Powered by http://ark.intel.com").send(ctx)

        args["description"] = "Gathering info..."
        message = await Message.EmbedText(**args).send(ctx)

        # Use google to search for ark URL
        ark_url = self.get_ark_url(text)
        if not ark_url:
            args["description"] = "No results returned for `{}`.".format(text.replace("`", "").replace("\\", ""))
            await Message.EmbedText(**args).edit(ctx, message)
            return

        html = urlopen(ark_url)
        html = html.read().decode("utf-8")
        page = BeautifulSoup(html, "lxml")
        data = self.parse_ark_data(page)
        print(data)

        if not data:
            args["description"] = "No results returned for `{}`.".format(text.replace("`", "").replace("\\", ""))
            await Message.EmbedText(**args).edit(ctx, message)
            return

        for x in data:
            if any(field in x[0] for field in self.desired_fields):
                self.fields[x[0]] = x[1]

        # At this point - we should have a single response
        # Let's format and display.
        fields = [{"name": x, "value": self.fields[x], "inline": True} for x in self.fields]
        thumbnail = self.get_ark_thumbnail(page)
        title = self.get_ark_name(page)
        await Message.Embed(
            thumbnail=thumbnail,
            pm_after=12,
            title=title,
            fields=fields,
            url=ark_url,
            footer="Powered by http://ark.intel.com",
            color=ctx.author
        ).edit(ctx, message)
