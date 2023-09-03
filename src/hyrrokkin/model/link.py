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


class Link:

    def __init__(self, link_id, from_node_id, from_port_name, to_node_id, to_port_name, link_type):
        self.link_id = link_id
        self.from_node_id = from_node_id
        self.from_port = from_port_name
        self.to_node_id = to_node_id
        self.to_port = to_port_name
        self.link_type = link_type

    def get_link_id(self):
        return self.link_id

    def get_link_type(self):
        return self.link_type

    @staticmethod
    def load(link_id, from_dict):
        (from_node_id, from_port) = from_dict["from_port"].split(":")
        (to_node_id, to_port) = from_dict["to_port"].split(":")
        link_type = from_dict.get("link_type", "")
        return Link(link_id, from_node_id, from_port, to_node_id, to_port, link_type)

    def save(self):
        return {
            "from_port": self.from_node_id + ":" + self.from_port,
            "to_port": self.to_node_id + ":" + self.to_port,
            "link_type": self.link_type
        }
