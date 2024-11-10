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
import traceback
import time

from hyrrokkin.executor.node_execution_states import NodeExecutionStates
from hyrrokkin.schema.schema import Schema
from hyrrokkin.utils.resource_loader import ResourceLoader
from hyrrokkin.executor.graph_link import GraphLink
from hyrrokkin.services.node_services import NodeServices
from hyrrokkin.services.node_wrapper import NodeWrapper
from hyrrokkin.services.configuration_services import ConfigurationServices
from hyrrokkin.services.configuration_wrapper import ConfigurationWrapper

def async_exception_safe(func):
    async def wrapper(*args, **kwargs):
        execution_thread = args[0]
        try:
            await func(*args, **kwargs)
        except Exception as ex:
            traceback.print_exception(ex)
            execution_thread.fail()
    return wrapper

class ExecutionThread(threading.Thread):

    def __init__(self, graph_executor, schema, executor_queue, execution_folder, execution_limit=4, injected_inputs={}, output_listeners={}):
        super().__init__()
        self.graph_executor = graph_executor
        self.schema = schema
        self.executor_queue = executor_queue
        self.execution_folder = execution_folder
        self.node_outputs = {}
        self.node_wrappers = {}
        self.configuration_wrappers = {}
        self.execution_limit = execution_limit
        self.injected_inputs = injected_inputs
        self.output_listeners = output_listeners

        # new state
        self.nodes = {}  # node-id = > NodeWrapper
        self.links = {}  # link-id = > GraphLink
        self.out_links = {}  # node-id = > output-port = > [GraphLink]
        self.in_links = {}  # node-id = > input-port = > [GraphLink]

        self.loop = asyncio.new_event_loop()

        self.dirty_nodes = {}  # node-id => True
        self.executing_nodes = {}  # node-id => True
        self.executed_nodes = {} # node-id => True
        self.failed_nodes = {} # node-id => Exception

        self.executing_tasks = set()

        self.lock = threading.Lock()

        self.paused = True
        self.terminate_on_complete = False

        self.completion_callback = None
        self.stopping = False

        self.is_executing = {}
        self.execution_states = {}
        self.statuses = {}

        self.pending_node_clients = {}
        self.pending_configuration_clients = {}
        self.pending_node_messages = {}
        self.pending_configuration_messages = {}

        self.logger = logging.getLogger("ExecutionThread")
        self.__futures = set()
        self.failed = False

    def fail(self):
        self.failed = True
        self.loop.stop()

    def is_failed(self):
        return self.failed or len(self.failed_nodes) > 0

    def handle_loop_exception(self, context):
        self.logger.error("Loop Exception")
        self.logger.error(context)

    def run(self):
        asyncio.set_event_loop(self.loop)
        # self.loop.set_exception_handler(lambda loop, context: self.handle_loop_exception(context))
        self.loop.set_exception_handler(lambda loop, context: print("EXN"))
        self.loop.run_forever()
        self.executor_queue.put(None)

    def pause(self):
        self.paused = True

    async def resume(self):
        self.paused = False
        self.dispatch()

    @async_exception_safe
    async def run_coro(self, terminate_on_complete):
        self.terminate_on_complete = terminate_on_complete
        self.paused = False

        # notify the nodes of their connections
        for node_id in self.nodes:
            self.notify_connection_counts(node_id)
        #
        # # for nodes that do not have any outputs from the previous execution
        # for node_id in all_node_ids:
        #     self.dirty_nodes[node_id] = True
        #     self.reset_execution(node_id)

        self.dispatch()

    def stop_executor(self):
        if self.stopping:
            return
        self.stopping = True

        self.loop.call_soon(self.loop.stop)

    async def stop_executor_coro(self):
        self.stop_executor()

    @async_exception_safe
    async def package_added(self,package):
        package_id = package.get_id()
        self.register_package(package_id, package)

    @async_exception_safe
    async def node_added(self, node, loading=False):
        node_id = node.get_node_id()
        self.nodes[node_id] = node
        self.register_node(node_id)
        self.mark_dirty(node_id)
        if not loading:
            self.notify_connection_counts(node_id)
            self.dispatch()
            print("node added")

    @async_exception_safe
    async def node_removed(self, node_id):
        if node_id in self.node_wrappers:
            del self.node_wrappers[node_id]
        if node_id in self.node_outputs:
            del self.node_outputs[node_id]
        if node_id in self.dirty_nodes:
            del self.dirty_nodes[node_id]
        if node_id in self.in_links:
            del self.in_links[node_id]
        if node_id in self.out_links:
            del self.out_links[node_id]
        if node_id in self.nodes:
            del self.nodes[node_id]

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

    @async_exception_safe
    async def link_added(self, link, loading=False):
        graph_link = GraphLink(self, link.from_node_id,link.from_port,link.to_node_id,link.to_port)
        self.links[link.get_link_id()] = graph_link
        if link.to_node_id not in self.in_links:
            self.in_links[graph_link.to_node_id] = defaultdict(list)
        self.in_links[graph_link.to_node_id][link.to_port].append(graph_link)
        if link.from_node_id not in self.out_links:
            self.out_links[graph_link.from_node_id] = defaultdict(list)
        self.out_links[graph_link.from_node_id][link.from_port].append(graph_link)

        if not loading:
            self.mark_dirty(link.to_node_id)
            self.notify_connection_counts(graph_link.to_node_id)
            self.notify_connection_counts(graph_link.from_node_id)
            self.dispatch()
            print("link added")

    @async_exception_safe
    async def link_removed(self, link_id):
        link = self.links[link_id]

        self.in_links[link.to_node_id][link.to_port].remove(link)
        self.out_links[link.from_node_id][link.from_port].remove(link)
        del self.links[link_id]

        self.notify_connection_counts(link.to_node_id)
        self.notify_connection_counts(link.from_node_id)

        self.mark_dirty(link.to_node_id)
        self.dispatch()

    def notify_connection_counts(self, node_id):
        try:
            if node_id in self.node_wrappers:
                input_connection_counts = {}
                output_connection_counts = {}
                in_links = self.in_links.get(node_id,{})
                for port in in_links:
                    input_connection_counts[port] = len(in_links[port])
                out_links = self.out_links.get(node_id, {})
                for port in out_links:
                    output_connection_counts[port] = len(out_links[port])

                self.node_wrappers[node_id].connections_changed(input_connection_counts,output_connection_counts)
        except:
            self.logger.exception("notify_connection_counts")

    async def clear(self):
        pass # TODO

    @async_exception_safe
    async def request_execution_coro(self, node_id):
        self.request_execution(node_id)

    @async_exception_safe
    async def open_client(self, target_id, client_id, client_options, client_service_class):
        (target_type, _) = target_id
        if target_type == "node":
            node_id = target_id[1]
            wrapper = self.node_wrappers.get(node_id,None)
            pending = self.pending_node_clients
        elif target_type == "configuration":
            package_id = target_id[1]
            wrapper = self.configuration_wrappers.get(package_id, None)
            pending = self.pending_configuration_clients
        else:
            self.logger.error(f"invalid target_id: {target_id}")
            return
        if wrapper:
            wrapper.open_client(client_id, client_options, client_service_class)
        else:
            node_or_package_id = target_id[1]
            if node_or_package_id not in pending:
                pending[node_or_package_id] = []
            pending[node_or_package_id].append((client_id,client_options,client_service_class))

    @async_exception_safe
    async def recv_message(self, target_id, client_id, *msg):
        (target_type, _) = target_id

        if target_type == "node":
            node_id = target_id[1]
            wrapper = self.node_wrappers.get(node_id,None)
            pending = self.pending_node_messages
        elif target_type == "configuration":
            package_id = target_id[1]
            wrapper = self.configuration_wrappers.get(package_id,None)
            pending = self.pending_configuration_messages
        else:
            self.logger.error(f"invalid target_id: {target_id}")
            return

        if wrapper:
            wrapper.recv_message(client_id, *msg)
        else:
            node_or_package_id = target_id[1]
            if node_or_package_id not in pending:
                pending[node_or_package_id] = []
            pending[node_or_package_id].append((client_id,msg))

    @async_exception_safe
    async def close_client(self, target_id, client_id):
        (target_type, _) = target_id

        if target_type == "node":
            node_id = target_id[1]
            wrapper = self.node_wrappers.get(node_id, None)
            pending = self.pending_node_messages
        elif target_type == "configuration":
            package_id = target_id[1]
            wrapper = self.configuration_wrappers.get(package_id, None)
            pending = self.pending_configuration_messages
        else:
            self.logger.error(f"invalid target_id: {target_id}")
            return

        if wrapper:
            wrapper.close_client(client_id)

        node_or_package_id = target_id[1]
        if node_or_package_id in pending:
            if client_id in pending[node_or_package_id]:
                pending[node_or_package_id].remove(client_id)

    def register_node(self, node_id):
        node = self.nodes[node_id]
        node_type_name = node.get_node_type()
        node_id = node.get_node_id()
        node_type = self.schema.get_node_type(node_type_name)
        (package_id, _) = Schema.split_descriptor(node_type_name)

        services = NodeServices(node_id)
        node_wrapper = NodeWrapper(self.graph_executor, self.execution_folder, node_id, services)
        if package_id in self.configuration_wrappers:
            node_wrapper.set_configuration_wrapper(self.configuration_wrappers[package_id])
        classname = node_type.get_classname()
        cls = ResourceLoader.get_class(classname)
        try:
            instance = cls(services)
            node_wrapper.set_instance(instance)
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

    def register_package(self, package_id, package):
        package_configuration = package.get_configuration()
        if "classname" in package_configuration:
            classname = package_configuration["classname"]

            services = ConfigurationServices(package_id)
            configuration_wrapper = ConfigurationWrapper(self.graph_executor, self.execution_folder, package_id, services)

            services.set_wrapper(configuration_wrapper)
            cls = ResourceLoader.get_class(classname)
            instance = cls(services)
            configuration_wrapper.set_instance(instance)
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
        if self.paused or self.stopping:
            return

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
            self.executor_queue.put(lambda e: e.execution_complete_update())
            if self.terminate_on_complete:
                self.stop_executor()
            return

    def can_execute(self, node_id):
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

    @async_exception_safe
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

    def schedule_package_added(self, package):
        asyncio.run_coroutine_threadsafe(self.package_added(package), self.loop)

    def schedule_node_added(self, node, loading=False):
        asyncio.run_coroutine_threadsafe(self.node_added(node, loading), self.loop)

    def schedule_node_removed(self, node_id):
        asyncio.run_coroutine_threadsafe(self.node_removed(node_id), self.loop)

    def schedule_link_added(self, link, loading=False):
        asyncio.run_coroutine_threadsafe(self.link_added(link, loading), self.loop)

    def schedule_link_removed(self, link_id):
        asyncio.run_coroutine_threadsafe(self.link_removed(link_id), self.loop)

    def schedule_open_client(self, target_id, client_id, client_options, client_service_class):
        asyncio.run_coroutine_threadsafe(self.open_client(target_id, client_id, client_options, client_service_class), self.loop)

    def schedule_recv_message(self, target_id, client_id, *msg):
        asyncio.run_coroutine_threadsafe(self.recv_message(target_id, client_id, *msg), self.loop)

    def schedule_close_client(self, node_id, client_id):
        asyncio.run_coroutine_threadsafe(self.close_client(node_id, client_id), self.loop)

    def schedule_request_node_execution(self, node_id):
        asyncio.run_coroutine_threadsafe(self.request_execution_coro(node_id), self.loop)

    def schedule_run(self, terminate_on_complete):
        asyncio.run_coroutine_threadsafe(self.run_coro(terminate_on_complete), self.loop)

    def schedule_resume(self):
        asyncio.run_coroutine_threadsafe(
            self.resume(),
            self.loop)

    def schedule_stop_executor(self):
        asyncio.run_coroutine_threadsafe(self.stop_executor_coro(), self.loop)

    def schedule_clear(self):
        asyncio.run_coroutine_threadsafe(self.clear(), self.loop)

    def reset_execution(self, node_id):
        self.node_wrappers[node_id].reset_execution()

    # called in the loop from node
    def request_execution(self, node_id):
        self.mark_dirty(node_id)
        self.dispatch()

    def set_status(self, node_id, state, message):
        self.statuses[node_id] = [state, message]
        if self.graph_executor.status_callback:
            self.executor_queue.put(lambda graph_executor: graph_executor.status_update(node_id, message, state))

    def set_node_execution_state(self, node_id, execution_state, exn=None, is_manual=False):
        at_time = time.time()
        if self.graph_executor.node_execution_callback:
            self.executor_queue.put(lambda graph_executor: graph_executor.node_execution_update(at_time, node_id, execution_state, exn, is_manual))

    def send_node_message(self, node_id, client_id, *msg):
        self.executor_queue.put(lambda graph_executor: graph_executor.message_update(node_id, client_id, *msg))

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

    def close(self):
        for node_id in self.node_wrappers:
            self.node_wrappers[node_id].close()

        self.node_wrappers = {}

        for package_id in self.configuration_wrappers:
            self.configuration_wrappers[package_id].close()

        self.configuration_wrappers = {}








