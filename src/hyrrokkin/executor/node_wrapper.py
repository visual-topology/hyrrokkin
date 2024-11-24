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

import logging
import inspect

from .wrapper import Wrapper

class NodeWrapper(Wrapper):

    def __init__(self, execution_engine, execution_folder, node_id, services):
        super().__init__(execution_engine, execution_folder)

        self.node_id = node_id

        self.services = services

        self.properties = self.get_datastore_utils().get_node_properties(self.node_id)

        self.configuration = None
        self.logger = logging.getLogger(f"NodeWrapper[{node_id}]")
        self.services.wrapper = self

    def get_id(self):
        return self.node_id

    def get_type(self):
        return "node"

    def __repr__(self):
        return f"NodeWrapper({self.node_id})"

    def connections_changed(self, input_connection_counts, output_connection_counts):
        try:
            if hasattr(self.instance, "connections_changed"):
                self.instance.connections_changed(input_connection_counts, output_connection_counts)
        except:
            self.logger.exception(f"Error in connections_changed for {str(self)}")

    def reset_execution(self):
        try:
            if hasattr(self.instance, "reset_run"):
                self.instance.reset_run()
        except:
            self.logger.exception(f"Error in reset_execution for node {self.node_id}")

    async def execute(self, inputs):
        # note - any exceptions raised in the node instance's run method will be caught by the caller
        if hasattr(self.instance, "run"):
            if inspect.iscoroutinefunction(self.instance.run):
                return await self.instance.run(inputs)
            else:
                return self.instance.run(inputs)
        else:
            return {}

    def set_status(self, state, status_message):
        self.execution_engine.set_status(self.node_id, "node", status_message, state)

    def set_execution_state(self, execution_state):
        self.execution_engine.set_node_execution_state(self.node_id, execution_state, is_manual=True)

    def request_execution(self):
        self.execution_engine.request_execution(self.node_id)

    def get_property(self, property_name, default_value):
        return self.properties.get(property_name, default_value)

    def set_property(self, property_name, property_value):
        if property_value is not None:
            self.properties[property_name] = property_value
        else:
            if property_name in self.properties:
                del self.properties[property_name]

        self.get_datastore_utils().set_node_property(self.node_id, property_name, property_value)

    def reload_properties(self):
        self.properties = self.get_datastore_utils().get_node_properties(self.node_id)

    def get_data(self, key):
        return self.get_datastore_utils().get_node_data(self.node_id, key)

    def set_data(self, key, data):
        self.get_datastore_utils().set_node_data(self.node_id, key, data)

    def set_configuration_wrapper(self, configuration_wrapper):
        self.configuration_wrapper = configuration_wrapper

    def get_configuration_wrapper(self, package_id):
        return self.configuration_wrapper if package_id is None else self.executor.get_configuration_wrapper(package_id)











