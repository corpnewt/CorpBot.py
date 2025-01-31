import aiohttp, json

def setup(bot):
	# Not a cog
	pass

async def async_post_json(url, data = None, headers = None, ssl = None):
    async with aiohttp.ClientSession(headers=headers) as session:
        async with session.post(url, data=data, ssl=ssl) as response:
            return await response.json()

async def async_post_text(url, data = None, headers = None, ssl = None):
    async with aiohttp.ClientSession(headers=headers) as session:
        async with session.post(url, data=data, ssl=ssl) as response:
            res = await response.read()
            return res.decode("utf-8", "replace")

async def async_post_bytes(url, data = None, headers = None, ssl = None):
    async with aiohttp.ClientSession(headers=headers) as session:
        async with session.post(url, data=data, ssl=ssl) as response:
            return await response.read()

async def async_head(url, headers = None, ssl = None):
    async with aiohttp.ClientSession(headers=headers) as session:
        async with session.head(url, ssl=ssl) as response:
            return response.headers

async def async_head_json(url, headers = None, ssl = None):
    async with aiohttp.ClientSession(headers=headers) as session:
        async with session.head(url, ssl=ssl) as response:
            return await response.json()

async def async_dl(url, headers=None, ssl=None, return_headers=False, assert_status=200, chunk_size=4096, max_size=8000000):
    total_size = 0
    data = b""
    response_headers = None
    async with aiohttp.ClientSession(headers=headers) as session:
        async with session.get(url, ssl=ssl) as response:
            response_headers = response.headers
            if assert_status:
                if isinstance(assert_status,int):
                    # Wrap it in a tuple - as we can check for multiple
                    # using the "in" operator
                    assert_status = (assert_status,)
                assert response.status in assert_status
            while True:
                chunk = await response.content.read(chunk_size) # Defaults to 4k
                data += chunk
                total_size += len(chunk)
                if not chunk:
                    break
                if max_size and total_size > max_size:
                    # Too big... Ditch the data and bail from the loop
                    data = None
                    break
    return (data,response_headers) if return_headers else data

async def async_text(url, headers=None, ssl=None, return_headers=False, assert_status=200, chunk_size=4096, max_size=8000000):
    data,headers = await async_dl(
        url,
        headers=headers,
        ssl=ssl,
        return_headers=True,
        assert_status=assert_status,
        chunk_size=chunk_size,
        max_size=max_size
    )
    if data is not None:
        data = data.decode("utf-8","replace")
    return (data,headers) if return_headers else data

async def async_json(url, headers=None, ssl=None, return_headers=False, assert_status=200, chunk_size=4096, max_size=8000000):
    data,headers = await async_dl(
        url,
        headers=headers,
        ssl=ssl,
        return_headers=True,
        assert_status=assert_status,
        chunk_size=chunk_size,
        max_size=max_size
    )
    if data is not None:
        data = json.loads(data.decode("utf-8","replace"))
    return (data,headers) if return_headers else data