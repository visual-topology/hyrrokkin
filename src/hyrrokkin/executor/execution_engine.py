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

import asyncio
import threading
import logging
from collections import defaultdict
import time

from hyrrokkin.executor.node_execution_states import NodeExecutionStates
from hyrrokkin.utils.resource_loader import ResourceLoader

from .graph_link import GraphLink
from .node_services import NodeServices
from .node_wrapper import NodeWrapper
from .configuration_services import ConfigurationServices
from .configuration_wrapper import ConfigurationWrapper

class ExecutionEngine():

    def __init__(self, classmap, execution_folder, execution_limit=4,
                 injected_inputs={}, output_listeners={},
                 execution_complete_callback=None,
                 status_callback=None,
                 node_execution_callback=None,
                 message_callback=None):
        super().__init__()

        self.classmap = classmap

        self.execution_folder = execution_folder
        self.node_outputs = {}
        self.node_wrappers = {}
        self.configuration_wrappers = {}
        self.execution_limit = execution_limit
        self.injected_inputs = injected_inputs
        self.output_listeners = output_listeners
        self.execution_complete_callback = execution_complete_callback
        self.status_callback = status_callback
        self.node_execution_callback = node_execution_callback
        self.message_callback = message_callback

        # new state
        self.node_types = {}  # node-id = > node-type-id
        self.links = {}  # link-id = > GraphLink
        self.out_links = {}  # node-id = > output-port = > [GraphLink]
        self.in_links = {}  # node-id = > input-port = > [GraphLink]

        self.pending_connection_counts = set() # node-id

        self.dirty_nodes = {}  # node-id => True
        self.executing_nodes = {}  # node-id => True
        self.executed_nodes = {} # node-id => True
        self.failed_nodes = {} # node-id => Exception

        self.executing_tasks = set()

        self.lock = threading.Lock()

        self.paused = True
        self.terminate_on_complete = False

        self.is_executing = {}
        self.execution_states = {}

        self.pending_node_clients = {}
        self.pending_configuration_clients = {}
        self.pending_node_messages = {}
        self.pending_configuration_messages = {}

        self.logger = logging.getLogger("ExecutionThread")

        self.failed = False

    def pause(self):
        self.paused = True
        print("paused")

    def resume(self):
        self.paused = False
        print("resumed")
        self.dispatch()

    async def run_coro(self, terminate_on_complete):
        self.terminate_on_complete = terminate_on_complete
        self.paused = False

        #
        # # for nodes that do not have any outputs from the previous execution
        # for node_id in all_node_ids:
        #     self.dirty_nodes[node_id] = True
        #     self.reset_execution(node_id)

        self.dispatch()

    async def add_package(self,package_id):
        await self.register_package(package_id)

    async def add_node(self, node_id, node_type_id, loading=False):
        await self.register_node(node_id, node_type_id)
        self.mark_dirty(node_id)
        if not loading:
            self.dispatch()
        else:
            self.pending_connection_counts.add(node_id)

    async def remove_node(self, node_id):
        if node_id in self.node_wrappers:
            del self.node_wrappers[node_id]
        if node_id in self.node_outputs:
            del self.node_outputs[node_id]
        if node_id in self.dirty_nodes:
            del self.dirty_nodes[node_id]
        if node_id in self.failed_nodes:
            del self.failed_nodes[node_id]
        if node_id in self.in_links:
            del self.in_links[node_id]
        if node_id in self.out_links:
            del self.out_links[node_id]
        if node_id in self.node_types:
            del self.node_types[node_id]

    def get_outputs_from(self, output_node_id):
        input_node_ports = []
        node_out_links = self.out_links.get(output_node_id, {})
        for (output_port, link_list) in node_out_links.items():
            for link in link_list:
                input_node_ports.append((link.to_node_id, link.to_port))
        return input_node_ports

    def get_inputs_to(self, input_node_id):
        output_node_ports = []
        node_in_links = self.in_links.get(input_node_id, {})
        for (input_port, link_list) in node_in_links.items():
            for link in link_list:
                output_node_ports.append((link.from_node_id, link.from_port))
        return output_node_ports

    async def add_link(self, link_id, from_node_id, from_port, to_node_id, to_port, loading=False):
        graph_link = GraphLink(self,from_node_id,from_port,to_node_id,to_port)
        self.links[link_id] = graph_link
        if to_node_id not in self.in_links:
            self.in_links[to_node_id] = defaultdict(list)
        self.in_links[to_node_id][to_port].append(graph_link)
        if from_node_id not in self.out_links:
            self.out_links[from_node_id] = defaultdict(list)
        self.out_links[from_node_id][from_port].append(graph_link)

        if not loading:
            self.mark_dirty(to_node_id)
            self.dispatch()

    async def remove_link(self, link_id):
        link = self.links[link_id]

        self.in_links[link.to_node_id][link.to_port].remove(link)
        self.out_links[link.from_node_id][link.from_port].remove(link)
        del self.links[link_id]

        self.mark_dirty(link.to_node_id)
        self.dispatch()

    async def clear(self):
        pass # TODO

    async def request_execution_coro(self, node_id):
        self.request_execution(node_id)

    async def open_client(self, target_id, target_type, client_id, client_options, client_service_class):
        if target_type == "node":
            wrapper = self.node_wrappers.get(target_id,None)
            pending = self.pending_node_clients
        elif target_type == "configuration":
            wrapper = self.configuration_wrappers.get(target_id, None)
            pending = self.pending_configuration_clients
        else:
            self.logger.error(f"invalid target_id: {target_id}")
            return

        if wrapper:
            wrapper.open_client(client_id, client_options, client_service_class)
        else:
            if target_id not in pending:
                pending[target_id] = []
            pending[target_id].append((client_id,client_options,client_service_class))

    async def recv_message(self, target_id, target_type, client_id, *msg):
        if target_type == "node":
            wrapper = self.node_wrappers.get(target_id,None)
            pending = self.pending_node_messages
        elif target_type == "configuration":
            wrapper = self.configuration_wrappers.get(target_id,None)
            pending = self.pending_configuration_messages
        else:
            self.logger.error(f"invalid target_type: {target_type}")
            return

        if wrapper:
            wrapper.recv_message(client_id, *msg)
        else:
            if target_id not in pending:
                pending[target_id] = []
            pending[target_id].append((client_id,msg))

    async def close_client(self, target_id, target_type, client_id):
        if target_type == "node":
            wrapper = self.node_wrappers.get(target_id, None)
            pending = self.pending_node_messages
        elif target_type == "configuration":
            wrapper = self.configuration_wrappers.get(target_id, None)
            pending = self.pending_configuration_messages
        else:
            self.logger.error(f"invalid target_type: {target_type}")
            return

        if wrapper:
            wrapper.close_client(client_id)

        if target_id in pending:
            if client_id in pending[target_id]:
                pending[target_id].remove(client_id)

    async def register_node(self, node_id, node_type_id):
        (package_id, node_type_id) = node_type_id.split(":")
        services = NodeServices(node_id)
        node_wrapper = NodeWrapper(self, self.execution_folder, node_id, services)
        if package_id in self.configuration_wrappers:
            node_wrapper.set_configuration_wrapper(self.configuration_wrappers[package_id])
        classname = self.classmap[package_id]["nodes"][node_type_id]
        cls = ResourceLoader.get_class(classname)
        try:
            instance = cls(services)
            node_wrapper.set_instance(instance)
            await node_wrapper.load()
        except Exception as ex:
            print(ex)

        self.node_wrappers[node_id] = node_wrapper

        self.is_executing[node_id] = 0
        # self.set_node_execution_state(node_id, NodeExecutionStates.pending.value)

        if node_id in self.pending_node_clients:
            for (client_id, client_options, client_service_class) in self.pending_node_clients[node_id]:
               node_wrapper.open_client(client_id, client_options, client_service_class)
            del self.pending_node_clients[node_id]

        if node_id in self.pending_node_messages:
            for (client_id, msg) in self.pending_node_messages[node_id]:
                node_wrapper.recv_message(client_id, *msg)
            del self.pending_node_messages[node_id]

    async def register_package(self, package_id):
        classname = self.classmap.get(package_id,{}).get("configuration","")
        if not classname:
            return

        services = ConfigurationServices(package_id)
        configuration_wrapper = ConfigurationWrapper(self, self.execution_folder, package_id, services)

        services.set_wrapper(configuration_wrapper)
        cls = ResourceLoader.get_class(classname)
        instance = cls(services)
        configuration_wrapper.set_instance(instance)
        await configuration_wrapper.load()

        self.configuration_wrappers[package_id] = configuration_wrapper

        if package_id in self.pending_configuration_clients:
            for (client_id, client_options, client_service_class) in self.pending_configuration_clients[package_id]:
                configuration_wrapper.open_client(client_id, client_options, client_service_class)
            del self.pending_configuration_clients[package_id]

        if package_id in self.pending_configuration_messages:
            for (client_id, msg) in self.pending_configuration_messages[package_id]:
                configuration_wrapper.recv_message(client_id, *msg)
            del self.pending_configuration_messages[package_id]

    def executing_node_count(self):
        return len(self.executing_nodes)

    def mark_dirty(self, node_id):

        if node_id in self.dirty_nodes:
            return

        self.dirty_nodes[node_id] = True

        if node_id in self.executed_nodes:
            del self.executed_nodes[node_id]
        if node_id in self.failed_nodes:
            del self.failed_nodes[node_id]

        self.set_node_execution_state(node_id, NodeExecutionStates.pending.value)
        self.reset_execution(node_id)

        # mark all downstream nodes as dirty

        outputs = self.get_outputs_from(node_id)
        for (to_node_id, _) in outputs:
            self.mark_dirty(to_node_id)

    def dispatch(self):
        if self.paused:
            return

        self.pending_connection_counts = set()

        launch_nodes = []
        launch_limit = (self.execution_limit - self.executing_node_count())

        if launch_limit > 0:
            for node_id in self.dirty_nodes:
                if self.can_execute(node_id):
                    launch_nodes.append(node_id)

                if len(launch_nodes) >= launch_limit:
                    break

        for node_id in launch_nodes:
            del self.dirty_nodes[node_id]
            self.executing_nodes[node_id] = True
            task = asyncio.create_task(self.execute(node_id))
            task.add_done_callback(self.executing_tasks.discard)
            self.executing_tasks.add(task)

        if len(self.executing_nodes) == 0:
            if self.execution_complete_callback:
                self.execution_complete_callback()

    def can_execute(self, node_id):
        if node_id in self.executing_nodes:
            return False
        for (output_node_id, output_port) in self.get_inputs_to(node_id):
            if output_node_id not in self.executed_nodes:
                return False
        return True

    def pre_execute(self, node_id):
        inputs = {}
        # collect together the input values at each input port
        # start with output values from connected ports
        in_links = self.in_links.get(node_id, {})
        for input_port_name in in_links:
            inputs[input_port_name] = []
            for link in in_links[input_port_name]:
                inputs[input_port_name].append(link.get_value())

        # add in any injected input values
        for (injected_node_id, injected_input_port_name) in self.injected_inputs:
            if injected_node_id == node_id:
                if injected_input_port_name not in inputs:
                    inputs[injected_input_port_name] = []
                injected_value = self.injected_inputs[(injected_node_id,injected_input_port_name)]
                inputs[injected_input_port_name].append(injected_value)

        return inputs

    async def execute(self, node_id):
        inputs = self.pre_execute(node_id)
        try:
            node_wrapper = self.node_wrappers[node_id]
            node_wrapper.reload_properties()
            self.set_node_execution_state(node_id, NodeExecutionStates.executing.value)
            results = await node_wrapper.execute(inputs)
            if results is None:
                results = {}
            self.set_node_execution_state(node_id, NodeExecutionStates.executed.value)
            self.post_execute(node_id, results, None)
        except Exception as ex:
            self.set_node_execution_state(node_id, NodeExecutionStates.failed.value, ex)
            self.post_execute(node_id, None, ex)

        self.dispatch()

    def post_execute(self, node_id, result, exn):
        if node_id in self.executing_nodes:
            del self.executing_nodes[node_id]
        if node_id in self.node_outputs:
            del self.node_outputs[node_id]
        if exn is not None:
            self.failed_nodes[node_id] = exn
        else:
            self.executed_nodes[node_id] = True
        if result is not None:
            self.node_outputs[node_id] = {}

            for port_name in result:
                self.node_outputs[node_id][port_name] = result[port_name]

            for port_name in result:
                if (node_id, port_name) in self.output_listeners:
                    self.output_listeners[(node_id,port_name)](result[port_name])


    def reset_execution(self, node_id):
        self.node_wrappers[node_id].reset_execution()

    # called in the loop from node
    def request_execution(self, node_id):
        self.mark_dirty(node_id)
        self.dispatch()

    def get_node_property(self, node_id, property_name):
        if node_id in self.node_wrappers:
            return self.node_wrappers[node_id].get_property(property_name)
        else:
            return None

    def set_node_property(self, node_id, property_name, property_value):
        if node_id in self.node_wrappers:
            self.node_wrappers[node_id].set_property(property_name, property_value)

    def get_package_property(self, package_id, property_name):
        if package_id in self.configuration_wrappers:
            return self.configuration_wrappers[package_id].get_property(property_name)
        else:
            return None

    def set_package_property(self, package_id, property_name, property_value):
        if package_id in self.configuration_wrappers:
            self.configuration_wrappers[package_id].set_property(property_name, property_value)

    def get_configuration_wrapper(self, package_id):
        return self.configuration_wrappers.get(package_id,None)

    def set_status(self, origin_id, origin_type, state, message):
        if self.status_callback:
            self.status_callback(origin_id, origin_type, message, state)

    def set_node_execution_state(self, node_id, execution_state, exn=None, is_manual=False):
        at_time = time.time()
        if self.node_execution_callback:
            self.node_execution_callback(at_time, node_id, execution_state, exn, is_manual)

    def send_message(self, origin_id, origin_type, client_id, *msg):
        if self.message_callback:
            self.message_callback(origin_id, origin_type, client_id, *msg)

    def count_failed(self):
        return len(self.failed_nodes)

    def close(self):
        for node_id in self.node_wrappers:
            self.node_wrappers[node_id].close()

        self.node_wrappers = {}

        for package_id in self.configuration_wrappers:
            self.configuration_wrappers[package_id].close()

        self.configuration_wrappers = {}








