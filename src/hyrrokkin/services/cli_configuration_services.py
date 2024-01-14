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
import os.path

from hyrrokkin.utils.data_store_utils import DataStoreUtils

class ConfigurationServices:

    def __init__(self, package_id, working_dir):
        self.package_id = package_id
        self.properties = {}
        self.working_dir = working_dir
        self.temp_dir = os.path.join(self.working_dir,"tmp")
        self.logger = logging.getLogger("package_configuration:" + self.package_id)

    def set_status_info(self, status_message):
        self.logger.info(status_message)

    def set_status_warning(self, status_message):
        self.logger.warning(status_message)

    def set_status_error(self, status_message):
        self.logger.error(status_message)

    def clear_status(self):
        pass

    def get_property(self, property_name, default_value=None):
        dsu = DataStoreUtils(self.working_dir)
        return dsu.get_package_property(self.package_id, property_name)

    def set_property(self, property_name, property_value):
        dsu = DataStoreUtils(self.working_dir)
        dsu.set_package_property(self.package_id, property_name, property_value)

    def get_data(self, key):
        dsu = DataStoreUtils(self.working_dir)
        return dsu.get_package_data(self.package_id, key)

    def set_data(self, key, data):
        dsu = DataStoreUtils(self.working_dir)
        dsu.set_package_data(self.package_id, key, data)
