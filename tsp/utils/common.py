import logging
import random
from time import sleep
from typing import Any, Callable, Tuple, Type

logger = logging.getLogger(__name__)


def retry_with_backoff(
    func: Callable,
    retries: int = 5,
    backoff_in_seconds: float = 1,
    exceptions: Tuple[Type[Exception], ...] = (Exception,),
) -> Any:
    x = 0

    while True:
        try:
            return func()
        except exceptions:
            if x == retries:
                logger.error("Max retry reached, re-raising original exception")
                raise

            sleep_time = backoff_in_seconds * 2**x + random.uniform(0, 1)  # nosec

            sleep(sleep_time)

            logger.warning("Exception encountered, will retry in %.2f seconds", sleep_time)

            x += 1
