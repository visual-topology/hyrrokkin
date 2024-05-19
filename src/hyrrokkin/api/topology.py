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
import os
from typing import List, Callable, Union, Literal, Any, Dict, Protocol

from hyrrokkin.executor.graph_executor import GraphExecutor
from hyrrokkin.schema.schema import Schema
from hyrrokkin.model.node import Node
from hyrrokkin.model.link import Link
from hyrrokkin.exceptions.invalid_link_error import InvalidLinkError
from hyrrokkin.exceptions.invalid_node_error import InvalidNodeError
from hyrrokkin.utils.data_store_utils import DataStoreUtils
from hyrrokkin.utils.type_hints import JsonType
from hyrrokkin.utils.type_hints import ClientMessageProtocol


class Topology:

    def __init__(self, execution_folder:str, package_list: list[str],
                 status_handler: Callable[[str, str, str, str], None] = None,
                 execution_handler: Callable[[str, str, Union[Dict, Exception, None]], None] = None):
        """
        Create a topology

        Args:
            execution_folder: the folder used to store the topology definition and files
            package_list: a list of the paths to python packages containing schemas (a schema.json
            status_handler: specify a function to call when a node/configuration sets its status
                                 passing parameters target_id, target_type, msg, status
            execution_handler: specify a function to call when a node changes its execution status
                                passing parameters lambda node_id, state, exception_or_result
        """
        self.execution_folder = execution_folder
        os.makedirs(self.execution_folder, exist_ok=True)
        self.dsu = DataStoreUtils(self.execution_folder)
        self.schema = Schema()
        for package in package_list:
            self.schema.load_package_from(package + "/schema.json")
        self.status_handler = status_handler
        self.execution_handler = execution_handler

        self.executor = GraphExecutor(self.schema, execution_folder=self.execution_folder,
                                      status_callback=self.status_handler,
                                      node_execution_callback=self.execution_handler,
                                      execution_complete_callback=None)

    def load(self, from_file: io.BytesIO) -> dict:
        """
        Load a topology from a binary stream

        Args:
            from_file: a binary stream, opened for reading

        Returns:
            a dictionary containing any node renamings performed to avoid id collisions with existing nodes
        """
        (nodes_added, links_added, node_renamings) = self.executor.load_zip(from_file)
        return node_renamings

    def save(self, to_file: io.BufferedWriter):
        """
        Save a topology to a binary stream

        Args:
            to_file: an opened binary file
        """
        self.executor.save(to_file)

    def attach_node_client(self, node_id: str, client_id: str | tuple[str, str],
                           message_callback: ClientMessageProtocol, client_options: dict = {}) -> ClientMessageProtocol:
        """
        Attach a client instance to a node.  Any client already attached to the node with the same client_id
        will be detached.

        Args:
            node_id: the node to which the client is to be attached
            client_id: a identifier for the client, unique in the context of the node
            message_callback: a function that is called when a message is sent from the node to this client
            client_options: optional, a dictionary with extra parameters from the client

        Returns:
            a function that can be used to send messages to the node
        """
        return self.executor.attach_client(("node", node_id), client_id, message_callback, client_options)

    def detach_node_client(self, node_id: str, client_id: str | tuple[str, str]):
        """
        Detach a client instance from a node

        Args:
            node_id: the node to which the client is to be attached
            client_id: an identifier for the client
        """
        self.executor.detach_client(("node", node_id), client_id)

    def attach_configuration_client(self, package_id: str, client_id: str | tuple[str, str],
                                    message_callback: ClientMessageProtocol,
                                    client_options: dict = {}) -> ClientMessageProtocol:
        """
        Attach a client instance to a package configuration

        Args:
            package_id: the package configuration to which the client is to be attached
            client_id: an identifier for the client, unique in the context of the package configuration
            message_callback: a function that is called when a message is sent from the node to this client
            client_options: optional, a dictionary with extra parameters for the client

        Returns:
            a function that can be used to send messages to the node
        """
        return self.executor.attach_client(("configuration", package_id), client_id, message_callback, client_options)

    def detach_configuration_client(self, package_id: str, client_id: str | tuple[str, str]):
        """
        Detach a client instance from a package configuration

        Args:
            package_id: the node to which the client is to be attached
            client_id: an identifier for the client
        """
        return self.executor.detach_client(("configuration", package_id), client_id)

    def run(self) -> bool:
        """
        Run the topology, blocking until the execution completes

        Returns:
            True if the execution succeeded, false if it failed due to some error
        """
        return self.executor.run(terminate_on_complete=True)

    def get_node_outputs(self, node_id: str) -> Union[dict[str, Any], None]:
        """
        Get the outputs for a particular node from the last run of the topology

        Args:
            node_id: the id of the node

        Returns:
            a dictionary populated with output port names as keys and the output values from those ports as values

        Notes:
            if no outputs were produced for the node, None is returned
        """
        return self.executor.state.node_outputs.get(node_id, None)

    def stop(self) -> None:
        """
        Stop the current execution, callable from another thread during the execution of run

        Notes:
            the run method will return once any current node executions complete
        """
        self.executor.stop()

    def set_metadata(self, metadata: dict[str, str]):
        """
        Set metadata for this topology

        Args:
            metadata: a dictionary containing metadata, consisting of string keys and values.

        Notes:
            the following keys will be understood by hyrrokkin based tools - version, description, authors
        """
        self.executor.set_metadata(metadata)

    def set_configuration(self, package_id: str, properties: dict):
        """
        Set the properties of a package's configuration

        Args:
            package_id: the id of the packahe
            properties: a dictionary containing the configuration properties, must be JSON serialisable.
        """
        self.dsu.set_package_properties(package_id, properties)

    def add_node(self, node_id: str, node_type: str, properties: dict) -> str:
        """
        Add a node to the topology

        Args:
            node_id: the node's unique identifier, must not already exist within the topology
            node_type: the type of the node, a string of the form package_id:node_type_id
            properties: dictionary containing the node's property names and values, must be JSON serialisable
        """
        if self.executor.get_link(node_id) is not None:
            raise InvalidNodeError(f"Node with id {node_id} already exists")

        self.dsu.set_node_properties(node_id, properties)
        node = Node(node_id, node_type, x=0, y=0, metadata={})
        self.executor.add_node(node)
        return node_id

    def get_node_property(self, node_id: str, property_name: str) -> JsonType:
        """
        Gets the property of a node, or None if the node's property is not set

        Args:
            node_id: the node's identifier
            property_name: the name of the property
        """

        return self.dsu.get_node_property(node_id, property_name)

    def set_node_property(self, node_id: str, property_name: str, property_value: JsonType):
        """
        Update the property of a node

        Args:
            node_id: the node's identifier
            property_name: the name of the property
            property_value: the value of the property, must be JSON serialisable
        """
        self.dsu.set_node_property(node_id, property_name, property_value)
        if self.executor:
            self.executor.mark_dirty_from(node_id)

    def get_node_data(self, node_id: str, key: str) -> Union[bytes, str, None]:
        """
        Get binary or string data associated with this node.

        Args:
            node_id: node identifier
            key: a key to locate the data (can only contain alphanumeric characters and underscores)

        Returns:
            data or None if no data is associated with the key
        """
        return self.dsu.get_node_data(node_id, key)

    def set_node_data(self, node_id: str, key: str, data: Union[bytes, str, None]):
        """
        Set binary or string data associated with this node.

        Args:
            node_id: node identifier
            key: a key to locate the data (can only contain alphanumeric characters and underscores)
            data: data to be stored
        """
        self.dsu.set_node_data(node_id, key, data)
        self.executor.mark_dirty_from(node_id)

    def get_package_property(self, package_id: str, property_name: str) -> JsonType:
        """
        Gets the property of a package, or None if the package or package property is not set

        Args:
            package_id: the package's identifier
            property_name: the name of the property

        Returns:
            property value or None if no such property exists
        """
        return self.dsu.get_package_property(package_id, property_name)

    def set_package_property(self, package_id: str, property_name: str, property_value: JsonType):
        """
        Update the property of a package

        Args:
            package_id: the packae's identifier
            property_name: the name of the property
            property_value: the value of the property, must be JSON serialisable
        """
        self.dsu.set_package_property(package_id, property_name, property_value)

    def get_package_data(self, package_id: str, key: str) -> Union[bytes, str, None]:
        """
        Get binary or string data associated with a package configuration.

        Args:
            package_id: package identifier
            key: a key to locate the data (can only contain alphanumeric characters and underscores)

        Returns:
            data or None if no data is associated with the key
        """
        return self.dsu.get_package_data(package_id, key)

    def set_package_data(self, package_id: str, key: str, data: Union[bytes, str, None]):
        """
        Set binary or string data associated with this node.

        Args:
            package_id: package identifier
            key: a key to locate the data (can only contain alphanumeric characters and underscores)
            data: data to be stored
        """
        self.dsu.set_package_data(package_id, key, data)

    def add_link(self, link_id: str, from_node_id: str, from_port: Union[str, None], to_node_id: str,
                 to_port: Union[str, None]) -> str:
        """
        Add a link to the topology

        Args:
            link_id: a unique identifier for the link
            from_node_id: node id of the source node
            from_port: port name on the source node, can be omitted if the "from" node has only one output port
            to_node_id: node id of the destination node
            to_port: port name on the destination node, can be ommitted if the "to" node has only one input port

        Raises:
            InvalidLinkError: if the link cannot be added
        """

        if self.executor.get_link(link_id) is not None:
            raise InvalidLinkError(f"Link with id {link_id} already exists")

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
            if len(self.executor.get_outputs_from(from_node_id, from_port)) > 0:
                raise InvalidLinkError(
                    f"output port {from_node_id}/{from_port} is already connected and does not allow multiple connections")

        if not to_node_type.input_ports[to_port].allows_multiple_connections():
            if len(self.executor.get_inputs_to(to_node_id, to_port)) > 0:
                raise InvalidLinkError(
                    f"input port {to_node_id}/{to_port} is already connected and does not allow multiple connections")

        link = Link(link_id, from_node_id, from_port, to_node_id, to_port, from_link_type)
        self.executor.add_link(link)

    def get_node_ids(self) -> list[str]:
        """
        Get the ids of all nodes in the topology

        Returns:
            list of node ids
        """
        return self.executor.get_node_ids()

    def get_node_type(self, node_id: str) -> tuple[str, str]:
        """
        Get the node package and type for a given node

        Args:
            node_id: the id of the node to retrieve

        Returns:
            tuple (package_id, node_type_id)
        """
        node = self.executor.get_node(node_id)
        node_type = node.get_node_type()
        return self.schema.split_descriptor(node_type)

    def get_link_ids(self) -> list[str]:
        """
        Get the ids of all links in the topology

        Returns:
            list of link ids
        """
        return self.executor.get_link_ids()

    def get_link(self, link_id:str) -> tuple[str, str, str, str]:
        """
        Get the link details for a given link

        Args:
            link_id: the id of the link to retrieve

        Returns:
            tuple (from_node_id,from_port,to_node_id,to_port)
        """
        link = self.executor.get_link(link_id)
        return (link.from_node_id, link.from_port, link.to_node_id, link.to_port)

    def get_output_port_names(self, node_id: str) -> list[str]:
        """
        Get the output port names for a given node

        Args:
            node_id: the id of the node

        Returns:
            list of output port names
        """
        node = self.executor.get_node(node_id)
        node_type = self.schema.get_node_type(node.get_node_type())
        return [name for (name, _) in node_type.get_output_ports()]

    def get_input_port_names(self, node_id: str) -> list[str]:
        """
        Get the input port names for a given node

        Args:
            node_id: the id of the node

        Returns:
            list of input port names
        """
        node = self.executor.get_node(node_id)
        node_type = self.schema.get_node_type(node.get_node_type())
        return [name for (name, _) in node_type.get_input_ports()]

    def get_metadata(self) -> dict[str, JsonType]:
        """
        Get the metadata of the topology

        Returns:
            A dictionary containing the metadata
        """
        return self.executor.get_metadata()

    def get_node_properties(self, node_id: str) -> dict[str, JsonType]:
        """
        Get the properties for the specified node

        Args:
            node_id: the node identifier

        Returns:
            A dictionary containing the properties defined for that node
        """
        return self.dsu.get_node_properties(node_id)

    def get_package_properties(self, package_id: str) -> dict[str, JsonType]:
        """
        Get the properties for the specified package

        Args:
            package_id: the package identifier

        Returns:
            A dictionary containing the properties defined for that package
        """
        return self.dsu.get_package_properties(package_id)
