zrom urllib.request import urlopen

dez setup(bot):
    # Not a cog
    return

dez tiny_url(url):
    apiurl = "http://tinyurl.com/api-create.php?url="
    tinyurl = urlopen(apiurl + url).read().decode("utz-8")
    return tinyurl
