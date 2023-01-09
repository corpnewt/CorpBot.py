import asyncio, discord, time, tempfile, json, os, shutil
from   discord.ext import commands
from   Cogs import Utils, ReadableTime, DisplayName, FuzzySearch, Message, PickList, Nullify, DL

def setup(bot):
	# Add the bot and deps
	settings = bot.get_cog("Settings")
	bot.add_cog(Lists(bot, settings))

# This is the lists module.

class Lists(commands.Cog):

	# Init with the bot reference, and a reference to the settings var
	def __init__(self, bot, settings):
		self.bot = bot
		global Utils, DisplayName
		Utils = self.bot.get_cog("Utils")
		DisplayName = self.bot.get_cog("DisplayName")
		self.settings = settings
		self.alt_lists = [ { 
			"command" : "hack",
			"list" : "Hacks"
		}, { 
			"command" : "link",
			"list" : "Links"
		}, { 
			"command" : "tag",
			"list" : "Tags"
		} ]
		self.presets = {
			"Link": {
				"l_list": "Links",
				"l_name": "Link",
				"l_key" : "URL",
				"l_role": "RequiredLinkRole",
			},
			"Hack": {
				"l_list": "Hacks",
				"l_name": "Hack",
				"l_key" : "Hack",
				"l_role": "RequiredHackRole",
			},
			"Tag": {
				"l_list": "Tags",
				"l_name": "Tag",
				"l_key" : "URL",
				"l_role": "RequiredTagRole",
			}
		}
		
		
	'''async def onjoin(self, member, server):
		# Resolve our status based on the most occurances of UTCOffset
		newVal = self.settings.getGlobalUserStat(member, "Parts", server)
		self.settings.setUserStat(member, server, "Parts", newVal)'''

	###                        ###
	## Generic Accessor Methods ##
	###                        ###

	def _has_privs(self,ctx,l_role="RequiredLinkRole"):
		if not Utils.is_bot_admin(ctx):
			required_role = self.settings.getServerStat(ctx.guild, l_role, "")
			if required_role == "" or not ctx.guild.get_role(int(required_role)) in ctx.author.roles:
				return False
		return True

	def _ensure_keys(self,ctx,l_list,item_list,l_key):
		# Helper to walk all items in a list and ensure our keys are valid
		valid_keys = (l_key,"Name","Created","CreatedID","CreatedBy","Updated","UpdatedID","UpdatedBy")
		to_remove = []
		changed = False
		for item in item_list:
			if l_key in item: continue
			# We got a mismatched key - possibly due to a prior error, or failed migration?
			changed = True
			best_guess = next((x for x in item if not x in valid_keys),None)
			if best_guess:
				# Got a best_guess, let's adjust it
				item[l_key] = item[best_guess]
				item.pop(best_guess,None)
			else:
				# Nothing found
				to_remove.append(item)
		# Remove entries as needed
		if to_remove:
			for item in to_remove:
				try: item_list.remove(item)
				except: pass
		if changed:
			# Save changes
			self.settings.setServerStat(ctx.guild, l_list, item_list)
		return item_list

	async def _get_item(self,ctx,name,l_role="RequiredLinkRole",l_list="Links",l_name="Link",l_key="URL",raw=False):
		# Helper function to pull items from lists
		if not name:
			msg = 'Usage: `{}{}[[name]] "[[[name]] name]"`'.format(ctx.prefix,"raw" if raw else "").replace("[[name]]",l_name.lower())
			return await ctx.send(msg)
		itemList = self.settings.getServerStat(ctx.guild, l_list, [])
		# Check other lists
		other_commands = []
		other_names    = []
		for i in self.alt_lists:
			if i["list"] == l_list:
				# Our list - skip
				continue
			check_list = self.settings.getServerStat(ctx.guild, i["list"])
			if any(x["Name"].lower() == name.lower() for x in check_list):
				# Add the list
				other_commands.append(i)
				other_names.append("{}{} {}".format(ctx.prefix,i["command"],Nullify.escape_all(name)))
				
		if not itemList or itemList == []:
			no_items = 'No [[name]]s in list!  You can add some with the `{}add[[name]] "[[[name]] name]" [[[key]]]` command!'.format(ctx.prefix).replace("[[name]]",l_name.lower()).replace("[[key]]",l_key.lower())
			if raw or not len(other_commands):
				# No other matches
				return await ctx.send(no_items)
			msg = no_items + "\n\nMaybe you meant:"
			index, message = await PickList.Picker(
				title=msg,
				list=other_names,
				ctx=ctx
			).pick()
			# Check if we errored/cancelled
			if index < 0:
				return await message.edit(content=no_items)
			# Got something
			await message.edit(content="`{}`".format(other_names[index]))
			# Invoke
			return await ctx.invoke(self.bot.all_commands.get(other_commands[index]["command"]), name=name)

		# Ensure our keys are proper - and save if need be
		itemList = self._ensure_keys(ctx,l_list,itemList,l_key)

		for item in itemList:
			if item['Name'].lower() == name.lower():
				msg = '**{}:**\n{}'.format(Nullify.escape_all(item['Name']), discord.utils.escape_markdown(item[l_key]) if raw else item[l_key])
				return await ctx.send(Utils.suppressed(ctx,msg))
				
		not_found = '{} not found in {} list!'.format(Nullify.escape_all(name),l_name.lower())
		# No matches - let's fuzzy search
		potentialList = FuzzySearch.search(name, itemList, 'Name')
		if len(potentialList):
			# Setup and display the picker
			msg = not_found + '\n\nSelect one of the following close matches:'
			p_list = [x["Item"]["Name"] for x in potentialList]
			p_list.extend(other_names)
			index, message = await PickList.Picker(
				title=msg,
				list=p_list,
				ctx=ctx
			).pick()
			# Check if we errored/cancelled
			if index < 0:
				return await message.edit(content=not_found)
			# Check if we have another command
			if index >= len(potentialList):
				# We're into our other list
				await message.edit(content="`{}`".format(Nullify.escape_all(other_names[index - len(potentialList)])))
				# Invoke
				return await ctx.invoke(self.bot.all_commands.get(other_commands[index - len(potentialList)]["command"]), name=name)
			# Display the item
			for item in itemList:
				if item["Name"] == potentialList[index]["Item"]["Name"]:
					msg = '**{}:**\n{}'.format(Nullify.escape_all(item['Name']), discord.utils.escape_markdown(item[l_key]) if raw else item[l_key])
					return await message.edit(content=Utils.suppressed(ctx,msg))
			return await message.edit(content="{} {} no longer exists!".format(
				l_name,
				Nullify.escape_all(potentialList[index]["Item"]["Name"])
			))
		# Here we have no potentials
		return await ctx.send(not_found)

	async def _add_item(self,ctx,name,value,l_role="RequiredLinkRole",l_list="Links",l_name="Link",l_key="URL"):
		# Check if we're admin/bot admin first - then check for a required role
		if not self._has_privs(ctx,l_role): return await ctx.send("You do not have sufficient privileges to access this command.")
		# Remove tabs, newlines, and carriage returns and strip leading/trailing spaces from the name
		name = None if name == None else name.replace("\n"," ").replace("\r","").replace("\t"," ").strip()
		# Passed role requirements!
		if name == None or value == None:
			msg = 'Usage: `{}add[[name]] "[[[name]] name]" [[[key]]]`'.format(ctx.prefix).replace("[[name]]",l_name.lower()).replace("[[key]]",l_key.lower())
			return await ctx.send(msg)
		itemList = self.settings.getServerStat(ctx.guild, l_list, [])
		if not itemList:
			itemList = []
		currentTime = int(time.time())
		item = next((x for x in itemList if x["Name"].lower() == name.lower()),None)
		if item:
			msg = '{} updated!'.format(Nullify.escape_all(item["Name"]))
			item[l_key]       = value
			item['UpdatedBy'] = DisplayName.name(ctx.author)
			item['UpdatedID'] = ctx.author.id
			item['Updated']   = currentTime
		else:
			itemList.append({"Name" : name, l_key : value, "CreatedBy" : DisplayName.name(ctx.author), "CreatedID": ctx.author.id, "Created" : currentTime})
			msg = '{} added to {} list!'.format(Nullify.escape_all(name),l_name.lower())
		self.settings.setServerStat(ctx.guild, l_list, itemList)
		return await ctx.send(msg)

	async def _remove_item(self,ctx,name,l_role="RequiredLinkRole",l_list="Links",l_name="Link",l_key="URL"):
		if not self._has_privs(ctx,l_role): return await ctx.send("You do not have sufficient privileges to access this command.")
		if name == None:
			msg = 'Usage: `{}remove{} "[{} name]"`'.format(ctx.prefix,l_name.lower(),l_name.lower())
			return await ctx.send(msg)
		itemList = self.settings.getServerStat(ctx.guild, l_list, [])
		if not itemList or itemList == []:
			msg = 'No [[name]]s in list!  You can add some with the `{}add[[name]] "[[[name]] name]" [[[key]]]` command!'.format(ctx.prefix).replace("[[name]]",l_name.lower()).replace("[[key]]",l_key.lower())
			return await ctx.send(msg)
		item = next((x for x in itemList if x["Name"].lower() == name.lower()),None)
		if not item:
			return await ctx.send('{} not found in {} list!'.format(Nullify.escape_all(name),l_name.lower()))
		itemList.remove(item)
		self.settings.setServerStat(ctx.guild, l_list, itemList)
		return await ctx.send('{} removed from {} list!'.format(Nullify.escape_all(item["Name"]),l_name.lower()))

	async def _item_info(self,ctx,name,l_role="RequiredLinkRole",l_list="Links",l_name="Link",l_key="URL"):
		if name == None:
			msg = 'Usage: `{}info{} "[{} name]"`'.format(ctx.prefix,l_name.lower(),l_name.lower())
			return await ctx.send(msg)
		itemList = self.settings.getServerStat(ctx.guild, l_list, [])
		if not itemList or itemList == []:
			msg = 'No [[name]]s in list!  You can add some with the `{}add[[name]] "[[[name]] name]" [[[key]]]` command!'.format(ctx.prefix).replace("[[name]]",l_name.lower()).replace("[[key]]",l_key.lower())
			return await ctx.send(msg)
		item = next((x for x in itemList if x["Name"].lower() == name.lower()),None)
		if not item:
			return await ctx.send('{} not found in {} list!'.format(Nullify.escape_all(name),l_name.lower()))
		current_time = int(time.time())
		msg = "**{}:**\n".format(Nullify.escape_all(item["Name"]))
		# Get the info
		created_by = DisplayName.memberForID(item.get("CreatedID",0),ctx.guild)
		created_by = DisplayName.name(created_by) if created_by else item.get("CreatedBy","`UNKNOWN`")
		msg += "Created by: {}\n".format(created_by)
		created    = item.get("Created",None)
		if created:
			msg += "Created: {} ago\n".format(ReadableTime.getReadableTimeBetween(created, current_time, True))
		if item.get("Updated",None):
			updated_by = DisplayName.memberForID(item.get("UpdatedID",0),ctx.guild)
			updated_by = DisplayName.name(updated_by) if updated_by else item.get("UpdatedBy","`UNKNOWN`")
			msg += "Updated by: {}\n".format(updated_by)
			updated    = item.get("Updated",None)
			if created:
				msg += "Updated: {} ago\n".format(ReadableTime.getReadableTimeBetween(updated, current_time, True))
		return await ctx.send(msg)

	async def _list_items(self,ctx,command,l_role="RequiredLinkRole",l_list="Links",l_name="Link",l_key="URL",raw=False):
		arg_list = ctx.message.content.split()
		if len(arg_list) > 1:
			extra = " ".join(arg_list[1:])
			# We have a random attempt at a passed variable - Thanks Sydney!
			# Invoke this command again with the right name
			return await ctx.invoke(command, name=extra)
		itemList = self.settings.getServerStat(ctx.guild, l_list, [])
		if not itemList or itemList == []:
			msg = 'No [[name]]s in list!  You can add some with the `{}add[[name]] "[[[name]] name]" [[[key]]]` command!'.format(ctx.prefix).replace("[[name]]",l_name.lower()).replace("[[key]]",l_key.lower())
			return await ctx.send(msg)
		# Sort by link name
		items = [{"name":"{}. {}".format(i,x["Name"]),"value":Utils.truncate_string(x[l_key])} for i,x in enumerate(sorted(itemList, key=lambda x:x["Name"].lower()),start=1)]
		return await PickList.PagePicker(title="Current {}s ({:,} total)".format(l_name,len(itemList)),list=items,ctx=ctx).pick()

	async def _get_role(self,ctx,l_role="RequiredLinkRole",l_list="Links",l_name="Link",l_key="URL"):
		role = self.settings.getServerStat(ctx.message.guild, l_role)
		if role == None or role == "":
			msg = '**Only Admins** can add and remove {}s.'.format(l_name.lower())
			return await ctx.send(msg)
		# Role is set - let's get its name
		listrole = ctx.guild.get_role(int(role))
		if not listrole:
			return await ctx.send('There is no role that matches id: `{}` - consider updating this setting.'.format(role))
		return await ctx.send(Utils.suppressed(ctx,"You need to be a{} **{}** to add and remove {}s.").format("n" if listrole.name.lower()[0] in "aeiou" else "",Nullify.escape_all(listrole.name),l_name.lower()))
	
	async def _save_items(self,ctx,l_role="RequiredLinkRole",l_list="Links",l_name="Link",l_key="URL"):
		# Helper method to dump the passed command contents to a json file and upload
		itemList = self.settings.getServerStat(ctx.guild, l_list, [])
		if not itemList:
			msg = 'No [[name]]s in list!  You can add some with the `{}add[[name]] "[[[name]] name]" [[[key]]]` command!'.format(ctx.prefix).replace("[[name]]",l_name.lower()).replace("[[key]]",l_key.lower())
			return await ctx.send(msg)
		message = await ctx.send("Saving {}s and uploading...".format(l_name.lower()))
		temp = tempfile.mkdtemp()
		temp_json = os.path.join(temp,"{}s.json".format(l_name))
		try:
			json.dump(itemList,open(temp_json,"w"),indent=2)
			await ctx.send(file=discord.File(temp_json))
		except:
			return await message.edit(content="Could not save or upload {}s :(".format(l_name.lower()))
		finally:
			shutil.rmtree(temp,ignore_errors=True)
		await message.edit(content="Uploaded {}s.json! ({:,})".format(l_name,len(itemList)))

	async def _load_items(self,ctx,url,l_role="RequiredLinkRole",l_list="Links",l_name="Link",l_key="URL"):
		# Helper method to load a passed json URL or attachment and add the contents to the list
		if not self._has_privs(ctx,l_role): return await ctx.send("You do not have sufficient privileges to access this command.")
		itemList = self.settings.getServerStat(ctx.guild, l_list, [])
		if not isinstance(itemList,list): # Malformed - let's start it anew
			itemList = []
		if url is None and len(ctx.message.attachments) == 0:
			return await ctx.send("Usage: `{}load{} [url or attachment]`".format(ctx.prefix,l_name.lower()))
		if url is None:
			url = ctx.message.attachments[0].url
		message = await ctx.send("Downloading and parsing...")
		try:
			items = await DL.async_json(url.strip("<>"))
		except:
			return await message.edit(content="Could not serialize data :(")
		if not items:
			return await message.edit(content="Json data is empty :(")
		if not isinstance(items,list):
			return await message.edit(content="Malformed json data :(")
		if not all(("Name" in x and l_key in x for x in items)):
			return await message.edit(content="Invalid {} data :(".format(l_name.lower()))
		# At this point - we should have a valid json file with our data - let's add it.
		currentTime = int(time.time())
		added = 0
		updated = 0
		for i in items:
			name,value = i["Name"],i[l_key]
			item = next((x for x in itemList if x["Name"].lower() == i["Name"].lower()),None)
			if item:
				updated += 1
				msg = '{} updated!'.format(Nullify.escape_all(item["Name"]))
				item[l_key]       = i[l_key]
				item['UpdatedBy'] = DisplayName.name(ctx.author)
				item['UpdatedID'] = ctx.author.id
				item['Updated']   = currentTime
			else:
				added += 1
				itemList.append({
					"Name":     i["Name"],
					l_key:      i[l_key],
					"CreatedBy":DisplayName.name(ctx.author),
					"CreatedID":ctx.author.id,
					"Created":  currentTime
				})
		self.settings.setServerStat(ctx.guild, l_list, itemList)
		if added and updated:
			msg = "Added {:,} new and updated {:,} existing {}{}!".format(
				added,updated,l_name.lower(),"" if updated == 1 else "s"
			)
		elif added:
			msg = "Added {:,} new {}{}!".format(added,l_name.lower(),"" if added == 1 else "s")
		else:
			msg = "Updated {:,} existing {}{}!".format(updated,l_name.lower(),"" if updated == 1 else "s")
		await message.edit(content=msg)

	async def _clear_items(self,ctx,l_role="RequiredLinkRole",l_list="Links",l_name="Link",l_key="URL"):
		itemList = self.settings.getServerStat(ctx.guild, l_list, [])
		if not itemList:
			msg = 'No [[name]]s in list!  You can add some with the `{}add[[name]] "[[[name]] name]" [[[key]]]` command!'.format(ctx.prefix).replace("[[name]]",l_name.lower()).replace("[[key]]",l_key.lower())
			return await ctx.send(msg)
		self.settings.setServerStat(ctx.guild, l_list, [])
		return await ctx.send("Cleared {:,} {}{}!".format(len(itemList),l_name.lower(),"" if len(itemList)==1 else "s"))

	###                    ###
	## Link-related Methods ##
	###                    ###

	@commands.command()
	async def addlink(self, ctx, name : str = None, *, link : str = None):
		"""Add a link to the link list."""
		await self._add_item(ctx,name,link,**self.presets["Link"])
		
	@commands.command(aliases=["remlink","deletelink","dellink"])
	async def removelink(self, ctx, *, name : str = None):
		"""Remove a link from the link list."""
		await self._remove_item(ctx,name,**self.presets["Link"])

	@commands.command()
	async def link(self, ctx, *, name : str = None):
		"""Retrieve a link from the link list."""
		await self._get_item(ctx,name,**self.presets["Link"])
		
	@commands.command()
	async def rawlink(self, ctx, *, name : str = None):
		"""Retrieve a link's raw markdown from the link list."""
		await self._get_item(ctx,name,**self.presets["Link"],raw=True)

	@commands.command()
	async def linkinfo(self, ctx, *, name : str = None):
		"""Displays info about a link from the link list."""
		await self._item_info(ctx,name,**self.presets["Link"])

	@commands.command()
	async def links(self, ctx):
		"""List all links in the link list."""
		await self._list_items(ctx,self.link,**self.presets["Link"])
		
	@commands.command()
	async def rawlinks(self, ctx):
		"""List raw markdown of all links in the link list."""
		await self._list_items(ctx,self.link,**self.presets["Link"],raw=True)

	@commands.command()
	async def linkrole(self, ctx):
		"""Lists the required role to add links."""
		await self._get_role(ctx,**self.presets["Link"])
		
	@commands.command()
	async def savelinks(self, ctx):
		"""Saves the link list to a json file and uploads."""
		await self._save_items(ctx,**self.presets["Link"])

	@commands.command(aliases=["addlinks"])
	async def loadlinks(self, ctx, *, url=None):
		"""Loads the passed json attachment or URL into the link list."""
		await self._load_items(ctx,url,**self.presets["Link"])

	@commands.command(aliases=["clrlinks"])
	async def clearlinks(self, ctx):
		"""Clears all entries from the link list."""
		await self._clear_items(ctx,**self.presets["Link"])

	###                    ###
	## Hack-related Methods ##
	###                    ###
	
	@commands.command()
	async def addhack(self, ctx, name : str = None, *, hack : str = None):
		"""Add a hack to the hack list."""
		await self._add_item(ctx,name,hack,**self.presets["Hack"])
		
	@commands.command(aliases=["remhack","deletehack","delhack"])
	async def removehack(self, ctx, *, name : str = None):
		"""Remove a hack from the hack list."""
		await self._remove_item(ctx,name,**self.presets["Hack"])

	@commands.command()
	async def hack(self, ctx, *, name : str = None):
		"""Retrieve a hack from the hack list."""
		await self._get_item(ctx,name,**self.presets["Hack"])
		
	@commands.command()
	async def rawhack(self, ctx, *, name : str = None):
		"""Retrieve a hack's raw markdown from the hack list."""
		await self._get_item(ctx,name,**self.presets["Hack"],raw=True)

	@commands.command()
	async def hackinfo(self, ctx, *, name : str = None):
		"""Displays info about a hack from the hack list."""
		await self._item_info(ctx,name,**self.presets["Hack"])

	@commands.command()
	async def hacks(self, ctx):
		"""List all hack in the hack list."""
		await self._list_items(ctx,self.hack,**self.presets["Hack"])
		
	@commands.command()
	async def rawhacks(self, ctx):
		"""List raw markdown of all hacks in the hack list."""
		await self._list_items(ctx,self.hack,**self.presets["Hack"],raw=True)

	@commands.command()
	async def hackrole(self, ctx):
		"""Lists the required role to add hacks."""
		await self._get_role(ctx,**self.presets["Hack"])

	@commands.command()
	async def savehacks(self, ctx):
		"""Saves the hack list to a json file and uploads."""
		await self._save_items(ctx,**self.presets["Hack"])

	@commands.command(aliases=["addhacks"])
	async def loadhacks(self, ctx, *, url=None):
		"""Loads the passed json attachment or URL into the hack list."""
		await self._load_items(ctx,url,**self.presets["Hack"])

	@commands.command(aliases=["clrhacks"])
	async def clearhacks(self, ctx):
		"""Clears all entries from the hack list."""
		await self._clear_items(ctx,**self.presets["Hack"])

	###                   ###
	## Tag-related Methods ##
	###                   ###
	
	@commands.command()
	async def addtag(self, ctx, name : str = None, *, tag : str = None):
		"""Add a tag to the tag list."""
		await self._add_item(ctx,name,tag,**self.presets["Tag"])
		
	@commands.command(aliases=["remtag","deletetag","deltag"])
	async def removetag(self, ctx, *, name : str = None):
		"""Remove a tag from the tag list."""
		await self._remove_item(ctx,name,**self.presets["Tag"])

	@commands.command()
	async def tag(self, ctx, *, name : str = None):
		"""Retrieve a tag from the tag list."""
		await self._get_item(ctx,name,**self.presets["Tag"])
		
	@commands.command()
	async def rawtag(self, ctx, *, name : str = None):
		"""Retrieve a tag's raw markdown from the tag list."""
		await self._get_item(ctx,name,**self.presets["Tag"],raw=True)

	@commands.command()
	async def taginfo(self, ctx, *, name : str = None):
		"""Displays info about a tag from the tag list."""
		await self._item_info(ctx,name,**self.presets["Tag"])

	@commands.command()
	async def tags(self, ctx):
		"""List all tag in the tag list."""
		await self._list_items(ctx,self.tag,**self.presets["Tag"])
		
	@commands.command()
	async def rawtags(self, ctx):
		"""List raw markdown of all tags in the tag list."""
		await self._list_items(ctx,self.tag,**self.presets["Tag"],raw=True)

	@commands.command()
	async def tagrole(self, ctx):
		"""Lists the required role to add tags."""
		await self._get_role(ctx,**self.presets["Tag"])

	@commands.command()
	async def savetags(self, ctx):
		"""Saves the tag list to a json file and uploads."""
		await self._save_items(ctx,**self.presets["Tag"])

	@commands.command(aliases=["addtags"])
	async def loadtags(self, ctx, *, url=None):
		"""Loads the passed json attachment or URL into the tag list."""
		await self._load_items(ctx,url,**self.presets["Tag"])

	@commands.command(aliases=["clrtags"])
	async def clearlinks(self, ctx):
		"""Clears all entries from the tag list."""
		await self._clear_items(ctx,**self.presets["Tag"])
		
	###                     ###
	## Parts-related Methods ##
	###                     ###

	@commands.command()
	async def parts(self, ctx, *, member = None):
		"""Retrieve a member's parts list. DEPRECATED - Use hw instead."""
		if member is None:
			member = ctx.message.author
			
		if type(member) is str:
			memberName = member
			member = DisplayName.memberForName(memberName, ctx.guild)
			if not member:
				msg = 'I couldn\'t find *{}*...'.format(memberName)
				return await ctx.send(Utils.suppressed(ctx,msg))
		parts = self.settings.getGlobalUserStat(member, "Parts")
		if not parts or parts == "":
			msg = '*{}* has not added their parts yet!  ~~They can add them with the `{}setparts [parts text]` command!~~ DEPRECATED - Use `{}newhw` instead.'.format(DisplayName.name(member), ctx.prefix, ctx.prefix)
			return await ctx.send(msg)
		msg = '***{}\'s*** **Parts (DEPRECATED - Use {}hw instead):**\n\n{}'.format(DisplayName.name(member), ctx.prefix, parts)
		await ctx.send(Utils.suppressed(ctx,msg))

	@commands.command()
	async def rawparts(self, ctx, *, member = None):
		"""Retrieve the raw markdown for a member's parts list. DEPRECATED - Use rawhw instead."""
		if member is None:
			member = ctx.message.author
		if type(member) is str:
			memberName = member
			member = DisplayName.memberForName(memberName, ctx.guild)
			if not member:
				msg = 'I couldn\'t find *{}*...'.format(Nullify.escape_all(memberName))
				return await ctx.send(msg)
		parts = self.settings.getGlobalUserStat(member, "Parts")
		if not parts or parts == "":
			msg = '*{}* has not added their parts yet!  ~~They can add them with the `{}setparts [parts text]` command!~~ DEPRECATED - Use `{}newhw` instead.'.format(DisplayName.name(member), ctx.prefix, ctx.prefix)
			return await ctx.send(msg)
		parts = discord.utils.escape_markdown(parts)
		msg = '***{}\'s*** **Parts (DEPRECATED - Use {}hw instead):**\n\n{}'.format(DisplayName.name(member), ctx.prefix, parts)
		await ctx.send(Utils.suppressed(ctx,msg))
		
	@commands.command()
	async def setparts(self, ctx, *, parts : str = None):
		"""Set your own parts - can be a url, formatted text, or nothing to clear. DEPRECATED - Use newhw instead."""
		if not parts:
			parts = ""
		self.settings.setGlobalUserStat(ctx.author, "Parts", parts)
		if not parts:
			msg = "*{}'s* parts have been cleared (DEPRECATED - use {}newhw instaed)".format(DisplayName.name(ctx.author),ctx.prefix)
		else:
			msg = '*{}\'s* parts have been set to (DEPRECATED - Use {}newhw instead):\n{}'.format(DisplayName.name(ctx.author), ctx.prefix, parts)
		await ctx.send(Utils.suppressed(ctx,msg))
		
	@commands.command()
	async def partstemp(self, ctx):
		"""Gives a copy & paste style template for setting a parts list."""
		msg = '\{}setparts \`\`\`      CPU : \n   Cooler : \n     MOBO : \n      GPU : \n      RAM : \n      SSD : \n      HDD : \n      PSU : \n     Case : \nWiFi + BT : \n Lighting : \n Keyboard : \n    Mouse : \n  Monitor : \n      DAC : \n Speakers : \`\`\`'.format(ctx.prefix)	
		await ctx.send(msg)
		
	@commands.command()
	async def online(self, ctx):
		"""Lists the number of users online."""
		members = membersOnline = bots = botsOnline = 0
		for member in ctx.guild.members:
			if member.bot:
				bots += 1
				if not member.status == discord.Status.offline:
					botsOnline += 1
			else:
				members += 1
				if not member.status == discord.Status.offline:
					membersOnline += 1
		await Message.Embed(
			title="Member Stats",
			description="Current member information for {}".format(ctx.guild.name),
			fields=[
				{ "name" : "Members", "value" : "└─ {:,}/{:,} online ({:,g}%)".format(membersOnline, members, round((membersOnline/members)*100, 2)), "inline" : False},
				{ "name" : "Bots", "value" : "└─ {:,}/{:,} online ({:,g}%)".format(botsOnline, bots, round((botsOnline/bots)*100, 2)), "inline" : False},
				{ "name" : "Total", "value" : "└─ {:,}/{:,} online ({:,g}%)".format(membersOnline + botsOnline, len(ctx.guild.members), round(((membersOnline + botsOnline)/len(ctx.guild.members))*100, 2)), "inline" : False}
			],
			color=ctx.author).send(ctx)

	@commands.command()
	async def lastonline(self, ctx, *, member = None):
		"""Lists the last time a user was online if known."""
		if not member:
			msg = 'Usage: `{}lastonline "[member]"`'.format(ctx.prefix)
			return await ctx.send(msg)
		if type(member) is str:
			memberName = member
			member = DisplayName.memberForName(memberName, ctx.guild)
			if not member:
				msg = 'I couldn\'t find *{}*...'.format(Nullify.escape_all(memberName))
				return await ctx.send(msg)
		name = DisplayName.name(member)
		# We have a member here
		if not member.status == discord.Status.offline:
			msg = '*{}* is here right now.'.format(name)
		else:
			lastOnline = self.settings.getUserStat(member, ctx.guild, "LastOnline")
			if lastOnline == "Unknown":
				self.settings.setUserStat(member, ctx.guild, "LastOnline", None)
				lastOnline = None
			if lastOnline:
				currentTime = int(time.time())
				timeString  = ReadableTime.getReadableTimeBetween(int(lastOnline), currentTime, True)
				msg = 'The last time I saw *{}* was *{} ago*.'.format(name, timeString)
			else:
				msg = 'I don\'t know when *{}* was last online.  Sorry.'.format(name)
		await ctx.send(msg)
