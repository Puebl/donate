"""
Migration script: Drain and close N1 deals, create NN deals.

Usage (run from payment/ directory):
    python -m scripts.migrate_n1_to_nn           # Execute migration
    python -m scripts.migrate_n1_to_nn --dry-run  # Preview only (no changes)

This script:
1. Finds all active N1 deals in the database
2. Closes each deal at Tinkoff via closeSpDeal (remaining balance -> platform commission)
3. Marks the deal as closed in the local database
4. Creates a new NN deal for each streamer
5. Reports a summary of operations

IMPORTANT:
- Run AFTER deploying the new code (deal_type column must exist)
- Run AFTER applying the Alembic migration
- The remaining balance of closed deals goes to the platform as commission
- If a streamer needs to withdraw first, do that manually before running this script
- Script is idempotent: safe to run multiple times (skips already-migrated streamers)
"""

import argparse
import asyncio
import logging
from datetime import timedelta

from sqlalchemy import select, and_

from src.api.payment_gateways.tinkoff.client.service import tinkoff_client
from src.api.payment_gateways.tinkoff.uow import TinkoffUnitOfWork
from src.core.database.connection import db_helper
from src.core.database.models import Deal
from src.core.database.utils import get_utc_now

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)


async def _migrate_single_deal(session, deal, stats: dict[str, int]) -> None:
    """Migrate a single N1 deal to NN for its streamer.

    Raises on unrecoverable error so the caller can handle rollback.
    """
    uow = TinkoffUnitOfWork(session)

    existing_nn = await session.scalar(
        select(Deal).where(
            and_(
                Deal.streamer_id == deal.streamer_id,
                Deal.deal_type == "NN",
                Deal.open_status.is_(True),
            )
        )
    )
    if existing_nn:
        logger.info(
            "  [SKIP] Deal %s: streamer %s already has NN deal %s",
            deal.deal_id,
            deal.streamer_id,
            existing_nn.deal_id,
        )
        stats["skipped"] += 1
        return

    locked = await uow.deals.lock_deal(deal.deal_id)
    if locked == 0:
        logger.warning("  [SKIP] Deal %s: already locked", deal.deal_id)
        stats["skipped"] += 1
        return

    try:
        if deal.amount > 0:
            logger.warning(
                "  [WARN] Deal %s has remaining balance: %d kopecks. "
                "Closing deal — remaining goes to platform per Tinkoff rules.",
                deal.deal_id,
                deal.amount,
            )

        try:
            await tinkoff_client.close_deal(deal.deal_id)
            logger.info("  [OK] Closed deal %s at Tinkoff", deal.deal_id)
        except Exception as e:
            logger.warning(
                "  [WARN] Tinkoff close_deal failed for %s: %s. "
                "Proceeding with DB close.",
                deal.deal_id,
                e,
            )

        await uow.deals.close(deal.deal_id)
        logger.info("  [OK] Marked deal %s as closed in DB", deal.deal_id)

        new_deal_resp = await tinkoff_client.create_deal(deal_type="NN")
        new_deal_id = new_deal_resp.deal_id

        await uow.deals.create(
            streamer_id=deal.streamer_id,
            deal_id=new_deal_id,
            open_status=True,
            deal_type="NN",
            expires_at=get_utc_now() + timedelta(days=55),
        )
        logger.info(
            "  [OK] Created NN deal %s for streamer %s",
            new_deal_id,
            deal.streamer_id,
        )

        await uow.deals.unlock_deal(deal.deal_id)
        await session.commit()

        stats["migrated"] += 1

    except Exception:
        try:
            await uow.deals.unlock_deal(deal.deal_id)
            await session.commit()
        except Exception:
            await session.rollback()
        raise


async def migrate_n1_to_nn(dry_run: bool = False) -> dict[str, int]:
    """Migrate all active N1 deals to NN deals."""
    logger.info("Starting N1 -> NN migration (dry_run=%s)", dry_run)

    stats = {"total": 0, "migrated": 0, "skipped": 0, "failed": 0}

    async with db_helper.get_async_session_not_closed() as session:
        stmt = select(Deal).where(
            and_(
                Deal.open_status.is_(True),
                Deal.deal_type == "N1",
            )
        )
        result = await session.scalars(stmt)
        n1_deals = list(result.all())
        stats["total"] = len(n1_deals)

        logger.info("Found %d active N1 deals", stats["total"])

        if stats["total"] == 0:
            logger.info("No N1 deals to migrate. Done.")
            return stats

        if dry_run:
            for deal in n1_deals:
                existing_nn = await session.scalar(
                    select(Deal).where(
                        and_(
                            Deal.streamer_id == deal.streamer_id,
                            Deal.deal_type == "NN",
                            Deal.open_status.is_(True),
                        )
                    )
                )
                if existing_nn:
                    logger.info(
                        "  [DRY-RUN] [SKIP] Deal %s: streamer %s already has NN deal %s",
                        deal.deal_id,
                        deal.streamer_id,
                        existing_nn.deal_id,
                    )
                    stats["skipped"] += 1
                else:
                    logger.info(
                        "  [DRY-RUN] Would migrate deal %s (streamer=%s, amount=%s)",
                        deal.deal_id,
                        deal.streamer_id,
                        deal.amount,
                    )
                    stats["migrated"] += 1
            logger.info(
                "Dry run complete. %d deals would be migrated, %d skipped.",
                stats["migrated"],
                stats["skipped"],
            )
            return stats

        for deal in n1_deals:
            try:
                logger.info(
                    "Processing deal %s (streamer_id=%s, amount=%s)",
                    deal.deal_id,
                    deal.streamer_id,
                    deal.amount,
                )
                await _migrate_single_deal(session, deal, stats)
            except Exception as e:
                stats["failed"] += 1
                logger.error(
                    "  [ERROR] Deal %s: %s: %s",
                    deal.deal_id,
                    type(e).__name__,
                    e,
                )
                await session.rollback()
                continue

    logger.info("=" * 50)
    logger.info("Migration Summary:")
    logger.info("  Total N1 deals found: %d", stats["total"])
    logger.info("  Successfully migrated: %d", stats["migrated"])
    logger.info("  Skipped:               %d", stats["skipped"])
    logger.info("  Failed:                %d", stats["failed"])
    logger.info("=" * 50)

    if stats["failed"] > 0:
        logger.warning("Some deals failed to migrate. Please review the errors above.")

    return stats


def main():
    parser = argparse.ArgumentParser(
        description="Migrate N1 deals to NN multisplit deals",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without making changes",
    )
    args = parser.parse_args()

    asyncio.run(migrate_n1_to_nn(dry_run=args.dry_run))


if __name__ == "__main__":
    main()
