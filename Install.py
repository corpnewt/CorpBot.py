import os
import sys
import subprocess
import threading
import shlex
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

if __name__ == '__main__':
    r = Run()
    modules = [
        # Get the latest commit of pomice to ensure we have Lavalink v4 changes
        {"name":"pomice","item":"git+https://github.com/cloudwithax/pomice.git"},
        # Remove the updated discord.py that pomice overwrites, and
        # remove py-cord so we can reinstall it with the proper version
        {"name":"discord.py","uninstall":True},
        {"name":"pycord","item":"py-cord[voice]","uninstall":True},
        # Get the latest commit of py-cord to ensure we have pyhton 3.12 changes
        {"name":"pycord","item":"git+https://github.com/Pycord-Development/pycord.git#egg=py-cord[voice]"},
        {"name":"certifi"},
        {"name":"pillow"},
        {"name":"Requests"},
        {"name":"parsedatetime"},
        {"name":"psutil"},
        {"name":"pyparsing"},
        {"name":"pyquery"},
        {"name":"pyaiml","item":"git+https://github.com/paulovn/python-aiml"},
        {"name":"speedtest-cli"},
        {"name":"pytz"},
        {"name":"wikipedia"},
        {"name":"googletrans (direct api branch)","item":"git+https://github.com/ssut/py-googletrans@feature/enhance-use-of-direct-api"},
        {"name":"giphypop","item":"git+https://github.com/shaunduncan/giphypop.git#egg=giphypop"},
        {"name":"numpy"},
        {"name":"pymongo"},
        {"name":"geopy"},
        {"name":"pyfiglet"},
        {"name":"regex"}
    ]
    db_path = os.path.join(os.path.dirname(os.path.realpath(__file__)),"Cogs","PandorasDB.py")
    print("\nChecking for {}...".format(db_path))
    if os.path.exists(db_path):
        print("Branch has database support - including redis...")
        modules.append({"name":"redis (locked to 3.5.3 for the time being until v4.x is sorted)","item":"redis==3.5.3"})
    else:
        print("No database support - omitting redis...")
    item = 0
    for module in modules:
        item+=1
        print("\n\n{} {} - {} of {}\n\n".format("Removing" if module.get("uninstall") else "Updating",module["name"], item, len(modules)))
        if module.get("uninstall"):
            r.run({"args":[sys.executable, "-m", "pip", "uninstall","-y", module.get("item", module["name"])], "stream":True})
        else:
            r.run({"args":[sys.executable, "-m", "pip", "install", "-U", module.get("item", module["name"])], "stream":True})
    # Prompt for the users to press enter to exit
    print("\nDone.")
    if not "-n" in sys.argv[1:] and not "--no-interaction" in sys.argv[1:]:
        prompt = "\nPress [enter] to leave the script..."
        if sys.version_info >= (3, 0):
            input(prompt)
        else:
            raw_input(prompt)
