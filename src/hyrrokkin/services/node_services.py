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

import typing
from hyrrokkin.base.configuration_base import ConfigurationBase
from hyrrokkin.exceptions.node_execution_failed import NodeExecutionFailed
from hyrrokkin.services.status_states import StatusStates

class NodeServices:

    """
    Defines a set of services that a Hyrrokkin node can access.
    """

    def __init__(self, node_id: str):
        self.node_id = node_id
        self.wrapper = None

    def get_node_id(self) -> str:
        """
        :return: a string containing the node's unique ID
        """
        return self.node_id

    def set_status_info(self, status_message:str):
        """
        Set an info status message for the node.

        :param status_message: a short descriptive message or empty string
        """
        self.wrapper.set_status(StatusStates.info.value, status_message)

    def set_status_warning(self, status_message:str):
        """
        Set a warning status message for the node.

        :param status_message: a short descriptive message or empty string
        """
        self.wrapper.set_status(StatusStates.warning.value, status_message)

    def set_status_error(self, status_message:str):
        """
        Set an error status message for the node.

        :param status_message: a short descriptive message or empty string
        """
        self.wrapper.set_status(StatusStates.error.value, status_message)

    def clear_status(self):
        """
        Clear any previous status message on the node
        """
        self.wrapper.set_status(StatusStates.clear.value, "")

    def raise_execution_error(self, error_message:str, from_exn:Exception=None):
        """
        Raise an exception due to an execution failure

        :param error_message: short text describing the failure
        :param from_exn: optional, an exception that is the cause of the failure
        """
        exn = NodeExecutionFailed(self.node_id, error_message)
        if from_exn:
            raise exn from from_exn
        else:
            raise exn

    def get_property(self, property_name:str, default_value=None):
        """
        Get the current value for the node's property

        :param property_name: the name of the property
        :param default_value: a default value to return if the named property is not defined on the node
        :return: property value
        """
        stored_value = self.wrapper.get_property(property_name)
        if stored_value is None:
            return default_value
        else:
            return stored_value

    def set_property(self, property_name:str, property_value):
        """
        Set the current value for the node's property

        :param property_name: the name of the property
        :param property_value: the property value

        :notes: property values MUST be JSON-serialisable
        """
        self.wrapper.set_property(property_name, property_value)

    def open_file(self, path:str, mode:str="r", is_temporary=False, **kwargs) -> typing.Union[typing.TextIO,typing.BinaryIO]:
        """
        Open a file a within this node's filestore.

        If is_temporary is False, data written to these files will be persisted when the topology to which this node belongs is saved and reloaded.

        :param path: the relative path to the file within the filestore
        :param mode: the mode with which the file is to be opened
        :param is_temporary: whether the file should be persisted when the network is saved
        :param kwargs: other arguments to the open call

        :return: opened file
        :raises: exception if file cannot be opened

        :notes: This method calls Python's builtin open function.  For a description of the available arguments to the open function, see https://docs.python.org/3/library/functions.html#open
        """
        return self.wrapper.open_file(path, mode, is_temporary, **kwargs)

    def get_configuration(self) -> typing.Union[None,ConfigurationBase]:
        """
        Obtain a configuration object if defined for the node's package.

        :return: a configuration object or None
        """
        return self.wrapper.get_configuration().get_instance()





