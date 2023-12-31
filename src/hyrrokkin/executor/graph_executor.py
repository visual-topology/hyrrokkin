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
from hyrrokkin.services.node_services import NodeServices
from hyrrokkin.services.node_wrapper import NodeWrapper
from hyrrokkin.services.configuration_services import ConfigurationServices
from hyrrokkin.services.configuration_wrapper import ConfigurationWrapper

from hyrrokkin.utils.resource_loader import ResourceLoader
from hyrrokkin.executor.execution_thread import ExecutionThread
from hyrrokkin.executor.execution_state import ExecutionState


def default_node_factory(executor, network, node_id):
    services = NodeServices(node_id)
    wrapper = NodeWrapper(executor, network, node_id, services)
    return (services, wrapper)


def default_configuration_factory(executor, network, package_id):
    services = ConfigurationServices(package_id)
    wrapper = ConfigurationWrapper(executor, network, package_id, services)
    return (services, wrapper)


class GraphExecutor:

    def __init__(self, schema, message_callback, status_callback, node_execution_callback, execution_complete_callback,
                 execution_folder=".", node_factory=default_node_factory, configuration_factory=default_configuration_factory):
        self.network = Network(schema, execution_folder)
        self.queue = queue.Queue()
        self.stop_on_execution_complete = False
        self.message_callback = message_callback
        self.status_callback = status_callback
        self.node_execution_callback = node_execution_callback
        self.execution_complete_callback = execution_complete_callback
        self.node_factory = node_factory
        self.configuration_factory = configuration_factory
        self.et = None
        self.state = ExecutionState()
        self.paused = False

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

    def run(self, terminate_on_complete=False, execute_to_nodes="*", cache_outputs_for_nodes="*"):

        self.et = ExecutionThread(self, self.queue, self.network, self.node_factory, self.configuration_factory, self.state)
        self.et.start()

        self.stop_on_execution_complete = terminate_on_complete

        self.et.schedule_run(terminate_on_complete, execute_to_nodes=execute_to_nodes, cache_outputs_for_nodes=cache_outputs_for_nodes)

        while True:
            notify_fn = self.queue.get()
            if notify_fn is None:
                break
            request_stop = notify_fn(self)
            if request_stop:
                break

        self.et.join()
        self.et.loop.close()
        self.et = None

    def create_instance_for_configuration(self, package_id, classname):
        if package_id not in self.state.configuration_wrappers:
            (services, configuration_wrapper) = self.configuration_factory(self, self.network, package_id)
            services.set_wrapper(configuration_wrapper)
            cls = ResourceLoader.get_class(classname)
            instance = cls(services)
            configuration_wrapper.set_instance(instance)
            self.state.configuration_wrappers[package_id] = configuration_wrapper

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

    def recv_node_message(self, node_id, content):
        self.et.schedule_recv_node_message(node_id, content)

    def recv_configuration_message(self, package_id, content):
        self.et.schedule_recv_configuration_message(package_id, content)

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
        (added_node_ids, added_link_ids) = self.network.load_dir()
        for node_id in added_node_ids:
            node = self.network.get_node(node_id)
            if self.et:
                self.et.schedule_node_added(node)
        for link_id in added_link_ids:
            link = self.network.get_link(link_id)
            if self.et:
                self.et.schedule_link_added(link)

    def load_zip(self, f):
        (added_node_ids, added_link_ids) = self.network.load_zip(f)
        for node_id in added_node_ids:
            node = self.network.get_node(node_id)
            if self.et:
                self.et.schedule_node_added(node)
        for link_id in added_link_ids:
            link = self.network.get_link(link_id)
            if self.et:
                self.et.schedule_link_added(link)

    def set_metadata(self, metadata):
        self.network.set_metadata(metadata)

    def get_metadata(self):
        return self.network.get_metadata()

    def set_package_configuration(self, package_id, properties):
        for (name, value) in properties.items():
            self.network.set_package_property(package_id, name, value)

    def set_node_property(self, node_id, property_name, property_value):
        self.network.set_node_property(node_id, property_name, property_value)
        dirty_nodes = self.network.get_node_ids_from(node_id)
        for dirty_node_id in dirty_nodes:
            if dirty_node_id in self.state.node_outputs:
                del self.state.node_outputs[dirty_node_id]

    def get_node_property(self, node_id, property_name):
        return self.network.get_node_property(node_id, property_name)

    def set_package_property(self, package_id, property_name, property_value):
        self.network.set_package_property(package_id, property_name, property_value)

    def get_package_properties(self):
        return self.network.get_package_properties()

    def request_node_execution(self, node_id):
        self.et.schedule_request_node_execution(node_id)

    # notifications from execution

    def notify(self, notify_fn):
        self.queue.put(notify_fn)

    def message_update(self, target_id, target_type, content, for_session_id=None, except_session_id=None):
        if self.message_callback:
            self.message_callback(target_id, target_type, content,for_session_id,except_session_id)
        return False

    def status_update(self, target_id, target_type, message, status):
        if self.status_callback:
            self.status_callback(target_id, target_type, message, status)
        return False

    def node_execution_update(self, node_id, node_execution_state):
        if self.node_execution_callback:
            self.node_execution_callback(node_id, node_execution_state)
        return False

    def execution_complete_update(self):
        if self.execution_complete_callback:
            self.execution_complete_callback()
        return self.stop_on_execution_complete



