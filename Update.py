import sys
import os
import subprocess

# Get our cli args
def getopts(argv):
    opts = {}  # Empty dictionary to store key-value pairs.
    while argv:  # While there are arguments left to parse...
        if argv[0][0] == '-':  # Found a "-name value" pair.
            opts[argv[0]] = argv[1]  # Add key and value to the dictionary.
        argv = argv[1:]  # Reduce the argument list by copying it starting from index 1.
    return opts

# Set some reboot vars
reboot = False
pypath = "python3"
# Update defaults to false - we can pass true if need be
update = True
# Default to no channel for return message
return_channel = None
# Our path
dir_path = os.path.dirname(os.path.realpath(__file__))
main_path = dir_path + "/" + "Main.py"

# Check if we were rebooted
if len(sys.argv) > 1:
    # We got some args
    args = getopts(sys.argv)

    # Check for reboot
    for key in args:
        if key.lower() == '-reboot':
            # We got a reboot
            if args[key].lower()[:1] == "y" or args[key].lower() == "true":
                # We rebooted!
                reboot = True
        elif key.lower() == "-path":
            # We got a path
            pypath = args[key]
        elif key.lower() == "-update":
            # We got update!
            if args[key].lower()[:1] == "n" or args[key].lower() == "false":
                # update flag
                update = False
        elif key.lower() == "-mainpath":
            # We got a script path
            main_path = args[key]
        elif key.lower() == "-channel":
            # We got a return channel
            try:
                # Cast as int if possible
                return_channel = int(args[key])
            except Exception:
                return_channel = None


# Update first, then restart as new process
# Allows us to enact changes in one go
print("\n\n##############################")
print("#          UPDATING          #")
print("##############################\n")
print("\nTrying to update via git...\n")
print("Using update script...\n")
try:
    u = subprocess.Popen(['git', 'pull', 'origin', 'rewrite'])
    u.wait()
except Exception:
    print("Something went wrong!  Make sure you have git installed and in your path var!")
print(" ")
try:
    if reboot:
        r = "True"
    else:
        r = "False"
    sub_args = [pypath, main_path, "-reboot", r, "-path", pypath, "-update", "False"]
    if not return_channel == None:
        # Add our return channel if we have one
        sub_args.append("-channel")
        sub_args.append(str(return_channel))
    subprocess.Popen(sub_args)
    # Kill this process
    exit(0)
except Exception:
    pass
