import os
from subprocess import Popen
import threading

# os.chdir('data')

commands = [["python", "sumo_client.py"], ["python", "sumo_manager.py"]]

procs = [Popen(command) for command in commands]
for p in procs:
    p.wait()
