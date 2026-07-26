from enum import StrEnum


class TriggerType(StrEnum):
    INTERVAL = "interval"
    CRON = "cron"
    DATE = "date"
