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


class NumberSumNode:

    def __init__(self,services):
        self.services = services
        self.constant = services.get_property("constant",0) 
        services.set_property("constant",self.constant)
        self.clients = {}
        # if no configruation class is defined for this node's package, 
        # get_configuration() will return None
        self.configuration = services.get_configuration()
        self.is_readonly = self.configuration.get_is_readonly()
    
    def open_client(self,client_id, client_options, send_fn):
        self.clients[client_id] = send_fn
        if self.is_readonly:
            return None # ignore messages from this client 
        else:
            return lambda *msg: self.__handle_message(client_id, *msg)


    def __handle_message(self,client_id,*msg):
        new_constant = msg[0]
        if not (isinstance(new_constant,int) or isinstance(new_constant,float)):
            # warn that the client has provided an invalid value
            self.services.set_status_warning("New constant requested by client is neither integer nor float, ignoring") 
        if new_constant != self.constant:
            self.constant = new_constant
            self.services.set_property("constant",self.constant)
            self.service.request_run()
            # inform that the constant has been updated
            self.services.set_status_info("Constant updated, awaiting re-run")

    def close_client(self, client_id):
        del self.clients[client_id]

    def run(self, inputs):
        try:
            input_values = inputs.get("data_in",[])
            output_value  = sum(input_values)+self.constant
            for client_id in self.clients:
                self.clients[client_id](output_value)
                return { "data_out": output_value }
            # clear the status after a successful execution    
            self.services.clear_status()
        except Exception as ex:
            # something has gone wrong, set the status to error
            self.services.set_status_error(f"Run failed due to {str(ex)}") 
            # raising an exception within the run method indicates that the node has 
            # failed 
            raise

    def reset_run(self):
        for client_id in self.clients:
            self.clients[client_id](None)

    def connections_changed(self, input_connection_counts, output_connection_counts):
        if self.input_connection_counts["data_in"] == 0:
            self.services.set_status_warning("No inputs are currently connected")

