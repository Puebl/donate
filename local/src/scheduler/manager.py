from apscheduler.schedulers.asyncio import AsyncIOScheduler

from .base import BaseTask, TaskScheduler

from .config import create_apscheduler
from .tasks import ACTIVE_TASKS
from .logger import scheduler_logger


class APSchedulerImpl(TaskScheduler):
    def __init__(self):
        self._scheduler: AsyncIOScheduler | None = None
        self._tasks: dict[str, BaseTask] = {}

    async def start(self) -> None:
        if self._scheduler is None:
            self._scheduler = create_apscheduler()
        self._scheduler.start()
        scheduler_logger.info("APScheduler запущен")

        await self._setup_jobs()

    async def shutdown(self) -> None:
        if self._scheduler:
            self._scheduler.shutdown()
            scheduler_logger.info("APScheduler остановлен")

    async def add_task(self, task: BaseTask) -> None:
        if self._scheduler is None:
            raise RuntimeError("Scheduler не инициализирован")

        config = task.config
        self._tasks[config.id] = task

        self._scheduler.add_job(
            task.execute,
            trigger=config.trigger_type.value, # type:ignore
            id=config.id,
            name=config.name,
            max_instances=config.max_instances,
            coalesce=config.coalesce,
            misfire_grace_time=config.misfire_grace_time,
            replace_existing=True,
            **config.trigger_kwargs,
        )

        scheduler_logger.info(f"Задача добавлена: {config.name}")

    async def remove_task(self, task_id: str) -> None:
        if self._scheduler is None:
            raise RuntimeError("Scheduler не инициализирован")

        self._scheduler.remove_job(task_id)
        self._tasks.pop(task_id, None)
        scheduler_logger.info(f"Задача удалена: {task_id}")

    async def get_tasks(self) -> list[BaseTask]:
        return list(self._tasks.values())

    async def pause_task(self, task_id: str) -> None:
        if self._scheduler is None:
            raise RuntimeError("Scheduler не инициализирован")

        self._scheduler.pause_job(task_id)
        scheduler_logger.info(f"Задача приостановлена: {task_id}")

    async def resume_task(self, task_id: str) -> None:
        if self._scheduler is None:
            raise RuntimeError("Scheduler не инициализирован")

        self._scheduler.resume_job(task_id)
        scheduler_logger.info(f"Задача возобновлена: {task_id}")

    async def _setup_jobs(self) -> None:
        tasks = ACTIVE_TASKS

        for task in tasks:
            await self.add_task(task)

        scheduler_logger.info(f"Инициализировано {len(tasks)} задач")


apscheduler = APSchedulerImpl()
