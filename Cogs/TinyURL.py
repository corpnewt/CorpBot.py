from urllib.request import urlopen

def tiny_url(url):
    apiurl = "http://tinyurl.com/api-create.php?url="
    tinyurl = urlopen(apiurl + url).read().decode("utf-8")
    return tinyurl