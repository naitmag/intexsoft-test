import sys
import uuid
from datetime import datetime
from typing import List

from app.app_layer.commands.base import Command, CommandRegistry
from app.app_layer.domain.models.models import (
    Account,
    Bank,
    LegalClient,
    PhysicalClient,
    Transaction,
)
from app.app_layer.utils.converter import CurrencyConverter


def gen_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:8]}"


def now_iso() -> str:
    return datetime.utcnow().isoformat() + "Z"


class HelpCommand(Command):
    def __init__(self, repository, storage, registry: CommandRegistry):
        super().__init__(repository, storage)
        self.registry = registry

    def name(self) -> str:
        return "help"

    def help(self) -> str:
        return "help - показать список команд"

    def execute(self, args: List[str]) -> None:
        print("Список команд:")
        for name, cmd in sorted(self.registry.commands.items()):
            print(f"  {name:20} - {cmd.help()}")


class SaveCommand(Command):
    def name(self) -> str:
        return "save"

    def help(self) -> str:
        return "save [path] - сохранить данные в json (по умолчанию data.json)"

    def execute(self, args: List[str]):
        path = args[0] if args else self.storage.path
        self.storage.path = path
        self.storage.save(self.repository.to_serializable())
        print(f"Сохранено в {path}")


class LoadCommand(Command):
    def name(self) -> str:
        return "load"

    def help(self) -> str:
        return "load [path] - загрузить данные из json (по умолчанию data.json)"

    def execute(self, args: List[str]):
        path = args[0] if args else self.storage.path
        self.storage.path = path
        data = self.storage.load()
        if not data:
            print("Файл пуст или не существует.")
            return
        self.repository.load_serializable(data)
        print(f"Загружено из {path}")


class CreateBankCommand(Command):
    def name(self) -> str:
        return "create_bank"

    def help(self) -> str:
        return "create_bank <name> <commission_physical_pct> <commission_legal_pct> - создать банк"

    def execute(self, args: List[str]):
        if len(args) < 3:
            print("Использование:", self.help())
            return
        name = args[0]
        try:
            cp = float(args[1])
            cl = float(args[2])
        except ValueError:
            print("Комиссии должны быть числами (проценты).")
            return
        bid = gen_id("bank")
        bank = Bank(bid, name, {"physical": cp, "legal": cl})
        self.repository.banks[bid] = bank
        self.storage.save(self.repository.to_serializable())
        print(f"Банк создан: id={bid}, name={name}")


class ListBanksCommand(Command):
    def name(self) -> str:
        return "list_banks"

    def help(self) -> str:
        return "list_banks - показать все банки"

    def execute(self, args: List[str]):
        if not self.repository.banks:
            print("Банков нет.")
            return
        for b in self.repository.banks.values():
            print(
                f"{b.id}: {b.name} | комиссия межбанк (physical={b.commission_for_interbank.get('physical')}%, "
                f"legal={b.commission_for_interbank.get('legal')}%)"
            )


class CreateClientCommand(Command):
    def name(self) -> str:
        return "create_client"

    def help(self) -> str:
        return (
            "create_client <bank_id> <type:physical|legal> <name> - создать клиента и открыть счет в банке "
            "(нужно указать валюту после команды)"
        )

    def execute(self, args: List[str]):
        if len(args) < 3:
            print("Использование: create_client <bank_id> <type> <name> <currency>")
            return
        bank_id, ctype, name = args[0], args[1], args[2]
        currency = args[3] if len(args) > 3 else "USD"
        if bank_id not in self.repository.banks:
            print("Банк не найден")
            return
        if ctype not in ("physical", "legal"):
            print("Тип клиента должен быть 'physical' или 'legal'")
            return
        cid = gen_id("client")
        client = (
            PhysicalClient(cid, name) if ctype == "physical" else LegalClient(cid, name)
        )
        self.repository.clients[cid] = client
        # create account
        aid = gen_id("acct")
        account = Account(aid, bank_id, cid, currency, balance=0.0)
        self.repository.accounts[aid] = account
        client.accounts.append(aid)
        self.repository.banks[bank_id].accounts.append(aid)
        self.storage.save(self.repository.to_serializable())
        print(f"Клиент создан: id={cid}, name={name}; открыт счет {aid} в {currency}")


