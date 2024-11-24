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


class ExecutionClient():

    def __init__(self, graph_executor, target_id, target_type, client_id, client_service, client_options, execution_client_service_class):
        self.graph_executor = graph_executor
        self.target_id = target_id
        self.target_type = target_type # node or configuration
        self.client_id = client_id
        self.client_service = client_service
        self.client_options = client_options
        self.execution_client_service_class = execution_client_service_class
        self.client_service.open(lambda *msg: self.send_message(*msg))
        self.pending_messages = []
        self.connected = False

    def set_connected(self):
        self.connected = True
        for message in self.pending_messages:
            self.graph_executor.forward_client_message(self.target_id, self.target_type, self.client_id, *message)
        self.pending_messages = []

    def get_execution_client_service_class(self):
        return self.execution_client_service_class

    def send_message(self, *msg):
        # send a message to the configuration or node
        if self.connected:
            self.graph_executor.forward_client_message(self.target_id, self.target_type, self.client_id, *msg)
        else:
            self.pending_messages.append(msg)

    def message_callback(self, *msg):
        self.client_service.handle_message(*msg)

    def disconnect(self):
        self.execution_thread = None

    def get_client_options(self):
        return self.client_options
