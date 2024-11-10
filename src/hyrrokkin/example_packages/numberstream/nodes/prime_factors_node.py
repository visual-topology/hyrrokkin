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

import math
from functools import reduce

class PrimeFactorsNode:

    def __init__(self,services):
        self.services = services

    def is_prime(self,n):
        root = int(math.sqrt(n))
        for i in range(2, root + 1):
            if n % i == 0:
                return False
        return True

    def find_prime_factors(self,n):
        factors = self.services.get_configuration().get_prime_factors(n) or []
        if not factors:
            i = 2
            r = n
            while True:
                if r % i == 0:
                    factors.append(i)
                    r //= i
                    if self.is_prime(r):
                        break
                else:
                    i += 1
            if r > 1:
                factors.append(r)
            assert (reduce(lambda x, y: x * y, factors, 1) == n and all(self.is_prime(f) for f in factors))
            self.services.get_configuration().set_prime_factors(n, factors)
        return factors

    def run(self, inputs):
        input_values = inputs.get("data_in",[])
        if len(input_values):
            value = input_values[0]
            if not isinstance(value,int):
                raise Exception(f"input value {value} is invalid (not integer)")
            if value < 2:
                raise Exception(f"input value {value} is invalid (< 2)")

            prime_factors = self.services.get_configuration().get_prime_factors(value)
            if not prime_factors:
                prime_factors = self.find_prime_factors(value)
            return { "data_out":prime_factors }





