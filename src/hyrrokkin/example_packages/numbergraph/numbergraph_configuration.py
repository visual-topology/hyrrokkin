import pickle

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

    def close(self):
        self.services.set_data("prime_factors", pickle.dumps(self.prime_factor_cache))
        self.services.set_status_info(f"saved cache ({len(self.prime_factor_cache)} items)")







