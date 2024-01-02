import asyncio
import pika
from pika import exceptions
from pika.adapters.asyncio_connection import AsyncioConnection
import functools
from configurations.conf import Proto


# class BEServicerRMQ(object):
#     def __init__(self):
#         self._credentials = pika.PlainCredentials(Proto.RMQ_USR, Proto.RMQ_PWD)
#         self._parameters = pika.ConnectionParameters('localhost', Proto.RMQ_PORT, "/", self._credentials,
#                                                      heartbeat=600,
#                                                      blocked_connection_timeout=300)
#         self._properties = pika.BasicProperties(app_id='EchoChat-BE',
#                                                 content_type='application/json')
#
#         self._connection = None
#         self._channel = None
#
#     def connect(self):
#         self._connection = pika.BlockingConnection(self._parameters)
#         self._channel = self._connection.channel()
#         self._channel.exchange_declare(exchange=Proto.RMQ_EXCHANGE, exchange_type='direct')
#         self._channel.queue_declare(queue=Proto.RMQ_QUEUE_NOTI,
#                                     durable=True,
#                                     exclusive=False,
#                                     auto_delete=False)
#         self._channel.queue_declare(queue=Proto.RMQ_QUEUE_MSG,
#                                     durable=True,
#                                     exclusive=False,
#                                     auto_delete=False)
#         self._channel.queue_bind(queue=Proto.RMQ_QUEUE_NOTI,
#                                  exchange=Proto.RMQ_EXCHANGE,
#                                  routing_key=Proto.RMQ_ROUTING_KEY_NOTI)
#         self._channel.queue_bind(queue=Proto.RMQ_QUEUE_MSG,
#                                  exchange=Proto.RMQ_EXCHANGE,
#                                  routing_key=Proto.RMQ_ROUTING_KEY_MSG)
#
#     def send_data(self, routing, data):
#         self._channel.basic_publish(exchange=Proto.RMQ_EXCHANGE, routing_key=routing, body=data, properties=self._properties)
#
#     def close_connection(self):
#         if self._connection is not None:
#             self._channel = None
#             self._connection.close()


