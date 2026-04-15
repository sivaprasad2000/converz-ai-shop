"""
Outbox worker — polls the outbox table for PENDING events and relays them to Elasticsearch.

Each iteration:
  1. Claim a batch of PENDING rows with SELECT ... FOR UPDATE (skip locked).
  2. For each row, dispatch to the appropriate ES handler.
  3. Mark the row SENT on success, FAILED (with incremented attempts) on error.
"""

import logging
import os
import time
from datetime import datetime, timezone

from app import create_app
from app.extensions import db
from app.models.outbox import Outbox, OutboxStatus

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [worker] %(levelname)s %(message)s",
)
log = logging.getLogger(__name__)

POLL_INTERVAL   = int(os.getenv("WORKER_POLL_INTERVAL",  "5"))   # seconds between polls
BATCH_SIZE      = int(os.getenv("WORKER_BATCH_SIZE",     "50"))  # rows per iteration
MAX_ATTEMPTS    = int(os.getenv("WORKER_MAX_ATTEMPTS",   "3"))   # give up after N failures


# ---------------------------------------------------------------------------
# Event handlers
# ---------------------------------------------------------------------------

def _handle_product_created(es, payload: dict) -> None:
    es.index(index="products", id=payload["id"], body=payload)


def _handle_product_updated(es, payload: dict) -> None:
    es.index(index="products", id=payload["id"], body=payload)


def _handle_product_deleted(es, payload: dict) -> None:
    es.delete(index="products", id=payload["id"], ignore=[404])


_HANDLERS = {
    "product.created": _handle_product_created,
    "product.updated": _handle_product_updated,
    "product.deleted": _handle_product_deleted,
}


# ---------------------------------------------------------------------------
# Core loop
# ---------------------------------------------------------------------------

def _utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def process_batch(app) -> int:
    """Process one batch of PENDING outbox rows. Returns the number processed."""
    processed = 0

    with app.app_context():
        es = app.elasticsearch

        # Claim rows — FOR UPDATE SKIP LOCKED prevents concurrent workers from
        # double-processing the same row.
        rows = (
            db.session.query(Outbox)
            .filter(
                Outbox.status == OutboxStatus.PENDING,
                Outbox.attempts < MAX_ATTEMPTS,
            )
            .order_by(Outbox.created_at)
            .limit(BATCH_SIZE)
            .with_for_update(skip_locked=True)
            .all()
        )

        for row in rows:
            handler = _HANDLERS.get(row.event_type)
            try:
                if handler is None:
                    raise ValueError(f"No handler for event_type '{row.event_type}'")
                handler(es, row.payload)
                row.status       = OutboxStatus.SENT
                row.processed_at = _utcnow()
                log.info("event_type=%s aggregate_id=%s → sent", row.event_type, row.aggregate_id)
            except Exception as exc:
                row.attempts += 1
                if row.attempts >= MAX_ATTEMPTS:
                    row.status = OutboxStatus.FAILED
                    log.error(
                        "event_type=%s aggregate_id=%s → failed (attempts=%d): %s",
                        row.event_type, row.aggregate_id, row.attempts, exc,
                    )
                else:
                    log.warning(
                        "event_type=%s aggregate_id=%s → retrying (attempt %d/%d): %s",
                        row.event_type, row.aggregate_id, row.attempts, MAX_ATTEMPTS, exc,
                    )
            processed += 1

        db.session.commit()

    return processed


def main() -> None:
    flask_env = os.getenv("FLASK_ENV", "development")
    app = create_app(flask_env)
    log.info("Outbox worker started (env=%s, batch=%d, poll=%ds)", flask_env, BATCH_SIZE, POLL_INTERVAL)

    while True:
        try:
            n = process_batch(app)
            if n:
                log.info("Processed %d outbox row(s)", n)
        except Exception as exc:
            log.exception("Unexpected error during batch: %s", exc)

        time.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    main()
