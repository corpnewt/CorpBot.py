import sys, os, subprocess, time

# This module will start the script, and reboot it and etc

# Set defaults
bot = "Main.py"
install = "Install.py"
dir_path = os.path.dirname(os.path.realpath(__file__))
bot_path = os.path.join(dir_path,bot)
install_path = os.path.join(dir_path,install)
restart_on_error = True
wait_before_restart = 1

def get_bin(binary):
    # Returns the location in PATH (if any) of the passed var
    command = "where" if os.name == "nt" else "which"
    try:
        p = subprocess.run([command,binary], check=True, stderr=subprocess.DEVNULL, stdout=subprocess.PIPE)
        return p.stdout.decode("utf-8").replace("\r","").split("\n")[0]
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
        print("Something went wrong!  Make sure you have git installed and in your path var!")
    print(" ")

def install():
    if not git:
        return
    print("\n##############################")
    print("#      INSTALLING DEPS       #")
    print("##############################\n")
    print("\nRunning Install.py with --no-interaction")
    try:
        u = subprocess.Popen([sys.executable, install_path, "--no-interaction"])
        u.wait()
    except:
        print("Something went wrong!  Make sure you have git installed and in your path var!")
    print(" ")

def main():
    # Update before we start our loop
    update()
    while True:
        # Start the bot and wait for it to exit
        bot_process = subprocess.Popen([sys.executable, bot_path])
        bot_process.wait()
        # Return code time!  Here's what they'll mean:
        # 1 = Error - restart the bot without updating
        # 2 = Rebooting - update, then restart
        # 3 = Regular exit - ignore, and quit too
        # 4 = Install deps - update, install, then restart
        # Anything else assumes an issue with the script
        # and will subsequently restart.

        print("Return code:  {}".format(bot_process.returncode))

        if bot_process.returncode == 3:
            print("\nShut down.")
            if os.name == "nt":
                print("\nPress [enter] to close this window...")
            exit(0)
        elif bot_process.returncode in (2,4):
            print("\nRebooting...")
            update()
            if bot_process.returncode == 4:
                print("\nInstalling dependencies...")
                install()
        # Wait before we restart
        time.sleep(wait_before_restart)
        if bot_process.returncode not in (2,4):
            continue # Restart the loop
        break
    print("Restarting the local file...")
    # Restart WatchDog.py anew - this allows for updates to take effect
    p = subprocess.Popen([sys.executable]+sys.argv)
    p.communicate()
    exit(p.returncode)

git = get_git()
if git is None:
    print("Git is not found in your PATH var!\nUpdates will be disabled!")

# Enter the loop
main()
