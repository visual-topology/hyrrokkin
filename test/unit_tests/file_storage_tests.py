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

numberstream_schema_path = "hyrrokkin_example_packages.numberstream"

class FileStorageTests(unittest.TestCase):

    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)

    def test1(self):

        with tempfile.NamedTemporaryFile(suffix=".zip", delete=True) as saved:

            t = Topology([numberstream_schema_path])
            t.add_node("n0", "numberstream:number_producer", {"value": 99})

            test_string1 = "ABC 123"
            test_string2 = "123 ABC"

            with t.open_node_file("n0","a/b/c.txt",mode="w") as f:
                f.write(test_string1)

            with t.open_node_file("n0", "a/b/c.txt", mode="w", is_temporary=True) as f:
                f.write(test_string2)

            with open(saved.name, "wb") as f:
                t.save(f)

            t2 = Topology([numberstream_schema_path])

            with open(saved.name, "rb") as f:
                t2.load(f)

            with t2.open_node_file("n0","a/b/c.txt","r") as f:
                self.assertEqual(test_string1,f.read())

            self.assertRaises(FileNotFoundError,lambda: t2.open_node_file("n0", "a/b/c.txt", "r", is_temporary=True))

    def test2(self):
        with tempfile.NamedTemporaryFile(suffix=".zip", delete=True) as saved:
            test_string1 = "ABC 123"
            test_string2 = "123 ABC"
            t = Topology([numberstream_schema_path])
            with t.open_configuration_file("numberstream","a.txt","w") as f:
                f.write(test_string1)
            with t.open_configuration_file("numberstream","a.txt","w",is_temporary=True) as f:
                f.write(test_string2)

            with open(saved.name, "wb") as f:
                t.save(f)

            t2 = Topology([numberstream_schema_path])

            with open(saved.name, "rb") as f:
                t2.load(f)

            with t2.open_configuration_file("numberstream", "a.txt", "r") as f:
                self.assertEqual(test_string1,f.read())

            self.assertRaises(FileNotFoundError, lambda: t2.open_configuration_file("n0", "a.txt", "r", is_temporary=True))


if __name__ == '__main__':
    import logging
    logging.basicConfig(level=logging.INFO)
    unittest.main()