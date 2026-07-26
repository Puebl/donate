from abc import ABC, abstractmethod

from .tasks import BaseTask


class TaskScheduler(ABC):
    @abstractmethod
    async def start(self) -> None:
        pass

    @abstractmethod
    async def shutdown(self) -> None:
        pass

    @abstractmethod
    async def add_task(self, task: BaseTask) -> None:
        pass

    @abstractmethod
    async def remove_task(self, task_id: str) -> None:
        pass

    @abstractmethod
    async def get_tasks(self) -> list[BaseTask]:
        pass

    @abstractmethod
    async def pause_task(self, task_id: str) -> None:
        pass

    @abstractmethod
    async def resume_task(self, task_id: str) -> None:
        pass
