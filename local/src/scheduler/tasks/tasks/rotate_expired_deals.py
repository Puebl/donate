import logging
from datetime import timedelta

from src.core.database.connection import db_helper
from src.core.database.utils import get_utc_now
from src.api.payment_gateways.tinkoff.client.service import tinkoff_client
from src.api.payment_gateways.tinkoff.uow import TinkoffUnitOfWork
from ..base import BaseTask
from ..config import TaskConfig
from ..enums import TriggerType

logger = logging.getLogger(__name__)


class RotateExpiredDealsTask(BaseTask):
    active: bool = True

    @property
    def config(self) -> TaskConfig:
        return TaskConfig(
            id="rotate_expired_deals",
            name="Rotate Expired Deals",
            trigger_type=TriggerType.INTERVAL,
            trigger_kwargs={"hours": 6},
            max_instances=1,
        )

    async def execute(self):
        async with db_helper.get_async_session_not_closed() as session:
            uow = TinkoffUnitOfWork(session)

            expiring_deals = await uow.deals.get_expiring_deals(days_before_expiry=5)
            logger.info(f"Found {len(expiring_deals)} expiring deals to rotate")

            rotated = 0
            skipped = 0
            failed = 0

            for deal in expiring_deals:
                try:
                    locked = await uow.deals.lock_deal(deal.deal_id)
                    if locked == 0:
                        logger.warning(f"Deal {deal.deal_id} already locked, skipping")
                        skipped += 1
                        continue

                    try:
                        if deal.amount > 0:
                            logger.warning(
                                f"Deal {deal.deal_id} has remaining balance of {deal.amount}. "
                                f"Closing anyway — remaining funds handled by Tinkoff."
                            )

                        await tinkoff_client.close_deal(deal.deal_id)
                        await uow.deals.close(deal.deal_id)

                        new_deal_resp = await tinkoff_client.create_deal(deal_type="NN")
                        if new_deal_resp.success:
                            await uow.deals.create(
                                streamer_id=deal.streamer_id,
                                deal_id=new_deal_resp.deal_id,
                                open_status=True,
                                deal_type="NN",
                                expires_at=get_utc_now() + timedelta(days=55),
                            )
                            logger.info(
                                f"Rotated deal {deal.deal_id} -> {new_deal_resp.deal_id} "
                                f"for streamer {deal.streamer_id}"
                            )
                            rotated += 1
                        else:
                            logger.error(
                                f"Failed to create new deal for streamer {deal.streamer_id}: "
                                f"{new_deal_resp.message}"
                            )
                            failed += 1

                    except Exception as e:
                        logger.error(f"Error rotating deal {deal.deal_id}: {e}")
                        failed += 1
                    finally:
                        await uow.deals.unlock_deal(deal.deal_id)

                    await session.commit()

                except Exception as e:
                    logger.error(f"Error processing deal {deal.deal_id}: {e}")
                    failed += 1
                    await session.rollback()

            logger.info(
                f"Deal rotation completed: {rotated} rotated, {skipped} skipped, {failed} failed"
            )
