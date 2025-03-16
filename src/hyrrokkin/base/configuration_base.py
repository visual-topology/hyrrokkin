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


from abc import abstractmethod
from typing import Dict, List, Any

from hyrrokkin.utils.type_hints import ClientMessageProtocol
from hyrrokkin.executor.configuration_services import ConfigurationServices


class ConfigurationBase:

    @abstractmethod
    def __init__(self, services:ConfigurationServices):
        """
        Create an instance of this Configuration

        Args:
            services: an object providing useful services, for example to get or set property values
        """
        pass

    @abstractmethod
    async def load(self):
        """
        Load any resources associated with this Configuration
        """
        pass

    @abstractmethod
    def open_client(self, client_id:str, client_options:dict, send_fn:ClientMessageProtocol) -> ClientMessageProtocol:
        """
        Called when a client is attached to the configuration

        Arguments:
            client_id: a unique identifier for the client 
            client_options: a set of parameters accompanying the connection
            send_fn: a function that the node can use to send messages to the client

        Returns:
            a function that the client can use to send messages to the configuration

        """
        pass

    @abstractmethod
    def close_client(self, client_id:str):
        """
        Called when a client is detached from the configuration

        Arguments:
            client_id: the unique identifier of the client that is being detached

        Notes:
            a call to close_client is preceeded by a call to open_client with the same client_id
        """
        pass

    @abstractmethod
    def close(self):
        """
        Called before the configuration instance is deleted
        """
        pass

    