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

class ConfigurationWrapper:

    def __init__(self, network, package_id, services):
        self.network = network
        self.package_id = package_id
        self.instance = None
        self.services = services
        self.message_handler = None
        self.logger = logging.getLogger(f"ConfigurationWrapper[{package_id}]")

    def set_instance(self, instance):
        self.instance = instance

    def get_instance(self):
        return self.instance

    def set_property(self, property_name, property_value):
        property_value = copy.deepcopy(property_value)
        self.network.set_package_property(self.package_id, property_name, property_value)

    def get_property(self, property_name):
        return self.network.get_package_property(self.package_id, property_name)

    def set_status(self, state, status_message):
        pass

    def open_file(self, path, mode, is_temporary, **kwargs):
        return self.network.open_file(self.package_id, "configuration", path, mode, is_temporary, **kwargs)
