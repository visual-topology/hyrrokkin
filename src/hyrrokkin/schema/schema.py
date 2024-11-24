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

import os.path
import json

from hyrrokkin.schema.package import Package
from hyrrokkin.utils.resource_loader import ResourceLoader


class Schema:

    def __init__(self):
        self.packages = {}

    def get_packages(self):
        return self.packages

    def get_classmap(self):
        classmap = {}
        for package_id in self.packages:
            classmap[package_id] = self.packages[package_id].get_classmap()
        return classmap

    def get_node_type(self, node_type_name):
        (package_id, node_type_id) = Schema.split_descriptor(node_type_name)
        return self.packages[package_id].get_node_type(node_type_id)

    def load_package_from(self, fq_resource):
        b = ResourceLoader.load_resource(fq_resource)
        s = b.decode("utf-8")
        package_content = json.loads(s)
        return self.load_package_from_dict(package_content, fq_resource)

    def load_package_from_dict(self, from_dict, schema_resource_path):
        package_resource_path = os.path.split(schema_resource_path)[0]
        package = Package.load(from_dict, package_resource_path)
        self.add_package(package)
        return package.get_id()

    def add_package(self, package):
        package_id = package.get_id()
        if package_id in self.packages:
            raise Exception("package %s already exists in schema" % (package_id))
        self.packages[package_id] = package

    def save(self):
        return [package.save() for package in self.packages.values()]

    @staticmethod
    def load(saved_schema):
        schema = Schema()
        for saved_package in saved_schema:
            schema.add_package(Package.load(saved_package))
        return schema

    @staticmethod
    def split_descriptor(descriptor):
        comps = descriptor.split(":")
        if len(comps) > 2:
            raise Exception("Invalid descriptor: %s")
        if len(comps) == 2:
            return (comps[0], comps[1])
        else:
            return (None, comps[1])

    @staticmethod
    def form_descriptor(package_id, id):
        if not package_id:
            return id
        else:
            return "%s:%s" % (package_id, id)
