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

from hyrrokkin.api.topology import Topology
from hyrrokkin.utils.yaml_exporter import export_to_yaml

logging.basicConfig(level=logging.INFO)

numberstream_package = "hyrrokkin_example_packages.numberstream"

test_yaml = """
metadata:
  name: test topology
configuration:
  numberstream:
    key1: value1
nodes:
  n0:
    type: numberstream:number_producer
    properties:
      value: 99
  n1:
    type: numberstream:number_transformer
    properties:
      fn: 'lambda x: x*2'
  n2:
    type: numberstream:number_aggregator
    properties: {}
  n3:
    type: numberstream:number_display
    properties: {}
links:
- n0 => n1
- n1 => n2
- n2 => n3
"""


class YamlImportTests(unittest.TestCase):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def test1(self):
        t = Topology(tempfile.mkdtemp(),[numberstream_package])
        t.set_metadata({"name":"test topology"})
        t.set_package_property("numberstream","key1","value1")
        t.add_node("n0", "numberstream:number_producer", {"value": 99})
        t.add_node("n1", "numberstream:number_transformer", {"fn": "lambda x: x*2"})
        t.add_node("n2", "numberstream:number_aggregator", {})
        t.add_node("n3", "numberstream:number_display", {})
        t.add_link("l0", "n0", "data_out", "n1", "data_in")
        t.add_link("l1", "n1", "data_out", "n2", "data_in")
        t.add_link("l2", "n2", "data_out", "n3", "data_in")

        with tempfile.NamedTemporaryFile(suffix=".yaml", delete=True) as yamlf:
            with open(yamlf.name,"w") as of:
                export_to_yaml(t, of)
            with open(yamlf.name) as f:
                self.assertEqual(test_yaml.strip(),f.read().strip())


