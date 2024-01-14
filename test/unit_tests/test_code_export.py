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

import logging
import unittest
import tempfile
import os.path

from hyrrokkin.api.topology import Topology
from hyrrokkin.export.code_exporter import CodeExporter

from utils.process_utils import run

logging.basicConfig(level=logging.INFO)

numberstream_package = "hyrrokkin_example_packages.numberstream"


class CodeExportTests(unittest.TestCase):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def setUp(self):
        pass

    def run_tracked(self, topology, from_nodes=[]):
        topology.run(
            node_executing_callback=lambda *args: self.track_input(*args),
            node_executed_callback=lambda *args: self.track_output(*args), from_nodes=from_nodes)

    def test1(self):
        with tempfile.TemporaryDirectory() as d:
            os.makedirs(d, exist_ok=True)
            with tempfile.NamedTemporaryFile(suffix=".zip", delete=True) as save_path:
                t = Topology(tempfile.mkdtemp(),[numberstream_package])
                t.set_package_property("numberstream", "offset", 0)
                t.add_node("n0", "numberstream:number_producer", {"value": 99})
                t.add_node("n1", "numberstream:number_aggregator", {})
                t.add_node("n2", "numberstream:number_display", {})
                t.add_link("l0", "n0", "data_out", "n1", "data_in")
                t.add_link("l1", "n1", "data_out", "n2", "data_in")

                t.save(save_path)

                ce = CodeExporter(t.schema,save_path, d, "export.py")
                ce.export()

                output = run(d, "export.py")
                display_path = os.path.join(d, "node","n2", "data", "results.text")
                with open(display_path) as f:
                    self.assertEqual("[99]",f.read())


if __name__ == '__main__':
    unittest.main()
