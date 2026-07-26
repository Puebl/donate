from typing import Any

from pydantic import BaseModel

from .enums import TriggerType


class TaskConfig(BaseModel):
    id: str
    name: str
    trigger_type: TriggerType
    trigger_kwargs: dict[str, Any]
    max_instances: int = 1
    coalesce: bool = False
    misfire_grace_time: int = 15
