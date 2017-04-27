import requests
from   pyquery import PyQuery as pq

def normalStyle(types, names):
	padTo = 0
	for t in types:
		# Find out which has the longest
		tempLen = len(t)
		if tempLen > padTo:
			padTo = tempLen
	partdown = '```\n'
	for i in range(0, len(types)):
		partdown += types[i].rjust(padTo, ' ') + ' : ' + names[i] + '\n'
	partdown += '```'
	return partdown

def mdStyle(types, names):
	padTo = 0
	for t in types:
		# Find out which has the longest
		ty = "<" + t.replace(' ', '-') + ":"
		tempLen = len(ty)
		if tempLen > padTo:
			padTo = tempLen
	partdown = '```md\n'
	for i in range(0, len(types)):
		t = "<" + types[i].replace(' ', '-') + ":"
		partdown += t.ljust(padTo, ' ') + " " + names[i] + '>\n'
	partdown += '```'
	return partdown

def mdBlockStyle(types, names):
	padTo = 0
	for t in types:
		# Find out which has the longest
		ty = "[" + t
		tempLen = len(ty)
		if tempLen > padTo:
			padTo = tempLen
	partdown = '```md\n'
	for i in range(0, len(types)):
		ty = "[" + types[i]
		t = "| " + ty.rjust(padTo, ' ') + "]["
		partdown += t.rjust(padTo, ' ') + names[i] + ']\n'
	partdown += '```'
	return partdown

def boldStyle(types, names):
	partdown = ''
	for i in range(0, len(types)):
		partdown += "**" + types[i] + ":** " + names[i] + '\n'
	partdown = partdown[:-1]
	return partdown

def boldItalicStyle(types, names):
	partdown = ''
	for i in range(0, len(types)):
		partdown += "***" + types[i] + ":*** *" + names[i] + '*\n'
	partdown = partdown[:-1]
	return partdown
		
def getMarkdown( url, style = None):
	# Ensure we're using a list
	url = url.replace('/b/', '/list/')
	if not style:
		style = 'normal'
	try:
		response = requests.get(url)
	except Exception:
		return None
	dom = pq(response.text)
	names = []
	types = []
	for e in dom('td.component-type.tl'):
		types.append(e.text_content().strip())
	for e in dom('td.component-name.tl'):
		names.append(e.text_content().strip())
	if not len(types):
		return None
	if not len(types) == len(names):
		return None
	partout = ''
	if style.lower() == 'md':
		partout = mdStyle(types, names)
	elif style.lower() == 'mdblock':
		partout = mdBlockStyle(types, names)
	elif style.lower() == 'bold':
		partout = boldStyle(types, names)
	elif style.lower() == 'bolditalic':
		partout = boldItalicStyle(types, names)
	else:
		partout = normalStyle(types, names)
	return partout