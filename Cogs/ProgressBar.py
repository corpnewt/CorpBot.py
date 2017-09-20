def setup(bot):
	# This module isn't actually a cog
    return

def makeBar(progress):
    return '[{0}{1}] {2}%'.format('#'*(int(round(progress/2))), ' '*(50-(int(round(progress/2)))), progress)

def center(string, header = None):
    leftPad = ' '*(int(round((50-len(string))/2)))
    leftPad += string
    if header:
        output = header + leftPad[len(header):]
    else:
        output = leftPad
    return output