class BEServicerRMQ(object):
    SLEEP_INTERVAL = 1

    # last version missed heartbeat -> connection closed after 60s
    # https://stackoverflow.com/questions/70889479/how-to-use-pika-with-fastapis-asyncio-loop
    def __init__(self):
        self._credentials = pika.PlainCredentials(Proto.RMQ_USR, Proto.RMQ_PWD)
        self._parameters = pika.ConnectionParameters(Proto.RMQ_HOST, Proto.RMQ_PORT, "/", self._credentials, heartbeat=0)
        self._properties = pika.BasicProperties(content_type='application/json')
        self._connection = None
        self._channel = None
        self._stopping = False

    def _connect(self):
        self._stopping = False
        # print("connection to rabbitmq")
        return AsyncioConnection(self._parameters,
                                 on_open_callback=self._on_connection_open,
                                 on_close_callback=self._on_connection_closed).channel().basic_publish()

    def _on_connection_open(self, connection):
        print("RabbitMQ: Connection opened")
        self._connection = connection
        self._connection.channel(on_open_callback=self._on_channel_open)

    def _on_connection_closed(self, _unused_connection, exception):
        print("RabbitMQ: Connection closed:", type(exception), exception)
        self._channel = None
        if not self._stopping:
            self._connection = self._connect()

    def _on_channel_open(self, channel):
        print("RabbitMQ: Channel opened")
        self._channel = channel
        self._channel.confirm_delivery(self._on_delivery_confirmation)
        self._channel.add_on_close_callback(self._on_channel_closed)
        self._setup_exchange(Proto.RMQ_EXCHANGE)

    def _on_channel_closed(self, channel, reason):
        print("RabbitMQ: Channel closed:", type(reason), reason)
        # self._channel = None
        # self.stop()
        if not self._stopping:
            self._connection = self._connect()
        else:
            self.stop()

    def _on_delivery_confirmation(self, method_frame):
        confirmation_type = method_frame.method.NAME.split('.')[1].lower()
        if confirmation_type == 'ack':
            print("RabbitMQ: Message published")
        elif confirmation_type == 'nack':
            print("RabbitMQ: Message not published")
        else:
            print("RabbitMQ: Unknown confirmation type:", confirmation_type)

    def _setup_exchange(self, exchange_name):
        # print("setup exchange " + exchange_name)
        self._channel.exchange_declare(exchange=exchange_name, exchange_type="direct", durable=True, callback=self._on_exchange_declare_ok)

    def _on_exchange_declare_ok(self, _unused_frame):
        # print("exchange declared")
        # pass through a pair of queue and corresponding routing key
        cb_with_value_noti = functools.partial(self._on_queue_declare_ok, queue_route=[Proto.RMQ_QUEUE_NOTI, Proto.RMQ_ROUTING_KEY_NOTI])
        cb_with_value_msg = functools.partial(self._on_queue_declare_ok, queue_route=[Proto.RMQ_QUEUE_MSG, Proto.RMQ_ROUTING_KEY_MSG])
        self._channel.queue_declare(queue=Proto.RMQ_QUEUE_NOTI,
                                    durable=True, exclusive=False, auto_delete=False,
                                    callback=cb_with_value_noti)
        self._channel.queue_declare(queue=Proto.RMQ_QUEUE_MSG,
                                    durable=True, exclusive=False, auto_delete=False,
                                    callback=cb_with_value_msg)

    def _on_queue_declare_ok(self, _unused_frame, queue_route):
        # print("queue declared: " + queue_route[0] + " with routing key " + queue_route[1] + " bound to exchange " + Proto.RMQ_EXCHANGE)
        self._channel.queue_bind(queue_route[0], Proto.RMQ_EXCHANGE, routing_key=queue_route[1])

    def run(self):
        print("RabbitMQ producer is starting...")
        self._connection = self._connect()

    def stop(self):
        print("RabbitMQ producer is stopping...")
        self._stopping = True
        if self._connection is not None and not self._connection.is_closing:
            self._connection.close()

    def send_data(self, routing, data):
        if self._connection is None or not self._connection.is_open:
            print("RabbitMQ: Send data failed. Connection is not open.")
            return
        if self._channel is None or not self._channel.is_open:
            print("RabbitMQ: Send data failed. Channel is not open.")
            return
        try:
            self._channel.basic_publish(exchange=Proto.RMQ_EXCHANGE, routing_key=routing, body=data, properties=self._properties)
        except (exceptions.ChannelClosed, exceptions.ConnectionClosed, exceptions.AMQPError, exceptions.AMQPChannelError, exceptions.AMQPConnectionError) as e:
            print("RabbitMQ: Send data failed. Reconnecting..., exception:", type(e), e)
            self._connection = self._connect()
        except Exception as e:
            print("RabbitMQ: Send data failed. Reconnecting..., exception:", type(e), e)
            self._connection = self._connect()


RabbitMQService = BEServicerRMQ()

