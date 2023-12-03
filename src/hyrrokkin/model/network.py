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
import os.path
from copy import deepcopy
import zipfile
import json
from threading import RLock
import io
import tempfile
import shutil

from hyrrokkin.model.node import Node as Node
from hyrrokkin.model.link import Link as Link


class Network:

    def __init__(self, schema, savedir):
        self.schema = schema
        self.savedir = savedir
        self.nodes = {}
        self.links = {}
        self.metadata = {}
        self.package_properties = {}
        self.logger = logging.getLogger("network")
        self.lock = RLock()
        self.tempdir = None

    def __del__(self):
        if self.tempdir is not None:
            try:
                shutil.rmtree(self.tempdir)
            except:
                self.logger.exception(f"Unable to remove directory {self.tempdir} after deleting network")

    def get_schema(self):
        return self.schema

    def add_node(self, node):
        with self.lock:
            node_id = node.get_node_id()
            self.nodes[node_id] = node
            self.__save_dir()

    def move_node(self, node_id, x, y):
        with self.lock:
            self.nodes[node_id].move_to(x, y)
            self.__save_dir()

    def get_node(self, node_id):
        with self.lock:
            return self.nodes.get(node_id, None)

    def get_node_ids(self, traversal_order=None):
        with self.lock:
            if traversal_order is None:
                return list(self.nodes.keys())
            else:
                ordered_node_ids = []
                node_ids = list(self.nodes.keys())
                while len(node_ids):
                    for node_id in node_ids:
                        schedule = True
                        for link in self.links.values():
                            if link.to_node_id == node_id and link.from_node_id not in ordered_node_ids:
                                schedule = False
                                break
                        if schedule:
                            ordered_node_ids.append(node_id)
                            node_ids.remove(node_id)
                if traversal_order == False:
                    ordered_node_ids.reverse()
                return ordered_node_ids

    def get_node_ids_to(self, node_id):
        with self.lock:
            pred_node_ids = {node_id}
            for link in self.links.values():
                if link.to_node_id == node_id:
                    node_ids = self.get_node_ids_to(link.from_node_id)
                    for pred_node_id in node_ids:
                        pred_node_ids.add(pred_node_id)
            return list(pred_node_ids)

    def get_node_ids_from(self, node_id):
        with self.lock:
            succ_node_ids = {node_id}
            for link in self.links.values():
                if link.from_node_id == node_id:
                    node_ids = self.get_node_ids_from(link.to_node_id)
                    for succ_node_id in node_ids:
                        succ_node_ids.add(succ_node_id)
            return list(succ_node_ids)

    def add_link(self, link):
        with self.lock:
            link_id = link.get_link_id()
            self.links[link_id] = link
            self.__save_dir()
            return link

    def get_link(self, link_id):
        with self.lock:
            return self.links[link_id]

    def get_link_ids(self):
        with self.lock:
            return list(self.links.keys())

    def set_metadata(self, metadata):
        with self.lock:
            self.metadata = deepcopy(metadata)
        self.__save_dir()

    def get_metadata(self):
        with self.lock:
            return deepcopy(self.metadata)

    def remove_node(self, node_id):
        with self.lock:
            if node_id in self.nodes:
                del self.nodes[node_id]
            for dirpath in [self.tempdir, self.savedir]:
                if dirpath is not None:
                    file_storage = os.path.join(dirpath,"files",node_id)
                    if os.path.exists(file_storage):
                        try:
                            shutil.rmtree(file_storage)
                        except:
                            self.logger.exception(f"Unable to remove directory {file_storage} when removing node")
            self.__save_dir()

    def remove_link(self, link_id):
        with self.lock:
            if link_id in self.links:
                del self.links[link_id]
            self.__save_dir()

    def clear(self):
        with self.lock:
            self.nodes = {}
            self.links = {}
            self.__save_dir()

    def get_input_ports(self, node_id):
        with self.lock:
            node = self.nodes[node_id]
            node_type = self.schema.get_node_type(node.get_node_type())
            input_ports = []
            for (input_port_name, _) in node_type.get_input_ports():
                input_ports.append(input_port_name)
            return input_ports

    def get_output_ports(self, node_id):
        with self.lock:
            node = self.nodes[node_id]
            node_type = self.schema.get_node_type(node.get_node_type())
            output_ports = []
            for (output_port_name, _) in node_type.get_output_ports():
                output_ports.append(output_port_name)
            return output_ports

    def get_inputs_to(self, node_id, input_port_name=None):
        with self.lock:
            inputs = []
            for link in self.links.values():
                if link.to_node_id == node_id and (input_port_name is None or link.to_port == input_port_name):
                    inputs.append((link.from_node_id, link.from_port))
            return inputs

    def get_outputs_from(self, node_id, output_port_name=None):
        with self.lock:
            outputs = []
            for link in self.links.values():
                if link.from_node_id == node_id and (output_port_name is None or link.from_port == output_port_name):
                    outputs.append((link.to_node_id, link.to_port))
            return outputs

    def get_terminal_nodes(self):
        with self.lock:
            node_ids = set(self.nodes.keys())
            for link in self.links.values():
                node_ids.remove(link.from_node_id)
            return node_ids

    def get_node_property(self, node_id, property_name):
        with self.lock:
            node = self.get_node(node_id)
            if node:
                return node.get_property(property_name)
            else:
                return None

    def set_node_property(self, node_id, property_name, property_value):
        with self.lock:
            self.get_node(node_id).set_property(property_name, property_value)
            self.__save_dir()

    def open_file(self, owner_id, file_type, path, mode, is_temporary, **kwargs):
        if os.path.isabs(path):
            raise ValueError(f"Path {path} to be opened is absolute, but must be relative")
        if is_temporary:
            if self.tempdir is None:
                self.tempdir = tempfile.mkdtemp()
            filepath = os.path.join(self.tempdir,"files",file_type,owner_id,path)
        else:
            if self.savedir is None:
                self.savedir = tempfile.mkdtemp()
            filepath = os.path.join(self.savedir,"files",file_type,owner_id,path)
        parent_dir = os.path.split(filepath)[0]
        os.makedirs(parent_dir, exist_ok=True)
        return open(filepath, mode=mode, **kwargs)

    def get_package_property(self, package_id, property_name):
        with self.lock:
            return self.package_properties.get(package_id, {}).get(property_name, {})

    def set_package_property(self, package_id, property_name, property_value):
        with self.lock:
            if package_id not in self.package_properties:
                self.package_properties[package_id] = {}
            self.package_properties[package_id][property_name] = property_value
            self.save_dir()

    def get_package_properties(self):
        with self.lock:
            return copy.deepcopy(self.package_properties)

    def load(self, from_dict):
        with self.lock:
            added_node_ids = []
            added_link_ids = []
            self.package_properties = from_dict.get("package_properties", {})

            nodes = from_dict.get("nodes", {})
            # TODO deal with id-conflicts by renaming the incoming nodes and links
            for (node_id, node_content) in nodes.items():
                added_node_ids.append(node_id)
                node = Node.load(node_id, node_content["node_type"], node_content)
                self.add_node(node)
            links = from_dict.get("links", {})
            for (link_id, link_content) in links.items():
                added_link_ids.append(link_id)
                link = Link.load(link_id, link_content)
                self.add_link(link)
            self.set_metadata(from_dict.get("metadata", {"name": "", "description": ""}))
            return (added_node_ids, added_link_ids)

    def load_zip(self, f):
        with self.lock:
            with zipfile.ZipFile(f) as zf:
                zf.extract("topology.json", self.savedir)

                storage_paths = [name for name in zf.namelist() if name.startswith("files")]

                for storage_path in storage_paths:
                    zf.extract(storage_path,self.savedir)
            return self.load_dir()

    def load_dir(self):
        with self.lock:
            json_path = os.path.join(self.savedir, "topology.json")
            if os.path.exists(json_path):
                with open(json_path) as f:
                    saved_topology = json.loads(f.read())
                    (loaded_node_ids, loaded_link_ids) = self.load(saved_topology)
                    return (loaded_node_ids, loaded_link_ids)
            return ([],[])

    def save(self):
        with self.lock:
            saved = {"nodes": {}, "links": {}, "package_properties": self.package_properties}

            for (node_id, node) in self.nodes.items():
                saved["nodes"][node_id] = node.save()

            for (link_id, link) in self.links.items():
                saved["links"][link_id] = link.save()

            saved["metadata"] = deepcopy(self.metadata)
            return saved

    def save_zip(self, to_file=None):
        with self.lock:
            saved = self.save()
            f = to_file if to_file else io.BytesIO()
            zf = zipfile.ZipFile(f, "w")
            zf.writestr("topology.json", json.dumps(saved))
            if self.savedir is not None:
                for root, dirs, files in os.walk(os.path.join(self.savedir,"files")):
                    for file in files:
                        entry = os.path.relpath(os.path.join(root,file),self.savedir)
                        zf.write(os.path.join(self.savedir,entry),entry)
            zf.close()
            if to_file is None:
                return f.getvalue()

    def __save_dir(self):
        saved = self.save()
        with open(os.path.join(self.savedir,"topology.json"),"w") as f:
            f.write(json.dumps(saved))
