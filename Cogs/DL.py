import asyncio, aiohttp, json

def setup(bot):
	# Not a cog
	pass

async def async_post_json(url, data = None, headers = None):
    with aiohttp.ClientSession(headers=headers) as session:
        async with session.post(url, data=data) as response:
            return await response.json()

async def async_post_text(url, data = None, headers = None):
    with aiohttp.ClientSession(headers=headers) as session:
        async with session.post(url, data=data) as response:
            res = await response.read()
            return res.decode("utf-8", "replace")

async def async_post_bytes(url, data = None, headers = None):
    with aiohttp.ClientSession(headers=headers) as session:
        async with session.post(url, data=data) as response:
            return await response.read()

async def async_head_json(url, headers = None):
    with aiohttp.ClientSession(headers=headers) as session:
        async with session.head(url) as response:
            return await response.json()

async def async_dl(url, headers = None):
    # print("Attempting to download {}".format(url))
    total_size = 0
    data = b""
    async with aiohttp.ClientSession(headers=headers) as session:
        async with session.get(url) as response:
            assert response.status == 200
            while True:
                chunk = await response.content.read(4*1024) # 4k
                data += chunk
                total_size += len(chunk)
                if not chunk:
                    break
                if total_size > 8000000:
                    # Too big...
                    # print("{}\n - Aborted - file too large.".format(url))
                    return None
    return data

async def async_text(url, headers = None):
    data = await async_dl(url, headers)
    if data:
        return data.decode("utf-8", "replace")
    else:
        return data

async def async_json(url, headers = None):
    data = await async_dl(url, headers)
    if data:
        return json.loads(data.decode("utf-8", "replace"))
    else:
        return data
