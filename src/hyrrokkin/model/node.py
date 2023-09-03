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

class Node:

    def __init__(self, node_id, node_type, x, y, metadata, properties):
        self.x = x
        self.y = y
        self.node_id = node_id
        self.node_type = node_type
        self.metadata = metadata
        self.properties = properties

    def get_node_id(self):
        return self.node_id

    def move_to(self, x, y):
        self.x = x
        self.y = y

    def get_node_type(self):
        return self.node_type

    def get_metadata(self):
        return self.metadata

    def get_xy(self):
        return (self.x, self.y)

    def update_metadata(self, metadata):
        self.metadata = metadata

    def set_properties(self, properties):
        self.properties = properties

    def get_properties(self):
        return self.properties

    def set_property(self, property_name, property_value):
        if property_value is None:
            if property_name in self.properties:
                del self.properties[property_name]
        else:
            self.properties[property_name] = property_value

    def get_property(self, property_name):
        return self.properties.get(property_name, None)

    @staticmethod
    def load(node_id, node_type, from_dict={}):
        x = from_dict.get("x", None)
        y = from_dict.get("y", None)
        metadata = from_dict.get("metadata", None)
        properties = from_dict.get("properties", None)
        return Node(node_id, node_type, x, y, metadata, properties)

    def save(self):
        return {"x": self.x, "y": self.y, "node_type": self.node_type, "metadata": self.metadata,
                "properties": self.properties}
