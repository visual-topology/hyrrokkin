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
from typing import Any, Callable

class ClientServiceBase:

    @abstractmethod
    def __init__(self):
        """
        Creates an instance of an object used to communicate between a node or configuration
        instance and one of its clients.  The object should implement all of the methods defined
        in this abstract base class.  One instance will be passed to the client and one to the node or configuration.
        """
        pass

    @abstractmethod
    def open(self, message_forwarder: Callable[...,None] ):
        """
        Ater construction, this method will be called to attach a function that will forward a message to the peer
        client service object

        Args:
            message_forwarder: a function that can be called with a message consisting of one or more arguments
        """
        pass

    @abstractmethod
    def send_message(self, *msg:Any):
        """
        Send a message to the peer client-services object

        Args:
            *msg: a message consisting of one or more arguments
        """
        pass

    @abstractmethod
    def set_message_handler(self, message_handler: Callable[...,None]):
        """
        Set up a handler function to be called when a message is received from the
        peer client service object

        Note, any messages received by this client service instance before a message handler
        is set up should be queued and not lost.  The implementation should support this.

        Args:
            message_handler: a function that will consume a message consisting of one or more arguments
        """
        pass

    @abstractmethod
    def handle_message(self, *message:Any):
        """
        Called by hyrrokkin to pass a message received from the remote client service object

        Args:
            *message: a message consisting of one or more arguments
        """
        pass

    @abstractmethod
    def close(self):
        """
        Called by hyrrokkin when the client service link is shut down.  Free all resources.
        """
        pass



