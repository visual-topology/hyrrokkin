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

from hyrrokkin.model.network import Network

from hyrrokkin.executor.execution_thread import ExecutionThread
from hyrrokkin.executor.execution_state import ExecutionState
from hyrrokkin.executor.execution_client import ExecutionClient


class GraphExecutor:

    def __init__(self, schema, status_callback, node_execution_callback, execution_folder="."):
        self.network = Network(schema, execution_folder)
        self.queue = queue.Queue()
        self.stop_on_execution_complete = False
        self.status_callback = status_callback
        self.node_execution_callback = node_execution_callback
        self.state = ExecutionState()
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

    def attach_client(self, target_id, client_id, message_callback, client_options):
        self.detach_client(target_id, client_id) # in case a client with the same id is already connected to the target
        client = ExecutionClient(target_id, client_id, message_callback, client_options)
        self.execution_clients[(target_id, client_id)] = client
        if self.et:
            client.connect_execution(self.et)
            self.et.schedule_open_client(target_id, client_id, client_options)
        return lambda *msg: client.send_message(*msg)

    def detach_client(self, target_id, client_id):
        if (target_id, client_id) in self.execution_clients:
            client = self.execution_clients[(target_id, client_id)]
            client.disconnect()
            self.et.schedule_close_client(target_id, client_id)
            del self.execution_clients[(target_id, client_id)]

    def run(self, terminate_on_complete=False):

        self.et = ExecutionThread(self, self.queue, self.network, self.state, injected_inputs=self.injected_inputs, output_listeners=self.output_listeners)
        for (id, client_id) in self.execution_clients:
            client = self.execution_clients[(id, client_id)]
            client.connect_execution(self.et)
            self.et.schedule_open_client(id, client_id, client.get_client_options())

        self.et.start()

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

        return self.wait()

    def start(self):
        self.et = ExecutionThread(self, self.queue, self.network, self.state, injected_inputs=self.injected_inputs, output_listeners=self.output_listeners)
        for (id, client_id) in self.execution_clients:
            client = self.execution_clients[(id, client_id)]
            client.connect_execution(self.et)
            self.et.schedule_open_client(id, client_id, client.get_client_options())

        self.et.start()

        self.stop_on_execution_complete = False

        self.et.schedule_run(False)

        while True:
            notify_fn = self.queue.get()
            if notify_fn is None:
                break
            else:
                notify_fn(self)

    def wait(self):
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
        self.network.add_node(node)
        if self.et:
            self.et.schedule_node_added(node)

    def add_link(self, link):
        self.network.add_link(link)
        if self.et:
            self.et.schedule_link_added(link)

    def get_node(self, node_id):
        return self.network.get_node(node_id)

    def get_link(self, link_id):
        return self.network.get_link(link_id)

    def get_node_ids(self):
        return self.network.get_node_ids()

    def get_link_ids(self):
        return self.network.get_link_ids()

    def recv_node_message(self, node_id, client_id, msg):
        self.et.schedule_recv_message(("node", node_id), client_id, msg)

    def recv_configuration_message(self, package_id, client_id, msg):
        self.et.schedule_recv_message(("configuration", package_id), client_id, msg)

    def remove_node(self, node_id):
        self.network.remove_node(node_id)
        if self.et:
            self.et.schedule_node_removed(node_id)

    def remove_link(self, link_id):
        if self.et:
            self.et.schedule_link_removed(link_id)
        else:
            self.network.remove_link(link_id)

    def clear(self):
        self.network.clear()
        if self.et:
            self.et.schedule_clear()

    def get_inputs_to(self, node_id, input_port_name):
        return self.network.get_inputs_to(node_id, input_port_name)

    def get_outputs_from(self, node_id, output_port_name):
        return self.network.get_outputs_from(node_id, output_port_name)

    def save(self, to_file=None):
        return self.network.save_zip(to_file)

    def save_network_only(self):
        return self.network.save()

    def load_dir(self):
        (added_node_ids, added_link_ids, node_renamings) = self.network.load_dir({})
        for node_id in added_node_ids:
            node = self.network.get_node(node_id)
            if self.et:
                self.et.schedule_node_added(node)
        for link_id in added_link_ids:
            link = self.network.get_link(link_id)
            if self.et:
                self.et.schedule_link_added(link)
        return (added_node_ids, added_link_ids, node_renamings)

    def load_zip(self, f, merging=False):
        (added_node_ids, added_link_ids, node_renamings) = self.network.load_zip(f,merging=merging)
        for node_id in added_node_ids:
            node = self.network.get_node(node_id)
            if self.et:
                self.et.schedule_node_added(node)
        for link_id in added_link_ids:
            link = self.network.get_link(link_id)
            if self.et:
                self.et.schedule_link_added(link)
        return (added_node_ids, added_link_ids, node_renamings)

    def set_metadata(self, metadata):
        self.network.set_metadata(metadata)

    def get_metadata(self):
        return self.network.get_metadata()

    def mark_dirty_from(self, node_id):
        dirty_nodes = self.network.get_node_ids_from(node_id)
        for dirty_node_id in dirty_nodes:
            if dirty_node_id in self.state.node_outputs:
                del self.state.node_outputs[dirty_node_id]

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

    def node_execution_update(self, node_id, node_execution_state, exn_or_result):
        if self.node_execution_callback:
            self.node_execution_callback(node_id, node_execution_state, exn_or_result)
        return False

    def set_execution_complete_callback(self, execution_complete_callback):
        self.execution_complete_callback = execution_complete_callback

    def execution_complete_update(self):
        if self.execution_complete_callback:
            self.execution_complete_callback()
        return self.stop_on_execution_complete



