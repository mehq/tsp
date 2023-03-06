import threading
from time import sleep

import pika
import pika.exceptions
from django.conf import settings

from .common import Singleton

lock = threading.Lock()


class AMQPBase(metaclass=Singleton):
    PROBLEM_QUEUE_NAME = "tspproblems"
    SOLUTION_QUEUE_NAME = "tspsolutions"

    def __init__(self) -> None:
        self.connection: pika.BlockingConnection = self.get_connection()
        self.channel: pika.adapters.blocking_connection.BlockingChannel = self.get_channel()

        self.init_queues()

    def init_queues(self) -> None:
        self.channel = self.get_channel()
        self.channel.queue_declare(queue=self.PROBLEM_QUEUE_NAME, durable=True)
        self.channel.queue_declare(queue=self.SOLUTION_QUEUE_NAME, durable=True)

    @staticmethod
    def get_connection() -> pika.BlockingConnection:
        """
        Returns a rabbitmq connection.

        NOTE: Retry is useful when running inside containers as rabbitmq
        container will take time to boot up.
        """
        max_retries = 5
        retry_count = 0

        while True:
            try:
                return pika.BlockingConnection(
                    pika.URLParameters(settings.RABBITMQ_URL),
                )
            except pika.exceptions.AMQPConnectionError:
                if retry_count > max_retries:
                    raise

                sleep(1.5)

                retry_count += 1

    def get_channel(self) -> pika.adapters.blocking_connection.BlockingChannel:
        return self.connection.channel()

    def close(self) -> None:
        if self.connection and self.connection.is_open:
            self.connection.close()


class Publisher(AMQPBase, metaclass=Singleton):
    def publish_problem(self, body: bytes) -> None:
        if self.channel:
            self.channel.basic_publish(exchange="", routing_key=self.PROBLEM_QUEUE_NAME, body=body)

    def publish_solution(self, body: bytes) -> None:
        if self.channel:
            self.channel.basic_publish(exchange="", routing_key=self.SOLUTION_QUEUE_NAME, body=body)

    def close(self) -> None:
        with lock:
            super().close()

            if self.channel.is_open:
                self.channel.close()


class Consumer(AMQPBase):
    def consume_problem(self, callback) -> None:
        if self.channel:
            self.channel.basic_consume(self.PROBLEM_QUEUE_NAME, on_message_callback=callback)
            self.channel.start_consuming()

    def consume_solution(self, callback) -> None:
        if self.channel:
            self.channel.basic_consume(self.SOLUTION_QUEUE_NAME, on_message_callback=callback)
            self.channel.start_consuming()

    def close(self) -> None:
        with lock:
            super().close()

            self.channel.stop_consuming()

            if self.channel.is_open:
                self.channel.close()
