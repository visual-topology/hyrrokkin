import pickle
import math
from functools import reduce

def is_prime(n):
    root = int(math.sqrt(n))
    for i in range(2, root + 1):
        if n % i == 0:
            return False
    return True

class NumbergraphConfiguration:

    def __init__(self, services):
        self.services = services
        self.prime_factor_cache = None

    async def load(self):
        cache_data = self.services.get_data("prime_factors")
        self.prime_factor_cache = pickle.loads(cache_data) if cache_data else {}
        self.services.set_status_info(f"loaded cache ({len(self.prime_factor_cache)} items)")

    def get_prime_factors(self, n):
        if n in self.prime_factor_cache:
            return self.prime_factor_cache[n]
        else:
            return None

    def set_prime_factors(self, n, factors):
        self.prime_factor_cache[n] = factors

    def find_prime_factors(self,n):
        factors = self.get_prime_factors(n) or []
        if not factors:
            i = 2
            r = n
            while True:
                if r % i == 0:
                    factors.append(i)
                    r //= i
                    if is_prime(r):
                        break
                else:
                    i += 1
            if r > 1:
                factors.append(r)
            assert (reduce(lambda x, y: x * y, factors, 1) == n and all(is_prime(f) for f in factors))
            self.set_prime_factors(n, factors)
        return factors

    def close(self):
        self.services.set_data("prime_factors", pickle.dumps(self.prime_factor_cache))
        self.services.set_status_info(f"saved cache ({len(self.prime_factor_cache)} items)")







