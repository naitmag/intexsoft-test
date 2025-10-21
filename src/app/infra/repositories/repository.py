from typing import Any, Dict

from app.app_layer.domain.models.models import (
    Account,
    Bank,
    Client,
    LegalClient,
    PhysicalClient,
    Transaction,
)


class Repository:
    def __init__(self):
        self.banks: Dict[str, Bank] = {}
        self.clients: Dict[str, Client] = {}
        self.accounts: Dict[str, Account] = {}
        self.transactions: Dict[str, Transaction] = {}
        # default rate
        self.rates: Dict[str, float] = {"USD": 1.0, "EUR": 0.9, "RUB": 80.0, "BYN": 3}

    def to_serializable(self):
        return {
            "banks": {bid: b.to_dict() for bid, b in self.banks.items()},
            "clients": {cid: c.to_dict() for cid, c in self.clients.items()},
            "accounts": {aid: a.to_dict() for aid, a in self.accounts.items()},
            "transactions": {tid: t.to_dict() for tid, t in self.transactions.items()},
            "rates": self.rates,
        }

    def load_serializable(self, data: Dict[str, Any]):
        self.banks.clear()
        self.clients.clear()
        self.accounts.clear()
        self.transactions.clear()
        self.rates = data.get("rates", self.rates)
        for bid, bd in data.get("banks", {}).items():
            b = Bank(bid, bd["name"], bd.get("commission_for_interbank", {}))
            b.accounts = bd.get("accounts", [])
            self.banks[bid] = b
        for cid, cd in data.get("clients", {}).items():
            ctype = cd.get("type")
            if ctype == "physical":
                c = PhysicalClient(cid, cd["name"])
            else:
                c = LegalClient(cid, cd["name"])
            c.accounts = cd.get("accounts", [])
            c.transactions = cd.get("transactions", [])
            self.clients[cid] = c
        for aid, ad in data.get("accounts", {}).items():
            acct = Account(
                id=aid,
                bank_id=ad["bank_id"],
                client_id=ad["client_id"],
                currency=ad["currency"],
                balance=ad.get("balance", 0.0),
            )
            self.accounts[aid] = acct
        for tid, td in data.get("transactions", {}).items():
            tr = Transaction(**td)
            self.transactions[tid] = tr
