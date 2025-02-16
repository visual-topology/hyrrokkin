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

import queue
import socket
import threading
import logging

from .process_runner import ProcessRunner
from .thread_runner import ThreadRunner

from hyrrokkin.utils.message_utils import MessageUtils
from hyrrokkin.utils.resource_loader import ResourceLoader
from .execution_client import ExecutionClient


class ExecutionManager:

    def __init__(self, network, schema, status_callback, node_execution_callback, execution_folder=".", in_process=True):
        self.network = network
        self.schema = schema
        self.queue = queue.Queue()
        self.stop_on_execution_complete = False
        self.status_callback = status_callback
        self.node_execution_callback = node_execution_callback
        self.execution_folder = execution_folder
        self.paused = False
        self.reset()
        self.injected_inputs = {}
        self.output_listeners = {}
        self.host_name = "localhost"
        self.pid = None
        self.listening_sock = None
        self.connected = False
        self.msg_handler = None
        self.port = None
        self.lock = threading.RLock()
        self.running = False
        self.count_failed = 0
        self.terminate_on_complete = False
        self.logger = logging.getLogger("remote_graph_executor")
        self.in_process = in_process
        self.restarting = False

    def is_paused(self):
        return self.paused

    def inject_input(self, node_port, value):
        (node,port) = node_port
        self.injected_inputs[(node,port)] = value

    def add_output_listener(self, node_port, listener):
        (node, port) = node_port
        self.output_listeners[(node,port)] = listener

    # notifications from execution

    def status_update(self, target_id, target_type, message, status):
        if self.status_callback:
            self.status_callback(target_id, target_type, message, status)
        return False

    def node_execution_update(self, at_time, node_id, node_execution_state, exn, is_manual):
        if self.node_execution_callback:
            self.node_execution_callback(at_time, node_id, node_execution_state, exn, is_manual)
        return False

    def set_execution_complete_callback(self, execution_complete_callback):
        self.execution_complete_callback = execution_complete_callback

    def execution_complete_update(self):
        if self.execution_complete_callback:
            self.execution_complete_callback()
        return self.stop_on_execution_complete

    def __start_remote_graph_process(self):
        runner = ProcessRunner(self.host_name, self.port)
        runner.daemon = True
        runner.start()
        return runner

    def __start_remote_graph_thread(self):
        runner = ThreadRunner(self.host_name, self.port)
        runner.start()
        return runner

    def serialise_injected_inputs(self):
        ser = []
        for (node_id,input_port) in self.injected_inputs:
            ser.append([node_id,input_port,self.injected_inputs[(node_id,input_port)]])
        return ser

    def serialise_output_listeners(self):
        ser = []
        for (node_id,output_port) in self.output_listeners:
            ser.append([node_id,output_port])
        return ser

    def run(self, terminate_on_complete=True):
        self.terminate_on_complete=terminate_on_complete
        self.listening_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.listening_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.listening_sock.bind((self.host_name,0))
        _, self.port = self.listening_sock.getsockname()

        self.logger.info(f"Listening on port {self.port}")

        if self.in_process:
            self.runner = self.__start_remote_graph_thread()
        else:
            self.runner = self.__start_remote_graph_process()

        self.pid = self.runner.get_pid()

        self.listening_sock.listen(5)

        self.logger = logging.getLogger("execution_worker")

        self.sock, self.cliaddr = self.listening_sock.accept()

        self.sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)

        self.logger.info("Connected")

        # import fcntl
        # import os
        # fl = fcntl.fcntl(self.sock, fcntl.F_GETFL)
        # fl = fl & ~os.O_NONBLOCK
        # fcntl.fcntl(self.sock, fcntl.F_SETFL, fl)

        init_msg = {
            "action": "init",
            "execution_folder": self.execution_folder,
            "class_map": self.network.get_schema().get_classmap(),
            "injected_inputs": self.serialise_injected_inputs(),
            "output_listeners": self.serialise_output_listeners()
        }

        self.running = True

        self.send_message(init_msg)

        self.load_execution()

        for (target_id, target_type, client_id) in self.execution_clients:
            client = self.execution_clients[(target_id, target_type, client_id)]
            self.connect_client(target_id, target_type, client_id, client)

        while True:
            try:
                continue_connection = self.receive_message()
                if not continue_connection:
                    break
            except:
                self.logger.exception("receive message")
                break

        self.running = False
        self.logger.info("terminating connection")

        self.sock.close()
        self.listening_sock.close()

        self.runner.join()

        return self.count_failed == 0

    def start(self):
        while True:
            self.run(terminate_on_complete=False)
            if not self.restarting:
                break
            self.restarting = False

    def send_message(self, *message_parts):
        if self.running:
            message_bytes = MessageUtils.encode_message(*message_parts)
            try:
                self.lock.acquire()
                self.sock.send(len(message_bytes).to_bytes(4, "big"))
                self.sock.send(message_bytes)
            finally:
                self.lock.release()

    def receive_message(self):
        try:
            message_length_bytes = self.sock.recv(4)
            message_length = int.from_bytes(message_length_bytes, "big")
            if message_length == 0:
                return False
            message_bytes = self.sock.recv(message_length)
            message_parts = MessageUtils.decode_message(message_bytes)
        except:
            return False
        self.handle_message(message_parts)
        return True

    def handle_client_message(self, target_id, target_type, client_id, extras):
        if isinstance(client_id,list):
            client_id = tuple(client_id)
        client = self.execution_clients[(target_id,target_type, client_id)]
        client.message_callback(*extras)
        return True

    def forward_client_message(self, target_id, target_type, client_id, *msg):
        control_packet = {
            "action": "client_message",
            "target_id": target_id,
            "target_type": target_type,
            "client_id": client_id
        }
        self.send_message(control_packet, *msg)

    def connect_client(self, target_id, target_type, client_id, execution_client):
        self.open_client(target_id, target_type, client_id, execution_client.get_client_options(), execution_client.get_execution_client_service_class())
        execution_client.set_connected()

    def open_client(self, target_id, target_type, client_id, client_options, execution_service_class):
        self.send_message({
            "action": "open_client",
            "target_id": target_id,
            "target_type": target_type,
            "client_id": client_id,
            "client_options": client_options,
            "client_service_class": execution_service_class
        })

    def close_client(self, target_id, target_type, client_id):
        self.send_message({
            "action": "close_client",
            "target_id": target_id,
            "target_type": target_type,
            "client_id": client_id
        })

    def handle_message(self, message_parts):
        control_packet = message_parts[0]
        action = control_packet["action"]
        if action == "client_message":
            origin_id = control_packet["origin_id"]
            origin_type = control_packet["origin_type"]
            client_id = control_packet["client_id"]
            self.handle_client_message(origin_id, origin_type, client_id, message_parts[1:])
        elif action == "update_execution_state":
            self.node_execution_update(control_packet.get("at_time",None), control_packet["node_id"],
                                       control_packet["execution_state"], control_packet.get("exn",None),
                                        control_packet["is_manual"])
        elif action == "execution_complete":
            self.count_failed = control_packet["count_failed"]
            self.execution_complete_update()
            if self.terminate_on_complete:
                self.close_worker()
        elif action == "output_notification":
            self.notify_output(control_packet["node_id"],control_packet["output_port"],control_packet["value"])
        elif action == "status":
            self.status_update(control_packet["origin_id"],control_packet["origin_type"],control_packet["message"],control_packet["status"])
        else:
            self.logger.warning(f"Unhandled action {action}")

    def notify_output(self, node_id, output_port, value):
        self.output_listeners[(node_id, output_port)](value)

    def stop(self):
        self.logger.info("stopping")
        self.close_worker()

    def get_pid(self):
        return self.pid

    def reset(self):
        self.execution_complete_callback = None
        self.execution_clients = {}
        self.injected_inputs = {}
        self.output_listeners = {}

    def pause(self):
        self.paused = True
        self.send_message({
            "action": "pause"
        })

    def resume(self):
        self.paused = False
        self.send_message({
            "action": "resume"
        })

    def restart(self):
        self.restarting = True
        self.runner.stop(True)

    def attach_client(self, target_id, target_type, client_id, client_options, client_service_classes):
        self.detach_client(target_id, target_type, client_id)  # in case a client with the same id is already connected to the target
        cls = ResourceLoader.get_class(client_service_classes[0])
        client_service = cls()
        client = ExecutionClient(self, target_id, target_type, client_id, client_service, client_options, client_service_classes[1])
        self.execution_clients[(target_id, target_type, client_id)] = client
        if self.running:
            self.connect_client(target_id, target_type, client_id, client)
        return client_service

    def detach_client(self, target_id, target_type, client_id):
        if (target_id, target_type, client_id) in self.execution_clients:
            client = self.execution_clients[(target_id, target_type, client_id)]
            client.disconnect()
            self.close_client(target_id, target_type, client_id)
            del self.execution_clients[(target_id, target_type, client_id)]

    def load_execution(self):
        for (package_id, package) in self.schema.get_packages().items():
            self.add_package(package_id)

        # load all nodes and links

        all_node_ids = self.network.get_node_ids(traversal_order=True)

        for node_id in all_node_ids:
            node = self.network.get_node(node_id)
            self.add_node(node, loading=True)

        for link_id in self.network.get_link_ids():
            link = self.network.get_link(link_id)
            self.add_link(link, loading=True)

        if not self.paused:
            self.resume()


    def close_worker(self):
        self.send_message({"action": "close_worker"})

    def close(self):
        result = True
        return result

    def add_node(self, node, loading=False):
        self.send_message({
            "action": "add_node",
            "node_id": node.get_node_id(),
            "node_type_id": node.get_node_type(),
            "loading": loading
        })

    def add_link(self, link, loading=False):
        self.send_message({
            "action": "add_link",
            "link_id": link.get_link_id(),
            "link_type": link.get_link_type(),
            "from_node_id": link.from_node_id,
            "from_port": link.from_port,
            "to_node_id": link.to_node_id,
            "to_port": link.to_port,
            "loading": loading
        })

    def add_package(self, package_id):
        self.send_message({
            "action": "add_package",
            "package_id": package_id
        })

    def remove_node(self, node_id):
        self.send_message({
            "action": "remove_node",
            "node_id": node_id
        })

    def remove_link(self, link_id):
        self.send_message({
            "action": "remove_link",
            "link_id": link_id
        })

    def clear(self):
        self.send_message({
            "action": "clear"
        })

    def message_update(self, target_id, client_id, *message_content):
        # called to send a message from a node/configuration to an execution client
        if (target_id, client_id) in self.execution_clients:
            self.execution_clients[(target_id, client_id)].message_callback(*message_content)
        return False













