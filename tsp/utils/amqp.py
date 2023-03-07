import abc

import pika
import pika.exceptions
from django.conf import settings


class AMQPBase(abc.ABC):
    PROBLEM_QUEUE_NAME = "tspproblems"
    SOLUTION_QUEUE_NAME = "tspsolutions"

    def __init__(self) -> None:
        self.connection: pika.BlockingConnection = pika.BlockingConnection(
            pika.URLParameters(settings.RABBITMQ_URL),
        )
        self.channel: pika.adapters.blocking_connection.BlockingChannel = self.connection.channel()

        self.channel.queue_declare(queue=self.PROBLEM_QUEUE_NAME, durable=True)
        self.channel.queue_declare(queue=self.SOLUTION_QUEUE_NAME, durable=True)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        del exc_type, exc_val, exc_tb

        self.close()

    def close(self) -> None:
        try:
            if self.connection.is_open:
                self.connection.close()

            if self.channel.is_open:
                self.channel.close()
        except pika.exceptions.AMQPError:
            pass


class Publisher(AMQPBase):
    def publish_problem(self, body: bytes) -> None:
        self.channel.basic_publish(exchange="", routing_key=self.PROBLEM_QUEUE_NAME, body=body)

    def publish_solution(self, body: bytes) -> None:
        self.channel.basic_publish(exchange="", routing_key=self.SOLUTION_QUEUE_NAME, body=body)


class Consumer(AMQPBase):
    def consume_problem(self, callback) -> None:
        self.channel.basic_consume(self.PROBLEM_QUEUE_NAME, on_message_callback=callback)
        self.channel.start_consuming()

    def consume_solution(self, callback) -> None:
        self.channel.basic_consume(self.SOLUTION_QUEUE_NAME, on_message_callback=callback)
        self.channel.start_consuming()
