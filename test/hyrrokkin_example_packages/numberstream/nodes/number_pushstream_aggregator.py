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

from asyncio import Semaphore


class NumberPushStreamAggregator:

    def __init__(self, services):
        self.services = services

    def reset_execution(self):
        pass

    async def execute(self, inputs):

        values = []
        nr_inputs = len(inputs["data_in"])

        if nr_inputs == 0:
            return {"data_out": None }

        s = Semaphore(nr_inputs)
        for register_fn in inputs["data_in"]:
            await s.acquire()

            def cb(v):
                if v is not None:
                    values.append(v)
                else:
                    s.release()
            register_fn(cb)

        for _ in range(nr_inputs):
            await s.acquire()

        fn = self.services.get_property("fn", "lambda x: sum(x)")
        return {"data_out": eval(fn)(values)}



