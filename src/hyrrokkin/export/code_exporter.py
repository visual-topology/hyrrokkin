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

import os
import os.path
import zipfile
import json
import tempfile

from hyrrokkin.model.network import Network
from hyrrokkin.utils.data_store_utils import DataStoreUtils

dummy_services_paths = [
    os.path.join(os.path.split(__file__)[0], "../utils/data_store_utils.py"),
    os.path.join(os.path.split(__file__)[0], "../services/cli_node_services.py"),
    os.path.join(os.path.split(__file__)[0], "../services/cli_configuration_services.py")]


def get_import_for(classname):
    classplits = classname.split(".")
    module_path = ".".join(classplits[:-1])
    return f"import {module_path}"


class CodeExporter:

    def __init__(self, schema, topology_file, output_folder, output_filename):
        self.schema = schema
        self.network = Network(self.schema,tempfile.mkdtemp())
        self.output_folder = output_folder
        self.output_path = os.path.join(output_folder, output_filename)
        os.makedirs(output_folder, exist_ok=True)
        with zipfile.ZipFile(topology_file, "r") as zf:
            with zf.open("topology.json") as f:
                content = f.read().decode("utf-8")
                # with open(os.path.join(output_folder,"topology.json"),"w") as of:
                #    of.write(content)
                self.network.load(json.loads(content))

            storage_paths = [name for name in zf.namelist() if name.startswith("node") or name.startswith("package")]
            zf.extractall(output_folder, storage_paths)
        self.dsu = DataStoreUtils(self.output_folder)

    def export(self):

        imports = ["import logging", "import asyncio", ""]
        code = "\n\n"

        code += "logging.basicConfig(level=logging.INFO)\n"

        for dummy_services_path in dummy_services_paths:
            with open(dummy_services_path) as f:
                for line in f.readlines():
                    if line.startswith("#"):
                        continue
                    if line.startswith("from hyrrokkin"):
                        continue
                    if line.startswith("import") and line.strip() in imports:
                        continue
                    code += line
            code += "\n\n"

        code += "# define package configurations\n\n"

        configured_packages = set()
        for (package_id, package) in self.schema.get_packages().items():

            classname = package.get_configuration().get("classname", "")
            if classname:
                imp = get_import_for(classname)
                if imp.strip() not in imports:
                    imports.append(imp)
                package_id = package.get_id()

                code += f"{package_id}_service = ConfigurationServices('{package_id}','.')\n"
                code += f"{package_id}_configuration = {classname}({package_id}_service)\n"
                configured_packages.add(package_id)

        node_ids = self.network.get_node_ids()
        code += "\n\n# define an asynchronous method to create and run each node\n\n"

        code += "async def run():\n"
        for node_id in node_ids:
            node = self.network.get_node(node_id)
            node_package_id = node.get_node_type().split(":")[0]
            node_type = self.schema.get_node_type(node.get_node_type())

            classname = node_type.get_classname()
            imp = get_import_for(classname)
            if imp not in imports:
                imports.append(imp)

            if node_package_id in configured_packages:
                code += f"\t{node_id}_service = NodeServices('{node_id}','.',{package_id}_configuration)\n"
            else:
                code += f"\t{node_id}_service = NodeServices('{node_id}','.')\n"

            code += f"\t{node_id} = {classname}({node_id}_service)\n"
            inputs = []
            for (input_port_name, _) in node_type.get_input_ports():
                connected_outputs = self.network.get_inputs_to(node_id, input_port_name)
                input = f'"{input_port_name}": ['
                for (output_node_id, output_port_name) in connected_outputs:
                    input += f'{output_node_id}_outputs["{output_port_name}"]'
                input += ' ]'
                inputs.append(input)
            inputs = "{ " + ",".join(inputs) + " }"
            code += f"\t{node_id}_outputs = await {node_id}.execute({inputs})\n"

        code += "\n"
        code += "asyncio.run(run())\n"

        with open(self.output_path, "w") as f:
            f.write("\n".join(imports))
            f.write(code)
