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
from hyrrokkin.utils.yaml_importer import import_from_yaml

logging.basicConfig(level=logging.INFO)

numberstream_package = "hyrrokkin.example_packages.numberstream"

test_yaml = """
nodes:
  n0:
    type: numberstream:number_producer
    properties:
      value: 200
  n1:
    type: numberstream:number_aggregator
    
links:
  - n0 => n1  
"""

class YamlImportTests(unittest.TestCase):

    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)


    def test1(self):
        t = Topology(tempfile.mkdtemp(),[numberstream_package])
        with tempfile.NamedTemporaryFile(suffix=".yaml", delete=True) as yamlf:
            with open(yamlf.name,"w") as of:
                of.write(test_yaml)
            with open(yamlf.name) as f:
                import_from_yaml(t,f)

        self.assertTrue(t.run())

        self.assertEqual({"data_out":200},t.get_node_outputs("n0"))
