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

import unittest
import tempfile

from hyrrokkin.api.topology import Topology

numbergraph_package = "hyrrokkin.example_packages.numbergraph"

class BasicTests(unittest.TestCase):

    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)

    def __get_test_topology(self, status_handler=None, execution_handler=None):

        t = Topology(tempfile.mkdtemp(), [numbergraph_package], status_handler = status_handler, execution_handler = execution_handler)
        t.add_node("n0", "numbergraph:number_input_node", {"value": 99})
        t.add_node("n1", "numbergraph:prime_factors_node", {})
        t.add_node("n2", "numbergraph:number_display_node", {})

        t.add_link("l0", "n0", "data_out", "n1", "data_in")
        t.add_link("l1", "n1", "data_out", "n2", "integerlist_data_in")
        return t

    def test1(self):
        status_messages = []
        execution_events = []
        t = Topology(tempfile.mkdtemp(),[numbergraph_package], status_handler=lambda *msg: status_messages.append(msg),
                     execution_handler=lambda *event: execution_events.append(event))
        t.add_node("n1", "numbergraph:prime_factors_node",{})

        test_outputs = []
        self.assertTrue(t.run(inject_input_values={"n1:data_in":99},output_listeners={"n1:data_out": lambda v: test_outputs.append(v)}))
        self.assertEqual(len(test_outputs),1)
        self.assertEqual(test_outputs[0],[3,3,11])
        self.assertEqual(status_messages,[('numbergraph', 'configuration', 'loaded cache (0 items)', 'info'), ('numbergraph', 'configuration', 'saved cache (1 items)', 'info')])
        self.assertEqual(list(map(lambda x:x[1:],execution_events)),[('n1', 'pending', None, False), ('n1', 'executing', None, False), ('n1', 'executed', None, False)])

    def test2(self):
        status_messages = []
        execution_events = []
        t = self.__get_test_topology(status_handler=lambda *msg: status_messages.append(msg),
                     execution_handler=lambda *event: execution_events.append(event))
        test_outputs = []
        self.assertTrue(t.run(output_listeners={"n1:data_out": lambda v: test_outputs.append(v)}))
        self.assertEqual(len(test_outputs), 1)
        self.assertEqual(test_outputs[0],[3,3,11])
        self.assertEqual(status_messages,[('numbergraph', 'configuration', 'loaded cache (0 items)', 'info'),  ('n2', 'node', '[[3, 3, 11]]', 'info'), ('numbergraph', 'configuration', 'saved cache (1 items)', 'info')])
        self.assertEqual(list(map(lambda x:x[1:],execution_events)),[('n0', 'pending', None, False), ('n1', 'pending', None, False), ('n2', 'pending', None, False), ('n0', 'executing', None, False), ('n0', 'executed', None, False), ('n1', 'executing', None, False), ('n1', 'executed', None, False), ('n2', 'executing', None, False), ('n2', 'executed', None, False)])

        status_messages = []
        t.set_node_property("n0","value",999)
        test_outputs = []
        self.assertTrue(t.run(output_listeners={"n1:data_out":lambda v: test_outputs.append(v)}))
        self.assertEqual(len(test_outputs), 1)
        self.assertEqual(status_messages,[('numbergraph', 'configuration', 'loaded cache (1 items)', 'info'), ('n2', 'node', '[[3, 3, 3, 37]]', 'info'), ('numbergraph', 'configuration', 'saved cache (2 items)', 'info')])
        self.assertEqual(test_outputs[0], [3, 3, 3, 37])

    def test3(self):
        t = self.__get_test_topology()

        received_messages = []

        session = t.create_interactive_session()

        client_service_n0 = session.attach_node_client("n0","test")
        client_service_n0.send_message(100)

        client_service_n2 = session.attach_node_client("n2","test")
        client_service_n2.set_message_handler(lambda msg: received_messages.append(msg) if msg else None)
        session.run(lambda: session.stop())

        self.assertEqual(received_messages,['[[2, 2, 5, 5]]'])

    def test4(self):

        with tempfile.NamedTemporaryFile(suffix=".zip", delete=True) as saved:

            t = self.__get_test_topology()
            with open(saved.name, "wb") as f:
                t.save_zip(f)

            t2 = Topology(tempfile.mkdtemp(),[numbergraph_package])

            with open(saved.name, "rb") as f:
                t2.load_zip(f)

            test_outputs = []
            self.assertTrue(t.run(output_listeners={"n1:data_out": lambda v: test_outputs.append(v)}))
            self.assertEqual(test_outputs, [[3, 3, 11]])


    def test5(self):

        with tempfile.NamedTemporaryFile(suffix=".zip", delete=True) as saved:
            t = Topology(tempfile.mkdtemp(), [numbergraph_package])
            t.add_node("n0", "numbergraph:number_input_node", {"value": 99})

            # test the merging of two topologies
            with open(saved.name, "wb") as f:
                t.save_zip(f)

            t2 = Topology(tempfile.mkdtemp(),[numbergraph_package])

            with open(saved.name, "rb") as f:
                node_renamings1 = t2.load_zip(f)
                node_renamings2 = t2.load_zip(f) # load a second copy of the topology

            self.assertEqual(len(node_renamings1),0)
            self.assertEqual(len(node_renamings2),1)
            test_outputs1 = []
            test_outputs2 = []
            self.assertTrue(t2.run(output_listeners={
                "n0:data_out": lambda v: test_outputs1.append(v),
                node_renamings2["n0"]+":data_out":lambda v: test_outputs2.append(v)
            }))

            self.assertEqual(test_outputs1,[99])
            self.assertEqual(test_outputs2,[99])

    def test6(self):
        status_messages = []
        execution_events = []
        t = Topology(tempfile.mkdtemp(), [numbergraph_package], status_handler=lambda *msg:status_messages.append(msg),
                     execution_handler=lambda *event: execution_events.append(event))
        t.add_node("n0", "numbergraph:number_input_node", {"value": 1})
        t.add_node("n1", "numbergraph:prime_factors_node", {})
        t.add_node("n2", "numbergraph:number_display_node", {})

        t.add_link("l0", "n0", "data_out", "n1", "data_in")
        t.add_link("l1", "n1", "data_out", "n2", "integerlist_data_in")

        self.assertFalse(t.run())
        self.assertEqual(list(map(lambda x:x[1:3],execution_events)),[('n0', 'pending'), ('n1', 'pending'), ('n2','pending'), ('n0', 'executing'), ('n0', 'executed'), ('n1', 'executing'), ('n1', 'failed')])

if __name__ == '__main__':
    import logging
    logging.basicConfig(level=logging.INFO)
    unittest.main()