def makeBar(progress):
    return '[{0}{1}] {2}%'.format('#'*(int(round(progress/2))), ' '*(50-(int(round(progress/2)))), progress)