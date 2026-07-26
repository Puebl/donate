from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.executors.asyncio import AsyncIOExecutor
from pytz import utc

from src.core.settings.base import settings


def get_scheduler_config() -> dict:
    """Конфиг для APScheduler"""
    jobstores = {
        'default': SQLAlchemyJobStore(str(settings.POSTGRES.sync_url))
    }

    executors = {
        'default': AsyncIOExecutor(),
        'threadpool': AsyncIOExecutor()
    }

    job_defaults = {
        'coalesce': False,
        'max_instances': 1,
        'misfire_grace_time': 15
    }

    return {
        'jobstores': jobstores,
        'executors': executors,
        'job_defaults': job_defaults,
        'timezone': utc
    }


def create_apscheduler() -> AsyncIOScheduler:
    config = get_scheduler_config()
    return AsyncIOScheduler(**config)
