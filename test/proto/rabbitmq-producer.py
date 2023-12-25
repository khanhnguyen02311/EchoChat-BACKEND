import asyncio
import time

import pika
from pika.adapters.asyncio_connection import AsyncioConnection
import functools


class Proto:
    RMQ_HOST = "localhost"
    RMQ_PORT = 5672
    RMQ_USR = "echochatadmin"
    RMQ_PWD = "echochatadmin123"
    RMQ_QUEUE_NOTI = "queue_notifications"
    RMQ_QUEUE_MSG = "queue_messages"
    RMQ_EXCHANGE = "EchoChatBE"
    RMQ_ROUTING_KEY_NOTI = "notification"
    RMQ_ROUTING_KEY_MSG = "message"


class BEServicerRMQ(object):
    # old version missed heartbeat -> connection closed after 60s
    # https://stackoverflow.com/questions/70889479/how-to-use-pika-with-fastapis-asyncio-loop
    def __init__(self):
        self._credentials = pika.PlainCredentials(Proto.RMQ_USR, Proto.RMQ_PWD)
        self._parameters = pika.ConnectionParameters(Proto.RMQ_HOST, Proto.RMQ_PORT, "/", self._credentials)  # heartbeat=600, blocked_connection_timeout=300
        self._properties = pika.BasicProperties(content_type='application/json')
        self._connection = None
        self._channel = None

        self._message_amount = 0
        self._stopping = False

    def connect(self):
        # print("connection to rabbitmq")
        return AsyncioConnection(self._parameters,
                                 on_open_callback=self.on_connection_open,
                                 on_close_callback=self.on_connection_closed)

    def on_connection_open(self, connection):
        # print("connection opened")
        self._connection = connection
        self._connection.channel(on_open_callback=self.on_channel_open)

    def on_connection_closed(self, _unused_connection, reason):
        # print("connection closed")
        self._channel = None

    def on_channel_open(self, channel):
        # print("channel opened")
        self._channel = channel
        self._channel.add_on_close_callback(self.on_channel_closed)
        self.setup_exchange(Proto.RMQ_EXCHANGE)

    def on_channel_closed(self, channel, reason):
        # print("channel closed")
        self._channel = None
        if not self._stopping:
            self._connection.close()

    def setup_exchange(self, exchange_name):
        # print("setup exchange " + exchange_name)
        self._channel.exchange_declare(exchange=exchange_name, exchange_type="direct", durable=True, callback=self.on_exchange_declare_ok)

    def on_exchange_declare_ok(self, _unused_frame):
        # print("exchange declared")
        # pass through a pair of queue and corresponding routing key
        cb_with_value_noti = functools.partial(self.on_queue_declare_ok, queue_route=[Proto.RMQ_QUEUE_NOTI, Proto.RMQ_ROUTING_KEY_NOTI])
        self._channel.queue_declare(queue=Proto.RMQ_QUEUE_NOTI,
                                    durable=True, exclusive=False, auto_delete=False,
                                    callback=cb_with_value_noti)
        for i in range(100000):
            print(i)
            self.send_data("notification",
                           "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa" +
                           "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa" +
                           "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa")  # 256 bytes

    def on_queue_declare_ok(self, _unused_frame, queue_route):
        # print("queue declared: " + queue_route[0] + " with routing key " + queue_route[1] + " bound to exchange " + Proto.RMQ_EXCHANGE)
        self._channel.queue_bind(queue_route[0], Proto.RMQ_EXCHANGE, routing_key=queue_route[1])

    def send_data(self, routing, data):
        if self._channel is None or not self._channel.is_open:
            return
        self._channel.basic_publish(exchange=Proto.RMQ_EXCHANGE, routing_key=routing, body=data, properties=self._properties)
        self._message_amount += 1

    def close_connection(self):
        # print("connection closed")
        self._stopping = True
        if self._connection is not None:
            self._connection.close()


rmq = BEServicerRMQ()


async def init_rmq():
    rmq.connect()
    await asyncio.sleep(20)


if __name__ == "__main__":
    asyncio.run(init_rmq())
