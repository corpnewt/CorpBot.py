from urllib.request import urlopen


def setup(bot_start):
    return


async def tiny_url(url, bot):
    apiurl = "http://tinyurl.com/api-create.php?url="
    tinyurl = await bot.loop.run_in_executor(None, lambda: urlopen(apiurl + url).read().decode("utf-8"))
    # tinyurl = urlopen(apiurl + url).read().decode("utf-8")
    return tinyurl
