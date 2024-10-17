import os, sys, subprocess, threading, shlex, venv, argparse, json
try:
    from Queue import Queue, Empty
except:
    from queue import Queue, Empty

ON_POSIX = 'posix' in sys.builtin_module_names

class Run:

    def __init__(self):
        return

    def _read_output(self, pipe, q):
        while True:
            try:
                q.put(pipe.read(1))
            except ValueError:
                pipe.close()
                break

    def _stream_output(self, comm, shell = False):
        output = error = ""
        p = ot = et = None
        try:
            if shell and type(comm) is list:
                comm = " ".join(shlex.quote(x) for x in comm)
            if not shell and type(comm) is str:
                comm = shlex.split(comm)
            p = subprocess.Popen(comm, shell=shell, stdout=subprocess.PIPE, stderr=subprocess.PIPE, bufsize=1, universal_newlines=True, close_fds=ON_POSIX)
            # Setup the stdout thread/queue
            q = Queue()
            t = threading.Thread(target=self._read_output, args=(p.stdout, q))
            t.daemon = True # thread dies with the program
            # Setup the stderr thread/queue
            qe = Queue()
            te = threading.Thread(target=self._read_output, args=(p.stderr, qe))
            te.daemon = True # thread dies with the program
            # Start both threads
            t.start()
            te.start()

            while True:
                c = z = ""
                try:
                    c = q.get_nowait()
                except Empty:
                    pass
                else:
                    output += c
                try:
                    z = qe.get_nowait()
                except Empty:
                    pass
                else:
                    error += z
                sys.stdout.write(c)
                sys.stdout.write(z)
                sys.stdout.flush()
                p.poll()
                if c==z=="" and p.returncode != None:
                    break

            o, e = p.communicate()
            ot.exit()
            et.exit()
            return (output+o, error+e, p.returncode)
        except:
            if ot or et:
                try: ot.exit()
                except: pass
                try: et.exit()
                except: pass
            if p:
                return (output, error, p.returncode)
            return ("", "Command not found!", 1)

    def _run_command(self, comm, shell = False):
        c = None
        try:
            if shell and type(comm) is list:
                comm = " ".join(shlex.quote(x) for x in comm)
            if not shell and type(comm) is str:
                comm = shlex.split(comm)
            p = subprocess.Popen(comm, shell=shell, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            c = p.communicate()
            return (c[0].decode("utf-8", "ignore"), c[1].decode("utf-8", "ignore"), p.returncode)
        except:
            if c == None:
                return ("", "Command not found!", 1)
            return (c[0].decode("utf-8", "ignore"), c[1].decode("utf-8", "ignore"), p.returncode)

    def run(self, command_list, leave_on_fail = False):
        # Command list should be an array of dicts
        if type(command_list) is dict:
            # We only have one command
            command_list = [command_list]
        output_list = []
        for comm in command_list:
            args   = comm.get("args",   [])
            shell  = comm.get("shell",  False)
            stream = comm.get("stream", False)
            sudo   = comm.get("sudo",   False)
            stdout = comm.get("stdout", False)
            stderr = comm.get("stderr", False)
            mess   = comm.get("message", None)
            show   = comm.get("show",   False)
            
            if not mess == None:
                print(mess)

            if not len(args):
                # nothing to process
                continue
            if sudo:
                # Check if we have sudo
                out = self._run_command(["which", "sudo"])
                if "sudo" in out[0]:
                    # Can sudo
                    if type(args) is list:
                        args.insert(0, out[0].replace("\n", "")) # add to start of list
                    elif type(args) is str:
                        args = out[0].replace("\n", "") + " " + args # add to start of string
            
            if show:
                print(" ".join(args))

            if stream:
                # Stream it!
                out = self._stream_output(args, shell)
            else:
                # Just run and gather output
                out = self._run_command(args, shell)
                if stdout and len(out[0]):
                    print(out[0])
                if stderr and len(out[1]):
                    print(out[1])
            # Append output
            output_list.append(out)
            # Check for errors
            if leave_on_fail and out[2] != 0:
                # Got an error - leave
                break
        if len(output_list) == 1:
            # We only ran one command - just return that output
            return output_list[0]
        return output_list

def check_venv(force=False, clear=False, quiet=False):
    # Check for the virtual env
    needs_update = True
    venv_path = os.path.join(os.path.dirname(os.path.realpath(__file__)),"venv")
    if os.name == "nt":
        py_venv = os.path.join(venv_path,"Scripts","python.exe")
    else:
        py_venv = os.path.join(venv_path,"bin","python")
    if not force:
        # Only check pathing/versions if we're not forcing an update
        cfg_path = os.path.join(venv_path,"pyvenv.cfg")
        if os.path.isfile(cfg_path) and os.path.isfile(py_venv):
            # Both the pyvenv.cfg and our alias/bin exist,
            # try to get the path from pyvenv.cfg
            with open(cfg_path,"r") as f:
                cfg = f.read()
            home = exe = None
            for line in cfg.split("\n"):
                line = line.rstrip("\r") # Handle CRLF
                if line.startswith("home = "):
                    home = "home = ".join(line.split("home = ")[1:])
                elif line.startswith("executable = "):
                    exe = "executable = ".join(line.split("executable = ")[1:])
                if home and exe:
                    break
            # Compare to our executable's path
            c = venv.EnvBuilder().ensure_directories(venv_path)
            if (exe and exe == c.executable) or (home and home == c.python_dir):
                # It's a match - no need to update
                needs_update = False
    else:
        # We can't upgrade if we're forcing - so ensure we clear
        clear = True
    if needs_update:
        # Make sure we remove the existing python alias/exe/bin first
        if os.path.isfile(py_venv):
            os.remove(py_venv)
        # We either don't have a venv, or it's a different
        # version of py - let's create the venv and return
        if not quiet:
            print("{} venv...".format("Creating new" if clear else "Upgrading"))
        venv.EnvBuilder(clear=clear,upgrade=not clear,with_pip=True).create(venv_path)
    if os.path.isfile(py_venv):
        return py_venv
    return None

if __name__ == '__main__':
    parser = argparse.ArgumentParser(prog="Install.py", description="Installer for CorpBot.py dependencies.")
    parser.add_argument("-n", "--no-interaction", help="Don't require user interaction after tasks complete", action="store_true")
    parser.add_argument("-c", "--clear-venv", help="Clears the venv when accessed with a different python version instead of upgrading", action="store_true")
    parser.add_argument("-f", "--force-update-venv", help="Clears the venv and creates it anew", action="store_true")
    parser.add_argument("-l", "--list-dependencies", help="Prints JSON data showing required dependencies, whether they're installed, and their versions (overrides --no-interaction and --install-missing)", action="store_true")
    parser.add_argument("-m", "--install-missing", help="Only attmepts to install missing dependencies", action="store_true")
    parser.add_argument("-p", "--skip-pip", help="Skips updating pip in the venv in addition to the other dependencies", action="store_true")
    args = parser.parse_args()

    r = Run()

    # Set up the modules we intend to install
    modules = []
    if not args.skip_pip:
        # Include pip at the start if we're not told to skip it
        modules.append({"name":"pip"})
    # Add the rest of the standard modules
    modules.extend([
        # Get the latest commit of pomice to ensure we have Lavalink v4 changes
        {"name":"pomice","item":"git+https://github.com/cloudwithax/pomice.git"},
        # Get the latest commit of py-cord to ensure we have python 3.12 changes
        {"name":"py-cord","item":"git+https://github.com/Pycord-Development/pycord"},
        {"name":"pillow"},
        {"name":"requests"},
        {"name":"parsedatetime"},
        {"name":"psutil"},
        {"name":"plusminus"},
        {"name":"pyquery"},
        {"name":"python-aiml","item":"git+https://github.com/paulovn/python-aiml"},
        {"name":"speedtest-cli"},
        {"name":"pytz"},
        {"name":"wikipedia"},
        {"name":"googletrans","item":"git+https://github.com/ssut/py-googletrans"},
        {"name":"giphypop","item":"git+https://github.com/shaunduncan/giphypop.git#egg=giphypop"},
        {"name":"numpy"},
        {"name":"pymongo"},
        {"name":"geopy"},
        {"name":"pyfiglet"},
        {"name":"regex"}
    ])
    db_path = os.path.join(os.path.dirname(os.path.realpath(__file__)),"Cogs","PandorasDB.py")
    if os.path.exists(db_path):
        modules.append({"name":"redis"})
    
    # Let's ensure the virtual env
    py_venv = check_venv(
        force=args.force_update_venv,
        clear=args.clear_venv,
        quiet=args.list_dependencies
    )
    if not py_venv:
        raise FileNotFoundError("Could not locate or create a valid virtual env at {}".format(
            os.path.join(os.path.dirname(os.path.realpath(__file__)),"venv")
        ))
    
    if args.list_dependencies or args.install_missing:
        # Gather a list of what deps we have, and which are missing
        out = r.run({"args":[py_venv,"-m","pip","list"]})
        if out[2] != 0:
            exit(out[2])
        checks = {}
        for m in modules:
            if m.get("uninstall"):
                continue # Skip uninstalls
            checks[m.get("pkg_name",m["name"]).lower()] = None
        # Walk the pip list output and scrape for our modules
        for line in out[0].split("\n"):
            try:
                name,vers = line.lower().split()
            except:
                continue
            if name in checks:
                checks[name]=vers
        if args.list_dependencies:
            # Just printing the deps - do that and bail
            print(json.dumps(checks,indent=2))
            exit()
        elif args.install_missing:
            # Let's replace our modules with the ones that are missing
            new_modules = []
            for m in modules:
                name = m.get("pkg_name",m["name"]).lower()
                if not checks.get(name):
                    new_modules.append(m)
            # Replace the original list
            modules = new_modules
    exit_code = 0
    try:
        if not modules:
            print("No modules to install.")
        for item,module in enumerate(modules,start=1):
            print("\n\n{} {} - {} of {}\n\n".format("Removing" if module.get("uninstall") else "Updating",module["name"], item, len(modules)))
            if module.get("uninstall"):
                o = r.run({"args":[py_venv, "-m", "pip", "uninstall","-y", module.get("item", module["name"])], "stream":True})
            else:
                o = r.run({"args":[py_venv, "-m", "pip", "install", "-U", module.get("item", module["name"])], "stream":True})
            if o[2] != 0:
                exit_code = o[2]
        # Prompt for the users to press enter to exit
        print("\nDone.")
    except Exception as e:
        print("Something went wrong: {}".format(e))
    finally:
        if not args.no_interaction:
            prompt = "\nPress [enter] to leave the script..."
            if sys.version_info >= (3, 0):
                input(prompt)
            else:
                raw_input(prompt)
        exit(exit_code)
