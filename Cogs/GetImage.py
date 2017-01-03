import asyncio
import discord
from   discord.ext import commands
import json
import os
import tempfile
import shutil
import urllib.request
import urllib
import requests
import time
from   os.path     import splitext
from   PIL         import Image
try:
    from urllib.parse import urlparse
except ImportError:
    from urlparse import urlparse

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

def download(url, ext : str = "jpg", sizeLimit : int = 8000000, ua : str = 'CorpNewt DeepThoughtBot'):
	"""Download the passed URL and return the file path."""
	# Set up a temp directory
	dirpath = tempfile.mkdtemp()
	tempFileName = url.rsplit('/', 1)[-1]
	# Strip question mark
	tempFileName = tempFileName.split('?')[0]
	imagePath = dirpath + "/" + tempFileName
	
	try:
		rImage = requests.get(url, stream = True, headers = {'User-agent': ua})
	except:
		remove(dirpath)
		return None

	with open(imagePath, 'wb') as f:
		for chunk in rImage.iter_content(chunk_size=1024):
			if chunk:
				f.write(chunk)
	
	# Let's make sure it's less than the passed limit
	imageSize = os.stat(imagePath)
	
	while int(imageSize.st_size) > sizeLimit:
		# Image is too big - resize
		myimage = Image.open(imagePath)
		xsize, ysize = myimage.size
		ratio = sizeLimit/int(imageSize.st_size)
		xsize *= ratio
		ysize *= ratio
		myimage = myimage.resize((int(xsize), int(ysize)), Image.ANTIALIAS)
		myimage.save(imagePath)
		imageSize = os.stat(imagePath)
		
	img = Image.open(imagePath)
	ext = img.format
	img.close()
	
	if ext:
		os.rename(imagePath, '{}.{}'.format(imagePath, ext))
		return '{}.{}'.format(imagePath, ext)
	else:
		return imagePath
	
async def upload(path, bot, channel):
	with open (path, 'rb') as f:
		await bot.send_file(channel, path)

def addExt(path):
	img = Image.open(path)
	os.rename(path, '{}.{}'.format(path, img.format))
	path = '{}.{}'.format(path, img.format)
	return path
	
def remove(path):
	"""Removed the passed file's containing directory."""
	shutil.rmtree(os.path.dirname(path), ignore_errors=True)

async def get(url, bot, channel, title : str = 'Unknown', ua : str = 'CorpNewt DeepThoughtBot'):
	"""Download passed image, and upload it to passed channel."""
	message = await bot.send_message(channel, 'Downloading...')
	file = download(url)
	if not file:
		await bot.edit_message(message, 'Oh *shoot* - I couldn\'t get that image...')
		return

	message = await bot.edit_message(message, 'Uploading...')
	await upload(file, bot, channel)
	await bot.edit_message(message, title)
	remove(file)