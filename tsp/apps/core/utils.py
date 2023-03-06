import json
import time
from typing import Any, Dict, Optional

from tsp.utils.amqp import Consumer


def get_solution_delay(problem_id: str) -> Optional[Dict[str, Any]]:
    consumer = Consumer()
    retry_count = 5
    channel = consumer.get_channel()
    result = None

    while retry_count:
        method_frame, _, body = channel.basic_get(consumer.SOLUTION_QUEUE_NAME, auto_ack=False)

        if not method_frame or method_frame.NAME == "Basic.GetEmpty":
            time.sleep(0.1)
        else:
            json_body = json.loads(body)

            if json_body["id"] == problem_id:
                channel.basic_ack(delivery_tag=method_frame.delivery_tag)

                result = json_body["solution"]

        retry_count -= 1

    if channel.is_open:
        channel.close()

    return result
