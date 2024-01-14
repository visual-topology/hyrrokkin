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

class ClientService:

    def __init__(self, message_forwarder):
        self.message_forwarder = message_forwarder
        self.message_handler = None
        self.pending_messages = [] # messages to the node that cannot yet be delivered without a message handler
        self.is_open = True

    def send_message(self, *msg):
        if self.is_open:
            self.message_forwarder(*msg)
            return True
        return False

    def set_message_handler(self, message_handler):
        if self.is_open:
            self.message_handler = message_handler
            if self.message_handler:
                for message in self.pending_messages:
                    self.message_handler(*message)
                self.pending_messages = []

    def handle_message(self, *message):
        if self.is_open:
            if self.message_handler:
                self.message_handler(*message)
            else:
                self.pending_messages.append(message)

    def close(self):
        self.is_open = False
        self.message_forwarder = None

