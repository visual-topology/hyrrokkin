#   Narvi - a simple python web application server
#
#   Copyright (C) 2022-2023 Visual Topology Ltd
#
#   Licensed under the Open Software License version 3.0

import subprocess
import sys

import threading

class ProcessRunner(threading.Thread):

    def __init__(self, args, exit_callback=None):
        super().__init__()
        self.return_code = None
        self.sub = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        self.exit_callback = exit_callback

    def run(self):

        while self.return_code is None:
            self.handle_output(self.sub.stdout.readline())
            self.return_code = self.sub.poll()

        self.handle_output(self.sub.stdout.read())
        print("Stopped")
        if self.exit_callback:
            self.exit_callback()

    def handle_output(self,output):
        if output:
            if output.endswith("\n"):
                output = output[:-1]
            print("[%s]: %s" % (str(self.sub.pid), output))

    def get_pid(self):
        return self.sub.pid

    def stop(self, hard=False):
        if hard:
            self.sub.kill()
        else:
            self.sub.terminate()

    def get_return_code(self):
        return self.return_code

    def join(self):
        pass




