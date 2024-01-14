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

        t.run(cache_outputs_for_nodes="*")

        self.assertEqual(len(received_messages),1)
        self.assertEqual(received_messages[0],("Echo","Hello","World"))

        self.assertEqual({"data_out": 99},t.get_node_outputs("n0"))
        self.assertEqual({"data_out": 198}, t.get_node_outputs("n1"))
        self.assertEqual({"data_out": 198}, t.get_node_outputs("n2"))
        self.assertEqual(json.dumps([198]),t.get_node_data("n3","results"))

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

            t2.run(cache_outputs_for_nodes="*")

            self.assertEqual({"data_out":99},t2.get_node_outputs("n0"))

    def test3(self):
        t = Topology(tempfile.mkdtemp(), [numberstream_package])
        t.add_node("n0","numberstream:number_producer",{"value":99})
        t.add_node("n1","numberstream:number_aggregator", {})
        t.add_link("l0","n0","data_out","n1","data_in")

        t.run(cache_outputs_for_nodes="*")
        self.assertEqual({"data_out":99},t.get_node_outputs("n0"))
        self.assertEqual({"data_out": 99}, t.get_node_outputs("n1"))

        t.set_node_property("n0","value",100)

        t.run(cache_outputs_for_nodes=["n0","n1"])
        self.assertEqual({"data_out":100},t.get_node_outputs("n0"))
        self.assertEqual({"data_out": 100}, t.get_node_outputs("n1"))

    def test4(self):
        t = Topology(tempfile.mkdtemp(), [numberstream_package])
        t.add_node("n0a","numberstream:number_producer", {"value" : 99})
        t.add_node("n0b","numberstream:number_producer", {"value" : 100})
        t.add_node("n1","numberstream:number_aggregator", {})
        t.add_link("l0","n0a","data_out", "n1","data_in")
        t.add_link("l1","n0b", "data_out", "n1", "data_in")

        t.run(cache_outputs_for_nodes="*")

        self.assertEqual({"data_out":99},t.get_node_outputs("n0a"))
        self.assertEqual({"data_out":100},t.get_node_outputs("n0b"))
        self.assertEqual({"data_out": 199}, t.get_node_outputs("n1"))

    def test5(self):
        t = Topology(tempfile.mkdtemp(), [numberstream_package])
        t.add_node("n0","numberstream:number_pullstream_producer",{"min_value":0,"max_value":5})
        t.add_node("n1","numberstream:number_pullstream_transformer", { "fn": "lambda x:x+1"})
        t.add_node("n2","numberstream:number_pullstream_aggregator", { "fn": "lambda x: sum(x)"})
        t.add_link("l0","n0","data_out","n1","data_in")
        t.add_link("l1","n1", "data_out","n2", "data_in")

        t.run(cache_outputs_for_nodes=["n2"])
        self.assertIsNone(t.get_node_outputs("n0"))
        self.assertEqual({"data_out":21},t.get_node_outputs("n2"))

    def test5a(self):
        t = Topology(tempfile.mkdtemp(), [numberstream_package])
        t.add_node("n0", "numberstream:number_pushstream_producer", {"min_value": 0, "max_value": 5})
        t.add_node("n1", "numberstream:number_pushstream_transformer", {"fn": "lambda x:x*2"})
        t.add_node("n2", "numberstream:number_pushstream_aggregator", {"fn": "lambda x: sum(x)"})
        t.add_link("l0", "n0", "data_out", "n1", "data_in")
        t.add_link("l1", "n1", "data_out", "n2", "data_in")

        t.run(cache_outputs_for_nodes=["n2"])
        self.assertIsNone(t.get_node_outputs("n0"))
        self.assertEqual({"data_out": 30}, t.get_node_outputs("n2"))

    def test5b(self):
        t = Topology(tempfile.mkdtemp(), [numberstream_package])
        t.add_node("n0a", "numberstream:number_pushstream_producer", {"min_value": 0, "max_value": 5})
        t.add_node("n0b", "numberstream:number_pushstream_producer", {"min_value": 0, "max_value": 4})
        t.add_node("n1", "numberstream:number_pushstream_aggregator", {"fn": "lambda x: sum(x)"})
        t.add_link("l0", "n0a", "data_out", "n1", "data_in")
        t.add_link("l1", "n0b", "data_out", "n1", "data_in")

        t.run(cache_outputs_for_nodes=["n1"])
        self.assertIsNone(t.get_node_outputs("n0"))
        self.assertEqual({"data_out": 25}, t.get_node_outputs("n1"))

    def test6(self):
        t = Topology(tempfile.mkdtemp(), [numberstream_package])
        t.add_node("n0", "numberstream:number_pullstream_producer", {"min_value": 0, "max_value": 5})
        t.add_node("n1", "numberstream:number_pullstream_aggregator", {"fn": "lambda x: sum(x)"})
        t.add_node("n2", "numberstream:number_pullstream_aggregator", {"fn": "lambda x: len(x)"})

        t.add_link("l0", "n0", "data_out", "n1", "data_in")
        t.add_link("l1", "n0", "data_out", "n2", "data_in")

        t.run(cache_outputs_for_nodes=["n1","n2"])
        self.assertIsNone(t.get_node_outputs("n0"))
        self.assertEqual({"data_out":15},t.get_node_outputs("n1"))
        self.assertEqual({"data_out":6},t.get_node_outputs("n2"))


if __name__ == '__main__':
    import logging
    logging.basicConfig(level=logging.INFO)
    unittest.main()