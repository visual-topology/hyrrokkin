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

import json

class NumberDisplayNode:

    def __init__(self, services):
        self.services = services
        self.clients = {}

    def connections_changed(self, input_connection_counts, output_connection_counts):
        nr_integer_inputs = input_connection_counts.get("integer_data_in",0)
        nr_integerlist_inputs = input_connection_counts.get("integerlist_data_in",0)
        self.services.set_status_info(f"{nr_integer_inputs} input integers, {nr_integerlist_inputs} input integerlists")

    def reset_run(self):
        for client_id in self.clients:
            self.clients[client_id].send_message(None)

    def run(self, inputs):
        input_values = inputs.get("integer_data_in",[])+inputs.get("integerlist_data_in",[])
        txt = json.dumps(input_values)
        self.services.set_status_info(txt)
        for client_service in self.clients.values():
            client_service.send_message(txt)

    def open_client(self, client_id, client_options, client_service):
        self.clients[client_id] = client_service

    def close_client(self, client_id):
        del self.clients[client_id]

    def close(self):
        pass