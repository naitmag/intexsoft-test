from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass
from typing import Dict, List, Optional


@dataclass
class Transaction:
    id: str
    from_account: Optional[str]  # account id
    to_account: Optional[str]  # account id
    amount: float
    currency: str
    commission: float
    timestamp: str
    description: str

    def to_dict(self):
        return asdict(self)


@dataclass
class Account:
    id: str
    bank_id: str
    client_id: str
    currency: str
    balance: float = 0.0

    def to_dict(self):
        return asdict(self)


class Client(ABC):
    def __init__(self, id: str, name: str):
        self.id = id
        self.name = name
        self.accounts: List[str] = []  # account ids
        self.transactions: List[str] = []  # transaction ids

    @property
    @abstractmethod
    def type(self) -> str:
        pass

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "type": self.type,
            "accounts": self.accounts,
            "transactions": self.transactions,
        }


class PhysicalClient(Client):
    @property
    def type(self) -> str:
        return "physical"


class LegalClient(Client):
    @property
    def type(self) -> str:
        return "legal"


class Bank:
    def __init__(self, id: str, name: str, commission_for_interbank: Dict[str, float]):
        self.id = id
        self.name = name
        self.commission_for_interbank = commission_for_interbank
        self.accounts: List[str] = []

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "commission_for_interbank": self.commission_for_interbank,
            "accounts": self.accounts,
        }