class ListClientsCommand(Command):
    def name(self) -> str:
        return "list_clients"

    def help(self) -> str:
        return "list_clients - показать всех клиентов"

    def execute(self, args: List[str]):
        if not self.repository.clients:
            print("Клиентов нет.")
            return
        for c in self.repository.clients.values():
            print(f"{c.id}: {c.name} | type={c.type} | accounts={len(c.accounts)}")


class CreateAccountCommand(Command):
    def name(self) -> str:
        return "create_account"

    def help(self) -> str:
        return "create_account <bank_id> <client_id> <currency> <initial_balance?> - создать счет"

    def execute(self, args: List[str]):
        if len(args) < 3:
            print("Использование:", self.help())
            return
        bank_id, client_id, currency = args[0], args[1], args[2]
        balance = float(args[3]) if len(args) > 3 else 0.0
        if bank_id not in self.repository.banks:
            print("Банк не найден")
            return
        if client_id not in self.repository.clients:
            print("Клиент не найден")
            return
        aid = gen_id("acct")
        acct = Account(aid, bank_id, client_id, currency, balance)
        self.repository.accounts[aid] = acct
        self.repository.clients[client_id].accounts.append(aid)
        self.repository.banks[bank_id].accounts.append(aid)
        self.storage.save(self.repository.to_serializable())
        print(f"Счет создан: {aid}, баланс={balance} {currency}")


class ListAccountsCommand(Command):
    def name(self) -> str:
        return "list_accounts"

    def help(self) -> str:
        return "list_accounts <client_id> - показать счета клиента и балансы"

    def execute(self, args: List[str]):
        if len(args) < 1:
            print("Использование:", self.help())
            return
        client_id = args[0]
        if client_id not in self.repository.clients:
            print("Клиент не найден")
            return
        client = self.repository.clients[client_id]
        print(f"Счета клиента {client.name} ({client.id}):")
        for aid in client.accounts:
            acct = self.repository.accounts.get(aid)
            if acct:
                print(
                    f"  {acct.id} | {acct.bank_id} | {acct.balance:.2f} {acct.currency}"
                )


class TransferCommand(Command):
    def name(self) -> str:
        return "transfer"

    def help(self) -> str:
        return "transfer <from_account> <to_account> <amount> <currency_of_amount> <description?> - выполнить перевод"

    def execute(self, args: List[str]):
        if len(args) < 4:
            print("Использование:", self.help())
            return
        from_aid, to_aid, amount_str, currency = args[0], args[1], args[2], args[3]
        desc = " ".join(args[4:]) if len(args) > 4 else ""
        try:
            amount = float(amount_str)
            if amount <= 0:
                print("Сумма должна быть положительной")
                return
        except ValueError:
            print("Некорректная сумма")
            return
        if from_aid not in self.repository.accounts:
            print("Счет отправителя не найден")
            return
        if to_aid not in self.repository.accounts:
            print("Счет получателя не найден")
            return
        from_acct = self.repository.accounts[from_aid]
        to_acct = self.repository.accounts[to_aid]
        if from_acct.client_id not in self.repository.clients:
            print("Клиент отправителя не найден")
            return
        if to_acct.client_id not in self.repository.clients:
            print("Клиент получателя не найден")
            return

        converter = CurrencyConverter(self.repository.rates)

        # compute amount in sender's account currency
        amount_in_sender_currency = converter.convert(
            amount, currency, from_acct.currency
        )

        if from_acct.balance < amount_in_sender_currency:
            print("Недостаточно средств на счете отправителя.")
            return

        commission = 0.0
        # same bank no commission
        if from_acct.bank_id == to_acct.bank_id:
            commission = 0.0
        else:
            # interbank -> use sender bank's rates based on recipient client type
            sender_bank = self.repository.banks[from_acct.bank_id]
            recipient_client = self.repository.clients[to_acct.client_id]
            rate_pct = sender_bank.commission_for_interbank.get(
                recipient_client.type, 0.0
            )
            commission = amount * (rate_pct / 100.0)
            # commission charged in currency of transfer amount; convert to sender account currency when deducting
            commission_in_sender_currency = converter.convert(
                commission, currency, from_acct.currency
            )
            # deduct both transfer + commission from sender
            total_deduction = amount_in_sender_currency + commission_in_sender_currency
            if from_acct.balance < total_deduction:
                print("Недостаточно средств для перевода + комиссии.")
                return
            from_acct.balance -= commission_in_sender_currency
        # perform transfer
        from_acct.balance -= amount_in_sender_currency
        # convert amount to recipient currency
        amount_in_recipient_currency = converter.convert(
            amount, currency, to_acct.currency
        )
        to_acct.balance += amount_in_recipient_currency

        tid = gen_id("txn")
        txn = Transaction(
            id=tid,
            from_account=from_acct.id,
            to_account=to_acct.id,
            amount=amount,
            currency=currency,
            commission=commission,
            timestamp=now_iso(),
            description=desc,
        )
        self.repository.transactions[tid] = txn
        # attach to clients
        self.repository.clients[from_acct.client_id].transactions.append(tid)
        self.repository.clients[to_acct.client_id].transactions.append(tid)
        self.storage.save(self.repository.to_serializable())
        print(
            f"Перевод выполнен. txn_id={tid} | {amount} {currency} | комиссия={commission:.2f} {currency}"
        )
        print(
            f"Счет отправителя новый баланс: {from_acct.balance:.2f} {from_acct.currency}"
        )
        print(f"Счет получателя новый баланс: {to_acct.balance:.2f} {to_acct.currency}")


