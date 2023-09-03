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

from hyrrokkin.schema.port import Port
from hyrrokkin.utils.resource_loader import ResourceLoader


class NodeType:

    def __init__(self, metadata, display, input_ports, output_ports, classname, enabled=True):
        self.metadata = metadata
        self.display = display
        self.input_ports = input_ports
        self.output_ports = output_ports
        self.classname = classname
        self.enabled = enabled

    def is_enabled(self):
        return self.enabled

    def get_classname(self):
        return self.classname

    def get_input_ports(self):
        return self.input_ports.items()

    def get_output_ports(self):
        return self.output_ports.items()

    @staticmethod
    def load(from_dict, package_resource_path):
        # classname can be absolute or relative to the package path
        enabled = from_dict.get("enabled", True)
        classname = from_dict.get("classname", None)
        if classname:
            # assume relative first, get the fully qualified backend class name
            fq_classname = package_resource_path + "." + classname

            try:
                cls = ResourceLoader.get_class(fq_classname)
                classname = fq_classname
            except:
                cls = ResourceLoader.get_class(classname)

            # check class has expected attributes
            if not hasattr(cls, "execute"):
                raise Exception(f"Node class {classname} does not have the required execute method")

        return NodeType(metadata=from_dict.get("metadata", {}),
                        display=from_dict.get("display", {}),
                        input_ports={name: Port.load(port_dict) for (name, port_dict) in
                                     from_dict.get("input_ports", {}).items()},
                        output_ports={name: Port.load(port_dict) for (name, port_dict) in
                                      from_dict.get("output_ports", {}).items()},
                        classname=classname, enabled=enabled)
