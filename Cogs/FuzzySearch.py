import difflib
from   operator    import itemgetter

def setup(bot):
	# This module isn't actually a cog
    return

def search(searchTerm, list, keyName : str = None, numMatches : int = 3):
	"""Searches the provided list for the searchTerm - using a keyName if provided for dicts."""
	if len(list) < 1:
		return None
	# Iterate through the list and create a list of items
	searchList = []
	for item in list:
		if keyName:
			testName = item[keyName]
		else:
			testName = item
		matchRatio = difflib.SequenceMatcher(None, searchTerm.lower(), testName.lower()).ratio()
		# matchRatio = Levenshtein.ratio(searchTerm.lower(), testName.lower())
		searchList.append({ 'Item' : item, 'Ratio' : matchRatio })
	# sort the servers by population
	searchList = sorted(searchList, key=lambda x:x['Ratio'], reverse=True)
	if numMatches > len(searchList):
		# Less than three - let's just give what we've got
		numMatches = len(searchList)
	return searchList[:numMatches]
