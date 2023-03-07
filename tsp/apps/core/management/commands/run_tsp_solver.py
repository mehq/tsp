"""
TSP-solving background worker's run command.
"""
import json
import logging
import socket

import pika.exceptions
from django.core.management.base import BaseCommand
from pika.adapters.blocking_connection import BlockingChannel
from pika.spec import Basic, BasicProperties

from tsp.utils.amqp import Consumer, Publisher
from tsp.utils.common import retry_with_backoff
from tsp.utils.tsplib import find_route

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    def add_arguments(self, parser):
        # Named (optional) arguments
        parser.add_argument(
            "--max-retry",
            default=5,
            type=int,
            help="Maximum number of retries for establishing consumer connection.",
        )

    @staticmethod
    def _solve_problem(channel: BlockingChannel, method: Basic.Deliver, properties: BasicProperties, body: bytes):
        del properties

        problem = json.loads(body)
        problem_id = problem["id"]
        problem_data = problem["problem"]

        try:
            with Publisher() as publisher:
                publisher.publish_solution(
                    json.dumps(
                        {
                            "id": problem_id,
                            "solution": find_route(
                                problem_data["locations"],
                                problem_data.get("time_windows"),
                                problem_data.get("depot", 0),
                                problem_data.get("num_vehicles", 1),
                            ),
                        }
                    ).encode()
                )

            channel.basic_ack(delivery_tag=method.delivery_tag)

            logger.info("Solved problem with id: %s", problem_id)
        except Exception:  # pylint:disable=broad-except
            logger.error("Could not solve problem with id: %s", problem_id, exc_info=True, stack_info=True)

    def _real_handle(self):
        try:
            with Consumer() as consumer:
                consumer.consume_problem(self._solve_problem)
        except KeyboardInterrupt:
            consumer.close()

    def handle(self, *args, **options):
        max_retry = options["max_retry"]

        return retry_with_backoff(
            self._real_handle, retries=max_retry, exceptions=(pika.exceptions.AMQPError, socket.gaierror)
        )
