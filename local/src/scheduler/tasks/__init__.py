from .base import BaseTask
from .tasks import *

ACTIVE_TASKS = [el() for el in BaseTask.__subclasses__() if el.active]