# class BEServicerRMQ(object):
#     # Last version have some problems with long operations that shut the service off in the middle
#     PUBLIC_INTERVAL = 0.1
#
#     def __init__(self):
#         self._credentials = pika.PlainCredentials(Proto.RMQ_USR, Proto.RMQ_PWD)
#         self._parameters = pika.ConnectionParameters(Proto.RMQ_HOST, Proto.RMQ_PORT, "/", self._credentials, heartbeat=0)
#         self._properties = pika.BasicProperties(content_type='application/json')
#         self._connection = None
#         self._channel = None
#         self._stopping = False
#
#     def _connect(self):
#         self._connection = pika.SelectConnection(parameters=self._parameters,
#                                                  on_open_callback=self._on_connection_open,
#                                                  on_open_error_callback=self._on_connection_open_error,
#                                                  on_close_callback=self._on_connection_closed)
#
#     def _on_connection_open(self, unused_connection):
#         self._connection.channel(on_open_callback=self._on_channel_open)
#
#     def _on_connection_closed(self, connection, reply_code, reply_text):
#         """This method is invoked by pika when the connection to RabbitMQ is
#         closed unexpectedly. Since it is unexpected, we will reconnect to
#         RabbitMQ if it disconnects.
#
#         :param pika.connection.Connection connection: The closed connection obj
#         :param int reply_code: The server provided reply_code if given
#         :param str reply_text: The server provided reply_text if given
#
#         """
#         print('RabbitMQ: Connection closed, reopening in 2 seconds: (%s) %s', reply_code, reply_text)
#         self._channel = None
#         if self._stopping:
#             self._connection.ioloop.stop()
#         else:
#             self._connection.add_timeout(2, self._connection.ioloop.stop)
#
#     def _on_connection_open_error(self, unused_connection, err):
#         print("RabbitMQ: Connection open failed, reopening in 2 seconds:", type(err), err)
#         self._connection.ioloop.call_later(2, self._connection.ioloop.stop)
#
#     def _on_channel_open(self, channel):
#         """This method is invoked by pika when the channel has been opened.
#         The channel object is passed in, so we can make use of it.
#
#         Since the channel is now open, we'll declare the exchange to use.
#
#         :param pika.channel.Channel channel: The channel object
#
#         """
#         self._channel = channel
#         self._channel.add_on_close_callback(self._on_channel_closed)
#         self._setup_exchange(Proto.RMQ_EXCHANGE)
#
#     def _on_channel_closed(self, channel, reason):
#         print("RabbitMQ: Channel closed:", type(reason), reason)
#         # self._channel = None
#         # self.stop()
#         if not self._stopping:
#             self._connect()
#         else:
#             self._connection.close()
#
#     def _setup_exchange(self, exchange_name):
#         # print("setup exchange " + exchange_name)
#         self._channel.exchange_declare(exchange=exchange_name, exchange_type="direct", durable=True, callback=self._on_exchange_declare_ok)
#
#     def _on_exchange_declare_ok(self, _unused_frame):
#         # pass through a pair of queue and corresponding routing key
#         cb_with_value_noti = functools.partial(self._on_queue_declare_ok, queue_route=[Proto.RMQ_QUEUE_NOTI, Proto.RMQ_ROUTING_KEY_NOTI])
#         cb_with_value_msg = functools.partial(self._on_queue_declare_ok, queue_route=[Proto.RMQ_QUEUE_MSG, Proto.RMQ_ROUTING_KEY_MSG])
#         self._channel.queue_declare(queue=Proto.RMQ_QUEUE_NOTI,
#                                     durable=True, exclusive=False, auto_delete=False,
#                                     callback=cb_with_value_noti)
#         self._channel.queue_declare(queue=Proto.RMQ_QUEUE_MSG,
#                                     durable=True, exclusive=False, auto_delete=False,
#                                     callback=cb_with_value_msg)
#
#     def _on_queue_declare_ok(self, _unused_frame, queue_route):
#         self._channel.queue_bind(queue_route[0], Proto.RMQ_EXCHANGE, routing_key=queue_route[1])
#
#     def _schedule_next_message(self):
#         """If we are not closing our connection to RabbitMQ, schedule another
#         message to be delivered in PUBLISH_INTERVAL seconds.
#
#         """
#         self._connection.add_timeout(self.PUBLIC_INTERVAL,
#                                      self.send_data)
#
#     def run(self):
#         print("RabbitMQ producer is starting...")
#         self._connection = None
#         try:
#             self._connect()
#             self._connection.ioloop.start()
#         except KeyboardInterrupt:
#             self.stop()
#             if self._connection is not None and not self._connection.is_closed:
#                 # Finish closing
#                 self._connection.ioloop.start()
#
#     def stop(self):
#         print("RabbitMQ producer is stopping...")
#         self._stopping = True
#         if self._channel is not None and self._channel.is_open:
#             self._channel.close()
#         if self._connection is not None and self._connection.is_open:
#             self._connection.close()
#
#     def send_data(self, routing, data):
#         if self._connection is None or not self._connection.is_open:
#             print("RabbitMQ: Send data failed. Connection is not open.")
#             return
#         if self._channel is None or not self._channel.is_open:
#             print("RabbitMQ: Send data failed. Channel is not open.")
#             return
#         self._channel.basic_publish(exchange=Proto.RMQ_EXCHANGE, routing_key=routing, body=data, properties=self._properties)
#         self._schedule_next_message()
