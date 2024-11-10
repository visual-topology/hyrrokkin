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
import uuid
from copy import deepcopy
import zipfile
import json
import io
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
        self.logger = logging.getLogger("network")
        self.tempdir = None

    def __del__(self):
        if self.tempdir is not None:
            try:
                shutil.rmtree(self.tempdir)
            except:
                self.logger.exception(f"Unable to remove directory {self.tempdir} after deleting network")

    def get_directory(self):
        return self.savedir

    def get_schema(self):
        return self.schema

    def add_node(self, node):
        node_id = node.get_node_id()
        self.nodes[node_id] = node
        self.__save_dir()

    def move_node(self, node_id, x, y):
        self.nodes[node_id].move_to(x, y)
        self.__save_dir()

    def get_node(self, node_id):
        return self.nodes.get(node_id, None)

    def get_connection_counts(self, node_id):
        new_counts = {"inputs": {}, "outputs": {}}
        for link in self.links.values():
            if link.from_node_id == node_id:
                if link.from_port not in new_counts["outputs"]:
                    new_counts["outputs"][link.from_port] = 0
                new_counts["outputs"][link.from_port] = new_counts["outputs"][link.from_port] + 1
            if link.to_node_id == node_id:
                if link.to_port not in new_counts["inputs"]:
                    new_counts["inputs"][link.to_port] = 0
                new_counts["inputs"][link.to_port] = new_counts["inputs"][link.to_port] + 1
        return new_counts

    def get_node_ids(self, traversal_order=None):
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
        pred_node_ids = {node_id}
        for link in self.links.values():
            if link.to_node_id == node_id:
                node_ids = self.get_node_ids_to(link.from_node_id)
                for pred_node_id in node_ids:
                    pred_node_ids.add(pred_node_id)
        return list(pred_node_ids)

    def get_node_ids_from(self, node_id):
        succ_node_ids = {node_id}
        for link in self.links.values():
            if link.from_node_id == node_id:
                node_ids = self.get_node_ids_from(link.to_node_id)
                for succ_node_id in node_ids:
                    succ_node_ids.add(succ_node_id)
        return list(succ_node_ids)

    def add_link(self, link):
        link_id = link.get_link_id()
        self.links[link_id] = link
        self.__save_dir()
        return link

    def get_link(self, link_id):
        return self.links.get(link_id,None)

    def get_link_ids(self):
        return list(self.links.keys())

    def set_metadata(self, metadata):
        self.metadata = deepcopy(metadata)
        self.__save_dir()

    def get_metadata(self):
        return deepcopy(self.metadata)

    def remove_node(self, node_id):
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
        if link_id in self.links:
            del self.links[link_id]
        self.__save_dir()

    def clear(self):
        self.nodes = {}
        self.links = {}
        self.__save_dir()

    def get_input_ports(self, node_id):
        node = self.nodes.get(node_id,None)
        if node:
            node_type = self.schema.get_node_type(node.get_node_type())
            input_ports = []
            for (input_port_name, _) in node_type.get_input_ports():
                input_ports.append(input_port_name)
            return input_ports
        else:
            return []

    def get_output_ports(self, node_id):
        node = self.nodes.get(node_id,None)
        if node:
            node_type = self.schema.get_node_type(node.get_node_type())
            output_ports = []
            for (output_port_name, _) in node_type.get_output_ports():
                output_ports.append(output_port_name)
            return output_ports
        else:
            return []

    def get_inputs_to(self, node_id, input_port_name=None):
        inputs = []
        for link in self.links.values():
            if link.to_node_id == node_id and (input_port_name is None or link.to_port == input_port_name):
                inputs.append((link.from_node_id, link.from_port))
        return inputs

    def get_outputs_from(self, node_id, output_port_name=None):
        outputs = []
        for link in self.links.values():
            if link.from_node_id == node_id and (output_port_name is None or link.from_port == output_port_name):
                outputs.append((link.to_node_id, link.to_port))
        return outputs

    def get_terminal_nodes(self):
        node_ids = set(self.nodes.keys())
        for link in self.links.values():
            node_ids.remove(link.from_node_id)
        return node_ids

    def load(self, from_dict, node_renamings):

        added_node_ids = []
        added_link_ids = []

        nodes = from_dict.get("nodes", {})

        for (node_id, node_content) in nodes.items():
            # check for collision with existing node ids, rename if necessary
            if node_id in self.nodes and node_id not in node_renamings:
                node_renamings[node_id] = "n"+str(uuid.uuid4())

            renamed = node_id in node_renamings
            node_id = node_renamings.get(node_id,node_id)

            added_node_ids.append(node_id)
            node = Node.load(node_id, node_content["node_type"], node_content)
            if renamed:
                node.x += 100
                node.y += 100
            self.add_node(node)

        link_renamings = {}
        links = from_dict.get("links", {})
        for (link_id, link_content) in links.items():
            # check for collision with existing links ids, rename if necessary
            if link_id in self.links:
                link_renamings[link_id] = "l"+str(uuid.uuid4())
                link_id = link_renamings[link_id]
            added_link_ids.append(link_id)
            link = Link.load(link_id, link_content, node_renamings)
            self.add_link(link)

        # do not overwrite existing metadata...
        metadata = self.get_metadata()
        new_metadata = from_dict.get("metadata", {})
        for key in new_metadata:
            if key not in metadata:
                metadata[key] = new_metadata[key]
        self.set_metadata(metadata)

        return (added_node_ids, added_link_ids, node_renamings)

    def load_zip(self, f, merging=False):
        node_renamings = {}
        with zipfile.ZipFile(f) as zf:
            zipinfos = zf.infolist()
            for zipinfo in zipinfos:
                # if there is a collision on node id with an existing node
                # rename the new node and extract files to the new folder
                storage_comps = zipinfo.filename.split("/")
                if merging and storage_comps[0] == "node":
                    node_id = storage_comps[1]
                    if node_id in self.nodes:
                        if node_id not in node_renamings:
                            # create a new node renaming
                            node_renamings[node_id] = "n"+str(uuid.uuid4())
                        storage_comps[1] = node_renamings[node_id]
                        zipinfo.filename = "/".join(storage_comps)

            extract_zipinfos = [zipinfo for zipinfo in zipinfos if zipinfo.filename.startswith("node") or zipinfo.filename.startswith("package")]

            for zipinfo in extract_zipinfos:
                if merging and zipinfo.filename.startswith("package"):
                    continue # if merging, do not overwrite existing package properties and data
                zf.extract(zipinfo,self.savedir)
            zf.extract("topology.json", self.savedir)

        return self.load_dir(node_renamings, merging=merging)

    def load_dir(self, node_renamings, merging=False):
        json_path = os.path.join(self.savedir, "topology.json")
        loaded_node_ids = []
        loaded_link_ids = []
        if os.path.exists(json_path):
            with open(json_path) as f:
                saved_topology = json.loads(f.read())
                (loaded_node_ids, loaded_link_ids, node_renamings) = self.load(saved_topology,node_renamings)
            if merging:
                with open(json_path,"w") as of:
                    of.write(json.dumps(self.save()))
        return (loaded_node_ids, loaded_link_ids, node_renamings)

    def save(self):
        saved = {"nodes": {}, "links": {}}

        for (node_id, node) in self.nodes.items():
            saved["nodes"][node_id] = node.save()

        for (link_id, link) in self.links.items():
            saved["links"][link_id] = link.save()

        saved["metadata"] = deepcopy(self.metadata)
        return saved

    def save_zip(self, to_file=None):
        saved = self.save()
        f = to_file if to_file else io.BytesIO()
        zf = zipfile.ZipFile(f, "w")
        zf.writestr("topology.json", json.dumps(saved,indent=4))
        for subdir in ["node","package"]:
            for root, dirs, files in os.walk(os.path.join(self.savedir,subdir)):
                for file in files:
                    entry = os.path.relpath(os.path.join(root,file),self.savedir)
                    zf.write(os.path.join(self.savedir,entry),entry)
        zf.close()
        if to_file is None:
            return f.getvalue()

    def __save_dir(self):
        saved = self.save()
        path = os.path.join(self.savedir,"topology.json")
        with open(path,"w") as f:
            f.write(json.dumps(saved,indent=4))

