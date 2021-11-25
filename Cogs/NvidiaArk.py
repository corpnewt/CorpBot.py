from discord.ext import commands
from Cogs import Message
from Cogs import DL
from Cogs import PickList
from urllib.parse import quote
import re


def setup(bot):
    # Add the bot
    bot.add_cog(NvidiaArk(bot))


class NvidiaArk(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(no_pm=True, aliases=("nark", "nvark"))
    async def nvidiaark(self, ctx, *, text: str = None):
        """Searches TechPowerUP's site for GPU info."""

        args = {
            "title": "TechPowerUP Search",
            "description": "Usage: `{}nvark [gpu model]`".format(ctx.prefix),
            "footer": "Powered by https://www.techpowerup.com/",
            "color": ctx.author,
        }

        if not text:
            return await Message.EmbedText(**args).send(ctx)

        # Strip single quotes
        text = text.replace("'", "")
        text = re.sub(r"(N|n)(V|v)(I|i)(D|d)(I|i)(A|a)", "", text)

        if not text:
            return await Message.EmbedText(**args).send(ctx)

        args["description"] = "Gathering info..."
        message = await Message.EmbedText(**args).send(ctx)

        response = await self.search(text)

        if response == -1:
            args[
                "description"
            ] = "I see what you tried... good one! But we only support NVidia queries."
            return await Message.EmbedText(**args).edit(ctx, message)

        if not response:
            args["description"] = "No results returned for `{}`.".format(
                text.replace("`", "").replace("\\", "")
            )
            return await Message.EmbedText(**args).edit(ctx, message)

        elif len(response) == 1:
            # Set it to the first item
            response = await self.get_match_data(response[0])

        elif len(response) > 1:
            # Allow the user to choose which one they meant.
            index, message = await PickList.Picker(
                message=message,
                title="Multiple Matches Returned For `{}`:".format(
                    text.replace("`", "").replace("\\", "")
                ),
                list=[x.get("name", "UNDETERMINABLE")
                      for x in self.prettify(response)],
                ctx=ctx,
            ).pick()

            if index < 0:
                args["description"] = "Search cancelled."
                return await Message.EmbedText(**args).edit(ctx, message)

            # Got something
            response = await self.get_match_data(response[index])

        # At this point - we should have a single response
        # Let's display the data.
        await PickList.PagePicker(
            title=response.get("name", "NVidia Search"),
            list=response["fields"],
            url=response.get("url"),
            thumbnail=response.get("image", None),
            footer="Powered by https://www.techpowerup.com/",
            color=ctx.author,
            ctx=ctx,
            max=18,
            message=message,
        ).pick()

    async def search(self, gpu_name):
        BASE_URL = "https://www.techpowerup.com"
        URL = BASE_URL + "/gpu-specs/?ajaxsrch={}".format(quote(gpu_name))

        contents = await DL.async_text(URL)

        if "nothing found" in contents.lower():
            return []

        if not "vendor-nvidia" in contents.lower():
            return -1

        nvidia = True
        lines = contents.split("\n")
        data = []
        url = ""
        temp_name = ""

        for line_index in range(len(lines)):
            line = lines[line_index].strip()

            if '<td class="vendor-' in line.lower():
                if not "vendor-nvidia" in line.lower():
                    nvidia = False
                elif "vendor-nvidia" in line.lower():
                    nvidia = True

            if not nvidia:
                continue

            if '<a href="' in line.lower():
                try:
                    name = line.split(">")[1].split("<")[0]
                except IndexError:
                    continue

                if (
                    name.lower().strip() in gpu_name.lower().strip()
                    or gpu_name.lower().strip() in name.lower().strip()
                ):
                    if temp_name:
                        data.append({"name": temp_name, "url": url})
                        temp_name = ""

                    url = BASE_URL + \
                        lines[line_index].split('href="')[1].split('">')[0]
                    temp_name = name

                if "nvidia-" in line.lower():
                    temp_name += " ({0})".format(name)

            if (
                temp_name
                and "<td>" in line.lower()
                and ("GB" in line or "MB" in line or "KB" in line)
            ):
                temp_name += " -> {0} {1} {2}".format(
                    "{", line.split(">")[1].split("<")[0], "}"
                )

        return data

    async def get_match_data(self, match):
        BASE_URL = "https://www.techpowerup.com"
        contents = await DL.async_text(match["url"])
        lines = contents.split("\n")
        blacklist = {
            "Relative Performance",
            "Theoretical Performance",
            "Retail boards based on this design",
        }
        data = {"name": "", "url": match["url"], "image": None, "fields": []}
        capturing = False

        for line_index in range(len(lines)):
            line = lines[line_index]

            if '<h1 class="gpudb-name">' in line.lower():
                try:
                    clean = line.split(">")[1].split("<")[0].strip()
                    data["name"] = clean
                    continue
                except IndexError:
                    continue

            if '<img class="gpudb-large-image' in line.lower() and not data["image"]:
                data["image"] = line.split('src="')[1].split('"')[0]

            if any(x.lower() in line.lower() for x in blacklist):
                capturing = False
                continue

            if "<h2>" in line.lower() and "<h2>" != line.lower().strip():
                if "<h2>" != line.lower().strip():
                    capturing = True
                    continue
                else:
                    capturing = False
                    continue

            if '<dl class="clearfix">' in line.lower() and capturing:
                title = ""
                value = ""
                value_url = ""

                try:
                    if "<dt>" in lines[line_index + 1].strip():
                        title = lines[line_index +
                                      1].split(">")[1].split("<")[0]
                        value = (
                            lines[line_index + 3].strip()
                            if "<dd >" in lines[line_index + 2].strip()
                            or "<dd>" == lines[line_index + 2].strip()
                            else lines[line_index + 2].split("dd>")[1].split("</dd")[0]
                        )

                        if '<a href="' in value.lower():
                            value_url = value.split(
                                'href="')[1].split('"')[0].strip()
                            value = (
                                value.split(
                                    '<a href="{}">'.format(value_url))[1]
                                .split("</a>")[0]
                                .strip()
                            )

                        value = value.replace("</", "").replace("<br />", " ")

                        if "<span" in value.lower():
                            value = value.split("<")[0].strip()

                    elif '<dl class="clearfix">' in lines[line_index + 1].strip():
                        title = lines[line_index +
                                      2].split(">")[1].split("<")[0]
                        value = (
                            lines[line_index + 4].strip()
                            if "<dd >" in lines[line_index + 3].strip()
                            or "<dd>" == lines[line_index + 3].strip()
                            else lines[line_index + 3].split("dd>")[1].split("</dd")[0]
                        )

                        if '<a href="' in value.lower():
                            value_url = value.split(
                                'href="')[1].split('"')[0].strip()
                            value = (
                                value.split(
                                    '<a href="{}">'.format(value_url))[1]
                                .split("</a>")[0]
                                .strip()
                            )

                        value = value.replace("</", "").replace("<br />", " ")

                        if "<span" in value.lower():
                            value = value.split("<")[0].strip()
                except IndexError:
                    continue

                if "current price" in title.lower():
                    continue

                if title and value:
                    formatted = (
                        "[{0}]({1})".format(value, BASE_URL + value_url)
                        if value_url
                        else value
                    )

                    if any(
                        x.get("name") == title or x.get("value") == formatted
                        for x in data["fields"]
                    ):
                        continue

                    data["fields"].append(
                        {"name": title, "value": formatted, "inline": True}
                    )

        return data

    def prettify(self, items):
        # Extracts the longest item from a filtered list.
        #
        # FILTERING:
        # For each item, we do the following:
        #
        #     GeForce 940M (GM107) -> { 2GB, DDR3, 64 bit }   <-- split by ' (' here
        #
        #           => [ 'GeForce 940M', 'GM107) -> { 2GB, DDR3, 64 bit }
        #       [0] -> [ 'GeForce 940M']
        #       ^ index after splitting on ' ('
        #
        # We are essentially mapping each item by
        # capturing what comes before `(GM107)`
        longest = len(max([x.get("name", "").split(" (")[0]
                      for x in items], key=len))

        for index in range(len(items)):
            try:
                first, second = items[index].get("name", "").split(" (")
            except ValueError:
                continue

            items[index]["name"] = "{0}{1}{2}".format(
                first, " " * (longest - len(first) + 2) + "(", second
            )

        return self._prettify_ram(items)

    def _prettify_ram(self, items):
        # Extracts the longest item from a filtered list.
        #
        # FILTERING:
        # For each item, we do the following:
        #
        #     GeForce 940M (GM107) -> { 2GB, DDR3, 64 bit }   <-- split by '{' here
        #
        #           => [ 'GeForce 940M (GM107) -> ', '2GB, DDR3, 64 bit }' ]
        #       [1] -> [ '2GB, DDR3, 64 bit }'] <-- split by '}' here
        #       [0] -> [ '2GB, DDR3, 64 bit' ]
        #       ^ index after splitting on '}'
        #
        # We are essentially mapping each item by
        # capturing what's inside of `{` and `}`
        longest = len(max([x.get("name", "").split(
            "{ ")[1].split(" }")[0] for x in items], key=len))

        for index in range(len(items)):
            try:
                first, item = [
                    x.replace(" }", "") for x in items[index].get("name", "").split("{ ")]
            except ValueError:
                continue

            from math import floor, ceil

            total = longest + 4
            N = len(" " * (ceil((total - len(item)) / 2)))
            J = len(" " * (floor((total - len(item)) / 2)))

            items[index]["name"] = "{0}{1}{2}{3}{4}{5}".format(
                first, "{", " " * (N + 1), item, " " * (J + 1), "}"
            )

        return items
