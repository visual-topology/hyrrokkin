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

from hyrrokkin.services.status_states import StatusStates

class ConfigurationServices:
    """
    Defines a set of services that a Hyrrokkin configuration can access.
    """

    def __init__(self, package_id):
        self.package_id = package_id
        self.wrapper = None

    def set_wrapper(self, wrapper):
        self.wrapper = wrapper

    def __report_status(self, status_state, status_message):
        self.wrapper.set_status(StatusStates.info.value, status_message)

    def set_status_info(self, status_message: str):
        """
        Set an info status message for the configuration.

        :param status_message: a short descriptive message or empty string
        """
        self.__report_status(StatusStates.info.value, status_message)

    def set_status_warning(self, status_message: str):
        """
        Set a warning status message for the configuration.

        :param status_message: a short descriptive message or empty string
        """
        self.__report_status(StatusStates.warning.value, status_message)

    def set_status_error(self, status_message: str):
        """
        Set an error status message for the configuration.

        :param status_message: a short descriptive message or empty string
        """
        self.__report_status(StatusStates.error.value, status_message)

    def clear_status(self):
        """
        Clear any previous status message on the configuration
        """
        self.__report_status(StatusStates.clear.value, "")

    def get_property(self, property_name:str, default_value=None):
        """
        Get the current value for configuration's property

        :param property_name: the name of the property
        :param default_value: a default value to return if the named property is not defined on the configuration
        :return: property value
        """
        return self.wrapper.get_property(property_name, default_value)

    def set_property(self, property_name:str, property_value):
        """
        Set the current value for the configuration's property

        :param property_name: the name of the property
        :param property_value: the property value

        :notes: property values MUST be JSON-serialisable
        """
        self.wrapper.set_property(property_name, property_value)

    def get_data(self, key: str) -> typing.Union[bytes, str]:
        """
        Get binary or string data associated with this package configuration.

        :param key: a key to locate the data (can only contain alphanumeric characters and underscores)

        :return: data or None if no data is associated with the key
        """
        return self.wrapper.get_data(key)

    def set_data(self, key: str, data: typing.Union[bytes, str]):
        """
        Set binary or string data associated with this package configuration.

        :param key: a key to locate the data (can only contain alphanumeric characters and underscores)
        :param data: data to be stored
        """
        self.wrapper.set_data(key, data)
