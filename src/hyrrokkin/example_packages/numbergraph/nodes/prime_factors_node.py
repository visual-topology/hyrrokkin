import math

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
            self.services.get_configuration().set_prime_factors(n, factors)
        return factors

    async def run(self, inputs):
        input_values = inputs.get("data_in",[])
        if len(input_values):
            value = input_values[0]
            if not isinstance(value,int):
                raise Exception(f"input value {value} is invalid (not integer)")
            if value < 2:
                raise Exception(f"input value {value} is invalid (< 2)")
            prime_factors = self.find_prime_factors(value)
            return { "data_out":prime_factors }





