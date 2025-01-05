class NumberInputNode:

    def __init__(self, services):
        self.services = services

    def open_client(self,client_id, client_options, client_service):
        client_service.set_message_handler(lambda *msg: self.__handle_message(client_id, *msg))

    def __handle_message(self,client_id, value):
        if not isinstance(value,int):
            # warn that the client has provided an invalid value
            self.services.set_status_warning("New value passed by client is not integer")
        else:
            self.services.set_property("value", value)
            self.services.request_run()

    async def run(self, inputs):
        value = self.services.get_property("value", 10)
        return { "data_out": value }