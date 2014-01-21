from boto.sqs.connection import SQSConnection
# from boto.sqs.message import Message
from boto.sqs.jsonmessage import JSONMessage


def pop_loop(queue='pi-status', wait=5):
    # like pop(), but iterate
    sqs = SQSConnection()
    sqs_queue = sqs.create_queue(queue)

    while True:
        message = sqs_queue.read(wait_time_seconds=wait)
        if message is not None:
            body = message.get_body()
            message.delete()
            yield body


def pop(queue='pi-status', ):
    '''
    Pop the next Message off the queue, immediately delete it
    (mark it as consumed), and return the body string.

    Presumably, these will be a JSONMessage instances, and get_body() will return a dict/list/etc.
    '''
    sqs = SQSConnection()
    sqs_queue = sqs.create_queue(queue)

    message = sqs_queue.read()
    if message is not None:
        body = message.get_body()
        message.delete()
        return body


def push(body, queue='pi-status'):
    '''
    Create a JSON-encoded boto-style Message object and write it to the queue.
    '''
    sqs = SQSConnection()
    sqs_queue = sqs.create_queue(queue)

    message = JSONMessage(body=body)
    sqs_queue.write(message)
