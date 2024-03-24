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

from .client_service import ClientService

class Wrapper:

    def __init__(self, executor, network):
        self.executor = executor
        self.network = network
        self.instance = None
        self.client_services = {}

    def set_instance(self, instance):
        self.instance = instance

    def get_instance(self):
        return self.instance

    def open_client(self, client_id, client_options):

        def message_forwarder(*message_parts):
            # send a message to a client
            self.executor.message_update((self.get_type(), self.get_id()), client_id, *message_parts)

        client_service = ClientService(message_forwarder)
        self.client_services[client_id] = client_service
        try:
            if hasattr(self.instance, "open_client"):
                rec_fn = self.instance.open_client(client_id, client_options, lambda *msg: client_service.send_message(*msg))
                if rec_fn:
                    def safe_rec(*msg):
                        try:
                            rec_fn(*msg)
                        except Exception as ex:
                            self.logger.exception(f"Error receiving message into {str(self)}")

                    client_service.set_message_handler(lambda *msg: safe_rec(*msg))
        except:
            self.logger.exception(f"Error in open_client for {str(self)}")

    def recv_message(self, client_id, *message):
        if client_id in self.client_services:
            self.client_services[client_id].handle_message(*message)

    def close_client(self, client_id):
        if client_id in self.client_services:
            client_service = self.client_services[client_id]
            client_service.close()
            try:
                if hasattr(self.instance, "close_client"):
                    self.instance.close_client(client_id)
            except:
                self.logger.exception(f"Error in close_client for {str(self)}")
            del self.client_services[client_id]

    def close(self):
        try:
            if hasattr(self.instance, "close"):
                self.instance.close()
        except:
            self.logger.exception(f"Error in close for {str(self)}")

