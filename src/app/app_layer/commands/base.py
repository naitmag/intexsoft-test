from abc import ABC, abstractmethod
from typing import Dict, List

from app.infra.database.json import JsonStorage
from app.infra.repositories.repository import Repository


class Command(ABC):
    def __init__(self, repository: Repository, storage: JsonStorage):
        self.repository = repository
        self.storage = storage

    @abstractmethod
    def name(self) -> str:
        pass

    @abstractmethod
    def help(self) -> str:
        pass

    @abstractmethod
    def execute(self, args: List[str]):
        pass


class CommandRegistry:
    def __init__(self):
        self.commands: Dict[str, Command] = {}

    def register(self, cmd: Command):
        self.commands[cmd.name()] = cmd

    def execute(self, line: str):
        parts = line.strip().split()
        if not parts:
            return
        cmd_name = parts[0]
        args = parts[1:]
        if cmd_name not in self.commands:
            print(f"Unknown command: {cmd_name}. Введите 'help' для списка команд.")
            return
        try:
            self.commands[cmd_name].execute(args)
        except Exception as e:
            print(f"Ошибка при выполнении команды: {e}")
