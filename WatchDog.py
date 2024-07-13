import sys, os, subprocess, time, venv, json, getpass, socket, datetime
if os.name == "nt":
    import msvcrt
else:
    import select

# This module will start the script, and reboot it and etc

# Set defaults
bot = "Main.py"
install = "Install.py"
dir_path = os.path.dirname(os.path.realpath(__file__))
bot_path = os.path.join(dir_path,bot)
install_path = os.path.join(dir_path,install)
restart_on_error = True
wait_before_restart = 1

# Ensure the current directory is our parent dir
os.chdir(dir_path)

# Keep a reference to our expected venv python path
py_path = os.path.join(dir_path,"venv","Scripts","python.exe") if os.name == "nt" else os.path.join(dir_path,"venv","bin","python")

# https://stackoverflow.com/a/33117579 https://stackoverflow.com/a/59312877
def check_internet(host="8.8.8.8", port=53, timeout=3):
    """
    Host: 8.8.8.8 (google-public-dns-a.google.com)
    OpenPort: 53/tcp
    Service: domain (DNS/TCP)
    """
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(timeout)
        s.connect((host, port))
        return True
    except socket.error as ex:
        return False

def grab(prompt, **kwargs):
    # Takes a prompt, a default, and a timeout and shows it with that timeout
    # returning the result
    timeout = kwargs.get("timeout", 0)
    default = kwargs.get("default", None)
    # If we don't have a timeout - then skip the timed sections
    if timeout <= 0:
        if sys.version_info >= (3,0):
            return input(prompt)
        else:
            return str(raw_input(prompt))
    # Write our prompt
    sys.stdout.write(prompt)
    sys.stdout.flush()
    if os.name == "nt":
        start_time = time.time()
        i = ''
        while True:
            if msvcrt.kbhit():
                c = msvcrt.getche()
                if ord(c) == 13: # enter_key
                    break
                elif ord(c) >= 32: # space_char
                    i += c.decode() if sys.version_info >= (3,0) and isinstance(c,bytes) else c
            else:
                time.sleep(0.02) # Delay for 20ms to prevent CPU workload
            if len(i) == 0 and (time.time() - start_time) > timeout:
                break
    else:
        i, o, e = select.select( [sys.stdin], [], [], timeout )
        if i:
            i = sys.stdin.readline().strip()
    print('')  # needed to move to next line
    if len(i) > 0:
        return i
    else:
        return default

def check_venv():
    # Check for the virtual env
    print("Verifying venv and dependencies...")
    p = subprocess.run(
        [sys.executable,install_path,"--install-missing","--no-interaction"],
        stderr=subprocess.DEVNULL
    )
    print(" ")

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
    print("\n##############################")
    print("#      INSTALLING DEPS       #")
    print("##############################\n")
    print("\nRunning Install.py with --force-update-venv and --no-interaction")
    try:
        u = subprocess.Popen([sys.executable, install_path, "--force-update-venv", "--no-interaction"])
        u.wait()
    except:
        print("Something went wrong!")
    print(" ")

def update_deps():
    print("\n##############################")
    print("#       UPDATING DEPS        #")
    print("##############################\n")
    print("\nRunning Install.py with --no-interaction")
    try:
        u = subprocess.Popen([sys.executable, install_path, "--no-interaction"])
        u.wait()
    except:
        print("Something went wrong!")
    print(" ")

def main():
    # Check in a loop for internet, backing off until we hit 2m waits
    back_off = 10.
    back_off_max = 120
    while not check_internet():
        back_off_int = int(back_off)
        grab(
            "!! {}: No internet connection - trying again in {:,} seconds...".format(
                datetime.datetime.now().time().isoformat(),
                back_off_int
            ),
            timeout=back_off_int
        )
        back_off = min(back_off * 1.5, back_off_max)
    # Update before we start our loop
    update()
    # Ensure our virtual environment is set up as needed
    check_venv()
    if not os.path.isfile(py_path):
        print("Could not locate {}!".format(py_path))
        exit(1)
    while True:
        # Start the bot and wait for it to exit
        bot_process = subprocess.Popen([py_path, bot_path])
        bot_process.wait()
        # Return code time!  Here's what they'll mean:
        # 1 = Error - restart the bot without updating
        # 2 = Rebooting - update bot, then restart
        # 3 = Regular exit - ignore, and quit too
        # 4 = Install deps - update bot, install, then restart
        # 5 = Update deps - update bot, update deps, ethen restart
        # 6 = Invalid token - load settings_dict.json and prompt for new token
        # Anything else assumes an issue with the script
        # and will subsequently restart.

        if bot_process.returncode != 6:
            # Don't print if we need to prompt for a new token
            print("Return code:  {}".format(bot_process.returncode))

        if bot_process.returncode == 3:
            print("\nShut down.")
            if os.name == "nt":
                input("\nPress [enter] to close this window...")
            exit(0)
        elif bot_process.returncode in (2,4,5):
            print("\nRebooting...")
            update()
            if bot_process.returncode == 4:
                print("\nInstalling dependencies...")
                install()
            elif bot_process.returncode == 5:
                print("\nUpdating dependencies...")
                update_deps()
        elif bot_process.returncode == 6:
            if not os.path.isfile("settings_dict.json"):
                print("Could not locate settings_dict.json")
                exit(1)
            try:
                settings_dict = json.load(open("settings_dict.json"))
            except Exception as e:
                print("Failed to load settings_dict.json: {}".format(e))
                exit(1)
            while True:
                new_token = getpass.getpass("Paste the new token here (or q to quit): ")
                if not len(new_token):
                    continue
                if new_token.lower() == "q":
                    exit()
                # Save the token in the settings_dict.json
                settings_dict["token"] = new_token
                json.dump(settings_dict,open("settings_dict.json","w"),indent=4)
                print("\nUpdated token in settings_dict.json - restarting...\n")
                break
        # Wait before we restart
        time.sleep(wait_before_restart)
        if bot_process.returncode not in (2,4,5):
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
