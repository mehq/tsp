import json
import time
from typing import Any, Dict, Optional

from tsp.utils.amqp import Consumer


def get_solution_from_queue(problem_id: str) -> Optional[Dict[str, Any]]:
    retry_count = 5
    result = None

    with Consumer() as consumer:
        while retry_count:
            method_frame, _, body = consumer.channel.basic_get(consumer.SOLUTION_QUEUE_NAME, auto_ack=False)

            if not method_frame or method_frame.NAME == "Basic.GetEmpty":
                time.sleep(0.1)
            else:
                json_body = json.loads(body)

                if json_body["id"] == problem_id:
                    consumer.channel.basic_ack(delivery_tag=method_frame.delivery_tag)

                    result = json_body["solution"]

            retry_count -= 1

    return result
