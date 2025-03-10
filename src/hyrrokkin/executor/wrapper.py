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

import logging

from hyrrokkin.utils.resource_loader import ResourceLoader
from hyrrokkin.utils.data_store_utils import DataStoreUtils

class Wrapper:

    def __init__(self, execution_engine, execution_folder):
        self.execution_engine = execution_engine
        self.execution_folder = execution_folder
        self.datastore_utils = DataStoreUtils(self.execution_folder)
        self.instance = None
        self.client_services = {}
        self.logger = logging.getLogger("NodeWrapper")

    def set_instance(self, instance):
        self.instance = instance

    def get_instance(self):
        return self.instance

    def get_datastore_utils(self):
        return self.datastore_utils

    async def load(self):
        if self.instance is not None and hasattr(self.instance, "load"):
            await self.instance.load()

    def open_client(self, client_id, client_options, client_service_class):
        if isinstance(client_id,list):
            client_id = tuple(client_id)
        def message_forwarder(*message_parts):
            # send a message to a client
            self.execution_engine.send_message(self.get_id(), self.get_type(), client_id, *message_parts)
        try:
            if hasattr(self.instance, "open_client"):
                cls = ResourceLoader.get_class(client_service_class)
                client_service = cls()
                client_service.open(message_forwarder)
                self.client_services[client_id] = client_service
                self.instance.open_client(client_id, client_options, client_service)
        except:
            self.logger.exception(f"Error in open_client for {str(self)}")

    def recv_message(self, client_id, *message):
        if isinstance(client_id,list):
            client_id = tuple(client_id)
        if client_id in self.client_services:
            self.client_services[client_id].handle_message(*message)

    def close_client(self, client_id):
        if isinstance(client_id,list):
            client_id = tuple(client_id)
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

