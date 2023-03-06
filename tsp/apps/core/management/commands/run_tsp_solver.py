"""
TSP-solving background worker's run command.
"""
import json

from django.core.management.base import BaseCommand
from pika.adapters.blocking_connection import BlockingChannel
from pika.spec import Basic, BasicProperties

from tsp.utils.amqp import Consumer, Publisher
from tsp.utils.tsplib import find_route

publisher = Publisher()


class Command(BaseCommand):
    @staticmethod
    def _solve_problem(channel: BlockingChannel, method: Basic.Deliver, properties: BasicProperties, body: bytes):
        del properties

        problem = json.loads(body)
        problem_data = problem["problem"]

        publisher.publish_solution(
            json.dumps(
                {
                    "id": problem["id"],
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

    def handle(self, *args, **options):
        consumer = None

        try:
            consumer = Consumer()

            consumer.consume_problem(self._solve_problem)
        except KeyboardInterrupt:
            if consumer:
                consumer.close()
