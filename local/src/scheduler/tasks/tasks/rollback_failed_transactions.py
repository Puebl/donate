from src.api.user_service.service import UserService
from src.api.user_service.uow import UserUnitOfWork
from src.core.database.connection import db_helper
from ..base import BaseTask
from ..config import TaskConfig
from ..enums import TriggerType
from src.api.transaction.service import TransactionService
from src.api.transaction.uow import TransactionUow
from src.api.billing.service import BillingService
from src.api.billing.uow import BillingUnitOfWork
from src.api.payment_gateways.tinkoff.service import TinkoffService
from src.api.payment_gateways.tinkoff.uow import TinkoffUnitOfWork


class RollbackFailedTransactionsTask(BaseTask):
    active: bool = True

    @property
    def config(self) -> TaskConfig:
        return TaskConfig(
            id="rollback_failed_transactions",
            name="Rollback Failed Transactions",
            trigger_type=TriggerType.INTERVAL,
            trigger_kwargs={'minutes': 5}
        )

    async def execute(self):
        async with db_helper.get_async_session_not_closed() as session:
            billing_uow = BillingUnitOfWork(session)
            billing_service = BillingService(billing_uow)
            tinkoff_uow = TinkoffUnitOfWork(session)
            tinkoff_service = TinkoffService(tinkoff_uow)
            transaction_uow = TransactionUow(session)
            user_uow = UserUnitOfWork(session)
            user_service = UserService(tinkoff_service, user_uow)
            transaction_service = TransactionService(
                transaction_uow,
                billing_service,
                tinkoff_service,
            )

            result = await transaction_service.rollback_failed_transactions(user_service)
            print(f"Rollback completed: {result}")
