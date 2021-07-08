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

    def _stream_output(self, comm, shell=False):
        output = error = ""
        p = ot = et = None
        try:
            if shell and type(comm) is list:
                comm = " ".join(shlex.quote(x) for x in comm)
            if not shell and type(comm) is str:
                comm = shlex.split(comm)
            p = subprocess.Popen(comm, shell=shell, stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE, bufsize=1, universal_newlines=True, close_fds=ON_POSIX)
            # Setup the stdout thread/queue
            q = Queue()
            t = threading.Thread(target=self._read_output, args=(p.stdout, q))
            t.daemon = True  # thread dies with the program
            # Setup the stderr thread/queue
            qe = Queue()
            te = threading.Thread(
                target=self._read_output, args=(p.stderr, qe))
            te.daemon = True  # thread dies with the program
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
                if c == z == "" and p.returncode != None:
                    break

            o, e = p.communicate()
            ot.exit()
            et.exit()
            return (output+o, error+e, p.returncode)
        except:
            if ot or et:
                try:
                    ot.exit()
                except:
                    pass
                try:
                    et.exit()
                except:
                    pass
            if p:
                return (output, error, p.returncode)
            return ("", "Command not found!", 1)

    def _run_command(self, comm, shell=False):
        c = None
        try:
            if shell and type(comm) is list:
                comm = " ".join(shlex.quote(x) for x in comm)
            if not shell and type(comm) is str:
                comm = shlex.split(comm)
            p = subprocess.Popen(
                comm, shell=shell, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            c = p.communicate()
            return (c[0].decode("utf-8", "ignore"), c[1].decode("utf-8", "ignore"), p.returncode)
        except:
            if c == None:
                return ("", "Command not found!", 1)
            return (c[0].decode("utf-8", "ignore"), c[1].decode("utf-8", "ignore"), p.returncode)

    def run(self, command_list, leave_on_fail=False):
        # Command list should be an array of dicts
        if type(command_list) is dict:
            # We only have one command
            command_list = [command_list]
        output_list = []
        for comm in command_list:
            args = comm.get("args",   [])
            shell = comm.get("shell",  False)
            stream = comm.get("stream", False)
            sudo = comm.get("sudo",   False)
            stdout = comm.get("stdout", False)
            stderr = comm.get("stderr", False)
            mess = comm.get("message", None)
            show = comm.get("show",   False)

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
                        # add to start of list
                        args.insert(0, out[0].replace("\n", ""))
                    elif type(args) is str:
                        # add to start of string
                        args = out[0].replace("\n", "") + " " + args

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
        {"name": "discord [rewrite]", "item": "discord.py[voice]"},
        {"name": "pillow"},
        # {"name":"youtube-dl"},
        {"name": "Wavelink"},
        {"name": "Requests"},
        {"name": "parsedatetime"},
        {"name": "psutil"},
        {"name": "pyparsing"},
        {"name": "pyquery"},
        {"name": "pyaiml", "item": "git+https://github.com/paulovn/python-aiml"},
        {"name": "speedtest-cli"},
        {"name": "pytz"},
        {"name": "wikipedia"},
        {"name": "googletrans"},
        {"name": "giphypop",
            "item": "git+https://github.com/shaunduncan/giphypop.git#egg=giphypop"},
        {"name": "numpy"},
        {"name": "pymongo"},
        {"name": "igdb_api_python"},
        {"name": "redis"},
        {"name": "geopy"}
    ]
    item = 0
    for module in modules:
        item += 1
        print(
            "\n\nUpdating {} - {} of {}\n\n".format(module["name"], item, len(modules)))
        r.run({"args": [sys.executable, "-m", "pip", "install",
              "-U", module.get("item", module["name"])], "stream": True})
    # Prompt for the users to press enter to exit
    prompt = "Done.\n\nPress [enter] to leave the script..."
    if sys.version_info >= (3, 0):
        input(prompt)
    else:
        raw_input(prompt)
