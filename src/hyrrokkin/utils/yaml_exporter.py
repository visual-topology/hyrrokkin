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

from yaml import dump


def export_to_yaml(from_topology,to_file):

    exported = {
        "metadata":from_topology.get_metadata(),
        "configuration":from_topology.get_package_properties(),
        "nodes":{},
        "links":[]
    }

    node_ids = from_topology.get_node_ids()
    node_types = {}
    for node_id in node_ids:
        node_type,properties = from_topology.get_node(node_id)
        node_types[node_id] = node_type
        exported["nodes"][node_id] = {"type":node_type,"properties":properties}

    link_ids = from_topology.get_link_ids()
    for link_id in link_ids:
        from_node_id,from_port,to_node_id,to_port = from_topology.get_link(link_id)
        from_ports = from_topology.get_output_port_names(from_node_id)
        to_ports = from_topology.get_input_port_names(to_node_id)
        s = from_node_id
        if len(from_ports) > 1:
            s += ":" + from_port
        s += " => "
        s += to_node_id
        if len(to_ports) > 1:
            s += ":" + to_port
        exported["links"].append(s)


    dump(exported,to_file,default_flow_style=False, sort_keys=False)

