from typing import Dict


class CurrencyConverter:
    def __init__(self, rates: Dict[str, float]):
        self.rates = rates

    def convert(self, amount: float, from_currency: str, to_currency: str) -> float:
        if from_currency not in self.rates or to_currency not in self.rates:
            raise ValueError(f"Unknown currency: {from_currency} or {to_currency}")
        usd = amount / self.rates[from_currency]
        return usd * self.rates[to_currency]
