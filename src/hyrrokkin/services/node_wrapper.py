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

import copy
import logging
import asyncio

class NodeWrapper:

    def __init__(self, executor, network, node_id, services):
        self.executor = executor
        self.network = network
        self.node_id = node_id
        self.instance = None
        self.services = services

        self.configuration = None
        self.logger = logging.getLogger(f"NodeWrapper[{node_id}]")
        self.services.wrapper = self

    def set_instance(self, instance):
        self.instance = instance

    def reset_execution(self):
        try:
            if hasattr(self.instance, "reset_execution"):
                self.instance.reset_execution()
        except:
            self.logger.exception(f"Error in reset_execution for node {self.node_id}")

    async def execute(self, inputs):
        if hasattr(self.instance, "execute"):
            if asyncio.iscoroutinefunction(self.instance.execute):
                return await self.instance.execute(inputs)
            else:
                try:
                    return self.instance.execute(inputs)
                except Exception as ex:
                    print(ex)
                    return {}
        else:
            return {}

    def set_status(self, state, status_message):
        self.executor.notify(lambda executor: executor.status_update(self.node_id, "node", status_message, state))

    def set_property(self, property_name, property_value):
        property_value = copy.deepcopy(property_value)
        self.network.set_node_property(self.node_id, property_name, property_value)

    def get_property(self, property_name):
        return self.network.get_node_property(self.node_id, property_name)

    def open_file(self, path, mode, is_temporary, **kwargs):
        return self.network.open_file(self.node_id, "node", path, mode, is_temporary, **kwargs)

    def set_configuration(self, configuration):
        self.configuration = configuration

    def get_configuration(self):
        return self.configuration

    def recv_message(self, message):
        # to be overriden in sub-class
        pass




