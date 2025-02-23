class PrimeFactorsNode:

    def __init__(self,services):
        self.services = services

    async def run(self, inputs):
        input_values = inputs.get("data_in",[])
        if len(input_values):
            value = input_values[0]
            if not isinstance(value,int):
                raise Exception(f"input value {value} is invalid (not integer)")
            if value < 2:
                raise Exception(f"input value {value} is invalid (< 2)")
            prime_factors = self.services.get_configuration().find_prime_factors(value)
            return { "data_out":prime_factors }





