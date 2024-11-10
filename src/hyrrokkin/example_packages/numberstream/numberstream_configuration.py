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

import pickle

class NumberstreamConfiguration:

    def __init__(self, services):
        self.services = services
        cache_data = services.get_data("prime_factors")
        self.prime_factor_cache = pickle.loads(cache_data) if cache_data else {}
        self.services.set_status_info(f"loaded cache ({len(self.prime_factor_cache)} items)")

    def get_prime_factors(self, n):
        if n in self.prime_factor_cache:
            return self.prime_factor_cache[n]
        else:
            return None

    def set_prime_factors(self, n, factors):
        self.prime_factor_cache[n] = factors

    def close(self):
        self.services.set_data("prime_factors", pickle.dumps(self.prime_factor_cache))
        self.services.set_status_info(f"saved cache ({len(self.prime_factor_cache)} items)")







