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

class NodeServices:

    def __init__(self, node_id: str, working_dir, configuration=None):
        self.node_id = node_id
        self.configuration = configuration
        self.properties = {}
        self.logger = logging.getLogger("node:" + self.node_id)
        self.working_dir = working_dir
        self.temp_dir = os.path.join(self.working_dir,"tmp")

    def get_node_id(self):
        return self.node_id

    def set_status_info(self, status_message):
        self.logger.info(status_message)

    def set_status_warning(self, status_message):
        self.logger.warning(status_message)

    def set_status_error(self, status_message):
        self.logger.error(status_message)

    def clear_status(self):
        pass

    def raise_execution_failed(self, message, from_exn=None):
        exn = RuntimeError(self.node_id + ": " + message)
        if from_exn:
            raise exn from from_exn
        else:
            raise exn

    def get_property(self, property_name, default_value=None):
        return self.properties.get(property_name, default_value)

    def set_property(self, property_name, property_value):
        self.properties[property_name] = property_value

    def open_file(self, path, mode="r", is_temporary=False, **kwargs):
        path = os.path.join(self.temp_dir if is_temporary else self.working_dir,"files","node",self.node_id,path)
        folder = os.path.split(path)[0]
        os.makedirs(folder,exist_ok=True)
        return open(path, mode=mode, **kwargs)

    def get_configuration(self):
        return self.configuration


