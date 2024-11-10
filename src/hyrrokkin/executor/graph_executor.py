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

from hyrrokkin.executor.execution_thread import ExecutionThread
from hyrrokkin.executor.execution_client import ExecutionClient
from hyrrokkin.utils.resource_loader import ResourceLoader

class GraphExecutor:

    def __init__(self, network, schema, status_callback, node_execution_callback, execution_folder="."):
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


    def reset(self):
        self.execution_complete_callback = None
        self.et = None
        self.execution_clients = {}
        self.injected_inputs = {}
        self.output_listeners = {}

    def pause(self):
        self.paused = True
        if self.et:
            self.et.pause()

    def resume(self):
        self.paused = False
        if self.et:
            self.et.schedule_resume()

    def is_paused(self):
        return self.paused

    def inject_input(self, node_port, value):
        (node,port) = node_port
        self.injected_inputs[(node,port)] = value

    def add_output_listener(self, node_port, listener):
        (node, port) = node_port
        self.output_listeners[(node,port)] = listener

    def attach_client(self, target_id, client_id, client_options, client_service_classes):
        self.detach_client(target_id, client_id) # in case a client with the same id is already connected to the target
        cls = ResourceLoader.get_class(client_service_classes[0])
        client_service = cls()
        client = ExecutionClient(target_id, client_id, client_service, client_options, client_service_classes[1])
        self.execution_clients[(target_id, client_id)] = client
        if self.et:
            client.connect_execution(self.et)
            self.et.schedule_open_client(target_id, client_id, client_options, client_service_classes[1])
        return client_service

    def detach_client(self, target_id, client_id):
        if (target_id, client_id) in self.execution_clients:
            client = self.execution_clients[(target_id, client_id)]
            client.disconnect()
            self.et.schedule_close_client(target_id, client_id)
            del self.execution_clients[(target_id, client_id)]

    def load_execution(self):
        for (package_id, package) in self.schema.get_packages().items():
            self.et.schedule_package_added(package)

        # load all nodes and links

        all_node_ids = self.network.get_node_ids(traversal_order=True)

        for node_id in all_node_ids:
            self.et.schedule_node_added(self.network.get_node(node_id), loading=True)

        for link_id in self.network.get_link_ids():
            link = self.network.get_link(link_id)
            self.et.schedule_link_added(link, loading=True)

    def run(self, terminate_on_complete=False):
        self.et = ExecutionThread(self, self.network.get_schema(), self.queue, self.execution_folder, injected_inputs=self.injected_inputs, output_listeners=self.output_listeners)
        for (id, client_id) in self.execution_clients:
            client = self.execution_clients[(id, client_id)]
            client.connect_execution(self.et)
            self.et.schedule_open_client(id, client_id, client.get_client_options(), client.get_execution_client_service_class())

        self.et.start()

        self.load_execution()

        self.stop_on_execution_complete = terminate_on_complete

        self.et.schedule_run(terminate_on_complete)

        while True:
            notify_fn = self.queue.get()
            if notify_fn is None:
                break
            request_stop = notify_fn(self)
            if request_stop:
                break

        for (id, client_id) in self.execution_clients:
            client = self.execution_clients[(id, client_id)]
            client.disconnect()

        result = self.close()

        # drain final notifications
        while not self.queue.empty():
            notify_fn = self.queue.get()
            if notify_fn:
                notify_fn(self)

        return result

    def start(self):
        self.et = ExecutionThread(self, self.network.get_schema(), self.queue, self.execution_folder, injected_inputs=self.injected_inputs, output_listeners=self.output_listeners)
        for (id, client_id) in self.execution_clients:
            client = self.execution_clients[(id, client_id)]
            client.connect_execution(self.et)
            self.et.schedule_open_client(id, client_id, client.get_client_options(), client.get_execution_client_service_class())

        self.et.start()

        self.load_execution()

        self.stop_on_execution_complete = False

        self.et.schedule_run(False)

        while True:
            notify_fn = self.queue.get()
            if notify_fn is None:
                break
            else:
                notify_fn(self)

        # drain final notifications
        while not self.queue.empty():
            notify_fn = self.queue.get()
            if notify_fn:
                notify_fn(self)

    def close(self):
        self.et.join()
        self.et.loop.close()
        self.et.close()
        result = not self.et.is_failed()
        self.reset()
        return result

    def stop(self):
        if self.et:
            self.et.schedule_stop_executor()

    def add_node(self, node):
        if self.et:
            self.et.schedule_node_added(node)

    def add_link(self, link):
        if self.et:
            self.et.schedule_link_added(link)

    def recv_node_message(self, node_id, client_id, msg):
        self.et.schedule_recv_message(("node", node_id), client_id, msg)

    def recv_configuration_message(self, package_id, client_id, msg):
        self.et.schedule_recv_message(("configuration", package_id), client_id, msg)

    def remove_node(self, node_id):
        if self.et:
            self.et.schedule_node_removed(node_id)

    def remove_link(self, link_id):
        if self.et:
            self.et.schedule_link_removed(link_id)

    def clear(self):
        if self.et:
            self.et.schedule_clear()

    def get_configuration_wrapper(self, package_id):
        if self.et:
            return self.et.get_configuration_wrapper(package_id)
        else:
            return None

    def request_node_execution(self, node_id):
        self.et.schedule_request_node_execution(node_id)

    # notifications from execution

    def notify(self, notify_fn):
        self.queue.put(notify_fn)

    def message_update(self, target_id, client_id, *message_content):
        # called to send a message from a node/configuration to an execution client
        if (target_id, client_id) in self.execution_clients:
            self.execution_clients[(target_id, client_id)].message_callback(*message_content)
        return False

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