class ShowTransactionsCommand(Command):
    def name(self) -> str:
        return "show_txns"

    def help(self) -> str:
        return (
            "show_txns <client_id> <from_date?> <to_date?> - "
            "показать транзакции клиента между датами (формат YYYY-MM-DD)"
        )

    def execute(self, args: List[str]):
        if len(args) < 1:
            print("Использование:", self.help())
            return
        client_id = args[0]
        if client_id not in self.repository.clients:
            print("Клиент не найден")
            return
        client = self.repository.clients[client_id]
        date_from = None
        date_to = None
        if len(args) >= 2:
            try:
                date_from = datetime.fromisoformat(args[1])
            except Exception:
                print("Некорректный формат даты (from). Используйте YYYY-MM-DD")
                return
        if len(args) >= 3:
            try:
                date_to = datetime.fromisoformat(args[2])
            except Exception:
                print("Некорректный формат даты (to). Используйте YYYY-MM-DD")
                return
        txns = []
        for tid in client.transactions:
            txn = self.repository.transactions.get(tid)
            if not txn:
                continue
            ts = datetime.fromisoformat(txn.timestamp.replace("Z", ""))
            if date_from and ts < date_from:
                continue
            if date_to and ts > date_to:
                continue
            txns.append(txn)
        if not txns:
            print("Транзакций не найдено в указанном периоде.")
            return
        for t in sorted(txns, key=lambda x: x.timestamp):
            print(
                f"{t.timestamp} | {t.id} | {t.from_account} -> {t.to_account} | {t.amount} {t.currency} | "
                f"commission={t.commission:.2f} | {t.description}"
            )


class SetRateCommand(Command):
    def name(self) -> str:
        return "set_rate"

    def help(self) -> str:
        return "set_rate <currency> <rate_to_USD> - установить курс (количество currency = rate_to_USD USD base)"

    def execute(self, args: List[str]):
        if len(args) < 2:
            print("Использование:", self.help())
            return
        cur = args[0].upper()
        try:
            rate = float(args[1])
        except ValueError:
            print("Некорректный курс")
            return
        self.repository.rates[cur] = rate
        self.storage.save(self.repository.to_serializable())
        print(f"Курс {cur} установлен: {rate}")


class ListRatesCommand(Command):
    def name(self) -> str:
        return "list_rates"

    def help(self) -> str:
        return "list_rates - показать валютные курсы"

    def execute(self, args: List[str]):
        for k, v in self.repository.rates.items():
            print(f"{k}: {v}")


class ExitCommand(Command):
    def name(self) -> str:
        return "exit"

    def help(self) -> str:
        return "exit - выйти"

    def execute(self, args: List[str]):
        print("Выход.")
        sys.exit(0)
