import discord, asyncio, gzip, time, datetime, os, re
from   discord.ext import commands
from   Cogs import DL
from   Cogs import Message

def setup(bot):
	# Add the bot
	bot.add_cog(PciUsb(bot))

class PciUsb(commands.Cog):

	# Init with the bot reference, and a reference to the settings var
	def __init__(self, bot):
		self.bot = bot
		self.is_current = False
		self.pci_ids_url = "https://pci-ids.ucw.cz"
		self.pci_ids = {}
		self.usb_ids_url = "https://usb-ids.gowdy.us/"
		self.usb_ids = {}
		self.ids_wait_time = 86400 # Default of 24 hours (86400 seconds)
		self.ven_dev_regex = re.compile(r"(?i)(0x|VEN_)?(?P<vendor>[0-9a-fA-F]{1,4})(\s|:|&|,)+(0x|DEV_)?(?P<device>[0-9a-fA-F]{1,4})")

	def _is_submodule(self, parent, child):
		return parent == child or child.startswith(parent + ".")

	@commands.Cog.listener()
	async def on_unloaded_extension(self, ext):
		# Called to shut things down
		if not self._is_submodule(ext.__name__, self.__module__):
			return
		self.is_current = False

	@commands.Cog.listener()
	async def on_loaded_extension(self, ext):
		# See if we were loaded
		if not self._is_submodule(ext.__name__, self.__module__):
			return
		self.is_current = True
		# Load the local files first
		self._load_local_pci_ids()
		self._load_local_usb_ids()
		# Start the update loops
		self.bot.loop.create_task(self.update_pci_ids())

	async def update_pci_ids(self):
		print("Starting pci.ids/usb.ids update loop - repeats every {:,} second{}...".format(self.ids_wait_time,"" if self.ids_wait_time==1 else "s"))
		await self.bot.wait_until_ready()
		while not self.bot.is_closed():
			if not self.is_current:
				# Bail if we're not the current instance
				return
			t = time.time()
			# Get pci.ids first
			print("Updating pci.ids.gz/usb.ids.gz: {}".format(datetime.datetime.now().time().isoformat()))
			if not await self._dl_ids(self.pci_ids_url,"pci.ids.gz",self._load_local_pci_ids):
				print("Could not download pci.ids.gz!")
				if self._load_local_pci_ids():
					print(" - Falling back on local copy!")
			# Then get usb.ids
			if not await self._dl_ids(self.usb_ids_url,"usb.ids.gz",self._load_local_usb_ids):
				print("Could not download usb.ids.gz!")
				if self._load_local_usb_ids():
					print(" - Falling back on local copy!")
			print("pci.ids.gz/usb.ids.gz loop - took {:,} seconds.".format(time.time()-t))
			await asyncio.sleep(self.ids_wait_time)

	async def _dl_ids(self, url, name, load_endpoint):
		try:
			_html = await DL.async_text(url)
			assert _html
		except:
			return False
		# Try to scrape for the .gz compressed download link
		dl_url = None
		search = ">{}</a>".format(name)
		for line in _html.split("\n"):
			if search in line:
				# Got it - build the URL
				try:
					dl_url = "/".join([
						url.rstrip("/"),
						line.split('"')[1].lstrip("/")
					])
					break
				except:
					continue
		if not dl_url:
			return False
		# Got a download URL - let's actually download it
		try:
			saved_file = await DL.async_dl(dl_url)
			with open(name,"wb") as f:
				f.write(saved_file)
			assert os.path.isfile(name)
		except:
			return False
		return load_endpoint()

	def _load_local_pci_ids(self):
		pci_ids = self._load_local_ids_file("pci.ids.gz")
		if pci_ids:
			self.pci_ids = pci_ids
			return True
		return False
	
	def _load_local_usb_ids(self):
		usb_ids = self._load_local_ids_file("usb.ids.gz")
		if usb_ids:
			self.usb_ids = usb_ids
			return True
		return False

	def _load_local_ids_file(self, file_path="pci.ids.gz"):
		try:
			_ids_file = gzip.open(file_path) \
			.read().decode(errors="ignore").replace("\r","") \
			.split("\n")
		except:
			return None
		def get_id_name_from_line(line):
			# Helper to rip the id(s) out of the passed
			# line and convert to an int
			try:
				line = line.strip()
				if line.startswith("C "):
					line = line[2:]
				_id = int(line.split("  ")[0].replace(" ",""),16)
				name = "  ".join(line.split("  ")[1:])
				return (_id,name)
			except:
				return None
		# Walk our file and build out our dict
		_ids = {}
		_classes = False
		device = sub = None
		key = "devices"
		for line in _ids_file:
			if line.strip().startswith("# List of known device classes"):
				_classes = True
				key = "classes"
				device = sub = None
				continue
			if line.strip().startswith("#"):
				continue # Skip comments
			if line.startswith("\t\t"):
				if sub is None: continue
				# Got a subsystem/programming interface name
				try:
					_id,name = get_id_name_from_line(line)
					sub[_id] = name
				except:
					continue
			elif line.startswith("\t"):
				if device is None: continue
				# Got a device/subclass name
				try:
					_id,name = get_id_name_from_line(line)
					device[_id] = sub = {"name":name}
				except:
					sub = None
					continue
			else:
				# Got a vendor/class
				try:
					_id,name = get_id_name_from_line(line)
					if not key in _ids:
						_ids[key] = {}
					_ids[key][_id] = device = {"name":name}
				except:
					device = sub = None
					continue
		return _ids

	def _get_ven_dev(self, ven_dev):
		# Takes a passed ven:dev string and attempts to break it
		# into the respective parts
		#
		# Returns (vendor_int, device_int, ids_string)
		try:
			m = self.ven_dev_regex.search(ven_dev)
			ven_id = int(m.group("vendor"),16)
			dev_id = int(m.group("device"),16)
			ven_dev = "{}:{}".format(
				m.group("vendor").rjust(4,"0").upper(),
				m.group("device").rjust(4,"0").upper()
			)
			return (ven_id,dev_id,ven_dev)
		except Exception as e:
			print(e)
			pass
		return None

	def _get_info(self, vendor_id, device_id, search_dict):
		if not isinstance(vendor_id,int) or not isinstance(device_id,int):
			return None
		# Resolve the vendor and device ids
		vendor_dict = search_dict.get("devices",{}).get(vendor_id,{})
		vendor = vendor_dict.get("name","Unknown Vendor")
		device = vendor_dict.get(device_id,{}).get("name","Device Not Found")
		# Return results accordingly
		return (vendor, device)

	@commands.command(pass_context=True)
	async def pci(self, ctx, *, ven_dev = None):
		"""Searches pci-ids.ucw.cz for the passed PCI ven:dev id."""
		usage = "Usage: `{}pci vvvv:dddd` where `vvvv` is the vendor id, and `dddd` is the device id.".format(ctx.prefix)
		if not ven_dev:
			return await ctx.send(usage)
		ven_dev_check = self._get_ven_dev(ven_dev)
		if ven_dev_check is None:
			return await ctx.send(usage)
		info_check = self._get_info(ven_dev_check[0],ven_dev_check[1],self.pci_ids)
		if info_check is None:
			return await ctx.send("Something went wrong :(")
		result = "`{}`\n\n{}".format(
			ven_dev_check[2],
			info_check[1]
		)
		# Got data
		await Message.EmbedText(
			title="{} PCI Device Results".format(info_check[0]),
			description=result,
			footer="Powered by http://pci-ids.ucw.cz",
			color=ctx.author
		).send(ctx)
		
	@commands.command(pass_context=True)
	async def usb(self, ctx, *, ven_dev = None):
		"""Searches usb-ids.gowdy.us for the passed USB ven:dev id."""
		usage = "Usage: `{}usb vvvv:dddd` where `vvvv` is the vendor id, and `dddd` is the device id.".format(ctx.prefix)
		if not ven_dev:
			return await ctx.send(usage)
		ven_dev_check = self._get_ven_dev(ven_dev)
		if ven_dev_check is None:
			return await ctx.send(usage)
		info_check = self._get_info(ven_dev_check[0],ven_dev_check[1],self.usb_ids)
		if info_check is None:
			return await ctx.send("Something went wrong :(")
		result = "`{}`\n\n{}".format(
			ven_dev_check[2],
			info_check[1]
		)
		# Got data
		await Message.EmbedText(
			title="{} USB Device Results".format(info_check[0]),
			description=result,
			footer="Powered by http://usb-ids.gowdy.us",
			color=ctx.author
		).send(ctx)