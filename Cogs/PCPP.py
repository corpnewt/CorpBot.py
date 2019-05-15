from pyquery import PyQuery as pq
from Cogs import DL 

def setup(bot):
	# Not a cog
	return

def find_last_between( source, start_sep, end_sep ):
	result=[]
	tmp=source.split(start_sep)
	for par in tmp:
		if end_sep in par:
			result.append(par.split(end_sep)[0])
	if len(result) == 0:
		return None
	else:
		return result[len(result)-1] # Return last item

def normalStyle(types, names, escape = False):
	padTo = 0
	for t in types:
		# Find out which has the longest
		tempLen = len(t)
		if tempLen > padTo:
			padTo = tempLen
	if escape:
		partdown = '\`\`\`\n'
	else:
		partdown = '```\n'
	for i in range(0, len(types)):
		partdown += types[i].rjust(padTo, ' ') + ' : ' + names[i] + '\n'
	if escape:
		partdown += '\`\`\`'
	else:
		partdown += '```'
	return partdown

def mdStyle(types, names, escape = False):
	padTo = 0
	for t in types:
		# Find out which has the longest
		ty = "<" + t.replace(' ', '-') + ":"
		tempLen = len(ty)
		if tempLen > padTo:
			padTo = tempLen
	if escape:
		partdown = '\`\`\`md\n'
	else:
		partdown = '```md\n'
	for i in range(0, len(types)):
		t = "<" + types[i].replace(' ', '-') + ":"
		partdown += t.ljust(padTo, ' ') + " " + names[i] + '>\n'
	if escape:
		partdown += '\`\`\`'
	else:
		partdown += '```'
	return partdown

def mdBlockStyle(types, names, escape = False):
	padTo = 0
	for t in types:
		# Find out which has the longest
		ty = "[" + t
		tempLen = len(ty)
		if tempLen > padTo:
			padTo = tempLen
	if escape:
		partdown = '\`\`\`md\n'
	else:
		partdown = '```md\n'
	for i in range(0, len(types)):
		ty = "[" + types[i]
		t = "| " + ty.rjust(padTo, ' ') + "]["
		partdown += t.rjust(padTo, ' ') + names[i] + ']\n'
	if escape:
		partdown += '\`\`\`'
	else:
		partdown += '```'
	return partdown

def boldStyle(types, names, escape = False):
	partdown = ''
	for i in range(0, len(types)):
		if escape:
			partdown += "\*\*" + types[i] + ":\*\* " + names[i] + '\n'
		else:
			partdown += "**" + types[i] + ":** " + names[i] + '\n'
	partdown = partdown[:-1]
	return partdown

def boldItalicStyle(types, names, escape = False):
	partdown = ''
	for i in range(0, len(types)):
		if escape:
			partdown += "\*\*\*" + types[i] + ":\*\*\* \*" + names[i] + '\*\n'
		else:
			partdown += "***" + types[i] + ":*** *" + names[i] + '*\n'
	partdown = partdown[:-1]
	return partdown
		
async def getMarkdown( url, style = None, escape = False):
	# Ensure we're using a list
	if url.lower().endswith("pcpartpicker.com/list/"):
		# Not *just* the list... we want actual parts
		return None
	url = url.replace("#view=", "")
	if '/b/' in url.lower():
		# We have a build - let's try to convert to list
		try:
			response = await DL.async_text(url)
		except Exception:
			return None
		dom = pq(response)
		listLink = dom('span.header-actions')
		newLink = None
		for link in listLink.children():
			for attrib_name in link.attrib:
				if attrib_name == 'href':
					newLink = link.attrib['href']
		if newLink == None:
			return None
		url = "https://pcpartpicker.com" + str(newLink)
		
	# url = url.replace('/b/', '/list/')
	if not style:
		style = 'normal'
	try:
		response = await DL.async_text(url,{"user-agent":"Mozilla/5.0 (X11; CrOS i686 2268.111.0) AppleWebKit/536.11 (KHTML, like Gecko) Chrome/20.0.1132.57 Safari/536.11"})
	except Exception:
		return None
	# Let's walk the lines of the file and gather based on cues
	names = []
	types = []
	current_name = current_type = None
	primed = name_primed = False
	for i in response.split("\n"):
		if i.strip() == "":
			# skip empty lines
			continue
		if "tr__product" in i:
			# Clear and prime
			current_name = current_type = None
			primed = True
			continue
		if not primed:
			continue
		if "</tr>" in i:
			# Closing bracket for our stuff - dump name and type if we have them
			if current_name and current_type:
				names.append(current_name)
				types.append(current_type)
				primed = name_primed = False
				current_name = current_type = None
			continue
		# Should be primed here - and checking for name and type
		if name_primed:
			name_primed = False
			# Assume we should be pulling the name here
			try:
				current_name = i.split('">')[1].split("</a>")[0]
			except:
				pass
			continue
		if "td__component" in i:
			# Got the type
			try:
				current_type = i.split("</a></td>")[-2].split('">')[-1]
			except:
				# bad type
				pass
			continue
		if "td__name" in i:
			# Primed for name
			name_primed = True
			continue
	
	if not len(types):
		return None
	if not len(types) == len(names):
		# Only way this would happen that I've seen so far, is with custom entries
		return None
	partout = ''
	if style.lower() == 'md':
		partout = mdStyle(types, names, escape)
	elif style.lower() == 'mdblock':
		partout = mdBlockStyle(types, names, escape)
	elif style.lower() == 'bold':
		partout = boldStyle(types, names, escape)
	elif style.lower() == 'bolditalic':
		partout = boldItalicStyle(types, names, escape)
	elif style.lower() == 'normal':
		partout = normalStyle(types, names, escape)
	else:
		# No style present
		return None
	return partout
