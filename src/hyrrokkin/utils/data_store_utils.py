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
import json

class DataStoreUtils:

    def __init__(self, root_folder):
        self.root_folder = root_folder

    @staticmethod
    def __check_valid_data_key(key):
        for c in key:
            if not c.isalnum() and c != '_':
                raise ValueError("data key can only contain alphanumeric characters and underscores")

    def __get_data(self, owner_id, file_type, key):
        DataStoreUtils.__check_valid_data_key(key)
        filepath = os.path.join(self.root_folder, file_type, owner_id, "data", key)
        binary_filepath = filepath+".binary"
        if os.path.exists(binary_filepath):
            with open(binary_filepath, mode="rb") as f:
                return f.read()
        text_filepath = filepath+".text"
        if os.path.exists(text_filepath):
            with open(text_filepath, mode="r") as f:
                return f.read()
        return None

    def __set_data(self, owner_id, file_type, key, data):
        DataStoreUtils.__check_valid_data_key(key)

        folder = os.path.join(self.root_folder, file_type, owner_id, "data")

        filepath = os.path.join(folder, key)
        binary_filepath = filepath + ".binary"
        text_filepath = filepath+".text"

        if data is None:
            if os.path.exists(text_filepath):
                os.remove(text_filepath)
            if os.path.exists(binary_filepath):
                os.remove(binary_filepath)
            return

        os.makedirs(folder, exist_ok=True)

        if isinstance(data, bytes):
            with open(binary_filepath, "wb") as f:
                f.write(data)
            if os.path.exists(text_filepath):
                os.remove(text_filepath)

        elif isinstance(data, str):
            with open(text_filepath, "w") as f:
                f.write(data)
            if os.path.exists(binary_filepath):
                os.remove(binary_filepath)

    def __save_properties(self, owner_id, file_type, properties):
        folder = os.path.join(self.root_folder, file_type, owner_id)

        path = os.path.join(folder, "properties.json")
        if properties is None:
            if os.path.exists(path):
                os.remove(path)
        else:
            os.makedirs(folder, exist_ok=True)
            with open(path,"w") as f:
                f.write(json.dumps(properties))

    def __load_properties(self, owner_id, file_type):
        folder = os.path.join(self.root_folder, file_type, owner_id)

        path = os.path.join(folder, "properties.json")
        if os.path.exists(path):
            with open(path) as f:
                return json.loads(f.read())

        return {}

    def get_node_property(self, node_id, property_name):
        properties = self.__load_properties(node_id, "node")
        return properties.get(property_name, None)

    def set_node_property(self, node_id, property_name, property_value):
        properties = self.__load_properties(node_id, "node")
        if property_value is not None:
            properties[property_name] = property_value
        else:
            if property_name in properties:
                del properties[property_name]
        self.__save_properties(node_id, "node", properties)

    def get_node_properties(self, node_id):
        return self.__load_properties(node_id, "node")

    def set_node_properties(self, node_id, properties):
        self.__save_properties(node_id, "node", properties)

    def get_node_data(self, node_id, key):
        return self.__get_data(node_id, "node", key)

    def set_node_data(self, node_id, key, data):
        self.__set_data(node_id, "node", key, data)

    def get_package_property(self, package_id, property_name):
        properties = self.__load_properties(package_id, "package")
        return properties.get(property_name, None)

    def set_package_property(self, package_id, property_name, property_value):
        properties = self.__load_properties(package_id, "package")
        if property_value is not None:
            properties[property_name] = property_value
        else:
            if property_name in properties:
                del properties[property_name]
        self.__save_properties(package_id, "package", properties)

    def get_package_properties(self, package_id):
        return self.__load_properties(package_id, "package")

    def set_package_properties(self, package_id, properties):
        self.__save_properties(package_id, "package", properties)

    def get_package_data(self, package_id, key):
        return self.__get_data(package_id, "package", key)

    def set_package_data(self, package_id, key, data):
        self.__set_data(package_id, "package", key, data)


