import asyncio
from test.hyrrokkin_test.hyrrokkin_example_apps.numberstream.nodes.number_input import NumberInput

from test.hyrrokkin_test.hyrrokkin_example_apps.numberstream.nodes.number_display import NumberDisplay

import logging


class HyrrokkinServicesCLI:
    STATUS_STATE_INFO = "info"
    STATUS_STATE_WARNING = "warning"
    STATUS_STATE_ERROR = "error"
    STATUS_STATE_CLEAR = ""

    def __init__(self, node_id: str):
        self.node_id = node_id
        self.properties = {}

    def set_wrapper(self, wrapper):
        pass

    def get_node_id(self):
        return self.node_id

    def add_event_handler(self, element_id, event_type, callback):
        pass

    def set_attributes(self, element_id, attributes, except_session_id=None):
        pass

    def set_status(self, state, status_message):
        if state == HyrrokkinServicesCLI.STATUS_STATE_ERROR:
            logging.error(status_message)
        elif state == HyrrokkinServicesCLI.STATUS_STATE_WARNING:
            logging.warning(status_message)
        elif state == HyrrokkinServicesCLI.STATUS_STATE_INFO:
            logging.info(status_message)

    def send_node_message(self, msg, for_session_id=None, except_session_id=None):
        pass

    def request_execution(self):
        pass

    def raise_execution_failed(self, message, from_exn=None):
        raise Exception("Node Execution Failed")

    def get_property(self, property_name, default_value=None):
        return self.properties.get(property_name, default_value)

    def set_property(self, property_name, property_value):
        self.properties[property_name] = property_value


async def run():
    n0_service = HyrrokkinServicesCLI('n0')
    n0_service.set_property('value', 99)
    with open('node_storage/n0/test', 'rb') as f:
        n0_service.set_property('test', f.read())
    n0 = NumberInput(n0_service)
    n0_outputs = await n0.execute({})
    n1_service = HyrrokkinServicesCLI('n1')
    n1 = NumberDisplay(n1_service)
    n1_outputs = await n1.execute({"data_in": [n0_outputs["data_out"]]})


asyncio.run(run())
