import sys
import pika


def callback(ch, method, properties, body):
    print(f" [x] Received {body} from {method.routing_key}")


if __name__ == '__main__':
    try:
        connection = pika.BlockingConnection(pika.ConnectionParameters('localhost', 5672, "/", pika.PlainCredentials("guest", "guest")))
        channel = connection.channel()
        channel.basic_consume(queue="queue_notifications",
                              auto_ack=True,
                              on_message_callback=callback)
        channel.basic_consume(queue="queue_messages",
                              auto_ack=True,
                              on_message_callback=callback)
        print(" [*] Waiting for messages. To exit press CTRL+C")
        channel.start_consuming()

    except KeyboardInterrupt:
        print('Interrupted')
        sys.exit(0)
