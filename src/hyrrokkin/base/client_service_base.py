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

class ClientServiceBase:

    @abstractmethod
    def open(self, message_forwarder):
        # called when attached to a node/configuration
        # message_forwarder is a function which sends a message to the node or configuration
        pass

    @abstractmethod
    def close(self):
        # called when detached from a node/configuration
        pass

    @abstractmethod
    def send_message_from_client(self, *msg):
        # send a message to the node/configuration
        pass

    @abstractmethod
    def send_message_to_client(self, *msg):
        # send a message to the node/configuration
        pass

    @abstractmethod
    def set_to_client_message_handler(self, message_handler):
        # set a message handler for messages sent from the node or configuration to the client
        pass

    @abstractmethod
    def set_from_client_message_handler(self, message_handler):
        # set a message handler for messages sent to the node or configuration from the client
        pass



