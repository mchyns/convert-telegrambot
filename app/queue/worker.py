import logging
import sys
from redis import Redis
from rq import Connection, Queue, Worker
from app.config.settings import settings
from app.queue.jobs import REDIS_QUEUE_NAME

logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("app.worker")


def run_worker() -> None:
    """Run RQ worker to process document conversion jobs."""
    logger.info(f"Starting conversion worker listening to '{REDIS_QUEUE_NAME}' on {settings.REDIS_URL}")
    redis_conn = Redis.from_url(settings.REDIS_URL)

    with Connection(redis_conn):
        worker = Worker([Queue(REDIS_QUEUE_NAME)])
        try:
            worker.work()
        except (KeyboardInterrupt, SystemExit):
            logger.info("Worker stopped by system signal.")


if __name__ == "__main__":
    run_worker()
