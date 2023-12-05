import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(thread)d:%(threadName)s] [%(levelname)s] - %(message)s",
)

logger = logging.getLogger("saver")
