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

    async def run(self, inputs):
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