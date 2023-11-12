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

import io
from typing import Callable, Union, Literal, Any

from hyrrokkin.executor.graph_executor import GraphExecutor
from hyrrokkin.schema.schema import Schema
from hyrrokkin.model.node import Node
from hyrrokkin.model.link import Link
from hyrrokkin.exceptions.invalid_link_error import InvalidLinkError


class Topology:

    def __init__(self, package_list:list[str],
                 status_handler:Callable[[str,str,str,str],None]=lambda target_id, target_type, msg, status: None):
        """
        Create a topology

        :param package_list: a list of the paths to python packages containing schemas (a schema.json
        :param status_handler: specify a function to call when a node/configuration sets its status
        """
        self.schema = Schema()
        for package in package_list:
            self.schema.load_package_from(package + "/schema.json")
        self.status_handler = status_handler
        self.message_handler = lambda target_id, target_type, msg, for_session_id, except_session_id: None
        self.executor = None

    def __create_executor(self):
        if self.executor is None:
            self.executor = GraphExecutor(self.schema, message_callback=self.message_handler,
                                          status_callback=self.status_handler,
                                          node_execution_callback=None,
                                          execution_complete_callback=None)

    def load(self, from_file:io.BytesIO):
        """
        Load a topology from a binary stream

        :param from_path: a binary stream, opened for reading
        """
        self.__create_executor()
        self.executor.load(from_file)

    def save(self, to_file):
        """
       Save a topology to a binary stream

       :param to_file: a binary stream, opened for writing
       """
        self.__create_executor()
        self.executor.save(to_file)

    def run(self, execute_to_nodes:Union[list[str],Literal["*"]]="*", cache_outputs_for_nodes:Union[list[str],Literal["*"]]=[]):
        """
        Run the topology, blocking until the execution completes

        :param execute_to_nodes: a list of node ids to run, or "*" to run all nodes.
            These nodes and their predecessors may be executed, if their outputs were not ached from a previous run.
        :param cache_outputs_for_nodes: a list of node ids to cache outputs for, or "*" to cache outputs for all nodes.
            If a node's outputs are cached, they will be re-used in future runs and can be retrieved after a run completes.
        """
        self.__create_executor()
        self.executor.run(terminate_on_complete=True, execute_to_nodes=execute_to_nodes, cache_outputs_for_nodes=cache_outputs_for_nodes)

    def get_node_outputs(self, node_id: str) -> Union[dict[str,Any],None]:
        """
        Get the outputs for a particular node from the last run of the topology
        :param node_id: the id of the node
        :return: a dictionary populated with output port names as keys and the output values from those ports as values

        :notes: if no outputs are cached for the node, None is returned
        """
        self.__create_executor()
        return self.executor.state.node_outputs.get(node_id,None)

    def stop(self) -> None:
        """
        Stop the current execution, callable from another thread during the execution of run

        :notes: the run method will return once any current node executions complete
        """
        self.__create_executor()
        self.executor.stop()

    def set_metadata(self, metadata:dict[str,Any]):
        """
        Set metadata for this topology

        :param metadata: a dictionary containing metadata, that must be JSON serialisable.

        :notes: the following keys will be understood by tooling: name, version, description, author
        """
        self.__create_executor()
        self.executor.set_metadata(metadata)

    def set_configuration(self, package_id:str, properties:dict[str,Any]):
        """
        Set the properties for a package's configuration

        :param package_id: the package identifier
        :param properties: a dictionary containing property names and values, must be JSON serialisable
        """
        self.__create_executor()
        self.executor.set_package_configuration(package_id, properties)

    def add_node(self, node_id, node_type, properties) -> str:
        """
        Add a node to the topology

        :param node_id: the node's unique identifier, must not already exist within the topology
        :param node_type: the type of the node, a string of the form package_id:node_type_id
        :param properties:  dictionary containing property names and values, must be JSON serialisable
        """
        self.__create_executor()
        node = Node(node_id, node_type, x=0, y=0, metadata={}, properties=properties)
        self.executor.add_node(node)
        return node_id

    def get_node_property(self, node_id:str, property_name:str):
        """
        Gets the property of a node, or None if the node or node property is not set

        :param node_id: the node's identifier
        :param property_name: the name of the property
        """
        self.__create_executor()
        return self.executor.get_node_property(node_id, property_name)

    def set_node_property(self, node_id:str, property_name:str, property_value:Any):
        """
        Update the property of a node

        :param node_id: the node's identifier
        :param property_name: the name of the property
        :param property_value: the value of the property, must be JSON serialisable
        """
        self.__create_executor()
        self.executor.set_node_property(node_id, property_name, property_value)

    def open_node_file(self, node_id, path, mode, is_temporary=False, **kwargs):
        """Open a file within a node's filestore.

        If is_temporary is False, data written to these files will be persisted when the topology to which this node belongs is saved and reloaded.

        :param node_id: the id of the node to which the file will belong
        :param path: the relative path to the file within the filestore
        :param mode: the mode with which the file is to be opened
        :param is_temporary: whether the file should be persisted when the topology is saved
        :param kwargs: other arguments to the open call

        :return: opened file
        :raises: exception if file cannot be opened

        :notes: This method calls Python's builtin open function.  For a description of the available arguments to the open function, see https://docs.python.org/3/library/functions.html#open
        """
        self.__create_executor()
        return self.executor.network.open_file(node_id, "node", path, mode, is_temporary, **kwargs)

    def open_configuration_file(self, package_id, path, mode, is_temporary=False, **kwargs):
        """Open a file within a package configuration's filestore.

        If is_temporary is False, data written to these files will be persisted when the topology to which this configuration belongs is saved and reloaded.

        :param package_id: the id of the package to which the file will belong
        :param path: the relative path to the file within the filestore
        :param mode: the mode with which the file is to be opened
        :param is_temporary: whether the file should be persisted when the topology is saved
        :param kwargs: other arguments to the open call

        :return: opened file
        :raises: exception if file cannot be opened

        :notes: This method calls Python's builtin open function.  For a description of the available arguments to the open function, see https://docs.python.org/3/library/functions.html#open
        """
        self.__create_executor()
        return self.executor.network.open_file(package_id, "configuration", path, mode, is_temporary, **kwargs)

    def add_link(self, link_id:str, from_node_id:str, from_port:Union[str,None], to_node_id:str, to_port:Union[str,None]) -> str:
        """
        Add a link to the topology

        :param link_id: a unique identifier for the link
        :param from_node_id: node id of the source node
        :param from_port: port name on the source node
        :param to_node_id: node id of the destination node
        :param to_port: port name on the destination node

        :raises InvalidLinkError: if the link cannot be added
        """
        self.__create_executor()
        from_node = self.executor.get_node(from_node_id)
        if from_node is None:
            raise InvalidLinkError(f"{from_node_id} does not exist")

        from_node_type_name = from_node.get_node_type()
        from_node_type = self.schema.get_node_type(from_node_type_name)

        to_node = self.executor.get_node(to_node_id)
        if to_node is None:
            raise InvalidLinkError(f"{to_node_id} does not exist")
        to_node_type_name = to_node.get_node_type()
        to_node_type = self.schema.get_node_type(to_node_type_name)

        if from_port is None:
            if len(from_node_type.output_ports) == 1:
                from_port = next(iter(from_node_type.output_ports))
            else:
                output_port_names = ",".join(list(from_node_type.output_ports.keys()))
                raise InvalidLinkError(f"from_port not specified for link, should be one of ({output_port_names})")
        else:
            if from_port not in from_node_type.output_ports:
                raise InvalidLinkError(f"{from_port} is not a valid output port for node {from_node_id}")

        if to_port is None:
            if len(to_node_type.input_ports) == 1:
                to_port = next(iter(to_node_type.input_ports))
            else:
                input_port_names = ",".join(list(to_node_type.input_ports.keys()))
                raise InvalidLinkError(f"to_port not specified for link, should be one of ({input_port_names})")
        else:
            if to_port not in to_node_type.input_ports:
                raise InvalidLinkError(f"{to_port} is not a valid output port for node {to_node_id}")

        from_link_type = from_node_type.output_ports[from_port].link_type

        to_link_type = to_node_type.input_ports[to_port].link_type

        if from_link_type != to_link_type:
            raise InvalidLinkError(f"incompatible link types (from: {from_link_type}, to: {to_link_type})")

        if not from_node_type.output_ports[from_port].allows_multiple_connections():
            if len(self.executor.get_outputs_from(from_node_id,from_port)) > 0:
                raise InvalidLinkError(f"output port {from_node_id}/{from_port} is already connected and does not allow multiple connections")

        if not to_node_type.input_ports[to_port].allows_multiple_connections():
            if len(self.executor.get_inputs_to(to_node_id,to_port)) > 0:
                raise InvalidLinkError(f"input port {to_node_id}/{to_port} is already connected and does not allow multiple connections")

        link = Link(link_id, from_node_id, from_port, to_node_id, to_port, from_link_type)
        self.executor.add_link(link)
        return link_id

    def get_node_ids(self):
        """
        Get the ids of all nodes in the topology

        :return: list of node ids
        """
        return self.executor.get_node_ids()

    def get_node(self, node_id):
        """
        Get the node type and properties for a given node

        :param node_id: the id of the node to retrieve

        :return: tuple (node_type_id,node_properties)
        """
        node = self.executor.get_node(node_id)
        return (node.get_node_type(),node.get_properties())

    def get_link_ids(self):
        """
        Get the ids of all links in the topology

        :return: list of link ids
        """
        return self.executor.get_link_ids()

    def get_link(self, link_id):
        """
        Get the link details for a given link

        :param link_id: the id of the link to retrieve

        :return: tuple (from_node_id,from_port,to_node_id,to_port)
        """
        link = self.executor.get_link(link_id)
        return (link.from_node_id,link.from_port,link.to_node_id,link.to_port)

    def get_output_port_names(self,node_id):
        """
        Get the output port names for a given node

        :param node_id: the id of the node

        :return: list of output port names
        """
        node = self.executor.get_node(node_id)
        node_type = self.schema.get_node_type(node.get_node_type())
        return [name for (name,_) in node_type.get_output_ports()]

    def get_input_port_names(self, node_id):
        """
        Get the input port names for a given node

        :param node_id: the id of the node

        :return: list of input port names
        """
        node = self.executor.get_node(node_id)
        node_type = self.schema.get_node_type(node.get_node_type())
        return [name for (name, _) in node_type.get_input_ports()]

    def get_metadata(self):
        """
        Get the metadata of the topology

        :return: dictionary containing the metadata
        """
        return self.executor.get_metadata()

    def get_package_properties(self):
        """
        Get the package properties for the topology

        :return: dictionary containing the package properties - top level keys are the package-ids
        """
        return self.executor.get_package_properties()