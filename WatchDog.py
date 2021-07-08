import sys
import os
import subprocess
import time

# This module will start the script, and reboot it and etc

# Set defaults
bot = "Main.py"
dir_path = os.path.dirname(os.path.realpath(__file__))
bot_path = os.path.join(dir_path, bot)
restart_on_error = True
wait_before_restart = 1


def get_bin(binary):
    # Returns the location in PATH (if any) of the passed var
    command = "where" if os.name == "nt" else "which"
    try:
        p = subprocess.run(command+" "+binary, shell=True, check=True,
                           stderr=subprocess.DEVNULL, stdout=subprocess.PIPE)
        return p.stdout.decode("utf-8").split("\n")[0].split("\r")[0]
    except:
        return None


def get_git():
    # Returns the local instance of git - if any
    return get_bin("git")


def update():
    if not git:
        return
    print("\n##############################")
    print("#          UPDATING          #")
    print("##############################\n")
    print("\nTrying to update via git...\n")
    try:
        u = subprocess.Popen([git, 'pull'])
        u.wait()
    except:
        print(
            "Something went wrong!  Make sure you have git installed and in your path var!")
    print(" ")


def main():
    # Here we have our deps checked - let's go into a loop
    while True:
        # Start the bot and wait for it to exit
        bot_process = subprocess.Popen([sys.executable, bot_path])
        bot_process.wait()
        # Return code time!  Here's what they'll mean:
        # 1 = Error - restart the bot without updating
        # 2 = Rebooting - update, then restart
        # 3 = Regular exit - ignore, and quit too
        # Anything else assumes an issue with the script
        # and will subsequently restart.

        print("Return code:  {}".format(bot_process.returncode))

        if bot_process.returncode == 3:
            print("\nShut down.")
            exit(0)
        elif bot_process.returncode == 2:
            print("\nRebooting...")
            update()
        time.sleep(wait_before_restart)


git = get_git()
if git == None:
    print("Git is not found in your PATH var!\nUpdates will be disabled!")

# Update first
update()
# Enter the loop
main()
