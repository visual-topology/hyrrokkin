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
from hyrrokkin.executors.graph_executor import GraphExecutor


class TopologyRunner:

    def __init__(self, schema):
        self.executor = GraphExecutor(schema, lambda msg: print(msg))
        self.executor.pause()

    def load(self, topology_file):
        self.executor.load(topology_file)

    def run(self):
        self.executor.resume(terminate_on_complete=True)

    def save(self, topology_file):
        self.executor.save(topology_file)


def main():
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--package", nargs="+", help="Specify package(s)", required=True)
    parser.add_argument("--topology", help="Topology file to run", required=True)
    parser.add_argument("--save-on-exit", help="Save updated topology back to file after running", action="store_true")

    logging.basicConfig(level=logging.INFO)

    args = parser.parse_args()

    schema = Schema()

    for package_path in args.package:
        schema.load_package_from_dict(package_path)

    tr = TopologyRunner(schema)

    with open(args.topology, "rb") as f:
        tr.load(f)

    tr.run()

    if args.save:
        with open(args.topology, "wb") as f:
            tr.save(f)


if __name__ == '__main__':
    main()
