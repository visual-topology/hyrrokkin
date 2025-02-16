#   Hyrrokkin - a Python library for building and running executable graphs
#
#   MIT License - Copyright (C) 2022-2023  Visual Topology Ltd
#
#   Permission is hereby granted, free of charge, to any person obtaining a copy of this software
#   and associated documentation files (the "Software"), to deal in the Software without
#   restriction, including without limitation the rights to use, copy, modify, merge, publish,
#   distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the
#   Software is furnished to do so, subject to the following conditions:
#
#   The above copyright notice and this permission notice shall be included in all copies or
#   substantial portions of the Software.
#
#   THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING
#   BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
#   NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
#   DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
#   OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

import sys
import os
import signal
import logging
import asyncio
import traceback

from hyrrokkin.utils.message_utils import MessageUtils
from .execution_engine import ExecutionEngine

class RemoteExecutionWorker:

    def __init__(self, host_name, port):

        self.host_name = host_name
        self.port = port
        self.pid = os.getpid()

        self.reader = None
        self.writer = None
        self.engine = None
        self.injected_inputs = {}
        self.output_listeners = {}
        self.running = False

    async def run(self):
        self.reader, self.writer = await asyncio.open_connection(self.host_name, self.port)
        msg = await self.receive_message()
        control_packet = msg[0]
        action = control_packet["action"]

        if action == "init":
            self.init(control_packet)
        else:
            raise Exception("Protocol error")

        self.running = True
        while self.running:
            try:
                msg = await self.receive_message()
                if msg is None:
                    break
                await self.handle_message(*msg)
            except:
                traceback.print_exc()
        self.engine.close()
        self.writer.close()
        await self.writer.wait_closed()

    async def send_message(self, *message_parts):
        self.send_message_sync(*message_parts)
        await self.writer.drain()

    def send_message_sync(self, *message_parts):
        message_bytes = MessageUtils.encode_message(*message_parts)
        self.writer.write(len(message_bytes).to_bytes(4, "big"))
        self.writer.write(message_bytes)

    async def receive_message(self):
        message_length_bytes = await self.reader.read(4)
        if message_length_bytes == 0:
            return None
        message_length = int.from_bytes(message_length_bytes, "big")
        message_bytes = await self.reader.read(message_length)
        message_parts = MessageUtils.decode_message(message_bytes)
        return message_parts

    async def handle_message(self, control_packet, *extras):
        action = control_packet["action"]
        if action == "add_package":
            await self.engine.add_package(control_packet["package_id"])
        elif action == "add_node":
            await self.engine.add_node(control_packet["node_id"], control_packet["node_type_id"], control_packet["loading"])
        elif action == "add_link":
            await self.engine.add_link(control_packet["link_id"],control_packet["from_node_id"],control_packet["from_port"],
                                         control_packet["to_node_id"], control_packet["to_port"], control_packet["loading"])
        elif action == "pause":
            self.engine.pause()
        elif action == "resume":
            self.engine.resume()
        elif action == "close_worker":
            self.running = False
        elif action == "open_client":
            client_id = control_packet["client_id"]#  if not isinstance(control_packet["client_id"],list) else tuple(control_packet["client_id"])
            await self.engine.open_client(control_packet["target_id"],
                                    control_packet["target_type"],
                                    client_id,
                                    control_packet["client_options"],
                                    control_packet["client_service_class"])
        elif action == "client_message":
            client_id = control_packet["client_id"] # if not isinstance(control_packet["client_id"], list) else tuple(control_packet["client_id"])
            await self.engine.recv_message(control_packet["target_id"],
                                    control_packet["target_type"],
                                    client_id,
                                    *extras)
        elif action == "close_client":
            client_id = control_packet["client_id"] # if not isinstance(control_packet["client_id"], list) else tuple(control_packet["client_id"])
            await self.engine.close_client(control_packet["target_id"],
                                    control_packet["target_type"],
                                    client_id)
        elif action == "remove_node":
            await self.engine.remove_node(control_packet["node_id"])
        elif action == "remove_link":
            await self.engine.remove_link(control_packet["link_id"])
        elif action == "clear":
            await self.engine.clear()

    def create_output_listener(self, node_id, output_port):
        return lambda v: self.forward_output_value(node_id, output_port, v)

    def forward_output_value(self, node_id, output_port, value):
        self.send_message_sync({"action":"output_notification", "node_id": node_id, "output_port":output_port, "value":value})

    def execution_complete(self):
        self.send_message_sync({"action":"execution_complete", "count_failed": self.engine.count_failed()})

    def set_status(self, origin_id, origin_type, state, message):
        self.send_message_sync({"action":"status", "origin_id":origin_id, "origin_type":origin_type, "status":state, "message":message})

    def set_node_execution_state(self, at_time, node_id, execution_state, exn=None, is_manual=False):
        self.send_message_sync({"action": "update_execution_state",
                                "at_time": at_time,
                                "node_id": node_id,
                                "execution_state": execution_state,
                                "is_manual": is_manual,
                                "exn": None if exn is None else str(exn)})

    def send_client_message(self, origin_id, origin_type, client_id, *msg):
        print("send_client_message",origin_id,origin_type,client_id,*msg)
        self.send_message_sync({"action": "client_message", "origin_id":origin_id, "origin_type":origin_type, "client_id":client_id},*msg)

    def init(self, control_packet):
        self.execution_folder = control_packet["execution_folder"]
        self.class_map = control_packet["class_map"]
        injected_inputs = control_packet["injected_inputs"]
        output_listeners = control_packet["output_listeners"]
        for [node_id, input_port, value] in injected_inputs:
            self.injected_inputs[(node_id, input_port)] = value

        for [node_id, output_port] in output_listeners:
            self.output_listeners[(node_id, output_port)] = self.create_output_listener(node_id, output_port)

        self.engine = ExecutionEngine(self.class_map, self.execution_folder, 4, self.injected_inputs, self.output_listeners,
                                      execution_complete_callback=lambda: self.execution_complete(),
                                      status_callback=lambda *args: self.set_status(*args),
                                      node_execution_callback=lambda *args: self.set_node_execution_state(*args),
                                      message_callback=lambda *args: self.send_client_message(*args))



def main():
    print("Remote Execution Worker\n\n")
    from optparse import OptionParser
    usage = "usage"
    version = "version"
    parser = OptionParser(usage=usage,version=version)

    parser.add_option("","--host",dest="host",type="str",help="host name",default="")
    parser.add_option("","--port",dest="port",type="int",help="port number")
    parser.add_option("", "--verbose", action="store_true", help="verbose logging")

    (options,args) = parser.parse_args()
    os.putenv('PYTHONPATH',os.getcwd())

    if options.verbose:
        logging.basicConfig(level=logging.INFO)

    server = RemoteExecutionWorker(options.host,options.port)

    def handler(signum, frame):
        sys.stdout.flush()
        sys.stderr.flush()
        os._exit(0)

    signal.signal(3, handler)

    asyncio.run(server.run())

if __name__ == '__main__':
    main()




