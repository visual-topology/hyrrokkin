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

from hyrrokkin.base.client_service_base import ClientServiceBase

class TopologyInteractor:

    def __init__(self, executor, client_service_classes:tuple[str,str]):
        self.executor = executor
        self.client_service_classes = client_service_classes # (client-side,execution-side)

    def attach_node_client(self, node_id: str, client_id: str | tuple[str, str], client_options: dict = {}) -> ClientServiceBase:
        """
        Attach a client instance to a node.  Any client already attached to the node with the same client_id
        will be detached.

        Args:
            node_id: the node to which the client is to be attached
            client_id: a identifier for the client, unique in the context of the node
            client_options: optional, a dictionary with extra parameters from the client

        Returns:
             an object which implements the ClientService API and provides methods to interact with the client

        """
        return self.executor.attach_client(("node", node_id), client_id, client_options, self.client_service_classes)

    def detach_node_client(self, node_id: str, client_id: str | tuple[str, str]):
        """
        Detach a client instance from a node

        Args:
            node_id: the node to which the client is to be attached
            client_id: an identifier for the client
        """
        self.executor.detach_client(("node", node_id), client_id)

    def attach_configuration_client(self, package_id: str, client_id: str | tuple[str, str], client_options: dict = {}) -> ClientServiceBase:
        """
        Attach a client instance to a package configuration

        Args:
            package_id: the package configuration to which the client is to be attached
            client_id: an identifier for the client, unique in the context of the package configuration
            client_options: optional, a dictionary with extra parameters for the client

        Returns:
             an object which implements the ClientService API and provides methods to interact with the client
        """
        return self.executor.attach_client(("configuration", package_id), client_id, client_options, self.client_service_classes)

    def detach_configuration_client(self, package_id: str, client_id: str | tuple[str, str]):
        """
        Detach a client instance from a package configuration

        Args:
            package_id: the node to which the client is to be attached
            client_id: an identifier for the client
        """
        return self.executor.detach_client(("configuration", package_id), client_id)

    def pause(self):
        self.executor.pause()

    def resume(self):
        self.executor.resume()

    def run(self, execution_complete_callback) -> None:
        """
        Start and wait for the execution to be terminated (by calling the stop method)

        Args:
            execution_complete_callback: a function that is called whenever all nodes in the topology have finished execution

        """
        if execution_complete_callback:
            self.executor.set_execution_complete_callback(execution_complete_callback)

        self.executor.start()
        self.executor.close()

    def stop(self) -> None:
        """
        Stop the current execution, callable from another thread during the execution of wait

        Notes:
            the run method will return once any current node executions complete
        """
        self.executor.stop()
