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
import json

from hyrrokkin.api.topology import Topology

numberstream_package = "hyrrokkin_example_packages.numberstream"

class BasicTests(unittest.TestCase):

    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)

    def test1(self):
        t = Topology(tempfile.mkdtemp(),[numberstream_package])
        t.add_node("n0","numberstream:number_producer",{"value":99})
        t.add_node("n1", "numberstream:number_transformer", {"fn":"lambda x: x*2"})
        t.add_node("n2","numberstream:number_aggregator", {})
        t.add_node("n3", "numberstream:number_display", {})
        t.add_link("l0","n0","data_out","n1","data_in")
        t.add_link("l1", "n1", "data_out", "n2", "data_in")
        t.add_link("l2", "n2", "data_out", "n3", "data_in")

        received_messages = []
        sender = t.attach_node_client("n3","test",lambda *msg: received_messages.append(msg))
        sender("Hello","World")
        self.assertEqual(len(received_messages), 0)

        self.assertTrue(t.run())

        self.assertEqual(len(received_messages),1)
        self.assertEqual(received_messages[0],("Echo","Hello","World"))

        self.assertEqual({"data_out": 99},t.get_node_outputs("n0"))
        self.assertEqual({"data_out": 198}, t.get_node_outputs("n1"))
        self.assertEqual({"data_out": 198}, t.get_node_outputs("n2"))
        self.assertEqual(json.dumps([198]),str(t.get_node_data("n3","results"),"utf-8"))

    def test2(self):

        with tempfile.NamedTemporaryFile(suffix=".zip", delete=True) as saved:

            t = Topology(tempfile.mkdtemp(),[numberstream_package])
            t.add_node("n0", "numberstream:number_producer", {"value": 99})
            t.add_node("n1", "numberstream:number_aggregator", {})
            t.add_link("l0", "n0", "data_out", "n1", "data_in")

            with open(saved.name, "wb") as f:
                t.save(f)

            t2 = Topology(tempfile.mkdtemp(),[numberstream_package])

            with open(saved.name, "rb") as f:
                t2.load(f)

            self.assertTrue(t2.run())

            self.assertEqual({"data_out":99},t2.get_node_outputs("n0"))

    def test3(self):
        t = Topology(tempfile.mkdtemp(), [numberstream_package])
        t.add_node("n0","numberstream:number_producer",{"value":99})
        t.add_node("n1","numberstream:number_aggregator", {})
        t.add_link("l0","n0","data_out","n1","data_in")

        self.assertTrue(t.run())
        self.assertEqual({"data_out":99},t.get_node_outputs("n0"))
        self.assertEqual({"data_out": 99}, t.get_node_outputs("n1"))

        t.set_node_property("n0","value",100)

        self.assertTrue(t.run())
        self.assertEqual({"data_out":100},t.get_node_outputs("n0"))
        self.assertEqual({"data_out": 100}, t.get_node_outputs("n1"))

    def test4(self):
        t = Topology(tempfile.mkdtemp(), [numberstream_package])
        t.add_node("n0a","numberstream:number_producer", {"value" : 99})
        t.add_node("n0b","numberstream:number_producer", {"value" : 100})
        t.add_node("n1","numberstream:number_aggregator", {})
        t.add_link("l0","n0a","data_out", "n1","data_in")
        t.add_link("l1","n0b", "data_out", "n1", "data_in")

        self.assertTrue(t.run())

        self.assertEqual({"data_out":99},t.get_node_outputs("n0a"))
        self.assertEqual({"data_out":100},t.get_node_outputs("n0b"))
        self.assertEqual({"data_out": 199}, t.get_node_outputs("n1"))

    def test_merge(self):

        with tempfile.NamedTemporaryFile(suffix=".zip", delete=True) as saved:

            # test the merging of two topologies
            t = Topology(tempfile.mkdtemp(),[numberstream_package])
            t.add_node("n0", "numberstream:number_producer", {"value": 99})
            t.add_node("n1", "numberstream:number_aggregator", {})
            t.add_link("l0", "n0", "data_out", "n1", "data_in")

            with open(saved.name, "wb") as f:
                t.save(f)

            t2 = Topology(tempfile.mkdtemp(),[numberstream_package])

            with open(saved.name, "rb") as f:
                node_renamings1 = t2.load(f)
                node_renamings2 = t2.load(f) # load a second copy of the topology

            self.assertEqual(len(node_renamings1),0)
            self.assertEqual(len(node_renamings2),2)
            self.assertTrue(t2.run())

            self.assertEqual({"data_out":99},t2.get_node_outputs("n0"))
            self.assertEqual({"data_out":99},t2.get_node_outputs(node_renamings2["n0"]))

if __name__ == '__main__':
    import logging
    logging.basicConfig(level=logging.INFO)
    unittest.main()