from abc import ABC, abstractmethod

from .config import TaskConfig


class BaseTask(ABC):
    active: bool = True

    @property
    @abstractmethod
    def config(self) -> TaskConfig:
        pass

    @abstractmethod
    async def execute(self) -> None:
        pass
