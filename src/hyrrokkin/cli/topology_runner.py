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

import os.path
import logging
import sys

from hyrrokkin.api.topology import Topology

def main():
    import argparse

    parser = argparse.ArgumentParser()

    parser.add_argument("--package", nargs="+", help="Specify package(s)", required=True)
    parser.add_argument("--execution-folder", help="Folder containing topology", required=True)
    parser.add_argument("--import-path", help="topology file to import (.zip or .yaml/.yml)")
    parser.add_argument("--export-path", help="topology file to export (.zip or .yaml/.yml)")
    parser.add_argument("--run", action="store_true", help="run topology after loading")

    logging.basicConfig(level=logging.INFO)

    args = parser.parse_args()

    logger = logging.getLogger("topology_runner")

    def status_handler(source_id,source_type, msg, status):
        if status == "info":
            logger.info(f"[{source_type}:{source_id}] {msg}")
        elif status == "warning":
            logger.warning(f"[{source_type}:{source_id}] {msg}")
        elif status == "error":
            logger.error(f"[{source_type}:{source_id}] {msg}")
        elif status == "":
            # clear status, log nothing
            pass

    def exception_handler(node_id, state, exception_or_result):
        if state == "error":
            logger.exception(f"[node:{node_id}] execution error", exc_info=exception_or_result)

    t = Topology(args.execution_folder, args.package,
                 status_handler=status_handler,
                 execution_handler=exception_handler)

    if args.import_path:
        suffix = os.path.splitext(args.import_path)[1]
        try:
            if suffix == ".zip":
                with open(args.import_path,"rb") as f:
                    t.load(f)
            elif suffix == ".yaml" or suffix == ".yml":
                from hyrrokkin.utils.yaml_importer import import_from_yaml
                with open(args.import_path) as f:
                    import_from_yaml(t, f)
            else:
                raise Exception("Unsupported input file type, expecting .zip, .yaml or .yml")

        except Exception as ex:
            logger.exception(f"Error importing topology from {args.import_path}")
            sys.exit(0)

    if args.run:
        t.run()

    if args.export_path:
        suffix = os.path.splitext(args.export_path)[1]
        try:
            if suffix == ".zip":
                with open(args.export_path,"wb") as f:
                    t.save(f)
            elif suffix == ".yaml" or suffix == ".yml":
                from hyrrokkin.utils.yaml_exporter import export_to_yaml
                with open(args.export_path,"w") as f:
                    export_to_yaml(t, f)
            else:
                raise Exception("Unsupported export file type, expecting .zip, .yaml or .yml")
        except Exception as ex:
            logger.exception(f"Error exporting topology to {args.export_path}")
            sys.exit(0)


if __name__ == '__main__':
    main()
