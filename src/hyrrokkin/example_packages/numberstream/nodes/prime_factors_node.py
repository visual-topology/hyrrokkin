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
import json

def is_prime(n):
    lim = int(math.sqrt(n))
    for i in range(2,lim+1):
        if n % i == 0:
            return False
    return True

def find_primes(n, primes):
    if primes == []:
        primes.append(2)
    i = primes[-1]+1
    while i<=n:
        if is_prime(i):
            primes.append(i)
        i += 1

def find_prime_factors(n, primes=[]):
    lim = int(math.sqrt(n))
    if len(primes) == 0 or primes[-1] < lim:
        find_primes(lim, primes)
    factors = []
    idx = 0
    while idx < len(primes):
        if primes[idx] > n:
            break
        if n % primes[idx] == 0:
            factors.append(primes[idx])
            n = n // primes[idx]
            idx = 0
        else:
            idx += 1
        if n == 1:
            break

    if n > 1:
        factors.append(n)
    return factors

if __name__ == '__main__':
    primes = []
    for i in range(0,200):
        print(i,find_prime_factors(i,primes))
    print(primes)

class PrimeFactorsNode:

    def __init__(self,services):
        self.services = services

    def run(self, inputs):
        input_values = inputs.get("data_in",[])
        if len(input_values):
            value = input_values[0]
            saved_primes = self.services.get_data("primes")
            if saved_primes is not None:
                saved_primes = json.loads(saved_primes.decode("utf-8"))
            else:
                saved_primes = []
            factors = find_prime_factors(value, saved_primes)
            self.services.set_data("primes",json.dumps(saved_primes).encode("utf-8"))
            return { "data_out":factors }

    def connections_changed(self, input_connection_counts, output_connection_counts):
        pass
        # if input_connection_counts.get("data_in",0) == 0:
        #     self.services.set_status_warning("No inputs are currently connected")
        # else:
        #     print("Connections: inputs=" + json.dumps(input_connection_counts) + " outputs="+json.dumps(output_connection_counts))
        # for input_node in self.services.get_connected_input_nodes("data_in"):
        #     print("Input node: "+str(input_node))
        #
        # for output_node in self.services.get_connected_output_nodes("data_out"):
        #     print("Output node: "+str(output_node))
