import hyrrokkin.services.client_service
from hyrrokkin.utils.type_hints import JsonType
from hyrrokkin.utils.type_hints import ClientMessageProtocol
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
        self.executor.wait()

    def stop(self) -> None:
        """
        Stop the current execution, callable from another thread during the execution of wait

        Notes:
            the run method will return once any current node executions complete
        """
        self.executor.stop()
