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

    def set_status_info(self, status_message: str):
        """
        Set an info status message for the configuration.

        :param status_message: a short descriptive message or empty string
        """
        self.wrapper.set_status(StatusStates.info.value, status_message)

    def set_status_warning(self, status_message: str):
        """
        Set a warning status message for the configuration.

        :param status_message: a short descriptive message or empty string
        """
        self.wrapper.set_status(StatusStates.warning.value, status_message)

    def set_status_error(self, status_message: str):
        """
        Set an error status message for the configuration.

        :param status_message: a short descriptive message or empty string
        """
        self.wrapper.set_status(StatusStates.error.value, status_message)

    def clear_status(self):
        """
        Clear any previous status message on the configuration
        """
        self.wrapper.set_status(StatusStates.clear.value, "")

    def get_property(self, property_name:str, default_value=None):
        """
        Get the current value for configuration's property

        :param property_name: the name of the property
        :param default_value: a default value to return if the named property is not defined on the configuration
        :return: property value
        """
        stored_value = self.wrapper.get_property(property_name)
        if stored_value is None:
            return default_value
        else:
            return stored_value

    def set_property(self, property_name:str, property_value):
        """
        Set the current value for the configuration's property

        :param property_name: the name of the property
        :param property_value: the property value

        :notes: property values MUST be JSON-serialisable
        """
        self.wrapper.set_property(property_name, property_value)

    def open_file(self, path:str, mode, is_temporary, **kwargs):
        """
        Open a file a within this configuration's filestore.

        Data written to these files will be persisted when the topology to which this configuration belongs is saved and reloaded.

        :param path: the relative path to the file within the filestore
        :param mode: the mode with which the file is to be opened
        :param is_temporary: whether the file should be persisted when the node is saved
        :param kwargs: other arguments to the open call

        :return: opened file
        :raises: exception if file cannot be opened

        :notes: This method calls Python's builtin open function.  For a description of the available arguments to the open function, see https://docs.python.org/3/library/functions.html#open
        """
        return self.wrapper.open_file(path, mode, is_temporary, **kwargs)
