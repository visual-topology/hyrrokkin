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

class FileStorageTests(unittest.TestCase):

    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)

    def test1(self):

        with tempfile.NamedTemporaryFile(suffix=".zip", delete=True) as saved:

            t = Topology(tempfile.mkdtemp(),[numbergraph_package])
            t.add_node("n0", "numbergraph:integer_value_node", properties={"value": 99})

            test_binary1 = b"34723974"

            t.set_node_data("n0", "abc0", test_binary1)
            t.set_node_data("n0", "abc1", None)

            self.assertEqual(test_binary1, t.get_node_data("n0", "abc0"))
            self.assertIsNone(t.get_node_data("n0", "abc1"))

            with open(saved.name, "wb") as f:
                t.save_zip(f)

            t2 = Topology(tempfile.mkdtemp(),[numbergraph_package])

            with open(saved.name, "rb") as f:
                t2.load_zip(f)

            self.assertEqual(test_binary1, t2.get_node_data("n0", "abc0"))
            self.assertIsNone(t2.get_node_data("n0", "abc1"))


    def test2(self):
        with tempfile.NamedTemporaryFile(suffix=".zip", delete=True) as saved:

            test_binary1 = b"34723974"

            t = Topology(tempfile.mkdtemp(),[numbergraph_package])

            t.set_package_data("numbergraph","abc_0", test_binary1)

            with open(saved.name, "wb") as f:
                t.save_zip(f)

            t2 = Topology(tempfile.mkdtemp(),[numbergraph_package])

            with open(saved.name, "rb") as f:
                t2.load_zip(f)

            self.assertEqual(test_binary1, t2.get_package_data("numbergraph", "abc_0"))


if __name__ == '__main__':
    import logging
    logging.basicConfig(level=logging.INFO)
    unittest.main()