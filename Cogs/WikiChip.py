from discord.ext import commands
from Cogs import Message
from Cogs import DL
from Cogs import PickList
import re


def setup(bot):
    # Add the bot
    bot.add_cog(WikiChip(bot))


class WikiChip(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.schema = {
            "Microarchitecture": "Microarchitecture",
            "Codename": "Codename",
            "Family": "Family",
            "Cores": "# of Cores",
            "Threads": "# of Threads",
            "Series": "Series",
            "Frequency": "Base Clock Speed",
            "Turbo Frequency": "Max Clock Speed",
            "Max Memory": "Max Memory",
            "ISA": "ISA",
            "Word Size": "Word Size",
            "TDP": "TDP",
        }

    @commands.command(no_pm=True,aliases=("iamd",))
    async def wikichip(self, ctx, *, text: str = None):
        """Searches WikiChip for AMD CPU info."""

        args = {
            "title": "WikiChip AMD Search",
            "description": "Usage: `{}wikichip [cpu model]`".format(ctx.prefix),
            "footer": "Powered by https://en.wikichip.org/wiki/amd",
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

        args["description"] = "Gathering info..."
        message = await Message.EmbedText(**args).send(ctx)

        try:
            response = await self.get_data(text)
        except:
            response = None

        # Check if we got nothing
        if not response:
            args["description"] = "No results returned for `{}`.".format(
                text.replace("`", "").replace("\\", ""))
            await Message.EmbedText(**args).edit(ctx, message)
            return

        fields = [
            {
                "name": self.schema.get(x, ""),
                "value": response.get(x, None),
                "inline": True
            }
            for x in self.schema
            if self.schema.get(x) and response.get(x)
        ]

        await Message.Embed(
            pm_after=12,
            thumbnail=response.get("Thumbnail",None),
            title=response.get("Title","WikiChip AMD Search"),
            fields=fields,
            url=response.get("URL"),
            footer="Powered by https://en.wikichip.org/wiki/amd",
            color=ctx.author
        ).edit(ctx, message)

    async def get_data(self, cpu_name):
        """
        Queries the AMD section from wikichip,
        parses the contents, and looks for the codename/µarch.
        """
        formatted = next((x for x in re.sub(r"(?i)(ryzen|amd|ep(y|i)c|threadripper|tr)","",cpu_name).split() if len(x) > 1),None)
        if formatted is None: return
        
        for URL in ("https://en.wikichip.org/wiki/{}".format(formatted),"https://en.wikichip.org/wiki/amd/ryzen_threadripper/{}".format(formatted)):
            try:
                contents = await DL.async_text(URL)
            except AssertionError:
                continue
            break

        data = {"URL": URL}

        try:
            # <td class="header-main" colspan="2">Name Here</td>
            data["Title"] = contents.split('<td class="header-main"')[1].split(">")[1].split("</")[0]
        except:
            pass

        try:
            # Get the parent family image url if we can
            test_cont = contents
            if not "wikichip_ogimage" in test_cont: # No icon, get the family if possible
                family_url = "https://en.wikichip.org"+contents.split('<span class="subpages"')[1].split("</span")[0].split('<a href="')[-1].split('"')[0]
                test_cont = await DL.async_text(family_url)
            # Try to get any available icon url from the srcset
            data["Thumbnail"] = "https://en.wikichip.org"+test_cont.split("wikichip_ogimage")[0].split('src="')[-1].split('"')[0]
        except:
            pass

        try:
            data["Codename"] = re.search(
                r"(?<=\>).+(?=\<)",
                re.search(
                    r"\<a\s?href=\"\/wiki\/amd\/cores\/(\w|\d)+\s?(\w|\d)+?\"[^>]+\>[^<]+?\<\/a\>",
                    contents,
                ).group(),
            ).group()
        except Exception:
            pass

        try:
            data["Microarchitecture"] = re.search(
                r"(?<=\>).+(?=\<)",
                re.search(
                    r"\<a\s?href=\"\/wiki\/amd\/microarchitectures\/(\w|\d)+\s?(\w|\d)+?\"[^>]+\>[^<]+?\<\/a\>",
                    contents,
                ).group(),
            ).group()
        except Exception:
            pass

        try:
            if not data["Microarchitecture"]:
                data["Microarchitecture"] = re.search(
                    r"(?<=\>).+(?=\<)",
                    re.search(
                        r"\<a\s?href=\"\/wiki\/amd\/(\w|\d)+\s?(\w|\d)+?\s?\(microarch\)\"[^>]+\>[^<]+?\<\/a\>",
                        contents,
                    ).group(),
                ).group()
        except Exception:
            pass

        try:
            data["Family"] = re.search(
                r"(?<=\>).+(?=\<)",
                re.search(
                    r"(?<=Family\<\/td\>\<td\>)\<a[^>]+\>[^<]+\</a\>",
                    contents
                ).group()
            ).group()
        except Exception:
            pass

        for key, value in self.schema.items():
            val = re.search(
                r"(?<=%s\<\/td\>\<td\>)[^<]+(?=\</td\>)" % key,
                contents
            )

            if val:
                data[key] = val.group()

        try:
            data["TDP"] = re.search(
                # Masochism.
                r"(?<=\<abbr\stitle=\"Thermal Design Power\"\>TDP\<\/abbr\>\<\/td\>\<td\>)[^<]+(?=\<\/td\>)",
                contents
            ).group()
        except Exception:
            pass

        return data
