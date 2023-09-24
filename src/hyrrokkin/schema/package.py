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

from hyrrokkin.schema.node_type import NodeType
from hyrrokkin.schema.link_type import LinkType
from hyrrokkin.utils.resource_loader import ResourceLoader


class Package:

    def __init__(self, id, metadata, display, node_types, link_types, configuration):
        self.id = id
        self.metadata = metadata
        self.display = display
        self.node_types = node_types
        self.link_types = link_types
        self.configuration = configuration

    def get_node_types(self):
        return self.node_types

    def get_link_types(self):
        return self.link_types

    def get_id(self):
        return self.id

    def get_metadata(self):
        return self.metadata

    def get_node_type(self, node_type_id):
        return self.node_types[node_type_id]

    def get_configuration(self):
        return self.configuration

    def save(self):
        return {
            "id": self.id,
            "metadata": self.metadata,
            "display": self.display,
            "node_types": [
                node_type.save(id) for (id, node_type) in self.node_types.items()
            ],
            "link_types": [
                link_type.save(id) for (id, link_type) in self.link_types.items()
            ],
            "configuration": self.configuration
        }

    @staticmethod
    def load(from_dict, package_resource_path):
        node_types = from_dict.get("node_types", {})
        node_types = {id: NodeType.load(node_type_dict, package_resource_path) for (id, node_type_dict) in
                      node_types.items()}
        node_types = {id: nt for (id, nt) in node_types.items() if nt.is_enabled()}

        link_types = from_dict.get("link_types", {})
        if isinstance(link_types, list):
            link_types = {link_type["id"]: LinkType.load(link_type) for link_type in link_types}
        else:
            link_types = {id: LinkType.load(link_type_dict) for (id, link_type_dict) in link_types.items()}

        configuration = from_dict.get("configuration", {})

        if "classname" in configuration:
            # assume relative first, get the fully qualified backend class name
            fq_classname = package_resource_path + "." + configuration["classname"]

            try:
                cls = ResourceLoader.get_class(fq_classname)
                configuration["classname"] = fq_classname
            except Exception as ex:
                print(ex)
                pass

        return Package(
            from_dict["id"],
            from_dict.get("metadata", {}),
            from_dict.get("display", {}),
            node_types,
            link_types,
            configuration
        )
