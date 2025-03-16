import json

class NumberDisplayNode:

    def __init__(self, services):
        self.services = services
        self.clients = {}

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