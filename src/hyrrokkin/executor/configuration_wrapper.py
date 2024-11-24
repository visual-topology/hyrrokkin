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

from .wrapper import Wrapper

class ConfigurationWrapper(Wrapper):

    def __init__(self, executor, execution_folder, package_id, services):
        super().__init__(executor, execution_folder)
        self.package_id = package_id
        self.services = services
        self.properties = self.get_datastore_utils().get_package_properties(self.package_id)
        self.message_handler = None
        self.logger = logging.getLogger(f"ConfigurationWrapper[{package_id}]")

    def get_id(self):
        return self.package_id

    def get_type(self):
        return "configuration"

    def __repr__(self):
        return f"ConfigurationWrapper({self.package_id})"

    def get_property(self, property_name, default_value=None):
        return self.properties.get(property_name, default_value)

    def set_property(self, property_name, property_value):
        if property_value is not None:
            self.properties[property_name] = property_value
        else:
            if property_name in self.properties:
                del self.properties[property_name]
        self.get_datastore_utils().set_package_property(self.package_id, property_name, property_value)

    def set_status(self, state, status_message):
        self.execution_engine.set_status(self.package_id, "configuration", status_message, state)

    def get_data(self, key):
        return self.get_datastore_utils().get_package_data(self.package_id, key)

    def set_data(self, key, data):
        return self.get_datastore_utils().set_package_data(self.package_id, key, data)

    def get_configuration_wrapper(self, package_id):
        return self.execution_engine.get_configuration_wrapper(package_id)




