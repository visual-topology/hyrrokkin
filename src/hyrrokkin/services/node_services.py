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

from hyrrokkin.utils.type_hints import JsonType

class NodeServices:

    """
    Defines a set of services that a Hyrrokkin node can access.
    """

    def __init__(self, node_id: str):
        self.node_id = node_id
        self.wrapper = None

    def get_node_id(self) -> str:
        """
        Returns:
            a string containing the node's unique ID
        """
        return self.node_id

    def set_status_info(self, status_message:str):
        """
        Set an info status message for the node.

        Args:
            status_message: a short descriptive message or empty string
        """
        self.wrapper.set_status(StatusStates.info.value, status_message)

    def set_status_warning(self, status_message:str):
        """
        Set a warning status message for the node.

        Args:
            status_message: a short descriptive message or empty string
        """
        self.wrapper.set_status(StatusStates.warning.value, status_message)

    def set_status_error(self, status_message:str):
        """
        Set an error status message for the node.

        Args:
            status_message: a short descriptive message or empty string
        """
        self.wrapper.set_status(StatusStates.error.value, status_message)

    def clear_status(self):
        """
        Clear any previous status message on the node
        """
        self.wrapper.set_status(StatusStates.clear.value, "")

    def set_execution_state(self, execution_state:str):
        """
        Manually set the execution state of the node

        Args:
            execution_state: one of "pending", "executing", "executed", "failed"

        Notes:
            Normally this is tracked by hyrrokkin.  After making this call, the execution state will be
            tracked manually for the node involved.
        """
        self.wrapper.set_execution_state(execution_state)

    def request_run(self):
        """
        Request that this node be run
        """
        self.wrapper.request_execution()

    def get_property(self, property_name:str, default_value:JsonType=None) -> JsonType:
        """
        Get the current value for the node's property

        Args:
            property_name: the name of the property
            default_value: a default value to return if the named property is not defined on the node
        
        Returns:
            the property value
        """
        return self.wrapper.get_property(property_name, default_value)

    def set_property(self, property_name:str, property_value: JsonType):
        """
        Set the current value for the node's property

        Args:
            property_name: the name of the property
            property_value: the JSON-serialisable property value

        Notes: 
            property values MUST be JSON-serialisable
        """
        self.wrapper.set_property(property_name, property_value)

    def get_data(self, key:str) -> typing.Union[bytes,None]:
        """
        Get binary data (bytes) associated with this node.

        Args:
            key: a key to locate the data (can only contain alphanumeric characters and underscores)

        Returns:
            data or None if no data is associated with the key
        """
        return self.wrapper.get_data(key)

    def set_data(self, key:str, data:typing.Union[bytes,None]):
        """
        Set binary data (bytes) associated with this node.

        Args:
            key: a key to locate the data (can only contain alphanumeric characters and underscores)
            data: binary data (bytes) to be stored (or None to remove previously stored data for this key)
        """
        self.wrapper.set_data(key, data)

    def get_configuration(self) -> typing.Union[None,ConfigurationBase]:
        """
        Obtain a configuration object if defined for the node's package.

        Returns:
            a configuration object or None
        """
        return self.wrapper.get_configuration().get_instance()

    def fire_output_port_event(self, output_port_name:str, event_type:str, event_value:object=None):
        """
        Send an event from an output port to all nodes connected to that output port

        Args:
            output_port_name: the name of the output port
            event_type: the type of event to fire
            event_value: an optional value associated with the event
        """
        return self.wrapper.fire_output_port_event(output_port_name, event_type, event_value)




    




