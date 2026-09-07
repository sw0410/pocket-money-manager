from datetime import date
from dataclasses import dataclass

@dataclass
class Transaction:
    id: int
    date: str
    transaction_type: str
    category: str
    amount: int