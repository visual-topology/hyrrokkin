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

from hyrrokkin.schema.schema import Schema
from hyrrokkin.export.code_exporter import CodeExporter


class TopologyToCode:

    def __init__(self, schema, topology_file, output_folder, output_filename):
        self.exporter = CodeExporter(schema, topology_file, output_folder, output_filename)

    def run(self):
        self.exporter.export()


def main():
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--schema", nargs="+", help="Specify schema file(s)", required=True)
    parser.add_argument("--topology", help="Topology file to run", required=True)
    parser.add_argument("--output-folder", help="Folder to export code to", required=True)
    parser.add_argument("--output-filename", help="Name of output python file", default="topology.py")

    logging.basicConfig(level=logging.INFO)

    args = parser.parse_args()
    schema = Schema()
    for schema_path in args.schema:
        schema.load_package_from(schema_path)

    with open(args.topology, "rb") as f:
        tr = TopologyToCode(schema, f, args.output_folder, args.output_filename)
        tr.run()


if __name__ == '__main__':
    main()
