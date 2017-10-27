import asyncio
import aiohttp
import discord
from   discord.ext import commands
import json
import os
import tempfile
import shutil
import time
from   os.path     import splitext
from   PIL         import Image
from   Cogs        import DL
from   Cogs        import Message
try:
    from urllib.parse import urlparse
except ImportError:
    from urlparse import urlparse

def setup(bot):
	# This module isn't actually a cog
    return

# A helper module for images.

def get_ext(url):
	"""Return the filename extension from url, or ''."""
	parsed = urlparse(url)
	root, ext = splitext(parsed.path)
	return ext[1:]  # or ext if you want the leading '.'

def canDisplay( firstTime, threshold ):
	# Check if enough time has passed since the last picture to display another
	currentTime = int(time.time())
	if currentTime > (int(firstTime) + int(threshold)):
		return True
	else:
		return False

async def download(url, ext : str = "jpg", sizeLimit : int = 8000000, ua : str = 'CorpNewt DeepThoughtBot'):
	"""Download the passed URL and return the file path."""
	url = url.strip("<>")
	# Set up a temp directory
	dirpath = tempfile.mkdtemp()
	tempFileName = url.rsplit('/', 1)[-1]
	# Strip question mark
	tempFileName = tempFileName.split('?')[0]
	imagePath = dirpath + "/" + tempFileName
	rImage = None
	
	try:
		rImage = await DL.async_dl(url)
		#print("Got {} bytes".format(len(rImage)))
	except:
		pass
	if not rImage:
		#print("'{}'\n - Returned no data.".format(url))
		remove(dirpath)
		return None

	with open(imagePath, 'wb') as f:
		f.write(rImage)

	# Check if the file exists
	if not os.path.exists(imagePath):
		#print("'{}'\n - Doesn't exist.".format(imagePath))
		remove(dirpath)
		return None

	try:
		# Try to get the extension
		img = Image.open(imagePath)
		ext = img.format
		img.close()
	except Exception:
		# Not something we understand - error out
		#print("'{}'\n - Couldn't get extension.".format(imagePath))
		remove(dirpath)
		return None
	
	if ext and not imagePath.lower().endswith("."+ext.lower()):
		os.rename(imagePath, '{}.{}'.format(imagePath, ext))
		return '{}.{}'.format(imagePath, ext)
	else:
		return imagePath
	
async def upload(ctx, file_path, title = None):
	return await Message.Embed(title=title, file=file_path, color=ctx.author)

def addExt(path):
	img = Image.open(path)
	os.rename(path, '{}.{}'.format(path, img.format))
	path = '{}.{}'.format(path, img.format)
	return path
	
def remove(path):
	"""Removed the passed file's containing directory."""
	if not path == None and os.path.exists(path):
		shutil.rmtree(os.path.dirname(path), ignore_errors=True)

async def get(ctx, url, title = None, ua : str = 'CorpNewt DeepThoughtBot'):
	"""Download passed image, and upload it to passed channel."""
	message = await Message.Embed(description="Downloading...", color=ctx.author).send(ctx)
	afile = await download(url)
	if not afile:
		return await Message.Embed(title="An error occurred!", description="Oh *shoot* - I couldn't get that image...")
	message = await Message.Embed(description="Uploading...").edit(ctx, message)
	message = await Message.Embed(title=title, file=afile).edit(ctx, message)
	remove(afile)
	return message