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


class NumberInputNode:

    def __init__(self, services):
        self.services = services

    def open_client(self,client_id, client_options, send_fn):
        return lambda *msg: self.__handle_message(client_id, *msg)

    def __handle_message(self,client_id,*msg):
        new_value = msg[0]
        if not (isinstance(new_value,int)):
            # warn that the client has provided an invalid value
            self.services.set_status_warning("New vlue requested by client is not integer")
        else:
            self.services.set_property("value",new_value)
            self.services.request_run()

    def reset_run(self):
        pass

    async def run(self, inputs):
        value = self.services.get_property("value", 10)
        return { "data_out": value }


