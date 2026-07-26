from ..base import BaseTask
from ..config import TaskConfig
from ..enums import TriggerType


class PrintHelloTask(BaseTask):
    active: bool = False

    @property
    def config(self) -> TaskConfig:
        return TaskConfig(
            id="print_hello",
            name="Print Hello",
            trigger_type=TriggerType.INTERVAL,
            trigger_kwargs={'minutes': 1}
        )

    async def execute(self):
        print("example_task")
