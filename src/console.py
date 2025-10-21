from app.app_layer.commands.base import CommandRegistry
from app.app_layer.commands.commands import (
    CreateAccountCommand,
    CreateBankCommand,
    CreateClientCommand,
    ExitCommand,
    HelpCommand,
    ListAccountsCommand,
    ListBanksCommand,
    ListClientsCommand,
    ListRatesCommand,
    LoadCommand,
    SaveCommand,
    SetRateCommand,
    ShowTransactionsCommand,
    TransferCommand,
)
from app.infra.database.json import JsonStorage
from app.infra.repositories.repository import Repository


class ConsoleApp:
    def __init__(self, storage_path="data.json"):
        self.storage = JsonStorage(storage_path)
        self.repository = Repository()

        # load data
        self.repository.load_serializable(self.storage.load())
        self.registry = CommandRegistry()

        # register commands
        self.registry.register(
            HelpCommand(self.repository, self.storage, self.registry)
        )
        self.registry.register(SaveCommand(self.repository, self.storage))
        self.registry.register(LoadCommand(self.repository, self.storage))
        self.registry.register(CreateBankCommand(self.repository, self.storage))
        self.registry.register(ListBanksCommand(self.repository, self.storage))
        self.registry.register(CreateClientCommand(self.repository, self.storage))
        self.registry.register(ListClientsCommand(self.repository, self.storage))
        self.registry.register(CreateAccountCommand(self.repository, self.storage))
        self.registry.register(ListAccountsCommand(self.repository, self.storage))
        self.registry.register(TransferCommand(self.repository, self.storage))
        self.registry.register(ShowTransactionsCommand(self.repository, self.storage))
        self.registry.register(SetRateCommand(self.repository, self.storage))
        self.registry.register(ListRatesCommand(self.repository, self.storage))
        self.registry.register(ExitCommand(self.repository, self.storage))

    def run(self):
        print("Введите 'help' для списка команд.")
        while True:
            try:
                line = input("> ")
            except (EOFError, KeyboardInterrupt):
                print("\nВыход.")
                break
            if not line.strip():
                continue
            self.registry.execute(line)
